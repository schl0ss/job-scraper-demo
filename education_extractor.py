"""
Education Requirement Extractor
Resume Audit Study - Tech Demo

Extracts minimum education requirement (AA/BA/unspecified) from job description text.
Uses rule-based pattern matching as primary approach, with clear extension point for
LLM fallback on ambiguous cases.

This determines whether the resume generator produces 2 or 3 resumes per posting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class EducationLevel(Enum):
    ASSOCIATES = "AA"
    BACHELORS = "BA"
    UNSPECIFIED = "unspecified"


@dataclass
class ExtractionResult:
    level: EducationLevel
    confidence: str  # "high", "medium", "low"
    matched_text: str | None  # the snippet that triggered the match
    method: str  # "rule_based" or "llm_fallback"


# Patterns ordered by specificity. Each tuple: (compiled regex, education level)
# We check for bachelor's first since it's a higher requirement
BACHELOR_PATTERNS = [
    r"bachelor['\u2019]?s?\s+degree",
    r"\bba\s*/\s*bs\b",
    r"\bbs\s*/\s*ba\b",
    r"\bb\.?a\.?\s*/\s*b\.?s\.?\b",
    r"\bb\.?s\.?\s*/\s*b\.?a\.?\b",
    r"\bbachelor['\u2019]?s\b",
    r"\b4[\s-]year\s+degree\b",
    r"\bfour[\s-]year\s+degree\b",
    r"\bundergraduate\s+degree\b",
    r"\bbaccalaureate\b",
]

ASSOCIATES_PATTERNS = [
    r"associate['\u2019]?s?\s+degree",
    r"\bassociate['\u2019]?s\b",
    r"\ba\.?a\.?\s+degree\b",
    r"\ba\.?a\.?s\.?\s+degree\b",
    r"\b2[\s-]year\s+degree\b",
    r"\btwo[\s-]year\s+degree\b",
]

# Requirement context — words near the degree that signal it's required vs preferred
REQUIRED_CONTEXT = [
    r"require[ds]?",
    r"must\s+have",
    r"minimum",
    r"mandatory",
    r"necessary",
    r"essential",
]

PREFERRED_CONTEXT = [
    r"prefer(?:red)?",
    r"desired",
    r"nice\s+to\s+have",
    r"a\s+plus",
    r"or\s+equivalent\s+experience",
    r"or\s+equivalent\s+work",
]


def _find_pattern(text: str, patterns: list[str]) -> re.Match | None:
    """Find the first matching pattern in text."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match
    return None


def _check_context(text: str, match_pos: int, window: int = 200) -> str:
    """Check surrounding context to determine if requirement is 'required' vs 'preferred'."""
    start = max(0, match_pos - window)
    end = min(len(text), match_pos + window)
    context = text[start:end].lower()

    has_required = any(re.search(p, context) for p in REQUIRED_CONTEXT)
    has_preferred = any(re.search(p, context) for p in PREFERRED_CONTEXT)

    if has_required and not has_preferred:
        return "high"
    elif has_preferred and not has_required:
        return "medium"  # preferred, not required
    elif has_required and has_preferred:
        return "medium"  # mixed signals
    else:
        return "medium"  # mentioned but no clear context


def extract_education(description: str) -> ExtractionResult:
    """
    Extract minimum education requirement from a job description.

    Returns the highest education level mentioned as a requirement.
    If both BA and AA are mentioned, BA takes precedence (it's the min requirement).
    """
    text = description.strip()

    if not text:
        return ExtractionResult(
            level=EducationLevel.UNSPECIFIED,
            confidence="high",
            matched_text=None,
            method="rule_based",
        )

    # Check for bachelor's level
    ba_match = _find_pattern(text, BACHELOR_PATTERNS)
    if ba_match:
        confidence = _check_context(text, ba_match.start())
        return ExtractionResult(
            level=EducationLevel.BACHELORS,
            confidence=confidence,
            matched_text=ba_match.group(),
            method="rule_based",
        )

    # Check for associate's level
    aa_match = _find_pattern(text, ASSOCIATES_PATTERNS)
    if aa_match:
        confidence = _check_context(text, aa_match.start())
        return ExtractionResult(
            level=EducationLevel.ASSOCIATES,
            confidence=confidence,
            matched_text=aa_match.group(),
            method="rule_based",
        )

    # No education pattern found
    return ExtractionResult(
        level=EducationLevel.UNSPECIFIED,
        confidence="high",
        matched_text=None,
        method="rule_based",
    )
