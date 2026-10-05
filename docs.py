"""Submission documentation validator.

Validates a submission markdown document against the structure defined in
``template1.md`` for the Hacktoberfest "Build for a Friend" challenge.

The five mandatory section headings must be present, in order, and each must
contain descriptive content (not just whitespace or HTML comment placeholders).
Optional sections, when present, must appear after all mandatory sections.

Supports Requirement 7 (7.1, 7.3, 7.4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

MANDATORY = [
    "What I Built",
    "Demo",
    "Code",
    "How I Built It",
    "Why Does Open Innovation Matter?",
]
OPTIONAL = ["My Agent Session", "Prize Categories"]

# Matches a markdown ATX heading line, capturing its level (#'s) and text.
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
# Matches an HTML comment (used for placeholder guidance in the template).
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass
class DocReport:
    """Result of validating a submission document.

    Attributes:
        complete: True only when all mandatory headings are present, in order,
            each has descriptive content, and any optional sections follow the
            mandatory ones.
        missing: Mandatory heading titles that are absent from the document.
        empty: Mandatory heading titles that are present but have no descriptive
            content between the heading and the next heading (or end of file).
    """

    complete: bool
    missing: list[str] = field(default_factory=list)
    empty: list[str] = field(default_factory=list)


@dataclass
class _Section:
    title: str
    body: str


def _parse_sections(markdown_text: str) -> list[_Section]:
    """Split the document into sections keyed by their heading text.

    The body of a section is every line after its heading up to the next
    heading (of any level) or the end of the document. Content appearing before
    the first heading is ignored.
    """
    sections: list[_Section] = []
    current_title: str | None = None
    body_lines: list[str] = []

    for line in markdown_text.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            if current_title is not None:
                sections.append(_Section(current_title, "\n".join(body_lines)))
            current_title = match.group(2).strip()
            body_lines = []
        elif current_title is not None:
            body_lines.append(line)

    if current_title is not None:
        sections.append(_Section(current_title, "\n".join(body_lines)))

    return sections


def _has_content(body: str) -> bool:
    """Return True when the section body has descriptive content.

    HTML comments (the template's placeholder guidance) and surrounding
    whitespace do not count as descriptive content.
    """
    stripped = _HTML_COMMENT_RE.sub("", body)
    return bool(stripped.strip())


def validate(markdown_text: str) -> DocReport:
    """Validate submission markdown against the template structure.

    Checks that the five mandatory headings exist, appear in the required
    order, and each carries descriptive content. Optional sections, if present,
    must follow all mandatory sections. Heading text is matched
    case-insensitively.

    Args:
        markdown_text: The full submission document text.

    Returns:
        A :class:`DocReport`. ``complete`` is True only when every rule holds;
        otherwise ``missing`` and ``empty`` name the offending mandatory
        sections.
    """
    sections = _parse_sections(markdown_text or "")

    # Map lowercased heading text -> list of indices where it appears (in order).
    title_positions: dict[str, list[int]] = {}
    for index, section in enumerate(sections):
        title_positions.setdefault(section.title.lower(), []).append(index)

    # Map a section index -> whether it has descriptive content.
    content_by_index = {
        index: _has_content(section.body) for index, section in enumerate(sections)
    }

    missing: list[str] = []
    empty: list[str] = []
    mandatory_indices: list[int] = []

    for title in MANDATORY:
        positions = title_positions.get(title.lower())
        if not positions:
            missing.append(title)
            continue
        # Use the first occurrence of this mandatory heading.
        idx = positions[0]
        mandatory_indices.append(idx)
        if not content_by_index[idx]:
            empty.append(title)

    # Mandatory headings must appear in the required order.
    order_ok = mandatory_indices == sorted(mandatory_indices)

    # Any present optional section must follow every present mandatory section.
    optional_order_ok = True
    if mandatory_indices:
        last_mandatory = max(mandatory_indices)
        for title in OPTIONAL:
            for idx in title_positions.get(title.lower(), []):
                if idx < last_mandatory:
                    optional_order_ok = False
                    break
            if not optional_order_ok:
                break

    complete = (
        not missing and not empty and order_ok and optional_order_ok
    )

    return DocReport(complete=complete, missing=missing, empty=empty)
