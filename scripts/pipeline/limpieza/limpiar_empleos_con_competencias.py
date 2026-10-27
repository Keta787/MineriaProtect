"""Limpieza canónica del dataset enriquecido con competencias ESCO.

La entrada es `data/03_processed/empleos_con_competencias.csv` y nunca se
modifica. La salida conserva una fila por experiencia, añade las banderas de
calidad y valida que los nombres de competencias sean coherentes con los
contadores del oficio.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd


BASE = Path(__file__).resolve().parents[3]
PROCESADOS = BASE / "data" / "03_processed"
ENTRADA = PROCESADOS / "empleos_con_competencias.csv"
SALIDA = PROCESADOS / "empleos_con_competencias_limpio.csv"
LOG = BASE / "logs" / "bitacora_limpieza_empleos_competencias.csv"

COLUMNAS_BASE = {
    "resume_id",
    "start_date",
    "end_date",
    "university_level",
    "matched_code",
    "emparejado",
    "occupation_code",
    "occupation_label",
    "isco_group",
    "isco_group_label",
    "isco_level",
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
    "veces_ese_oficio",
    "saber_skills",
    "skills",
    "knowledge",
    "sin_tipo",
}
CONTADORES = [
    "n_skills_essential",
    "n_skills_competence",
    "n_skills_knowledge",
    "n_skills_sin_tipo",
]
LISTAS = ["skills", "knowledge", "sin_tipo"]


def _leer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(
        ruta,
        dtype=str,
        encoding="utf-8",
        keep_default_na=False,
        na_values=[""],
    )


def _numero_lista(valor: str | float) -> int:
    if pd.isna(valor) or not valor:
        return 0
    return len([item for item in valor.split("|") if item])


def _ausente(serie: pd.Series) -> pd.Series:
    """Indica ausencia tanto en CSV leído como texto como en DataFrame con NaN."""
    return serie.isna() | serie.astype("string").str.strip().eq("")


@dataclass
class ResultadoLimpieza:
    filas_entrada: int
    filas_salida: int
    personas: int
    columnas: int
    filas_clasificadas: int


class LimpiadorEmpleosConCompetencias:
    """Ejecuta la limpieza y validación del dataset enriquecido."""

    def __init__(self, entrada: Path = ENTRADA, salida: Path = SALIDA) -> None:
        if not entrada.exists():
            raise FileNotFoundError(
                f"No existe el dataset enriquecido: {entrada}. "
                "Genera primero empleos_con_competencias.csv."
            )
        self.entrada = entrada
        self.salida = salida
        self.original = _leer(entrada)
        self.df = self.original.copy()

    def validar_esquema(self) -> None:
        faltantes = sorted(COLUMNAS_BASE.difference(self.df.columns))
        if faltantes:
            raise ValueError(f"Faltan columnas del contrato enriquecido: {faltantes}")
        if self.df.empty:
            raise ValueError("El dataset enriquecido está vacío.")
        if _ausente(self.df["resume_id"]).any():
            raise AssertionError("resume_id contiene valores vacíos.")
        if (~_ausente(self.df["occupation_code"])).sum() == 0:
            raise AssertionError("No existe ninguna ocupación clasificada.")

    def normalizar_categorias(self) -> None:
        nivel = self.df["university_level"].replace("", "No reportado")
        self.df["university_level"] = nivel.replace("None", "No reportado")

        self.df["es_unknown_ocupacion"] = (
            self.df["occupation_code"].eq("")
            | self.df["occupation_code"].isna()
        ).astype(str).str.title()
        self.df["es_rescatado"] = self.df["emparejado"].eq("rescatado").astype(str).str.title()
        self.df["es_vigente"] = self.df["end_date"].eq("Present").astype(str).str.title()

    def validar_competencias(self) -> None:
        numericas = self.df[CONTADORES].apply(pd.to_numeric, errors="coerce")
        clasificado = self.df["saber_skills"].eq("ok")
        if numericas.loc[clasificado].isna().any().any():
            raise AssertionError("Hay contadores vacíos en experiencias clasificadas.")
        if (numericas.loc[clasificado, "n_skills_essential"] <= 0).any():
            raise AssertionError("Hay n_skills_essential cero o negativo en experiencias clasificadas.")
        if (numericas.loc[clasificado, CONTADORES[1:]] < 0).any().any():
            raise AssertionError("Hay contadores de tipo negativos en experiencias clasificadas.")

        suma = numericas[
            ["n_skills_competence", "n_skills_knowledge", "n_skills_sin_tipo"]
        ].sum(axis=1)
        if not (suma.loc[clasificado] == numericas.loc[clasificado, "n_skills_essential"]).all():
            raise AssertionError("Los contadores de skills no cierran por experiencia.")

        for columna, contador in zip(LISTAS, CONTADORES[1:]):
            conteo = self.df[columna].map(_numero_lista)
            esperado = numericas[contador].fillna(0)
            if not (conteo == esperado).all():
                raise AssertionError(
                    f"La lista {columna!r} no coincide con {contador!r}."
                )

        sin_clasificar = ~clasificado
        if not numericas.loc[sin_clasificar].isna().all().all():
            raise AssertionError(
                "Las experiencias no clasificadas deben conservar contadores vacíos."
            )

    def validar_grano(self) -> None:
        clave = ["resume_id", "matched_code", "start_date", "end_date"]
        if self.df.duplicated(subset=clave).any():
            raise AssertionError(
                "El dataset enriquecido tiene duplicados en la llave natural."
            )

    def ejecutar(self) -> ResultadoLimpieza:
        self.validar_esquema()
        self.validar_grano()
        self.normalizar_categorias()
        self.validar_competencias()

        self.salida.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(self.salida, index=False, encoding="utf-8")

        resultado = ResultadoLimpieza(
            filas_entrada=len(self.original),
            filas_salida=len(self.df),
            personas=int(self.df["resume_id"].nunique()),
            columnas=self.df.shape[1],
            filas_clasificadas=int(self.df["saber_skills"].eq("ok").sum()),
        )
        LOG.parent.mkdir(parents=True, exist_ok=True)
        fila = {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "script": Path(__file__).name,
            "entrada": str(self.entrada),
            "salida": str(self.salida),
            "filas_entrada": resultado.filas_entrada,
            "filas_salida": resultado.filas_salida,
            "personas": resultado.personas,
            "columnas": resultado.columnas,
            "filas_clasificadas": resultado.filas_clasificadas,
            "estado": "OK",
        }
        nuevo = not LOG.exists()
        with LOG.open("a", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=list(fila))
            if nuevo:
                escritor.writeheader()
            escritor.writerow(fila)
        return resultado


def main() -> None:
    resultado = LimpiadorEmpleosConCompetencias().ejecutar()
    print(
        f"Limpieza enriquecida completada: {resultado.filas_salida:,} filas, "
        f"{resultado.columnas} columnas, {resultado.personas:,} personas."
    )


if __name__ == "__main__":
    main()
