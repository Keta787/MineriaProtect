"""Verifica que el cuaderno ejecutado tenga 26 figuras, sin errores, y que los
conteos/medianas embebidos coincidan con el dataset."""

import base64
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[3]
NB = RAIZ / "notebooks" / "EDA_Columnas_Objetivo.ipynb"
DATOS = RAIZ / "data" / "03_processed" / "empleos_limpio_con_competencias .csv"

TIPOS = {"i1": np.int8, "i2": np.int16, "i4": np.int32, "i8": np.int64,
         "u1": np.uint8, "u2": np.uint16, "u4": np.uint32, "u8": np.uint64,
         "f4": np.float32, "f8": np.float64}


def decodificar(valor):
    """Convierte listas o el formato binario {dtype, bdata} de Plotly en ndarray."""
    if isinstance(valor, dict) and "bdata" in valor:
        crudo = base64.b64decode(valor["bdata"])
        return np.frombuffer(crudo, dtype=TIPOS[valor["dtype"]])
    return np.asarray(valor)


nb = json.loads(NB.read_text(encoding="utf-8"))
errores = [o for c in nb["cells"] for o in c.get("outputs", []) if o.get("output_type") == "error"]
figuras = {i: c["outputs"][0]["data"]["application/vnd.plotly.v1+json"]
           for i, c in enumerate(nb["cells"])
           if c.get("outputs") and "application/vnd.plotly.v1+json" in c["outputs"][0].get("data", {})}
print(f"Celdas: {len(nb['cells'])} | figuras Plotly: {len(figuras)} | errores: {len(errores)}")
assert not errores, "El cuaderno contiene errores"
assert len(figuras) == 26, "Se esperaban 26 figuras"

df = pd.read_csv(DATOS, encoding="utf-8", dtype=str, keep_default_na=False, na_values=[""])
num = lambda col: pd.to_numeric(df[col], errors="coerce")

# 06: la suma de barras debe igualar las duraciones <= 60
ini = df["start_date"].str.extract(r"Q([1-4])\s+(\d{4})").astype(float)
fin = df["end_date"].str.extract(r"Q([1-4])\s+(\d{4})").astype(float)
vigente = df["end_date"].str.strip().eq("Present")
dur_trim = ((fin[1] * 4 + fin[0]) - (ini[1] * 4 + ini[0]) + 1).where(~vigente)
barra06 = [t for t in figuras[25]["data"] if t["type"] == "bar"][0]
assert int(np.sum(decodificar(barra06["y"]))) == int((dur_trim <= 60).sum())

# 12 y 14: suma de conteos = cobertura de cada columna
for celda, col in [(43, "n_skills_competence"), (49, "n_skills_knowledge")]:
    barra = [t for t in figuras[celda]["data"] if t["type"] == "bar"][0]
    assert int(np.sum(decodificar(barra["y"]))) == int(num(col).notna().sum()), col

# 13 y 15: medianas y n por gran grupo (sin el grupo vacío "Sin grupo")
mayor = df["isco_group"].str.strip().str[0].map({
    "1": "1 · Gerentes y directivos", "2": "2 · Profesionales y científicos",
    "3": "3 · Técnicos y profesionales asociados", "4": "4 · Apoyo administrativo",
    "5": "5 · Servicios y vendedores", "6": "6 · Agricultura y pesca",
    "7": "7 · Oficiales y artesanos", "8": "8 · Operadores de máquinas",
    "9": "9 · Ocupaciones elementales", "0": "0 · Fuerzas armadas",
}).fillna("Sin grupo")

for celda, col in [(46, "n_skills_competence"), (52, "n_skills_knowledge")]:
    figura = figuras[celda]
    caja = [t for t in figura["data"] if t["type"] == "box"][0]
    grupos = list(caja["y"])
    assert "Sin grupo" not in grupos, "No debe dibujarse un grupo sin datos"
    medianas = decodificar(caja["median"]).astype(float)
    esperadas = num(col).groupby(mayor).median().reindex(grupos).astype(float)
    assert np.allclose(medianas, esperadas.to_numpy()), col
    etiquetas = figura["layout"]["yaxis"]["ticktext"]
    n_etiquetas = [int(g.rsplit("n = ", 1)[1].split(";")[0].replace(".", "")) for g in etiquetas]
    n_esperados = num(col).groupby(mayor).count().reindex(grupos).to_numpy()
    assert n_etiquetas == list(n_esperados), col

webps = sorted((RAIZ / "analysis" / "2026-10-25T16-00-00-eda-columnas-objetivo"
                / "plots" / "figuras_plotly").glob("*.webp"))
htmles = sorted(webps[0].parent.glob("*.html"))
assert len(webps) == len(htmles) == 26, "Faltan exportaciones"
print(f"Exportaciones: {len(htmles)} HTML + {len(webps)} WebP")
print("Verificación OK: conteos, medianas y n coinciden con el dataset")
