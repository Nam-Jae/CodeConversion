"""AnalyzerAgent - Uses LLM to discover transformation rules from XML pairs."""

from __future__ import annotations

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common import (
    AnalysisResult,
    FieldMapping,
    LLMClient,
    TransformationRule,
    XmlPair,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert XML transformation analyst. Your job is to compare XML input/output \
pairs and discover the complete set of rules that transform the input XML into the \
output XML.

Analyze the provided XML pairs carefully and produce a comprehensive set of \
transformation rules. You must examine every aspect of the transformation:

## 1. Structural Analysis
- Compare the root element and overall hierarchy of input vs output.
- Identify which input elements map to which output elements.
- Note any structural reorganization (flattening nested structures, grouping flat \
elements, reordering).

## 2. Field Mappings
Identify every field mapping between input and output. Classify each as:
- **1:1 mapping**: A single input field maps directly to a single output field \
(may involve a rename or path change).
- **1:N mapping**: A single input field is used in multiple output fields \
(value duplication, splitting).
- **N:1 mapping**: Multiple input fields are combined into a single output field \
(concatenation, aggregation, calculation).
- **constant**: An output field has a fixed value not derived from any input field.

For each mapping, provide the full XPath-like source and target paths.

## 3. Value Transformations
Detect any value changes between mapped fields:
- **Format changes**: Date format conversions (e.g., YYYY-MM-DD to MM/DD/YYYY), \
number formatting, string case changes (upper, lower, title).
- **Calculations**: Arithmetic operations (multiplication, division, sum, etc.) \
applied to numeric values.
- **Code mappings**: Enumerated value translations (e.g., "M" -> "Male", \
"USD" -> "US Dollar", status code translations).
- **String operations**: Trimming, padding, substring extraction, concatenation \
with literals, regex replacements.
- **Type conversions**: String to number, number to string with formatting, \
boolean to string.

## 4. Conditional Logic
Identify any rules that apply conditionally:
- If a field's presence or value determines which mapping to use.
- Default values that apply when an input field is missing or empty.
- Conditional inclusion/exclusion of output elements.

## 5. Constants and Defaults
- Output fields that always have the same value regardless of input.
- Default values used when input data is absent.
- Hardcoded metadata (timestamps, version numbers, static identifiers).

## 6. Collection/Repeating Element Handling
- How repeating input elements map to output collections.
- Any filtering, sorting, or grouping of repeated elements.
- Aggregation over collections (count, sum, min, max).

## 7. Namespace and Attribute Handling
- Namespace additions, removals, or changes.
- Attribute-to-element or element-to-attribute conversions.
- Attribute value transformations.

## Output Format
Return your analysis as a JSON object with this exact structure:

```json
{
  "field_mappings": [
    {
      "source_path": "InputRoot/Element/SubElement",
      "target_path": "OutputRoot/Element/SubElement",
      "mapping_type": "1:1",
      "description": "Human-readable description of this mapping"
    }
  ],
  "transformation_rules": [
    {
      "rule_type": "field_mapping | value_transform | conditional | aggregation | constant | sort",
      "description": "Detailed human-readable description of the rule",
      "details": {
        "source_path": "...",
        "target_path": "...",
        "operation": "description of the specific operation",
        "parameters": {}
      }
    }
  ],
  "input_schema_summary": "Brief description of the input XML structure and purpose",
  "output_schema_summary": "Brief description of the output XML structure and purpose",
  "notes": "Any additional observations, edge cases, or ambiguities"
}
```

## Important Guidelines
- Be exhaustive. Every output field must be accounted for by a mapping or constant rule.
- Be precise with paths. Use the actual element names from the XML.
- When multiple pairs are provided, look for patterns that are consistent across \
ALL pairs. Use differences between pairs to confirm conditional logic.
- If a transformation is ambiguous from a single pair, note this in the "notes" field.
- Return ONLY the JSON object, no markdown fences, no extra text.
"""


def _build_user_prompt(xml_pairs: list[XmlPair], feedback: str = "") -> str:
    """Build the user prompt containing all XML pairs for analysis."""
    sections: list[str] = []
    sections.append(
        f"Analyze the following {len(xml_pairs)} XML input/output pair(s) and "
        "discover all transformation rules.\n"
    )

    for i, pair in enumerate(xml_pairs, 1):
        sections.append(f"--- Pair {i} (ID: {pair.pair_id}) ---")
        sections.append(f"INPUT XML:\n{pair.input_xml.strip()}")
        sections.append(f"OUTPUT XML:\n{pair.output_xml.strip()}")
        sections.append("")

    if feedback:
        sections.append("=" * 60)
        sections.append("IMPORTANT - FEEDBACK FROM PREVIOUS ITERATION:")
        sections.append(
            "The previous analysis led to generated code that FAILED testing. "
            "Review the errors below carefully and produce CORRECTED rules that "
            "address every failure. Pay close attention to the diff output — it "
            "shows exactly where the generated code produced wrong results.\n"
        )
        sections.append(feedback)
        sections.append("=" * 60)
        sections.append("")

    sections.append(
        "Return a complete JSON analysis covering field mappings, transformation "
        "rules, schema summaries, and notes."
    )
    return "\n".join(sections)


def _extract_json(text: str) -> dict:
    """Extract a JSON object from LLM response text, handling markdown fences."""
    cleaned = text.strip()

    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        # Remove opening fence (with optional language tag)
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1 :]
        # Remove closing fence
        if cleaned.endswith("```"):
            cleaned = cleaned[: -len("```")]
        cleaned = cleaned.strip()

    return json.loads(cleaned)


class AnalyzerAgent:
    """Agent that uses an LLM to analyze XML input/output pairs and discover
    transformation rules."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    async def analyze(self, xml_pairs: list[XmlPair], feedback: str = "") -> AnalysisResult:
        """Analyze XML pairs and return structured transformation rules.

        Args:
            xml_pairs: List of input/output XML pairs to analyze.
            feedback: Optional feedback from a previous failed test iteration.

        Returns:
            AnalysisResult containing discovered field mappings and rules.
        """
        user_prompt = _build_user_prompt(xml_pairs, feedback=feedback)

        logger.info("Sending %d XML pair(s) to LLM for analysis", len(xml_pairs))
        raw_response = await self.llm_client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=8192,
            temperature=0.0,
        )
        logger.debug("Raw LLM response length: %d characters", len(raw_response))

        return self._parse_response(raw_response)

    def _parse_response(self, raw_response: str) -> AnalysisResult:
        """Parse the LLM JSON response into an AnalysisResult model."""
        try:
            data = _extract_json(raw_response)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            logger.debug("Raw response:\n%s", raw_response)
            return AnalysisResult(
                notes=f"LLM response was not valid JSON. Raw response:\n{raw_response}"
            )

        # Build FieldMapping list
        field_mappings: list[FieldMapping] = []
        for fm in data.get("field_mappings", []):
            try:
                field_mappings.append(
                    FieldMapping(
                        source_path=fm.get("source_path", ""),
                        target_path=fm.get("target_path", ""),
                        mapping_type=fm.get("mapping_type", "1:1"),
                        description=fm.get("description", ""),
                    )
                )
            except Exception as e:
                logger.warning("Skipping invalid field mapping %s: %s", fm, e)

        # Build TransformationRule list
        transformation_rules: list[TransformationRule] = []
        for tr in data.get("transformation_rules", []):
            try:
                transformation_rules.append(
                    TransformationRule(
                        rule_type=tr.get("rule_type", "field_mapping"),
                        description=tr.get("description", ""),
                        details=tr.get("details", {}),
                    )
                )
            except Exception as e:
                logger.warning("Skipping invalid transformation rule %s: %s", tr, e)

        return AnalysisResult(
            field_mappings=field_mappings,
            transformation_rules=transformation_rules,
            input_schema_summary=data.get("input_schema_summary", ""),
            output_schema_summary=data.get("output_schema_summary", ""),
            notes=data.get("notes", ""),
        )
