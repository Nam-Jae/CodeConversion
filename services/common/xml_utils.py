from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import OrderedDict
from io import StringIO
from typing import Any


def parse_xml(xml_string: str) -> ET.Element:
    """Parse an XML string and return the root element."""
    return ET.fromstring(xml_string.strip())


def xml_to_dict(element: ET.Element, strip_ns: bool = True) -> OrderedDict[str, Any]:
    """Convert an XML element to an ordered dictionary."""
    tag = _strip_namespace(element.tag) if strip_ns else element.tag
    result: OrderedDict[str, Any] = OrderedDict()

    # Attributes
    if element.attrib:
        attrs = {}
        for k, v in element.attrib.items():
            key = _strip_namespace(k) if strip_ns else k
            attrs[key] = v
        result["@attributes"] = attrs

    # Children
    children: dict[str, list[Any]] = {}
    for child in element:
        child_tag = _strip_namespace(child.tag) if strip_ns else child.tag
        child_dict = xml_to_dict(child, strip_ns)
        children.setdefault(child_tag, []).append(child_dict)

    for child_tag, child_list in children.items():
        result[child_tag] = child_list if len(child_list) > 1 else child_list[0]

    # Text
    if element.text and element.text.strip():
        if result:
            result["#text"] = element.text.strip()
        else:
            return OrderedDict([(tag, element.text.strip())])

    return OrderedDict([(tag, result if result else None)])


def compare_xml(xml1: str, xml2: str, strip_ns: bool = True) -> tuple[bool, list[str]]:
    """Compare two XML strings. Returns (is_equal, list_of_differences)."""
    diffs: list[str] = []
    try:
        root1 = parse_xml(xml1)
        root2 = parse_xml(xml2)
    except ET.ParseError as e:
        return False, [f"XML parse error: {e}"]

    _compare_elements(root1, root2, "", diffs, strip_ns)
    return len(diffs) == 0, diffs


def _compare_elements(
    e1: ET.Element, e2: ET.Element, path: str, diffs: list[str], strip_ns: bool
) -> None:
    tag1 = _strip_namespace(e1.tag) if strip_ns else e1.tag
    tag2 = _strip_namespace(e2.tag) if strip_ns else e2.tag
    current = f"{path}/{tag1}"

    if tag1 != tag2:
        diffs.append(f"Tag mismatch at {path}: '{tag1}' vs '{tag2}'")
        return

    # Compare text
    t1 = (e1.text or "").strip()
    t2 = (e2.text or "").strip()
    if t1 != t2:
        diffs.append(f"Text at {current}: '{t1}' vs '{t2}'")

    # Compare attributes
    a1 = {(_strip_namespace(k) if strip_ns else k): v for k, v in e1.attrib.items()}
    a2 = {(_strip_namespace(k) if strip_ns else k): v for k, v in e2.attrib.items()}
    if a1 != a2:
        diffs.append(f"Attributes at {current}: {a1} vs {a2}")

    # Compare children
    children1 = list(e1)
    children2 = list(e2)
    if len(children1) != len(children2):
        diffs.append(
            f"Child count at {current}: {len(children1)} vs {len(children2)}"
        )

    for i, (c1, c2) in enumerate(zip(children1, children2)):
        _compare_elements(c1, c2, current, diffs, strip_ns)


def xml_diff_report(expected_xml: str, actual_xml: str) -> str:
    """Generate a human-readable diff report."""
    is_equal, diffs = compare_xml(expected_xml, actual_xml)
    if is_equal:
        return "XML documents are identical."
    lines = [f"Found {len(diffs)} difference(s):"]
    for i, d in enumerate(diffs[:20], 1):
        lines.append(f"  {i}. {d}")
    if len(diffs) > 20:
        lines.append(f"  ... and {len(diffs) - 20} more")
    return "\n".join(lines)


def _strip_namespace(tag: str) -> str:
    """Remove namespace from a tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag
