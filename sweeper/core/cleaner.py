#!/usr/bin/env python3
"""
sweeper.core.cleaner – delete helpers + sweep log.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Iterable

from .collector import fmt_sz
from .rules import Candidate, LOCAL


def _delete_path(p: Path) -> None:
    if not p.exists():
        return
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
    else:
        p.unlink(missing_ok=True)


def clean(candidates: Iterable[Candidate], *, echo: bool = True) -> int:
    freed = 0
    for c in candidates:
        freed += c.size
        _delete_path(c.path)
        if echo:
            print("✓", fmt_sz(c.size).rjust(8), c.path)

    if echo:
        print("≈ Freed", fmt_sz(freed))

    # log
    try:
        log_dir = LOCAL / "DiskSweeper" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "sweeps.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M')} – freed {fmt_sz(freed)}\n")
    except Exception:
        pass

    return freed
