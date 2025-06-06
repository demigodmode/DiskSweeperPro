#!/usr/bin/env python3
"""
sweeper.core.collector
~~~~~~~~~~~~~~~~~~~~~~

• Walks the filesystem, respecting age & size thresholds
• Discovers Edge / Chrome caches for every profile
• Supplies `collect()` and `fmt_sz()` – the public API
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Iterable, Iterator, List, Set

from .rules import (
    Rule,
    Candidate,
    RULES,
    MB,
    GB,
    NOW,
    LOCAL,
)

# ── Internal helpers ──────────────────────────────────────────────────────


def _walk_size(p: Path, *, cutoff: float | None) -> int:
    """Return total size (bytes) under *p*, skipping files newer than *cutoff*."""
    total = 0
    if not p.exists():
        return 0

    try:
        stat = p.stat()
    except OSError:
        return 0

    # Single file
    if p.is_file():
        return stat.st_size if cutoff is None or stat.st_mtime < cutoff else 0

    # Directory walk
    for sub in p.rglob("*"):
        try:
            st = sub.stat()
            if cutoff is None or st.st_mtime < cutoff:
                total += st.st_size
        except OSError:
            pass
    return total


# ── Browser cache discovery ───────────────────────────────────────────────

EDGE_BASE = LOCAL / "Microsoft" / "Edge" / "User Data"
CHROME_BASE = LOCAL / "Google" / "Chrome" / "User Data"


def _iter_profile_caches(base: Path) -> Iterator[Path]:
    if not base.exists():
        return
    for prof in base.iterdir():
        if not prof.is_dir():
            continue
        for cache_dir in (prof / "Cache", prof / "Code Cache"):
            if cache_dir.exists():
                yield cache_dir


def edge_caches() -> Iterable[Path]:
    yield from _iter_profile_caches(EDGE_BASE)


def chrome_caches() -> Iterable[Path]:
    yield from _iter_profile_caches(CHROME_BASE)


# ── Patch the stubs created in rules.py so RULES already built stay valid ──

_rules_mod: ModuleType = __import__("sweeper.core.rules", fromlist=["dummy"])
setattr(_rules_mod, "_edge_caches", edge_caches)
setattr(_rules_mod, "_chrome_caches", chrome_caches)

for r in RULES:  # re-point the two rules that used the earlier stubs
    if r.label == "Edge Cache":
        r.path = edge_caches
    elif r.label == "Chrome Cache":
        r.path = chrome_caches

# ── Public API -------------------------------------------------------------


def collect(rules: List[Rule], *, include: Set[str]) -> List[Candidate]:
    """Return a list of Candidates whose rule.severity is in *include*."""
    found: list[Candidate] = []
    for r in rules:
        if r.severity not in include:
            continue
        paths = r.path() if callable(r.path) else [r.path]
        cutoff = NOW - r.min_age * 86_400 if r.min_age else None
        for p in paths:
            size = _walk_size(p, cutoff=cutoff)
            if size >= r.min_size:
                found.append(Candidate(r, p, size))
    return found


def fmt_sz(b: int) -> str:
    if b >= GB:
        return f"{b/GB:.1f} GB"
    if b >= MB:
        return f"{b/MB:.1f} MB"
    return f"{b:,} B"
