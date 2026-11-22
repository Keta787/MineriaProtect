"""Governance, SHA-256 data immutability, figure manifest, GeoGebra syntax & wording audit (MR-07/08)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd

from scripts.ScriptsCsv.EDA.validation import FigureManifest, FileFingerprint, FileHasher

from .config import APPROVED_FIGURES, NumericalMethodsConfig


# Prohibited phrases violating MR-07 (no causal overclaims) or MR-08 (ESCO attribution rule) — Bilingual EN + ES
PROHIBITED_WORDING_PATTERNS: Sequence[tuple[str, str]] = (
    # English MR-08 / MR-07
    (r"\bworker\s+knows\s+\d+\s+skills\b", "MR-08 violation (EN): attributes ESCO occupation skills to worker knowledge"),
    (r"\bperson\s+possesses\s+\d+\s+skills\b", "MR-08 violation (EN): attributes ESCO occupation skills to personal possession"),
    (r"\bcauses\s+higher\s+recurrence\b", "MR-07 violation (EN): causal claim instead of descriptive association"),
    (r"\bcauses\s+shorter\s+tenure\b", "MR-07 violation (EN): causal claim instead of descriptive/censoring reading"),
    # Spanish MR-08 / MR-07
    (r"\bel\s+trabajador\s+(?:sabe|domina|posee)\s+\d+(?:[.,]\d+)?\s+(?:habilidades|competencias)\b", "MR-08 violation (ES): atribuye skills del oficio ESCO al trabajador"),
    (r"\bla\s+persona\s+(?:sabe|domina|posee)\s+\d+(?:[.,]\d+)?\s+(?:habilidades|competencias)\b", "MR-08 violation (ES): atribuye skills del oficio ESCO a la persona"),
    (r"\bcausa\s+(?:mayor|más)\s+(?:reincidencia|habilidades|competencias)\b", "MR-07 violation (ES): afirmación causal en lugar de asociación descriptiva"),
    (r"\bprovoca\s+(?:menor|más\s+corta)\s+(?:duración|permanencia)\b", "MR-07 violation (ES): afirmación causal en lugar de lectura descriptiva/censura"),
    (r"\bcambiar\s+de\s+empleo\s+causa\b", "MR-07 violation (ES): afirmación causal sobre movilidad laboral"),
)

# Disclaimer/negation contexts where a prohibited phrase is cited explicitly to warn against it
_SAFEGUARD_CONTEXT_RE = re.compile(
    r"(no\s+significa|no\s+implica|nunca\s+causalidad|no\s+causa|sin\s+causalidad|"
    r"no\s+es\s+causal|evitar\s+afirmar|prohibid|mr-07|mr-08|violation|falso|distractor|"
    r"en\s+lugar\s+de|does\s+not\s+cause|never\s+claim|instead\s+of)",
    flags=re.IGNORECASE,
)

FULL_HASH_THRESHOLD_BYTES: int = 64 * (1 << 20)


def snapshot_read_only_inputs(cfg: NumericalMethodsConfig) -> Dict[str, FileFingerprint]:
    """Capture SHA-256 fingerprints of every read-only input before execution."""
    hasher = FileHasher()
    existing = [p for p in cfg.audit_input_paths() if p.exists()]
    return hasher.snapshot(existing)


def verify_read_only_inputs(before: Dict[str, FileFingerprint]) -> pd.DataFrame:
    """Confirm 100% of read-only inputs inside data/ remained byte-identical.

    Stores the FULL 64-character hexadecimal SHA-256 digests (without truncation)
    together with file size and explicit hash_mode transparency.
    """
    hasher = FileHasher()
    rows: List[Dict[str, object]] = []
    for path_str, original in before.items():
        path = Path(path_str)
        current = hasher.fingerprint(path)
        mode = (
            "full_sha256"
            if original.size_bytes <= FULL_HASH_THRESHOLD_BYTES
            else "sampled_24MiB_plus_meta_sha256"
        )
        rows.append(
            {
                "file_name": path.name,
                "file_path": path_str,
                "size_bytes": int(original.size_bytes),
                "hash_mode": mode,
                "sha256_before": original.sha256,
                "sha256_after": current.sha256,
                "intact": bool(original.sha256 == current.sha256),
            }
        )
    return pd.DataFrame(rows)


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
    """Scan generated markdown/html/notebook files (EN + ES) to ensure compliance with MR-07 and MR-08."""
    findings: List[Dict[str, object]] = []
    for p in paths:
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        hits: List[str] = []
        for line in txt.splitlines():
            if _SAFEGUARD_CONTEXT_RE.search(line):
                continue
            for pat, reason in PROHIBITED_WORDING_PATTERNS:
                if re.search(pat, line, flags=re.IGNORECASE) and reason not in hits:
                    hits.append(reason)
        findings.append(
            {
                "file": p.name,
                "file_path": str(p),
                "violations_count": len(hits),
                "violations": "; ".join(hits) if hits else "None",
                "passed": len(hits) == 0,
            }
        )
    return pd.DataFrame(findings)
