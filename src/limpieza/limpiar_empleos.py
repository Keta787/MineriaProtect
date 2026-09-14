"""
limpiar_empleos.py
==================
Pipeline formal de limpieza del dataset integrado `empleos` (bloque 4).

Flujo (orden canonico de la guia, seccion 7.1 de la auditoria):
    DIAGNOSTICO -> DUPLICADOS -> CATEGORIAS -> FALTANTES -> OUTLIERS -> VALIDACION -> EXPORTAR

Alcance:
    - Solamente `data/03_processed/empleos.csv` (el integrado de experiencias laborales).
    - NUNCA modifica el archivo original: trabaja sobre una copia y exporta
      `data/03_processed/empleos_limpio.csv` (salida unica; el CSV se mantiene).
    - Cada fase termina con un `assert` (nivel "Excepcional"): si una regla no se
      cumple, el pipeline corta en esa fase.
    - Cada corrida persiste una bitacora de ejecucion (fecha, sha256 del original,
      conteos) en `logs/` para trazabilidad del pipeline.

Metodo (resumen de decisiones, veridadas en la auditoria de la rama):
    - Duplicados por PK natural -> 0 reales; claves cortas = pluriempleo, se conservan.
    - Nulos estructurales de ocupacion/area (mar) -> banderas, NO imputar ni borrar.
    - `university_level == 'None'` (mnar) -> re-categorizar a 'No reportado'.
    - `end_date == 'Present'` (censura) -> bandera es_vigente.
    - Outliers de duracion (IQR/Tukey) -> conservar cola larga (senal de estabilidad);
      z-score solo como comparacion, no como criterio. (dur_Q = ordinal_fin - ordinal_ini + 1,
      igual que la auditoria: misma IQR Q1=2 Q3=11 superior 24,5.)
    - 11 fechas futuras (>2026, mcar) -> eliminar filas (error de dominio; la auditoria
      contaba "1 inicio + 11 fin" = 12 contando dos veces la fila Q1 2027 -> Q1 2028).

Las cifras canonicas de la auditoria estan centralizadas en `EXPECTED` (constante):
cada assert compara el valor obtenido contra ese canon y, si difiere, reporta
obtenido vs esperado.

Como ejecutar:
    python src/limpieza/limpiar_empleos.py

Requisitos:
    pandas   (ver requirements.txt; este script no necesita pyarrow)
"""

from __future__ import annotations

import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Consola: forzar UTF-8 (evita fallos con caracteres especiales en Windows).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Renderizado: tablas HTML en Jupyter, texto en consola.
try:
    from IPython.display import display as _display
except Exception:  # consola sin IPython instalado
    def _display(obj, *args, **kwargs):
        print(obj.to_string() if hasattr(obj, "to_string") else obj)


# ---------------------------------------------------------------------------
# Configuracion (un unico punto, igual que en el cuaderno de la sesion 3)
# ---------------------------------------------------------------------------
def _raiz_proyecto() -> Path:
    """Raiz del repo: busca hacia arriba la carpeta `data/` desde este archivo."""
    p = Path(__file__).resolve().parent
    while not (p / "data").exists() and p != p.parent:
        p = p.parent
    return p


RAIZ = _raiz_proyecto()
ORIGEN = RAIZ / "data" / "03_processed" / "empleos.csv"
DESTINO_CSV = RAIZ / "data" / "03_processed" / "empleos_limpio.csv"
LOGS_DIR = RAIZ / "logs"
BITACORA_EJECUCION = LOGS_DIR / "bitacora_limpieza_empleos.csv"

ANIO_CORTE = 2026              # Anio del proyecto: fechas posteriores = error de captura.
ANIO_LIMITE_HISTORICO = 1990   # Ventana temporal historica razonable (cola documentada).
CLAVE_PRIMARIA = ["resume_id", "matched_code", "start_date", "end_date"]

# Valores canonicos verificados en la auditoria (fase 3 re-verifica estos conteos).
CANONICOS = {
    "emparejado": 3,
    "university_level": 5,
    "isco_group_label": 426,
    "occupation_label": 2966,
}

# Cifras canonicas del integrado `empleos` (auditoria secciones 7.7 y 8.2),
# centralizadas para que cualquier discrepancia falle con diagnostico claro.
EXPECTED = {
    "filas_original": 1_506_445,
    "filas_limpio": 1_506_434,
    "personas_original": 284_247,
    "duplicado_exacto": 0,
    "duplicado_pk": 0,
    "clave_corta_fin": 74_357,          # (resume_id, start_date, end_date)
    "clave_corta_codigo": 9_601,        # (resume_id, start_date, matched_code)
    "none_recategorizados": 174_036,    # literal 'None' -> 'No reportado'
    "personas_unknown": 64_508,
    "personas_historial_unknown": 2_490,
    "fuera_iqr_filas": 141_591,
    "fuera_iqr_personas": 97_954,
    "fechas_futuras": 11,
    "duracion_iqr_q1": 2.0,
    "duracion_iqr_q3": 11.0,
    "duracion_iqr_superior": 24.5,
    "duracion_maxima": 160,
}


class LimpiadorEmpleos:
    """Limpieza del integrado `empleos`: diagnostico -> ... -> exportacion.

    `self.original` es inmutable a lo largo del pipeline; toda transformacion se
    aplica sobre `self.df` (copia de trabajo). La bitacora registra cada decision.
    """

    def __init__(self) -> None:
        if not ORIGEN.exists():
            raise FileNotFoundError(
                f"No existe el dataset integrado: {ORIGEN}\n"
                "Ejecuta primero la integracion (o restaura data/03_processed/empleos.csv)."
            )
        # dtype=str: los codigos (matched_code, occupation_code, isco_group) se leen
        # como TEXTO para no perder ceros a la izquierda (p. ej. ISCO '0110').
        # keep_default_na=False + na_values=[""]: solo la celda vacia es NaN; los
        # literales 'None', 'Present' y 'unknown' se conservan como texto (pandas
        # por defecto convierte 'None' a NaN, lo que romperia la fase 3).
        self.original = pd.read_csv(
            ORIGEN, dtype=str, encoding="utf-8", keep_default_na=False, na_values=[""]
        )
        self.df = self.original.copy()
        self.bitacora: list[dict] = []

    # ------------------------------------------------------------------ utils
    def _anotar(self, columna: str, problema: str, cantidad: int,
                metodo: str, razon: str, impacto: str) -> None:
        self.bitacora.append({
            "columna": columna,
            "problema": problema,
            "cantidad": cantidad,
            "metodo": metodo,
            "razon": razon,
            "impacto": impacto,
        })

    def _ordinal_trimestre(self, serie: pd.Series) -> pd.Series:
        """'Q<n> <aaaa>' -> anio*4 + trimestre; 'Present'/no-parseable -> NaN."""
        partes = serie.str.extract(r"^Q([1-4])\s+(\d{4})$")
        anio = pd.to_numeric(partes[1], errors="coerce")
        trimestre = pd.to_numeric(partes[0], errors="coerce")
        return anio * 4 + trimestre

    def _extraer_anio(self, columna: str) -> pd.Series:
        """Anio (entero) de una columna 'Qn AAAA'."""
        return pd.to_numeric(
            self.df[columna].str.extract(r"(\d{4})$", expand=False), errors="coerce"
        )

    def _duracion_trimestres(self) -> pd.Series:
        """Duracion por fila en trimestres (inclusiva). 'Present' (sin fin) -> NaN.

        Convencion de la auditoria (seccion 8.2): duracion = ordinal_fin - ordinal_ini + 1;
        un empleo de un solo trimestre dura 1. Con esta definicion se reproducen
        Q1=2, Q3=11, superior=24,5, mediana=5 y maximo=160.
        """
        return self._ordinal_trimestre(self.df["end_date"]) - self._ordinal_trimestre(
            self.df["start_date"]
        ) + 1

    def _limites_iqr(self, valores: pd.Series) -> dict:
        """Limites IQR regla de Tukey: [Q1 - 1.5*IQR, Q3 + 1.5*IQR]."""
        q1, q3 = valores.quantile([0.25, 0.75])
        iqr = q3 - q1
        return {"q1": q1, "q3": q3, "iqr": iqr,
                "inferior": q1 - 1.5 * iqr, "superior": q3 + 1.5 * iqr}

    # ------------------------------------------------------------- fase 1
    def fase1_diagnostico(self) -> pd.DataFrame:
        """Dimensiones, tipos, nulos, cardinalidades y fechas (nada se toca)."""
        df = self.original
        print("=" * 78)
        print("FASE 1 DE 7 - DIAGNOSTICO (sobre el original, sin modificar)")
        print("=" * 78)
        print(f"Filas: {len(df):,} | Columnas: {df.shape[1]} | Personas: {df['resume_id'].nunique():,}")
        assert int(df["resume_id"].nunique()) == EXPECTED["personas_original"], (
            f"Personas originales {df['resume_id'].nunique()} != {EXPECTED['personas_original']}"
        )
        print("Tipos de dato por columna:")
        _display(df.dtypes.rename("tipo").to_frame())

        nulos = df.isna().sum()
        nulos = nulos[nulos > 0]
        print("Nulos por columna:")
        print(nulos.to_string() if len(nulos) else "ninguno")

        print("Duplicados exactos:", int(df.duplicated().sum()))
        print("Rango de fechas:")
        for col in ["start_date", "end_date"]:
            anios = self._extraer_anio(col).dropna()
            print(f"  {col}: {int(anios.min())}-{int(anios.max())}")

        return df

    # ------------------------------------------------------------- fase 2
    def fase2_duplicados(self) -> None:
        """Duplicados: 0 exactos y 0 por PK natural; claves cortas = pluriempleo."""
        df = self.df
        exactos = int(df.duplicated().sum())
        pk = int(df.duplicated(subset=CLAVE_PRIMARIA).sum())

        # Claves cortas: "filas extra" (keep='first', lo que se eliminaria si se
        # deduplicara por esa clave) es la convencion de la auditoria.
        corta_start_end = int(df.duplicated(subset=["resume_id", "start_date", "end_date"], keep="first").sum())
        corta_start_code = int(df.duplicated(subset=["resume_id", "start_date", "matched_code"], keep="first").sum())

        print("=" * 78)
        print("FASE 2 DE 7 - DUPLICADOS")
        print("=" * 78)
        print(f"Duplicados exactos: {exactos} | Por PK natural: {pk}")
        print("Claves cortas = pluriempleo/transicion real (filas extra si se deduplicara):")
        print(f"  (resume, start, end)   = {corta_start_end:,} | (resume, start, code) = {corta_start_code:,}")

        # Nivel Excepcional: ningun duplicado real; cifras de claves cortas verificadas.
        assert exactos == EXPECTED["duplicado_exacto"], (
            f"Duplicados exactos: {exactos} != {EXPECTED['duplicado_exacto']}"
        )
        assert pk == EXPECTED["duplicado_pk"], (
            f"Duplicados por llave natural: {pk} != {EXPECTED['duplicado_pk']}"
        )
        assert corta_start_end == EXPECTED["clave_corta_fin"], (
            f"Clave corta (start,end): {corta_start_end} != {EXPECTED['clave_corta_fin']}"
        )
        assert corta_start_code == EXPECTED["clave_corta_codigo"], (
            f"Clave corta (start,code): {corta_start_code} != {EXPECTED['clave_corta_codigo']}"
        )

    # ------------------------------------------------------------- fase 3
    def fase3_categorias(self) -> None:
        """Re-verifica las categorias canonicas antes de tocar nada."""
        df = self.original
        print("=" * 78)
        print("FASE 3 DE 7 - CATEGORIAS (re-verificacion de cardinalidades)")
        print("=" * 78)
        tabla = {}
        for col, esperado in CANONICOS.items():
            # Los conteos canonicos de la auditoria excluyen el NaN (dropna=True),
            # p. ej. 2.966 etiquetas de ocupacion + 1 categoria NaN, 426 areas ISCO.
            obtenido = int(df[col].nunique())
            tabla[col] = {"esperado": esperado, "obtenido": obtenido, "ok": obtenido == esperado}
        _display(pd.DataFrame(tabla).T)
        for col, fila in tabla.items():
            assert fila["ok"], f"Cardinalidad no canonica en {col}: {fila['obtenido']} != {fila['esperado']}"

        print("\nDistribucion emparejado:")
        _display(df["emparejado"].value_counts(dropna=False).rename("cantidad").to_frame())
        print("Distribucion university_level:")
        _display(df["university_level"].value_counts(dropna=False).rename("cantidad").to_frame())

        # Aplicar caso B (MNAR): el literal 'None' pasa a categoria propia 'No reportado'.
        # No se imputa moda: fabricaria educacion para 174.036 filas.
        n_none = int(self.df["university_level"].eq("None").sum())
        self.df["university_level"] = self.df["university_level"].replace({"None": "No reportado"})
        assert int(self.df["university_level"].eq("None").sum()) == 0, "Queda 'None' sin re-categorizar"
        assert n_none == EXPECTED["none_recategorizados"], (
            f"'None' contados: {n_none} != {EXPECTED['none_recategorizados']}"
        )
        assert int(self.df["university_level"].eq("No reportado").sum()) == n_none, "Conteo 'No reportado' no coincide"
        print(f"\nRe-categorizacion caso B (MNAR): 'None' ({n_none:,}) -> 'No reportado'")
        _display(self.df["university_level"].value_counts(dropna=False).rename("cantidad").to_frame())
        self._anotar(
            "university_level", "Literal 'None' (MNAR)",
            n_none,
            "Re-categorizar a 'No reportado'",
            "Imputar la moda (Secondary school) fabricaria educacion para esa fila.",
            "Categoria propia, sin None restante.",
        )

    # ------------------------------------------------------------- fase 4
    def fase4_faltantes(self) -> None:
        """Banderas A-C (MAR estructural + censura); sin imputar ni borrar."""
        df = self.df
        df["es_unknown_ocupacion"] = df["emparejado"].eq("unknown")
        df["es_rescatado"] = df["emparejado"].eq("rescatado")
        df["es_vigente"] = df["end_date"].eq("Present")

        n_unknown = int(df["es_unknown_ocupacion"].sum())
        n_rescatado = int(df["es_rescatado"].sum())
        n_vigente = int(df["es_vigente"].sum())
        n_ocupacion_nan = int(df["occupation_code"].isna().sum())
        n_explicado = int((df["occupation_code"].isna()
                           & (df["es_unknown_ocupacion"] | df["es_rescatado"])).sum())

        personas_unknown = int(df.loc[df["es_unknown_ocupacion"], "resume_id"].nunique())
        completo_unknown = int(
            df.groupby("resume_id")["es_unknown_ocupacion"].mean().eq(1.0).sum()
        )

        print("=" * 78)
        print("FASE 4 DE 7 - FALTANTES (banderas A-C, sin imputar)")
        print("=" * 78)
        print(f"es_unknown_ocupacion : {n_unknown:,} (personas: {personas_unknown:,})")
        print(f"es_rescatado         : {n_rescatado:,}")
        print(f"es_vigente ('Present') : {n_vigente:,}")
        print(f"occupation_code NaN  : {n_ocupacion_nan:,} | explicados por bandera: {n_explicado:,}")
        print(f"Personas con historial completo 'unknown': {completo_unknown:,}")

        assert n_explicado == n_ocupacion_nan, "Quedan nulos de ocupacion sin bandera"
        assert n_unknown + n_rescatado == n_ocupacion_nan, "Banderas no reconciliadas con NaN"
        assert personas_unknown == EXPECTED["personas_unknown"], (
            f"Personas afectadas por 'unknown': {personas_unknown} != {EXPECTED['personas_unknown']}"
        )
        assert completo_unknown == EXPECTED["personas_historial_unknown"], (
            f"Personas con historial completo 'unknown': {completo_unknown} != "
            f"{EXPECTED['personas_historial_unknown']}"
        )

        self._anotar(
            "occupation_code/isco_*", "NaN estructural (MAR)",
            n_ocupacion_nan,
            "Banderas es_unknown_ocupacion y es_rescatado",
            "El NaN dice 'sin emparejar', no 'sin dato'; imputar inventaria ocupaciones.",
            f"Conserva {personas_unknown:,} personas ({completo_unknown:,} con historial completo 'unknown').",
        )
        self._anotar(
            "end_date", "'Present' (censura)",
            n_vigente,
            "Bandera es_vigente",
            "El empleo sigue y no tiene fin real; no se inventa fecha.",
            "Duración indefinida marcada.",
        )

    # ------------------------------------------------------------- fase 5
    def fase5_outliers(self) -> None:
        """IQR sobre el original (cola larga: conservar) y fechas futuras (eliminar)."""
        dur = self._duracion_trimestres().dropna()  # sobre la copia aun con las 11 futuras
        limites = self._limites_iqr(dur)
        fuera = (dur < limites["inferior"]) | (dur > limites["superior"])
        personas_fuera = int(self.df.loc[dur[fuera].index, "resume_id"].nunique())
        z = (dur - dur.mean()) / dur.std()
        n_z3 = int((z.abs() > 3).sum())

        def _es_futura():
            f_ini = self._extraer_anio("start_date")
            f_fin = self._extraer_anio("end_date")
            return (f_ini > ANIO_CORTE) | (f_fin > ANIO_CORTE)

        n_futuras = int(_es_futura().sum())

        print("=" * 78)
        print("FASE 5 DE 7 - OUTLIERS")
        print("=" * 78)
        print(f"IQR (Tukey) sobre dur_Q: Q1={limites['q1']:.2f} Q3={limites['q3']:.2f} "
              f"IQR={limites['iqr']:.2f} | limites [{limites['inferior']:.2f}, {limites['superior']:.2f}]")
        print(f"Fuera de limites: {int(fuera.sum()):,} filas / {personas_fuera:,} personas (todas por arriba)")
        print(f"|z| > 3 (solo comparacion): {n_z3:,}")
        print(f"Fechas futuras (anio > {ANIO_CORTE}): {n_futuras}")

        assert limites["q1"] == EXPECTED["duracion_iqr_q1"], (
            f"Q1 duracion {limites['q1']} != {EXPECTED['duracion_iqr_q1']}"
        )
        assert limites["q3"] == EXPECTED["duracion_iqr_q3"], (
            f"Q3 duracion {limites['q3']} != {EXPECTED['duracion_iqr_q3']}"
        )
        assert limites["superior"] == EXPECTED["duracion_iqr_superior"], (
            f"Limite IQR superior {limites['superior']} != {EXPECTED['duracion_iqr_superior']}"
        )
        assert int(dur.max()) == EXPECTED["duracion_maxima"], (
            f"Duracion maxima {int(dur.max())} != {EXPECTED['duracion_maxima']}"
        )
        assert int(fuera.sum()) == EXPECTED["fuera_iqr_filas"], (
            f"Filas fuera de IQR: {int(fuera.sum())} != {EXPECTED['fuera_iqr_filas']}"
        )
        assert personas_fuera == EXPECTED["fuera_iqr_personas"], (
            f"Personas fuera de IQR: {personas_fuera} != {EXPECTED['fuera_iqr_personas']}"
        )
        assert n_futuras == EXPECTED["fechas_futuras"], (
            f"Fechas futuras: {n_futuras} != {EXPECTED['fechas_futuras']}"
        )

        self._anotar(
            "dur_Q (derivada)", "Cola larga (>=25 trimestres fuera del IQR)",
            int(fuera.sum()),
            "Conservar (sin winsorizar)",
            "Carreras de ~40 anios son estabilidad real; borrar segmenta personas completas.",
            "0 filas eliminadas por atipicos.",
        )

        # Unicas filas eliminadas: fechas futuras (MCAR, error de dominio).
        antes = len(self.df)
        futura = _es_futura()
        self.df = self.df.loc[~futura].reset_index(drop=True)
        eliminadas = antes - len(self.df)
        print(f"Fechas futuras eliminadas: {eliminadas} | filas tras la fase: {len(self.df):,}")
        assert eliminadas == EXPECTED["fechas_futuras"], (
            f"Fechas futuras eliminadas: {eliminadas} != {EXPECTED['fechas_futuras']}"
        )
        assert int(_es_futura().sum()) == 0, "Quedan filas futuras tras la limpieza"

        self._anotar(
            "start_date/end_date", f"Fechas con anio > {ANIO_CORTE} (MCAR)",
            n_futuras,
            "Eliminar filas",
            "Fecha posterior al anio del proyecto es imposible; <1% y aislada (error de captura).",
            f"{n_futuras} filas eliminadas.",
        )

    # ------------------------------------------------------------- fase 6
    def fase6_validacion(self) -> None:
        """Tabla de umbrales de aceptacion (seccion 7.7) + asserts finales."""
        df = self.df
        dups = int(df.duplicated().sum())
        dups_pk = int(df.duplicated(subset=CLAVE_PRIMARIA).sum())
        sin_bandera = ["resume_id", "start_date", "end_date", "university_level",
                       "matched_code", "emparejado"]
        nulos_restantes = int(df[sin_bandera].isna().sum().sum())
        ocupacion_huerfanos = int(
            (df["occupation_code"].isna()
             & ~(df["es_unknown_ocupacion"] | df["es_rescatado"])).sum()
        )
        futuras = int(((self._extraer_anio("start_date") > ANIO_CORTE)
                       | (self._extraer_anio("end_date") > ANIO_CORTE)).sum())
        start_end = int((self._duracion_trimestres() < 0).sum())
        personas = int(df["resume_id"].nunique())

        umbrales = [
            ("Duplicados exactos", dups, 0),
            ("Duplicados por PK natural", dups_pk, 0),
            ("Nulos restantes sin bandera", nulos_restantes, 0),
            ("Nulos de ocupacion sin bandera", ocupacion_huerfanos, 0),
            ("Fechas futuras", futuras, 0),
            ("start > end", start_end, 0),
        ]
        tabla = pd.DataFrame(umbrales, columns=["criterio", "valor", "esperado"])
        tabla["ok"] = tabla["valor"].eq(tabla["esperado"])

        print("=" * 78)
        print("FASE 6 DE 7 - VALIDACION (tabla 7.7)")
        print("=" * 78)
        _display(tabla)
        print(f"Impacto: {len(self.original):,} filas / {self.original['resume_id'].nunique():,} personas "
              f"-> {len(df):,} filas / {personas:,} personas "
              f"(eliminadas: {len(self.original) - len(df)} filas por fechas futuras).")
        assert bool(tabla["ok"].all()), "Algun umbral de aceptacion no se cumple"
        assert len(df) == len(self.original) - EXPECTED["fechas_futuras"], (
            f"Filas eliminadas: {len(self.original) - len(df)} != "
            f"{EXPECTED['fechas_futuras']} (solo fechas futuras)"
        )
        assert len(df) == EXPECTED["filas_limpio"], (
            f"Filas finales: {len(df)} != {EXPECTED['filas_limpio']} (canonico de la auditoria)"
        )

    # ------------------------------------------------------------- fase 7
    def fase7_exportar(self) -> None:
        """Exporta el limpio (CSV, salida unica) sin tocar el original."""
        print("=" * 78)
        print("FASE 7 DE 7 - EXPORTAR")
        print("=" * 78)
        assert len(self.original) == EXPECTED["filas_original"], (
            f"El original cambio: {len(self.original)} != {EXPECTED['filas_original']}"
        )

        DESTINO_CSV.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(DESTINO_CSV, index=False, encoding="utf-8")
        print(f"Escrito: {DESTINO_CSV} ({DESTINO_CSV.stat().st_size / 1e6:.1f} MB)")
        print("El CSV es la salida unica del bloque 4 (los codigos conservan sus ceros a la izquierda).")
        print(f"Columnas finales ({self.df.shape[1]}): {', '.join(self.df.columns)}")
        print("El archivo original data/03_processed/empleos.csv NO fue modificado.")

    # ------------------------------------------------------------- bitacora
    def _persistir_bitacora_ejecucion(self) -> None:
        """Guarda una fila de trazabilidad en logs/bitacora_limpieza_empleos.csv.

        Solo se registran corridas que completaron las 7 fases (si un `assert`
        corta, la excepcion propaga y no llega aqui).
        """
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        filas = {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "script": Path(__file__).name,
            "python": sys.version.split()[0],
            "input_sha256": self._sha256(ORIGEN),
            "filas_original": len(self.original),
            "personas_original": int(self.original["resume_id"].nunique()),
            "filas_limpio": len(self.df),
            "personas_limpio": int(self.df["resume_id"].nunique()),
            "estado": "OK",
        }
        nuevo = not BITACORA_EJECUCION.exists()
        with BITACORA_EJECUCION.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(filas))
            if nuevo:
                writer.writeheader()
            writer.writerow(filas)
        print(f"Bitacora de ejecucion persistida: {BITACORA_EJECUCION}")

    @staticmethod
    def _sha256(ruta: Path) -> str:
        """SHA-256 del archivo de entrada (huella para reproducir la corrida)."""
        h = hashlib.sha256()
        with ruta.open("rb") as fh:
            for bloque in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(bloque)
        return h.hexdigest()

    # ------------------------------------------------------------- run
    def ejecutar(self) -> None:
        """Orden canonico completo con bitacora al final."""
        self.fase1_diagnostico()
        self.fase2_duplicados()
        self.fase3_categorias()
        self.fase4_faltantes()
        self.fase5_outliers()
        self.fase6_validacion()
        self.fase7_exportar()

        print("\n" + "=" * 78)
        print("BITACORA DE LA LIMPIEZA (trazabilidad original -> limpio)")
        print("=" * 78)
        _display(pd.DataFrame(self.bitacora))
        self._persistir_bitacora_ejecucion()


def main() -> None:
    LimpiadorEmpleos().ejecutar()
    print("\nLimpieza completada sin errores.")


if __name__ == "__main__":
    main()