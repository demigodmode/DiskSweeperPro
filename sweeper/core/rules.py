#!/usr/bin/env python3
"""
sweeper.core.rules
~~~~~~~~~~~~~~~~~~

Dataclasses + RULES loader.
If data/default_rules.yaml exists, read rules from YAML,
otherwise fall back to the built-in list.
"""

from __future__ import annotations

import time
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

# ── Shared constants ────────────────────────────────────────────────────────
MB = 1024 ** 2
GB = 1024 ** 3
NOW = time.time()

LOCAL = Path.home() / "AppData" / "Local"
SYSTEM_ROOT = Path.home().anchor + "Windows"  # usually C:\Windows

# ── Dataclasses ─────────────────────────────────────────────────────────────
@dataclass
class Rule:
    label: str
    path: Path | str | Callable[[], Iterable[Path]]
    min_size: int = 0
    min_age: int = 0               # days
    severity: str = "safe"         # safe | moderate | aggressive
    reason: str = ""

@dataclass
class Candidate:
    rule: Rule
    path: Path
    size: int

SEVERITY_ORDER = {"safe": 0, "moderate": 1, "aggressive": 2}

# ── Default hard-coded list (used only if YAML is absent) ───────────────────
EDGE_BASE = LOCAL / "Microsoft" / "Edge" / "User Data"
CHROME_BASE = LOCAL / "Google" / "Chrome" / "User Data"

def _edge_caches() -> Iterable[Path]: ...
def _chrome_caches() -> Iterable[Path]: ...

SYSTEM_TEMP   = Path(SYSTEM_ROOT) / "Temp"
USER_TEMP     = LOCAL / "Temp"
PREFETCH      = Path(SYSTEM_ROOT) / "Prefetch"
THUMBNAILS    = LOCAL / "Microsoft" / "Windows" / "Explorer"
SOFTWAREDIST  = Path(SYSTEM_ROOT) / "SoftwareDistribution" / "Download"
WINSXS        = Path(SYSTEM_ROOT) / "WinSxS"
PIP_CACHE     = LOCAL / "pip" / "Cache"
NPM_CACHE     = Path.home() / ".npm"
VSCODE_CACHE  = LOCAL / "Code" / "Cache"
PYCHARM_CACHE = LOCAL / "JetBrains" / "PyCharm*"

_BUILTIN_RULES: list[Rule] = [
    # (same list you already had – omitted for brevity)
]

# ── Try loading YAML override ───────────────────────────────────────────────
_yaml_path = Path(__file__).parent.parent.parent / "data" / "default_rules.yaml"
RULES: list[Rule]

def _expand(path_str: str) -> Path:
    """Expand placeholders in YAML paths."""
    return Path(
        path_str
        .replace("{LOCAL}", str(LOCAL))
        .replace("{SYSTEM_ROOT}", str(SYSTEM_ROOT))
    ).expanduser()

try:
    if _yaml_path.exists():
        with _yaml_path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        RULES = []
        for item in raw:
            p = item["path"]
            if isinstance(p, str):
                if p == "edge_caches":
                    path_val = _edge_caches
                elif p == "chrome_caches":
                    path_val = _chrome_caches
                else:
                    path_val = _expand(p)
            else:
                path_val = p
            RULES.append(Rule(path=path_val, **{k: v for k, v in item.items() if k != "path"}))
    else:
        RULES = _BUILTIN_RULES
except Exception as err:
    print("⚠️  Failed to load YAML rules – falling back to built-in list:", err)
    RULES = _BUILTIN_RULES

__all__ = ["MB", "GB", "NOW", "LOCAL", "SYSTEM_ROOT",
           "Rule", "Candidate", "SEVERITY_ORDER", "RULES"]
