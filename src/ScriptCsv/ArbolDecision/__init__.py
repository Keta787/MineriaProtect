"""Minimal re-export bridge to scripts/ScriptsCsv/ArbolDecision (zero duplicated logic)."""

from __future__ import annotations

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_CSV = _REPO_ROOT / "scripts" / "ScriptsCsv"
if str(_SCRIPTS_CSV) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_CSV))

from ArbolDecision import *  # noqa: F401, F403

