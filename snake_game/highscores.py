"""Persistent high-score table backed by a JSON file.

The table keeps at most :data:`config.HIGH_SCORE_LIMIT` entries, each made
of a three-letter initial and a score, ordered from highest to lowest.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

from .config import HIGH_SCORE_LIMIT

#: Where the table lives, next to the game package.
SCORES_FILE = Path(__file__).with_name("scores.json")


class ScoreEntry(TypedDict):
    """A single high-score table entry."""

    initials: str
    score: int


def _valid_entry(raw: object) -> ScoreEntry | None:
    """Return ``raw`` as a score entry if it is well formed, else ``None``.

    An entry is a mapping with a string ``initials`` of exactly three
    letters and an integer ``score`` of at least zero.
    """
    if not isinstance(raw, dict):
        return None
    initials = raw.get("initials")
    score = raw.get("score")
    if (
        not isinstance(initials, str)
        or len(initials) != 3
        or not initials.isalpha()
        or not isinstance(score, int)
        or isinstance(score, bool)
        or score < 0
    ):
        return None
    return ScoreEntry(initials=initials.upper(), score=score)


def load_scores(path: Path = SCORES_FILE) -> list[ScoreEntry]:
    """Load the high-score table from ``path``.

    Missing files, unreadable files and malformed JSON all yield an empty
    table, so the game always starts in a safe state. Entries that fail
    validation are dropped and the surviving ones are re-sorted from
    highest to lowest.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    entries = [entry for entry in (_valid_entry(item) for item in raw) if entry]
    entries.sort(key=lambda item: item["score"], reverse=True)
    return entries[:HIGH_SCORE_LIMIT]


def save_scores(table: list[ScoreEntry], path: Path = SCORES_FILE) -> None:
    """Write ``table`` to ``path`` as pretty-printed JSON.

    A failed write is swallowed so that a read-only disk or a missing
    directory can never take the game down; the previous file simply
    stays in place.
    """
    try:
        path.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass


def qualifies(score: int, table: list[ScoreEntry]) -> bool:
    """Return ``True`` if ``score`` would make it into ``table``.

    A score qualifies when the table still has a free slot, or when it is
    strictly greater than the lowest entry's score.
    """
    if len(table) < HIGH_SCORE_LIMIT:
        return True
    return score > min(entry["score"] for entry in table)


def add_score(score: int, initials: str, table: list[ScoreEntry]) -> list[ScoreEntry]:
    """Return ``table`` with ``(score, initials)`` inserted in rank order.

    The new entry is placed where it belongs, and the table is truncated
    back to :data:`config.HIGH_SCORE_LIMIT` entries. The argument is not
    mutated.
    """
    combined = table + [ScoreEntry(initials=initials.upper(), score=score)]
    combined.sort(key=lambda item: item["score"], reverse=True)
    return combined[:HIGH_SCORE_LIMIT]


def best(table: list[ScoreEntry]) -> ScoreEntry | None:
    """Return the top entry of ``table``, or ``None`` for an empty table."""
    return table[0] if table else None
