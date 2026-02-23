from __future__ import annotations

import builtins as _real_builtins
import os
import sys
import traceback
import types
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common import XmlPair, TestResult, TestDetail, compare_xml, xml_diff_report


# Modules that generated code is allowed to import
SAFE_MODULES = {
    "xml",
    "xml.etree",
    "xml.etree.ElementTree",
    "xml.dom",
    "xml.dom.minidom",
    "xml.sax",
    "xml.parsers",
    "xml.parsers.expat",
    "re",
    "datetime",
    "collections",
    "json",
    "copy",
    "math",
    "string",
    "io",
    "functools",
    "itertools",
}

_real_import = _real_builtins.__import__


def _restricted_import(
    name: str,
    globals: dict[str, Any] | None = None,
    locals: dict[str, Any] | None = None,
    fromlist: tuple[str, ...] = (),
    level: int = 0,
) -> Any:
    """Import hook that only allows safe modules."""
    if name not in SAFE_MODULES:
        raise ImportError(
            f"Module '{name}' is not allowed. "
            f"Only these modules are permitted: {', '.join(sorted(SAFE_MODULES))}"
        )
    return _real_import(name, globals, locals, fromlist, level)


def _build_sandbox_namespace() -> dict[str, Any]:
    """Build a restricted namespace for executing generated code."""
    import builtins as _builtins

    safe_builtins = {
        k: getattr(_builtins, k)
        for k in [
            "True",
            "False",
            "None",
            "abs",
            "all",
            "any",
            "bool",
            "bytes",
            "chr",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "hasattr",
            "hash",
            "hex",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "oct",
            "ord",
            "pow",
            "print",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "slice",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "zip",
            "ValueError",
            "TypeError",
            "KeyError",
            "IndexError",
            "AttributeError",
            "StopIteration",
            "RuntimeError",
            "Exception",
        ]
        if hasattr(_builtins, k)
    }
    safe_builtins["__import__"] = _restricted_import
    return {"__builtins__": safe_builtins}


def _snippet(xml_string: str, max_length: int = 300) -> str:
    """Return a truncated snippet of an XML string for reporting."""
    text = xml_string.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


class TesterAgent:
    """Executes generated Python code against XML pairs and validates results."""

    async def test_code(self, code: str, xml_pairs: list[XmlPair]) -> TestResult:
        """
        Execute the generated code in a restricted sandbox and test it
        against each XML pair.

        The generated code must define a ``transform_xml(input_xml)`` function
        that accepts an XML string and returns a transformed XML string.
        """
        # ------------------------------------------------------------------
        # 1. Compile and load the generated code into a sandbox
        # ------------------------------------------------------------------
        try:
            module = self._load_code_module(code)
        except SyntaxError as exc:
            return TestResult(
                total_pairs=len(xml_pairs),
                passed_pairs=0,
                accuracy=0.0,
                details=[],
                error_message=f"Syntax error in generated code: {exc}",
            )
        except Exception as exc:
            return TestResult(
                total_pairs=len(xml_pairs),
                passed_pairs=0,
                accuracy=0.0,
                details=[],
                error_message=f"Failed to load generated code: {exc}",
            )

        # Verify the transform_xml entry-point exists
        transform_fn = getattr(module, "transform_xml", None)
        if transform_fn is None:
            return TestResult(
                total_pairs=len(xml_pairs),
                passed_pairs=0,
                accuracy=0.0,
                details=[],
                error_message=(
                    "Generated code does not define a 'transform_xml' function."
                ),
            )

        # ------------------------------------------------------------------
        # 2. Run transform_xml against every pair
        # ------------------------------------------------------------------
        details: list[TestDetail] = []
        passed_count = 0

        for pair in xml_pairs:
            detail = self._test_single_pair(transform_fn, pair)
            details.append(detail)
            if detail.passed:
                passed_count += 1

        total = len(xml_pairs)
        accuracy = passed_count / total if total > 0 else 0.0

        return TestResult(
            total_pairs=total,
            passed_pairs=passed_count,
            accuracy=round(accuracy, 4),
            details=details,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_code_module(code: str) -> types.ModuleType:
        """Compile *code* and execute it inside a sandboxed module."""
        compiled = compile(code, "<generated>", "exec")

        module = types.ModuleType("generated_transform")
        namespace = _build_sandbox_namespace()
        module.__dict__.update(namespace)

        exec(compiled, module.__dict__)  # noqa: S102
        return module

    @staticmethod
    def _test_single_pair(
        transform_fn: Any,
        pair: XmlPair,
    ) -> TestDetail:
        """Execute *transform_fn* for one XML pair and build a TestDetail."""
        try:
            actual_xml: str = transform_fn(pair.input_xml)
        except Exception as exc:
            tb = traceback.format_exc()
            return TestDetail(
                pair_id=pair.pair_id,
                passed=False,
                expected_snippet=_snippet(pair.output_xml),
                actual_snippet="",
                diff=f"Runtime error: {exc}\n{tb}",
            )

        if not isinstance(actual_xml, str):
            return TestDetail(
                pair_id=pair.pair_id,
                passed=False,
                expected_snippet=_snippet(pair.output_xml),
                actual_snippet=str(actual_xml)[:300],
                diff=(
                    f"transform_xml returned {type(actual_xml).__name__}, "
                    "expected str."
                ),
            )

        # Compare expected vs actual
        is_equal, _diffs = compare_xml(pair.output_xml, actual_xml)
        diff_report = "" if is_equal else xml_diff_report(pair.output_xml, actual_xml)

        return TestDetail(
            pair_id=pair.pair_id,
            passed=is_equal,
            expected_snippet=_snippet(pair.output_xml),
            actual_snippet=_snippet(actual_xml),
            diff=diff_report,
        )
