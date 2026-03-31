"""
Employer Deduplication Engine
Resume Audit Study - Tech Demo

Implements the tiered resolution approach from the proposal:
  Tier 1: Normalized exact match (lowercase, strip punctuation, remove suffixes)
  Tier 2: Fuzzy matching + location awareness (rapidfuzz)
  Tier 3: Ambiguous cases flagged for human review
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from rapidfuzz import fuzz

# Common suffixes to strip during normalization
STRIP_SUFFIXES = [
    "incorporated", "inc", "llc", "llp", "corp", "corporation",
    "company", "co", "ltd", "limited", "group", "holdings",
    "health", "healthcare", "health care", "medical center",
    "hospital", "hospitals", "clinic", "clinics",
    "services", "solutions", "systems", "technologies",
    "the", "of", "at", "in",
]

STRIP_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in STRIP_SUFFIXES) + r")\b"
)


@dataclass
class Employer:
    canonical_id: int
    canonical_name: str
    metro: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    raw_name: str
    raw_metro: str
    matched_employer: Employer | None
    tier: str  # "exact", "fuzzy_auto", "fuzzy_metro", "new", "review"
    score: float | None = None


def normalize(name: str) -> str:
    """Normalize employer name for comparison."""
    s = name.lower().strip()
    # Remove punctuation except spaces
    s = re.sub(r"[^\w\s]", " ", s)
    # Remove common suffixes
    s = STRIP_PATTERN.sub("", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


class EmployerRegistry:
    """Canonical employer registry with tiered deduplication."""

    # Thresholds from the proposal
    AUTO_MERGE_THRESHOLD = 0.95
    METRO_MERGE_THRESHOLD = 0.80
    REVIEW_THRESHOLD = 0.80

    def __init__(self):
        self._employers: dict[int, Employer] = {}
        self._norm_index: dict[str, int] = {}  # normalized name -> canonical_id
        self._next_id = 1
        self._review_queue: list[MatchResult] = []

    @property
    def employers(self) -> list[Employer]:
        return list(self._employers.values())

    @property
    def review_queue(self) -> list[MatchResult]:
        return list(self._review_queue)

    def _add_employer(self, name: str, metro: str) -> Employer:
        emp = Employer(
            canonical_id=self._next_id,
            canonical_name=name,
            metro=metro,
            aliases=[name],
        )
        self._employers[self._next_id] = emp
        self._norm_index[normalize(name)] = self._next_id
        self._next_id += 1
        return emp

    def _add_alias(self, employer: Employer, alias: str):
        if alias not in employer.aliases:
            employer.aliases.append(alias)
        norm = normalize(alias)
        if norm not in self._norm_index:
            self._norm_index[norm] = employer.canonical_id

    def resolve(self, raw_name: str, metro: str) -> MatchResult:
        """Resolve a raw employer name to a canonical employer entity."""
        norm = normalize(raw_name)

        # Tier 1: Normalized exact match
        if norm in self._norm_index:
            emp = self._employers[self._norm_index[norm]]
            self._add_alias(emp, raw_name)
            return MatchResult(raw_name, metro, emp, tier="exact")

        # Tier 2: Fuzzy matching against all known normalized names
        best_score = 0.0
        best_emp = None

        for known_norm, emp_id in self._norm_index.items():
            # Use token_sort_ratio — handles word reordering
            score = fuzz.token_sort_ratio(norm, known_norm) / 100.0
            if score > best_score:
                best_score = score
                best_emp = self._employers[emp_id]

        if best_emp and best_score >= self.AUTO_MERGE_THRESHOLD:
            # High confidence — auto merge
            self._add_alias(best_emp, raw_name)
            return MatchResult(raw_name, metro, best_emp, tier="fuzzy_auto", score=best_score)

        if best_emp and best_score >= self.METRO_MERGE_THRESHOLD:
            # Medium confidence — merge only if same metro
            same_metro = best_emp.metro.lower().strip() == metro.lower().strip()
            if same_metro:
                self._add_alias(best_emp, raw_name)
                return MatchResult(raw_name, metro, best_emp, tier="fuzzy_metro", score=best_score)
            else:
                # Different metro, ambiguous — flag for review
                result = MatchResult(raw_name, metro, best_emp, tier="review", score=best_score)
                self._review_queue.append(result)
                # Still create as new for now
                new_emp = self._add_employer(raw_name, metro)
                result.matched_employer = new_emp
                return result

        # No good match — new employer
        new_emp = self._add_employer(raw_name, metro)
        return MatchResult(raw_name, metro, new_emp, tier="new")
