"""Generator Agent - Uses an LLM to produce Python XML transformation code."""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common import AnalysisResult, GeneratedCode, LLMClient, XmlPair

SYSTEM_PROMPT = """\
You are an expert Python developer specialising in XML transformations.

Your task is to generate a **complete, self-contained** Python function with the
following signature:

    def transform_xml(input_xml: str) -> str

Requirements:
- Use only the Python standard library (xml.etree.ElementTree in particular).
- The function receives a raw XML string, applies the transformation described
  by the specification below, and returns the resulting XML as a string.
- The output XML must be well-formed and match the expected output structure
  exactly (element names, nesting, ordering, text values, and attributes).
- Include all necessary imports **inside** the function so it is fully
  self-contained and can be imported and called independently.
- Do NOT read from or write to files; operate entirely on the provided string.
- Return the XML string with an XML declaration (<?xml version='1.0' …?>)
  only if the expected output includes one; otherwise omit it.
- Wrap your code in a single ```python code block.
"""

USER_PROMPT_TEMPLATE = """\
## Transformation Specification

### Input Schema Summary
{input_schema}

### Output Schema Summary
{output_schema}

### Field Mappings
{field_mappings}

### Transformation Rules
{rules}

### Additional Notes
{notes}

## XML Sample Pairs (input -> expected output)
{xml_pairs}
{feedback_section}
Generate the `transform_xml` function now.
"""

FEEDBACK_SECTION_TEMPLATE = """
## Feedback from Previous Attempt
The previously generated code **failed** testing.  Use the feedback below to
diagnose and fix the issues.

{feedback}
"""


class GeneratorAgent:
    """Generates Python transformation code via an LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    async def generate(
        self,
        analysis: AnalysisResult,
        xml_pairs: list[XmlPair],
        feedback: str = "",
    ) -> GeneratedCode:
        """Produce a GeneratedCode object containing a transform_xml function."""

        user_prompt = self._build_user_prompt(analysis, xml_pairs, feedback)
        llm_response = await self.llm_client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=8192,
            temperature=0.0,
        )
        code = self._extract_code(llm_response)
        description = self._extract_description(llm_response, code)

        return GeneratedCode(
            code=code,
            language="python",
            description=description,
            iteration=1,
        )

    # ------------------------------------------------------------------
    # Prompt construction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_user_prompt(
        analysis: AnalysisResult,
        xml_pairs: list[XmlPair],
        feedback: str,
    ) -> str:
        field_mappings = "\n".join(
            f"- {m.source_path} -> {m.target_path} ({m.mapping_type})"
            + (f"  # {m.description}" if m.description else "")
            for m in analysis.field_mappings
        ) or "None specified."

        rules = "\n".join(
            f"- [{r.rule_type}] {r.description}"
            + (f"  Details: {r.details}" if r.details else "")
            for r in analysis.transformation_rules
        ) or "None specified."

        pairs_text = ""
        for idx, pair in enumerate(xml_pairs, 1):
            pairs_text += (
                f"### Pair {idx} (id={pair.pair_id})\n"
                f"**Input XML:**\n```xml\n{pair.input_xml.strip()}\n```\n\n"
                f"**Expected Output XML:**\n```xml\n{pair.output_xml.strip()}\n```\n\n"
            )

        feedback_section = ""
        if feedback:
            feedback_section = FEEDBACK_SECTION_TEMPLATE.format(feedback=feedback)

        return USER_PROMPT_TEMPLATE.format(
            input_schema=analysis.input_schema_summary or "Not provided.",
            output_schema=analysis.output_schema_summary or "Not provided.",
            field_mappings=field_mappings,
            rules=rules,
            notes=analysis.notes or "None.",
            xml_pairs=pairs_text or "No sample pairs provided.",
            feedback_section=feedback_section,
        )

    # ------------------------------------------------------------------
    # Response parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_code(llm_response: str) -> str:
        """Extract Python code from the LLM response.

        Looks for fenced code blocks (```python ... ```) and falls back to the
        full response if no code block is found.
        """
        # Try ```python ... ``` first
        pattern = r"```python\s*\n(.*?)```"
        match = re.search(pattern, llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try generic ``` ... ```
        pattern = r"```\s*\n(.*?)```"
        match = re.search(pattern, llm_response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback: return the full response stripped
        return llm_response.strip()

    @staticmethod
    def _extract_description(llm_response: str, code: str) -> str:
        """Try to pull a brief description from text outside the code block."""
        # Remove code block(s) to isolate commentary
        cleaned = re.sub(r"```[\s\S]*?```", "", llm_response).strip()
        if cleaned:
            # Take at most the first 500 characters as a description
            return cleaned[:500].strip()
        return "Auto-generated XML transformation code."
