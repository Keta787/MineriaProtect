"""Governance, SHA-256 data immutability, figure manifest, GeoGebra syntax & wording audit (MR-07/08)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd

from scripts.ScriptsCsv.EDA.validation import FigureManifest, FileFingerprint, FileHasher

from .config import APPROVED_FIGURES, NumericalMethodsConfig


# Prohibited phrases violating MR-07 (no causal overclaims) or MR-08 (ESCO attribution rule)
PROHIBITED_WORDING_PATTERNS: Sequence[tuple[str, str]] = (
    (r"\bworker\s+knows\s+\d+\s+skills\b", "MR-08 violation: attributes ESCO occupation skills to worker knowledge"),
    (r"\bperson\s+possesses\s+\d+\s+skills\b", "MR-08 violation: attributes ESCO occupation skills to personal possession"),
    (r"\bcauses\s+higher\s+recurrence\b", "MR-07 violation: causal claim instead of descriptive association"),
    (r"\bcauses\s+shorter\s+tenure\b", "MR-07 violation: causal claim instead of descriptive/censoring reading"),
)


def snapshot_read_only_inputs(cfg: NumericalMethodsConfig) -> Dict[str, FileFingerprint]:
    """Capture SHA-256 fingerprints of every read-only input before execution."""
    hasher = FileHasher()
    existing = [p for p in cfg.audit_input_paths() if p.exists()]
    return hasher.snapshot(existing)


def verify_read_only_inputs(before: Dict[str, FileFingerprint]) -> pd.DataFrame:
    """Confirm 100% of read-only inputs inside data/ remained byte-identical."""
    hasher = FileHasher()
    df = hasher.verify(before)
    df = df.rename(
        columns={
            "archivo": "file_name",
            "ruta": "file_path",
            "sha256_antes": "sha256_before",
            "sha256_despues": "sha256_after",
            "sin_cambios": "intact",
        }
    )
    return df


def verify_figure_manifest(cfg: NumericalMethodsConfig) -> pd.DataFrame:
    """Confirm all 12 approved figures exist and are non-empty."""
    manifest = FigureManifest()
    report = manifest.check(cfg.figures_dir, APPROVED_FIGURES)
    manifest.assert_complete(report)
    return report.rename(columns={"figura": "figure", "existe": "exists", "tamano_kb": "size_kb"})


def validate_geogebra_scripts(geogebra_dir: Path) -> pd.DataFrame:
    """Parse every exported .txt GeoGebra script asserting valid point lists and target commands."""
    rows: List[Dict[str, object]] = []
    for path in sorted(geogebra_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        has_points = bool(re.search(r"^P\s*=\s*\{.*\}$", text, flags=re.MULTILINE))
        is_ols = "FitLine(P)" in text and "RSquare(P, f)" in text
        is_lag = "Polynomial(P)" in text and "L0(x)" in text
        rows.append(
            {
                "script_file": path.name,
                "has_point_list": has_points,
                "valid_command_set": bool(is_ols or is_lag),
                "family": "OLS" if is_ols else ("Lagrange" if is_lag else "UNKNOWN"),
                "passed": bool(has_points and (is_ols or is_lag)),
            }
        )
    return pd.DataFrame(rows)


def audit_wording_compliance(paths: Iterable[Path]) -> pd.DataFrame:
    """Scan generated markdown/notebook files to ensure compliance with MR-07 and MR-08."""
    findings: List[Dict[str, object]] = []
    for p in paths:
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        hits = []
        for pat, reason in PROHIBITED_WORDING_PATTERNS:
            if re.search(pat, txt, flags=re.IGNORECASE):
                hits.append(reason)
        findings.append(
            {
                "file": p.name,
                "violations_count": len(hits),
                "violations": "; ".join(hits) if hits else "None",
                "passed": len(hits) == 0,
            }
        )
    return pd.DataFrame(findings)
