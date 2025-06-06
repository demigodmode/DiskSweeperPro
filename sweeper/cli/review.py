#!/usr/bin/env python3
"""
sweeper.cli.review
~~~~~~~~~~~~~~~~~~

Command-line entry point that mimics the old monolithic script:
* report  – show everything
* clean   – delete safe + moderate
* deep    – delete all severities
"""

from __future__ import annotations

import argparse
import textwrap
from typing import Set

from ..core.collector import collect, fmt_sz
from ..core.cleaner import clean
from ..core.rules import RULES, SEVERITY_ORDER


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="disk-sweeper",
        description="Disk Sweeper Pro – severity-aware clean-up reviewer",
    )
    ap.add_argument(
        "mode",
        nargs="?",
        default="report",
        choices=["report", "clean", "deep"],
        help="report (dry-run) | clean (safe + moderate) | deep (all severities)",
    )
    return ap.parse_args()


def main() -> None:
    args = _parse_args()

    if args.mode == "report":
        include: Set[str] = {"safe", "moderate", "aggressive"}
    elif args.mode == "clean":
        include = {"safe", "moderate"}
    else:  # deep
        include = {"safe", "moderate", "aggressive"}

    destructive = args.mode in {"clean", "deep"}
    cands = collect(RULES, include=include)
    total = sum(c.size for c in cands)

    print("Disk-cleanup review")
    print(f"Mode: {args.mode} | Candidates: {len(cands)} | Potential space: {fmt_sz(total)}")
    print("—" * 88)
    for c in sorted(cands, key=lambda c: (SEVERITY_ORDER[c.rule.severity], -c.size)):
        reason = textwrap.shorten(c.rule.reason, width=48, placeholder="…")
        print(f"{fmt_sz(c.size):>9}  {c.rule.label:<22} {c.rule.severity:<10} {reason}")
        print(f"{'':>13}{c.path}")
    print("—" * 88)

    if destructive and cands:
        print("\nCleaning selected candidates…")
        clean(cands)


if __name__ == "__main__":
    main()
