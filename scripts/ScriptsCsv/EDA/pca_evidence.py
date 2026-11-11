"""Reuse the saved PCA diagnostics of notebooks 4.0 and 4.1.

The EDA must not refit a PCA: the transformation is owned by phase 3 and a PCA
over 2 839 dummy columns would not be a sound diagnostic.  This module reads
the outputs already stored in ``4.0_PCA.ipynb`` (10 k sample) and
``4.1_PCA_completo.ipynb`` (50 k sample) and turns them into tidy tables.

The two runs are shown together as a stability check: if PC1 and the number of
components needed for 80 % variance barely move between samples, the
diagnostic is robust.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import nbformat
import pandas as pd

from .config import EDAConfig

_VARIANCE_ROW = re.compile(
    r"^\s*\d+\s+(PC\d+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s*$"
)
_COMPONENTS = re.compile(
    r"Componentes 80/90 \((con|sin)\):\s*(\d+)\s*(\d+)"
)
_LOADING_HEADER = re.compile(r"Top loadings (PC\d+) \((con|sin)\):")
_LOADING_ROW = re.compile(r"^(\S+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s*$")


@dataclass(frozen=True)
class PCAEvidence:
    """Parsed PCA evidence of one notebook run."""

    source: str
    variance: pd.DataFrame
    components: pd.DataFrame
    loadings: pd.DataFrame


class PCAEvidenceReader:
    """Parse the text outputs of the two saved PCA notebooks."""

    def __init__(self, config: EDAConfig) -> None:
        self._config = config

    def _cell_text(self, path: Path) -> str:
        notebook = nbformat.read(path, as_version=4)
        chunks: List[str] = []
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            for output in cell.get("outputs", []):
                if output.get("output_type") == "stream":
                    chunks.append(output.get("text", ""))
                else:
                    data = output.get("data", {})
                    if "text/plain" in data:
                        chunks.append(data["text/plain"])
        return "\n".join(chunks)

    def _parse_variance(self, text: str, source: str) -> pd.DataFrame:
        blocks: List[List[Dict[str, object]]] = []
        current: List[Dict[str, object]] = []
        for line in text.splitlines():
            match = _VARIANCE_ROW.match(line)
            if match:
                current.append(
                    {
                        "component": match.group(1),
                        "explained_variance_ratio": float(match.group(2)),
                        "cumulative_variance": float(match.group(3)),
                    }
                )
            elif current:
                blocks.append(current)
                current = []
        if current:
            blocks.append(current)
        rows = []
        for index, block in enumerate(blocks):
            version = "con" if index == 0 else "sin"
            for row in block:
                rows.append({"source": source, "version": version, **row})
        return pd.DataFrame(rows)

    def _parse_components(self, text: str, source: str) -> pd.DataFrame:
        rows = []
        for match in _COMPONENTS.finditer(text):
            rows.append(
                {
                    "source": source,
                    "version": match.group(1),
                    "n80": int(match.group(2)),
                    "n90": int(match.group(3)),
                }
            )
        return pd.DataFrame(rows)

    def _parse_loadings(self, text: str, source: str) -> pd.DataFrame:
        rows: List[Dict[str, object]] = []
        current_pc = None
        current_version = None
        for line in text.splitlines():
            header = _LOADING_HEADER.search(line)
            if header:
                current_pc, current_version = header.group(1), header.group(2)
                continue
            if current_pc is None:
                continue
            match = _LOADING_ROW.match(line)
            if match:
                rows.append(
                    {
                        "source": source,
                        "version": current_version,
                        "component": current_pc,
                        "feature": match.group(1),
                        "abs_loading": float(match.group(2)),
                        "signed_loading": float(match.group(3)),
                    }
                )
            elif line.strip() and not line.strip().startswith(("abs_loading", "signed_loading")):
                current_pc = None
                current_version = None
        return pd.DataFrame(rows)

    def read(self, source: str) -> PCAEvidence:
        """Read one notebook and return its tidy PCA evidence."""
        path = self._config.pca_notebooks[source]
        text = self._cell_text(path)
        return PCAEvidence(
            source=source,
            variance=self._parse_variance(text, source),
            components=self._parse_components(text, source),
            loadings=self._parse_loadings(text, source),
        )

    def read_all(self) -> List[PCAEvidence]:
        """Read both runs, 10 k and 50 k."""
        return [self.read(source) for source in self._config.pca_notebooks]

    def stability(self, evidence: Iterable[PCAEvidence]) -> pd.DataFrame:
        """PC1 share and components for 80 % in each run and version."""
        frames = []
        for item in evidence:
            first = (
                item.variance.loc[item.variance["component"] == "PC1"]
                .set_index("version")["explained_variance_ratio"]
            )
            comps = item.components.set_index("version")
            for version in first.index:
                frames.append(
                    {
                        "fuente": item.source,
                        "version": "A · con outliers" if version == "con" else "B · sin outliers",
                        "pc1_pct": round(float(first[version] * 100), 2),
                        "componentes_80": int(comps.loc[version, "n80"]),
                        "componentes_90": int(comps.loc[version, "n90"]),
                    }
                )
        return pd.DataFrame(frames).sort_values(["version", "fuente"]).reset_index(drop=True)
