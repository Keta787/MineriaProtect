# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "nbformat>=5.10",
# ]
# ///
"""Construye la versión Plotly del notebook EDA_Columnas_Objetivo.

Genera `notebooks/EDA_Columnas_Objetivo.ipynb` sin salidas; la ejecución se hace
después con nbconvert/nbclient para persistir las figuras interactivas.

Uso:
    uv run analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/construir_notebook_plotly.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path.cwd()
for _ in range(10):
    if (ROOT / "data").exists():
        break
    ROOT = ROOT.parent
else:
    raise SystemExit("No se encontró data/")

DESTINO = ROOT / "notebooks" / "EDA_Columnas_Objetivo.ipynb"


def md(texto: str) -> nbformat.NotebookNode:
    return new_markdown_cell(textwrap.dedent(texto).strip())


def code(texto: str) -> nbformat.NotebookNode:
    return new_code_cell(textwrap.dedent(texto).strip())


celdas: list[nbformat.NotebookNode] = []

# --------------------------------------------------------------------------- 0
celdas += [
    md(
        """
        # EDA enfocado a las columnas objetivo — JobPath

        **Proyecto:** JobPath (Minería de Datos — UNIMINUTO Ibagué, 2026-2)

        **Dataset:** `data/03_processed/empleos_limpio_con_competencias .csv` (376.567 filas × 23 columnas)

        **Sesión scientific-eda:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`

        **Fecha:** 2026-10-25 · **Versión 2.0:** pandas para los cálculos + **Plotly** para las gráficas

        **Objetivo:** hacer un EDA descriptivo enfocado exclusivamente en las columnas objetivo
        (`Resume_id`, `Period_Time`, `University_Level`, `Isco_group`/`ISCO_group`,
        `Skill_competence`, `Skill_Knowledge`), con **26 figuras interactivas**. Cada figura
        se presenta con: ¿qué muestra?, ¿qué patrón evidencia? y ¿para qué ayuda a determinar?

        **Visualización:** todas las figuras se generan con `plotly.express` /
        `plotly.graph_objects`. El notebook embebe `plotly.js` una sola vez, así que las
        gráficas son interactivas **sin conexión a internet**. Además, cada figura se guarda
        como HTML interactivo y como imagen WebP en
        `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/plots/figuras_plotly/`.

        **Codificación:** UTF-8

        > **Grano del dataset:** 1 fila = 1 experiencia laboral, **NO** 1 persona.
        > Cualquier porcentaje de este notebook es *por experiencia*, no por persona.
        """
    ),
    md(
        """
        ## Índice

        1. [Importación de librerías](#1-importación-de-librerías)
        2. [Contexto, metodología y mapa de figuras](#2-contexto-metodología-y-mapa-de-figuras)
        3. [Carga de datos y preparación](#3-carga-de-datos-y-preparación)
        4. [Análisis univariado por columna objetivo](#4-análisis-univariado-por-columna-objetivo)
           - 4.1 `Resume_id` · 4.2 `Period_Time` · 4.3 `University_Level`
           - 4.4 `Isco_group` / `ISCO_group` · 4.5 `Skill_competence` · 4.6 `Skill_Knowledge`
        5. [Análisis bivariado](#5-análisis-bivariado)
        6. [Análisis multivariado y redundancia](#6-análisis-multivariado-y-redundancia)
        7. [Calidad de datos](#7-calidad-de-datos)
        8. [Hallazgos, conclusiones y recomendaciones](#8-hallazgos-conclusiones-y-recomendaciones)
        9. [Reproducibilidad](#9-reproducibilidad)
        """
    ),
    md(
        """
        ## 1. Importación de librerías

        **Todas las librerías necesarias se importan en esta única celda de código.** Se usa
        `pandas` para las agregaciones y `plotly` para las visualizaciones interactivas.
        """
    ),
    code(
        """
        # === TODAS LAS LIBRERÍAS NECESARIAS ===
        import warnings
        import textwrap
        from pathlib import Path

        warnings.filterwarnings("ignore")

        import numpy as np
        import pandas as pd

        import plotly
        import plotly.express as px
        import plotly.graph_objects as go
        import plotly.io as pio
        from plotly.subplots import make_subplots
        from plotly.offline import init_notebook_mode

        from IPython.display import display

        # plotly.js embebido: las figuras funcionan sin internet dentro del notebook
        init_notebook_mode(connected=False)
        pio.templates.default = "plotly_white"

        print("Librerías cargadas correctamente")
        print("pandas:", pd.__version__, "| plotly:", plotly.__version__)
        """
    ),
    md(
        """
        ## 2. Contexto, metodología y mapa de figuras

        - Se sigue la skill `scientific-eda`: contexto primero, journal append-only, scripts
          reproducibles con **PEP723 + `uv run`** y figuras guardadas en la sesión de análisis.
        - **Codificación:** UTF-8.
        - **Grano:** 1 fila = 1 experiencia laboral (`resume_id` agrupa la trayectoria de una persona).
        - **Regla clave:** `Skill_competence` y `Skill_Knowledge` describen lo que **exige el oficio
          según ESCO**, **NO** lo que sabe o posee la persona.
        - **Honestidad visual:** barras ordenadas por frecuencia, eje desde 0, porcentajes que suman
          100 cuando corresponde, `n` visible, un solo idioma en títulos/ejes y **ningún gráfico de
          pastel**. Los nombres originales ISCO-08 en inglés se conservan para trazabilidad.

        ### Mapeo de las columnas objetivo

        | Columna solicitada | Columna real en el dataset | Tratamiento |
        |---|---|---|
        | `Resume_id` | `resume_id` | Identificador de persona. 1 fila = 1 experiencia, NO 1 persona. |
        | `Period_Time` | Creada desde `start_date` y `end_date` | Concatenación `inicio - fin`; si el empleo sigue vigente se conserva `Present`. |
        | `University_Level` | `university_level` | Valores canónicos: `No reportado`, `Secondary school`, `Bachelor`, `Master`, `PhD`. En este archivo los vacíos ya vienen como `No reportado` literal; la normalización se mantiene como salvaguarda. |
        | `Isco_group` | `isco_group_label` (prioritario) / `isco_group` | Se unifican; 424 grupos ISCO-08. |
        | `Skill_competence` | `n_skills_competence` | Nº de competencias (saber hacer) que **exige el oficio** según ESCO. |
        | `Skill_Knowledge` | `n_skills_knowledge` | Nº de conocimientos (saber) que **exige el oficio** según ESCO. |
        | `ISCO_group` | `isco_group_label` / `isco_group` | Unificado con `Isco_group`; se conserva el código para derivar el gran grupo (1.º dígito). |

        ### Mapa de figuras

        | Sección | Pregunta que responde | Figuras |
        |---|---|---|
        | `Resume_id` | ¿Cuántas experiencias aporta cada persona? ¿Hay concentración? | 01–02 |
        | `Period_Time` | ¿Cuándo ocurren las experiencias, cuánto duran y cómo se censuran? | 03–06 |
        | `University_Level` | ¿Cómo se compone el nivel educativo? | 07 |
        | `Isco_group` | ¿Qué oficios dominan y cuánta cola larga hay? | 08–11 |
        | `Skill_competence` | ¿Cuánta competencia práctica exige cada oficio? | 12–13 |
        | `Skill_Knowledge` | ¿Cuánto conocimiento exige cada oficio? | 14–15 |
        | Cruces | Educación × oficio, competencias × nivel y duración × nivel | 16–21 |
        | Multivariado | Redundancia, flujos y fuerza de asociación | 22–24 |
        | Calidad | Cobertura ESCO, nulos y valores declarados | 25–26 |
        """
    ),
    md(
        """
        ## 3. Carga de datos y preparación

        ### ¿Qué vamos a hacer?

        Cargar `empleos_limpio_con_competencias .csv` con **encoding UTF-8**, crear `Period_Time`,
        normalizar `University_Level`, unificar `Isco_group`/`ISCO_group`, convertir los contadores
        ESCO a numéricos y derivar de las fechas trimestrales: año/trimestre de inicio, año de fin,
        duración observada y década. También se deriva el **gran grupo ISCO** (primer dígito del
        código de 4 dígitos) y se definen los helpers de estilo y exportación de Plotly.

        ### ¿Por qué es relevante?

        Deja una base trazable y consistente para todas las figuras, y evita repetir cálculos en
        cada celda. Las validaciones con `assert` detienen la ejecución si algún supuesto deja de
        cumplirse (por ejemplo, un nivel educativo inesperado).
        """
    ),
    code(
        """
        # ---------------- Raíz del proyecto ----------------
        root = Path.cwd()
        for p in [root, *root.parents]:
            if (p / "data").exists():
                root = p
                break

        SESSION = root / "analysis" / "2026-10-25T16-00-00-eda-columnas-objetivo"
        PLOTS = SESSION / "plots" / "figuras_plotly"
        PLOTS.mkdir(parents=True, exist_ok=True)

        # ---------------- Carga ----------------
        data_path = root / "data" / "03_processed" / "empleos_limpio_con_competencias .csv"
        df = pd.read_csv(data_path, encoding="utf-8", dtype=str,
                         keep_default_na=False, na_values=[""])

        print("Dataset:", data_path.name)
        print(f"Dimensiones: {df.shape[0]:,} filas x {df.shape[1]} columnas")
        print("Personas únicas (resume_id):", f"{df['resume_id'].nunique():,}")

        # ---------------- Columnas objetivo ----------------
        df["Period_Time"] = (df["start_date"].astype(str).str.strip()
                             + " - "
                             + df["end_date"].astype(str).str.strip())

        CANON_UNIV = ["No reportado", "Secondary school", "Bachelor", "Master", "PhD"]
        df["University_Level_norm"] = df["university_level"].astype(str).str.strip()
        df.loc[df["University_Level_norm"].isin(["", "nan", "None", "NaN"]),
               "University_Level_norm"] = "No reportado"
        df["University_Level_norm"] = df["University_Level_norm"].fillna("No reportado")

        df["Isco_group_unif"] = df["isco_group_label"].astype(str).str.strip()
        df.loc[df["Isco_group_unif"].isin(["", "nan", "None", "NaN"]),
               "Isco_group_unif"] = "SIN_GRUPO"

        # ---------------- Contadores ESCO a numérico ----------------
        for origen, destino in [
            ("n_skills_competence", "n_skills_competence_num"),
            ("n_skills_knowledge", "n_skills_knowledge_num"),
            ("n_skills_essential", "n_skills_essential_num"),
            ("n_skills_sin_tipo", "n_skills_sin_tipo_num"),
            ("veces_ese_oficio", "veces_ese_oficio_num"),
        ]:
            df[destino] = pd.to_numeric(df[origen], errors="coerce")

        # ---------------- Fechas trimestrales: ordinal, duración y década ----------------
        patron_q = r"Q([1-4])\\s+(\\d{4})"
        _ini = df["start_date"].str.extract(patron_q)
        _fin = df["end_date"].str.extract(patron_q)

        df["start_q"] = pd.to_numeric(_ini[0], errors="coerce")
        df["start_year"] = pd.to_numeric(_ini[1], errors="coerce")
        df["end_year"] = pd.to_numeric(_fin[1], errors="coerce")
        df["start_ord"] = df["start_year"] * 4 + df["start_q"]
        df["end_ord"] = df["end_year"] * 4 + pd.to_numeric(_fin[0], errors="coerce")

        df["es_vigente_bool"] = df["end_date"].astype(str).str.strip().eq("Present")
        # Duración inclusiva: fin - inicio + 1. Los empleos vigentes quedan como NaN (censura).
        df["dur_trim"] = (df["end_ord"] - df["start_ord"] + 1).where(~df["es_vigente_bool"])
        df["decada"] = (df["start_year"] // 10 * 10).astype("Int64")

        # ---------------- Gran grupo ISCO (primer dígito del código) ----------------
        MAJOR_ISCO = {
            "1": "1 · Gerentes y directivos",
            "2": "2 · Profesionales y científicos",
            "3": "3 · Técnicos y profesionales asociados",
            "4": "4 · Apoyo administrativo",
            "5": "5 · Servicios y vendedores",
            "6": "6 · Agricultura y pesca",
            "7": "7 · Oficiales y artesanos",
            "8": "8 · Operadores de máquinas",
            "9": "9 · Ocupaciones elementales",
            "0": "0 · Fuerzas armadas",
        }
        df["ISCO_major"] = (df["isco_group"].astype(str).str.strip().str[0]
                            .map(MAJOR_ISCO).fillna("Sin grupo"))

        # ---------------- Validaciones ----------------
        assert df["Period_Time"].notna().all()
        assert set(df["University_Level_norm"]) <= set(CANON_UNIV)
        assert df["dur_trim"].dropna().gt(0).all()
        assert int(df["n_skills_competence_num"].notna().sum()) == int(df["saber_skills"].eq("ok").sum())
        print("Validaciones OK: Period_Time completo, niveles canónicos, duración > 0 y cobertura ESCO consistente")

        # ---------------- Paleta, etiquetas y helpers ----------------
        C_AZUL, C_VERDE, C_NARANJA = "#5B8DB8", "#35754F", "#E39A50"
        C_GRIS, C_ROJO, C_TEXTO = "#C8C8C8", "#7A2626", "#1A1A1A"

        COLOR_NIVEL = {
            "No reportado": C_GRIS,
            "Secondary school": C_NARANJA,
            "Bachelor": C_AZUL,
            "Master": C_VERDE,
            "PhD": C_ROJO,
        }
        NIVEL_ES = {
            "No reportado": "No reportado",
            "Secondary school": "Secundaria",
            "Bachelor": "Pregrado",
            "Master": "Maestría",
            "PhD": "Doctorado",
        }
        OFICIO_ES = {
            "Shop sales assistants": "Vendedores de tienda",
            "Administrative and executive secretaries": "Secretarios administrativos",
            "Freight handlers": "Manipuladores de carga",
            "Secondary education teachers": "Profesores de secundaria",
            "Social work associate professionals": "Trabajadores sociales (asociados)",
            "Waiters": "Meseros",
            "Cleaners and helpers in offices, hotels and other establishments": "Personal de limpieza",
            "Child care workers": "Cuidadores de niños",
            "Cashiers and ticket clerks": "Cajeros y expendedores",
            "Kitchen helpers": "Ayudantes de cocina",
            "Retail and wholesale trade managers": "Gerentes de comercio",
            "Manufacturing labourers not elsewhere classified": "Peones de manufactura",
            "Accounting and bookkeeping clerks": "Auxiliares de contabilidad",
            "Accounting associate professionals": "Técnicos contables",
            "Advertising and marketing professionals": "Profesionales de publicidad y marketing",
            "supply chain assistant": "Asistente de cadena de suministro",
            "factory hand": "Operario de fábrica",
            "building cleaner": "Limpiador de edificios",
            "waiter/waitress": "Mesero/a",
            "kitchen assistant": "Ayudante de cocina",
            "cashier": "Cajero/a",
            "warehouse worker": "Trabajador de almacén",
            "shop assistant": "Vendedor de tienda",
            "sales assistant": "Asistente comercial",
            "administrative assistant": "Asistente administrativo",
        }

        mil = lambda n: f"{int(n):,}".replace(",", ".")
        pct_es = lambda v, d=1: f"{v:.{d}f}".replace(".", ",")


        def guardar(fig, nombre, alto=600, ancho=1150, margen_b=70, margen_l=80, margen_r=40):
            \"\"\"Aplica estilo común, exporta HTML + WebP y muestra la figura.\"\"\"
            fig.update_layout(
                template="plotly_white",
                height=alto,
                font=dict(family="Segoe UI, Arial, sans-serif", size=12, color=C_TEXTO),
                title=dict(x=0.01, xanchor="left", font=dict(size=17)),
                margin=dict(l=margen_l, r=margen_r, t=95, b=margen_b),
                hoverlabel=dict(bgcolor="white", font_size=12),
                paper_bgcolor="white",
                plot_bgcolor="white",
            )
            fig.update_xaxes(gridcolor="rgba(0,0,0,.08)", zeroline=False)
            fig.update_yaxes(gridcolor="rgba(0,0,0,.08)", zeroline=False)
            fig.write_html(PLOTS / f"{nombre}.html", include_plotlyjs="directory",
                           config={"displayModeBar": False})
            try:
                fig.write_image(PLOTS / f"{nombre}.webp", width=ancho, height=alto, scale=1)
            except Exception as exc:  # kaleido/Chrome puede no estar disponible
                print(f"[aviso] No se pudo exportar {nombre}.webp: {exc}")
            fig.show(config={"displayModeBar": False, "responsive": True})


        print("Preparación completada")
        df[["resume_id", "Period_Time", "University_Level_norm", "Isco_group_unif",
            "n_skills_competence", "n_skills_knowledge", "start_year", "dur_trim"]].head()
        """
    ),
    md(
        """
        **¿Qué muestra la salida?** Las primeras filas del dataset ya preparado, con las columnas
        objetivo y las derivadas de fecha/duración.

        **¿Qué patrón evidencia?** `Period_Time` combina inicio y fin; los contadores ESCO llegan como
        texto y se convierten a numérico; la duración es `NaN` cuando el empleo sigue vigente.

        **Hallazgos de la preparación:** el archivo tiene **376.567 experiencias** y **71.061 personas**.
        `university_level` **no tiene nulos reales** en este archivo: sus 42.807 valores ausentes vienen
        como la etiqueta literal `No reportado`. `isco_group_label` sí tiene **25.805 nulos** (6,85 %) y
        los contadores ESCO tienen **28.304 nulos** (7,52 %), concentrados en las filas
        `saber_skills = no_clasificado`.
        """
    ),
]
# --------------------------------------------------------------------------- 4
celdas += [
    md(
        """
        ## 4. Análisis univariado por columna objetivo

        Cada columna objetivo se analiza con al menos una figura interactiva. Antes de cada figura
        se explica **qué se va a analizar y por qué**; después, **qué muestra, qué patrón evidencia,
        para qué ayuda y el hallazgo**. Los valores citados salen de la ejecución de este notebook
        y del resumen verificable de la sesión.
        """
    ),
]

# ---------------------------------------------------------------- 4.1 Resume_id
celdas += [
    md(
        """
        ### 4.1 `Resume_id` (identificador de persona)

        **¿Qué vamos a analizar?** La diferencia entre el total de filas (experiencias laborales) y
        las personas únicas identificadas por `resume_id`.

        **¿Por qué es relevante?** El grano del dataset es **1 fila = 1 experiencia laboral, NO 1
        persona**. Si se ignora, cualquier porcentaje se interpreta mal.
        """
    ),
    code(
        """
        n_filas = len(df)
        n_personas = df["resume_id"].nunique()

        fig = go.Figure(go.Bar(
            x=["Experiencias laborales<br>(filas)", "Personas únicas<br>(resume_id)"],
            y=[n_filas, n_personas],
            marker_color=[C_AZUL, C_VERDE],
            width=0.5,
            text=[mil(n_filas), mil(n_personas)],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}<br>%{y:,}<extra></extra>",
        ))
        fig.add_annotation(
            x=0.5, y=n_filas * 0.52, xref="paper", yref="y", showarrow=False,
            text=f"<b>{n_filas / n_personas:.2f}</b> experiencias por persona<br>en promedio",
            font=dict(size=15, color="#333"),
        )
        fig.update_layout(
            title="Resume_id: el dataset tiene 5,3 experiencias por persona, no una",
            xaxis_title="", yaxis_title="Cantidad de registros", showlegend=False,
        )
        fig.update_yaxes(range=[0, n_filas * 1.15])

        guardar(fig, "01_resume_id_experiencias_vs_personas", alto=540)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** La comparación entre el número total de experiencias y el
        número de personas únicas: **376.567 experiencias** frente a **71.061 personas**.

        **¿Qué patrón o comportamiento evidencia?** Hay **5,3 experiencias por persona** en promedio;
        por tanto, una misma persona aporta varias filas al dataset.

        **¿Para qué ayuda a determinar?** Recuerda el grano correcto. Los porcentajes de este EDA son
        **por experiencia**, y cualquier conclusión sobre personas exige agregar o deduplicar por
        `resume_id`. También anticipa que la unidad de análisis está dominada por trayectorias, no
        por individuos.

        **Hallazgo preliminar:** el dataset es una colección de **trayectorias laborales**, no una
        encuesta de personas.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** Cuántas personas tienen 1, 2, 3… experiencias, y qué
        porcentaje de personas acumula hasta cada valor.

        **¿Por qué es relevante?** La media (5,3) puede ocultar una distribución muy desigual: si
        pocas personas acumulan muchas experiencias, la media no representa al conjunto.
        """
    ),
    code(
        """
        exp = df["resume_id"].value_counts()
        dist = exp.value_counts().sort_index().rename_axis("experiencias").reset_index(name="personas")
        dist["pct_acum"] = dist["personas"].cumsum() / len(exp) * 100

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(
            x=dist["experiencias"], y=dist["personas"], name="Personas",
            marker_color=C_AZUL,
            hovertemplate="%{x} experiencias<br>%{y:,} personas<extra></extra>",
        )
        fig.add_scatter(
            x=dist["experiencias"], y=dist["pct_acum"], name="% acumulado de personas",
            mode="lines+markers", line=dict(color=C_NARANJA, width=3),
            marker=dict(size=6), secondary_y=True,
            hovertemplate="Hasta %{x} experiencias<br>%{y:.1f}% de las personas<extra></extra>",
        )
        mediana = float(exp.median())
        fig.add_vline(
            x=mediana, line_dash="dash", line_color=C_ROJO,
            annotation_text=f"Mediana = {mediana:.0f}", annotation_position="top right",
        )
        fig.update_layout(
            title="La mitad de las personas acumula 5 experiencias o menos; la cola llega a 20",
            xaxis_title="Número de experiencias laborales por persona",
            yaxis_title="Personas", bargap=0.15,
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        )
        fig.update_xaxes(dtick=1, range=[0.4, 20.6])
        fig.update_yaxes(title_text="Personas", rangemode="tozero", secondary_y=False)
        fig.update_yaxes(title_text="% acumulado de personas", ticksuffix="%",
                         range=[0, 105], secondary_y=True, showgrid=False)

        guardar(fig, "02_resume_id_distribucion_por_persona", alto=600)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** La distribución de personas según su número de experiencias
        (barras) y el porcentaje acumulado de personas (línea).

        **¿Qué patrón o comportamiento evidencia?** La distribución es **campaniforme**: solo el
        **6,15 %** de las personas tiene una sola experiencia; la mediana es **5**, el percentil 90 es
        **9**, el 99 es **15** y el máximo es **20**. El 50 % de las personas se concentra entre 1 y 5
        experiencias, mientras que los valores altos son poco frecuentes (22 personas llegan a 20).

        **¿Para qué ayuda a determinar?** Muestra que el dataset **no está dominado por unas pocas
        personas con cientos de empleos**: la cola es corta y el máximo está acotado. Eso hace que la
        media (5,3) sea una síntesis razonable, aunque la unidad de análisis siga siendo la experiencia.

        **Hallazgo preliminar:** trayectorias de 3 a 5 empleos son lo típico; el pluriempleo intenso es
        excepcional.
        """
    ),
]

# ---------------------------------------------------------------- 4.2 Period_Time
celdas += [
    md(
        """
        ### 4.2 `Period_Time` (`start_date - end_date`)

        **¿Qué vamos a analizar?** Cuatro dimensiones del tiempo: (1) las combinaciones inicio-fin más
        frecuentes, (2) los años de inicio, (3) el trimestre de inicio dentro de cada año, y (4) la
        duración observada en trimestres.

        **¿Por qué es relevante?** `Period_Time` es una columna de alta cardinalidad (6.229
        combinaciones). Descomponerla en año, trimestre y duración permite encontrar tendencias,
        estacionalidad del registro y censura por la derecha (`Present`).
        """
    ),
    code(
        """
        top_periodo = df["Period_Time"].value_counts().head(20).sort_values()
        share_top20 = top_periodo.sum() / len(df) * 100

        fig = go.Figure(go.Bar(
            x=top_periodo.values, y=top_periodo.index, orientation="h",
            marker_color=C_AZUL,
            text=[mil(v) for v in top_periodo.values], textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>%{x:,} experiencias<extra></extra>",
        ))
        fig.update_layout(
            title=f"Los 20 periodos más frecuentes solo reúnen el {pct_es(share_top20)}% de las experiencias",
            xaxis_title="Experiencias", yaxis_title="Period_Time (inicio - fin)",
        )
        fig.update_xaxes(range=[0, top_periodo.max() * 1.18])

        guardar(fig, "03_period_time_top20", alto=720, margen_l=150)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Las 20 combinaciones `Period_Time` con más experiencias.

        **¿Qué patrón o comportamiento evidencia?** Dominan los periodos de **un año** registrados como
        `Q1 año - Q1 año+1` (por ejemplo, `Q1 2011 - Q1 2012`, con 7.310 casos). Entre las 20
        combinaciones más frecuentes solo se acumula el **23,4 %** de las filas: la columna es de **alta
        cardinalidad** y la mayoría de los valores aparecen pocas veces.

        **¿Para qué ayuda a determinar?** Indica que `Period_Time` **no debe usarse como categoría
        directa** en un modelo o tabla: aporta más información descompuesta en año de inicio, trimestre
        y duración. También confirma que el registro temporal está dominado por la rejilla trimestral.

        **Hallazgo preliminar:** la combinación inicio-fin es útil para trazabilidad, pero no para
        agrupar; conviene derivar variables temporales.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** La evolución del número de experiencias según el **año de
        inicio**.

        **¿Por qué es relevante?** Permite ubicar el periodo real de los datos, detectar el pico de
        actividad y entender posibles sesgos de memoria o de recolección.
        """
    ),
    code(
        """
        por_anio = df["start_year"].value_counts().sort_index()
        pico_anio = int(por_anio.idxmax())
        pico_val = int(por_anio.max())

        fig = go.Figure(go.Scatter(
            x=por_anio.index, y=por_anio.values, mode="lines+markers",
            line=dict(color=C_AZUL, width=2.5), marker=dict(size=4),
            fill="tozeroy", fillcolor="rgba(91,141,184,0.18)",
            hovertemplate="Año %{x}<br>%{y:,} experiencias<extra></extra>",
        ))
        fig.add_annotation(
            x=pico_anio, y=pico_val, text=f"Pico: {pico_anio} ({mil(pico_val)})",
            showarrow=True, arrowhead=2, ay=-45, ax=0,
            font=dict(color=C_ROJO), arrowcolor=C_ROJO,
        )
        fig.update_layout(
            title="Las experiencias se concentran entre 2000 y 2016; el pico es 2012",
            xaxis_title="Año de inicio de la experiencia", yaxis_title="Experiencias",
        )

        guardar(fig, "04_period_time_inicios_por_anio", alto=540)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** El número de experiencias que **comienzan** en cada año, entre
        1965 y 2021.

        **¿Qué patrón o comportamiento evidencia?** El **95,7 %** de las experiencias comienza en 1990
        o después, y el **55,6 %** en 2010 o después. El máximo está en **2012 (29.066 experiencias)**,
        seguido de 2011 y 2013. Antes de 1990 la frecuencia es baja.

        **¿Para qué ayuda a determinar?** Delimita el horizonte temporal real del análisis y advierte
        que las conclusiones describen sobre todo trayectorias recientes. El pico de 2012 puede reflejar
        el diseño de la muestra de JobHop, no un boom laboral; **no debe interpretarse como causalidad
        ni como evolución macroeconómica**.

        **Hallazgo preliminar:** datos fuertemente concentrados en las últimas tres décadas.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** La distribución conjunta de **año × trimestre de inicio**.

        **¿Por qué es relevante?** La rejilla temporal es trimestral; si el registro se concentra en
        ciertos trimestres, las comparaciones entre años pueden estar sesgadas por ese patrón.
        """
    ),
    code(
        """
        sub_q = df[df["start_year"].between(1990, 2021)]
        matriz_q = (sub_q.groupby(["start_year", "start_q"]).size()
                    .unstack(fill_value=0)
                    .reindex(columns=[1, 2, 3, 4], fill_value=0))

        fig = go.Figure(go.Heatmap(
            z=matriz_q.T.values,
            x=[int(a) for a in matriz_q.index],
            y=["Q1", "Q2", "Q3", "Q4"],
            colorscale="Blues",
            colorbar=dict(title="Experiencias"),
            hovertemplate="Año %{x}<br>%{y}<br>%{z:,} experiencias<extra></extra>",
        ))
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            title="El inicio de experiencias se concentra en Q1 (1990-2021)",
            xaxis_title="Año de inicio", yaxis_title="Trimestre de inicio",
        )

        guardar(fig, "05_period_time_heatmap_trimestre_anio", alto=520)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Un mapa de calor con la cantidad de experiencias que inician en
        cada combinación **año × trimestre** desde 1990.

        **¿Qué patrón o comportamiento evidencia?** La franja **Q1** es sistemáticamente la más intensa
        en casi todos los años; Q3 y Q4 concentran menos inicios. La estructura es estable desde los
        2000 y se intensifica entre 2010 y 2016.

        **¿Para qué ayuda a determinar?** Confirma que el trimestre de inicio **no es aleatorio**: hay
        una estacionalidad de registro (o de los contratos) que debe declararse. Al comparar años,
        conviene hacerlo dentro del mismo trimestre o usar la duración, no solo el año.

        **Hallazgo preliminar:** Q1 domina los inicios; el calendario trimestral deja una huella visible
        en los datos.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** La **duración observada** de cada experiencia, medida como
        `fin - inicio + 1` trimestres.

        **¿Por qué es relevante?** `Period_Time` dice cuándo ocurrió la experiencia, pero no cuánto
        duró. La duración es la dimensión que permite hablar de estabilidad o rotación, y obliga a
        tratar aparte los empleos vigentes.
        """
    ),
    code(
        """
        dur = df["dur_trim"].dropna()
        pct_vigentes = df["es_vigente_bool"].mean() * 100
        q1, q3 = dur.quantile([0.25, 0.75])
        en_rango = dur[dur <= 60]
        valores, conteos = np.unique(en_rango, return_counts=True)
        n_cola = int((dur > 60).sum())

        fig = go.Figure(go.Bar(
            x=valores, y=conteos, marker_color=C_AZUL,
            marker_line_width=0.4, marker_line_color="white",
            hovertemplate="%{x} trimestres<br>%{y:,} experiencias<extra></extra>",
        ))
        fig.add_vline(
            x=float(dur.median()), line_dash="dash", line_color=C_ROJO,
            annotation_text=f"Mediana = {dur.median():.0f}",
            annotation_position="top right",
        )
        fig.add_vline(x=float(q1), line_dash="dot", line_color="#666",
                      annotation_text=f"Q1 = {q1:.0f}", annotation_position="top left")
        fig.add_vline(x=float(q3), line_dash="dot", line_color="#666",
                      annotation_text=f"Q3 = {q3:.0f}", annotation_position="top left")
        fig.update_layout(
            title="La duración típica es de 5 trimestres (1,25 años); 66 % cae en 2, 5 o 9",
            xaxis_title="Duración observada en trimestres (fin - inicio + 1)",
            yaxis_title="Experiencias", showlegend=False, bargap=0.02,
        )
        fig.add_annotation(
            x=58, y=1, yref="paper", showarrow=False,
            text=(f"Se dibujan 0–60 trimestres; {mil(n_cola)} experiencias ({n_cola/dur.size*100:.2f} %) "
                  f"superan 60. Se excluyen {pct_vigentes:.2f} % de empleos vigentes (censurados)"),
            font=dict(size=10, color="#666"), xanchor="right",
        )

        guardar(fig, "06_period_time_duracion", alto=580)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** El histograma de la duración observada (barras) con líneas de
        referencia para la mediana y los cuartiles; el eje se recorta visualmente en 60 trimestres,
        aunque el máximo es 160 (la cola se declara en el propio gráfico para no ocultarla).

        **¿Qué patrón o comportamiento evidencia?** La mediana es **5 trimestres** (1,25 años), con
        Q1 = 2 y Q3 = 11 trimestres. El **66,4 %** de las duraciones cae exactamente en **2, 5 o 9
        trimestres**, y el **36,3 %** dura 4 trimestres o menos. Esto es una huella de la **rejilla
        trimestral** y de los cortes típicos de contrato (medio año, un año, dos años), no
        necesariamente de la duración real del empleo.

        **¿Para qué ayuda a determinar?** Caracteriza la rotación: la mitad de las experiencias dura
        poco más de un año. También advierte que la duración está **censurada** para los **18.956
        empleos vigentes (5,03 %)**, que se excluyen del cálculo. Para comparar grupos hay que usar la
        mediana y el IQR, no solo la media, porque la cola es larga.

        **Hallazgo preliminar:** empleos cortos y una fuerte discretización trimestral; la censura por
        la derecha debe declararse en cualquier análisis de duración.
        """
    ),
]

# ---------------------------------------------------------------- 4.3 University_Level
celdas += [
    md(
        """
        ### 4.3 `University_Level`

        **¿Qué vamos a analizar?** La distribución del nivel educativo, incluida la categoría
        `No reportado` de forma explícita.

        **¿Por qué es relevante?** Es la variable educativa del cruce con el grupo ocupacional. Ocultar
        los ausentes haría que los porcentajes no sumaran 100 % y sobreestimaría la composición real.
        """
    ),
    code(
        """
        vc_univ = df["University_Level_norm"].value_counts().reindex(CANON_UNIV, fill_value=0)

        fig = go.Figure(go.Bar(
            x=[NIVEL_ES[i] for i in vc_univ.index],
            y=vc_univ.values,
            marker_color=[COLOR_NIVEL[i] for i in vc_univ.index],
            text=[f"{mil(v)}<br>{v / len(df) * 100:.1f} %" for v in vc_univ.values],
            textposition="outside", cliponaxis=False,
            hovertemplate="%{x}<br>%{y:,} experiencias<extra></extra>",
        ))
        fig.update_layout(
            title="Predomina la secundaria (39,3 %), seguida del pregrado (34,4 %); 'No reportado' pesa 11,4 %",
            xaxis_title="Nivel educativo", yaxis_title="Experiencias", showlegend=False,
        )
        fig.update_yaxes(range=[0, vc_univ.max() * 1.22])

        guardar(fig, "07_university_level_distribucion", alto=560)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** El número y el porcentaje de experiencias por nivel educativo.

        **¿Qué patrón o comportamiento evidencia?** **Secundaria** es el nivel más frecuente
        (147.904; **39,3 %**), seguida de **Pregrado** (129.507; **34,4 %**), **Maestría** (54.697;
        **14,5 %**), **No reportado** (42.807; **11,4 %**) y **Doctorado** (1.652; **0,4 %**).

        **¿Para qué ayuda a determinar?** Define la composición educativa del conjunto de experiencias.
        La categoría `No reportado` se mantiene visible y **se incluye en los denominadores** para que
        los cruces sumen 100 %. Es una proporción relevante: cualquier conclusión sobre educación
        arrastra un 11,4 % de información no declarada.

        **Hallazgo preliminar:** la muestra está dominada por educación secundaria y pregrado; el
        doctorado es marginal (0,4 %).
        """
    ),
]

# ---------------------------------------------------------------- 4.4 ISCO
celdas += [
    md(
        """
        ### 4.4 `Isco_group` / `ISCO_group` (unificados con `isco_group_label`)

        **¿Qué vamos a analizar?** La distribución de los grupos ocupacionales: cuáles son los más
        frecuentes, cómo se organizan por gran grupo ISCO, cuánta cola larga existe y qué nivel de
        detalle aporta la ocupación específica.

        **¿Por qué es relevante?** Es la dimensión ocupacional del cruce con educación y competencias.
        Además, `Isco_group` e `ISCO_group` son la misma columna pedida dos veces: se unifican con
        `isco_group_label` y se conserva el código (`isco_group`) para derivar el gran grupo.

        **Decisión de unificación:** 424 valores únicos tanto en `isco_group` como en
        `isco_group_label`; se usa la etiqueta por legibilidad y el código para la jerarquía.
        """
    ),
    code(
        """
        top15 = df["Isco_group_unif"].value_counts().head(15)
        orden15 = top15.sort_values()
        etiquetas15 = [textwrap.fill(OFICIO_ES.get(i, i), 36) for i in orden15.index]
        share15 = top15.sum() / len(df) * 100

        fig = go.Figure(go.Bar(
            x=orden15.values, y=etiquetas15, orientation="h",
            marker_color=C_AZUL,
            text=[mil(v) for v in orden15.values], textposition="outside",
            cliponaxis=False, customdata=orden15.index,
            hovertemplate="%{customdata}<br>%{x:,} experiencias<extra></extra>",
        ))
        fig.update_layout(
            title=f"El top 15 de grupos ocupacionales reúne solo el {pct_es(share15)} % de las experiencias",
            xaxis_title="Experiencias", yaxis_title="",
        )
        fig.update_xaxes(range=[0, top15.max() * 1.22])

        guardar(fig, "08_isco_top15", alto=700, margen_l=290)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Los 15 grupos ocupacionales (ISCO-08) con más experiencias,
        ordenados por frecuencia. El nombre original en inglés aparece al pasar el cursor.

        **¿Qué patrón o comportamiento evidencia?** **Vendedores de tienda** (30.241), **secretarios
        administrativos** (24.440) y **manipuladores de carga** (13.736) encabezan la lista. El top 15
        reúne el **36,8 %** del total; los cinco primeros, el **22,6 %**. La concentración es **moderada**:
        no hay un único oficio dominante.

        **¿Para qué ayuda a determinar?** Define el Top 12 que se usará en el cruce con educación y
        muestra que la muestra está sesgada hacia ocupaciones de servicios, oficina y logística. Ese
        sesgo debe tenerse en cuenta antes de generalizar a todo el mercado laboral.

        **Hallazgo preliminar:** los oficios de ventas y apoyo administrativo son el núcleo de la muestra.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** La jerarquía **gran grupo ISCO → grupo ocupacional** para los
        40 grupos más frecuentes.

        **¿Por qué es relevante?** El código ISCO tiene una estructura jerárquica; el treemap permite
        ver de un vistazo qué grandes grupos aportan más experiencias y qué oficios los componen.
        """
    ),
    code(
        """
        top40 = df["Isco_group_unif"].value_counts().head(40).index
        arbol = (df[df["Isco_group_unif"].isin(top40)]
                 .groupby(["ISCO_major", "Isco_group_unif"], as_index=False)
                 .size())

        fig = px.treemap(
            arbol,
            path=[px.Constant("Top 40 grupos"), "ISCO_major", "Isco_group_unif"],
            values="size",
            color="size",
            color_continuous_scale="Blues",
        )
        fig.update_traces(textinfo="label+value", textfont=dict(size=11),
                          hovertemplate="%{label}<br>%{value:,} experiencias<extra></extra>")
        fig.update_layout(
            title="Servicios y ventas, técnicos y profesionales son los bloques ocupacionales más grandes",
            coloraxis_showscale=False,
            margin=dict(t=95, l=10, r=10, b=10),
        )

        guardar(fig, "09_isco_treemap_gran_grupo", alto=700, margen_b=20)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Un treemap con dos niveles: el gran grupo ISCO (primer dígito)
        y, dentro de él, los grupos ocupacionales más frecuentes. El tamaño es el número de experiencias.

        **¿Qué patrón o comportamiento evidencia?** **Servicios y vendedores (20,3 %)**, **técnicos y
        profesionales asociados (18,1 %)** y **profesionales y científicos (16,5 %)** son los bloques
        más grandes. Sin embargo, el bloque de servicios está dominado por un solo oficio (vendedores),
        mientras que profesionales y técnicos se reparten entre más grupos.

        **¿Para qué ayuda a determinar?** Muestra que la composición no es solo “muchos oficios”: hay
        **bloques jerárquicos** con distinta diversidad interna. Sirve para decidir qué gran grupo
        comparar y para detectar que "servicios" no es homogéneo.

        **Hallazgo preliminar:** la jerarquía ISCO revela concentración dentro de bloques y diversidad
        en otros; el análisis por gran grupo es más estable que el análisis por grupo individual.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** La **curva de cobertura** (Pareto) de los grupos ocupacionales:
        cuánto acumula el top 1, 2, …, 20 y qué queda en la cola.

        **¿Por qué es relevante?** Con 424 grupos, un gráfico de barras completo sería ilegible. La curva
        responde cuántos grupos hacen falta para cubrir la mayor parte de las experiencias.
        """
    ),
    code(
        """
        top20 = df["Isco_group_unif"].value_counts().head(20)
        acum = top20.cumsum() / len(df) * 100
        rank = list(range(1, len(top20) + 1))

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_bar(
            x=rank, y=top20.values, name="Experiencias por grupo",
            marker_color=C_AZUL, customdata=top20.index,
            hovertemplate="%{customdata}<br>%{y:,} experiencias<extra></extra>",
        )
        fig.add_scatter(
            x=rank, y=acum.values, name="% acumulado del total",
            mode="lines+markers", line=dict(color=C_NARANJA, width=3),
            marker=dict(size=6), secondary_y=True,
            hovertemplate="Top %{x}<br>%{y:.1f} % del total<extra></extra>",
        )
        fig.add_annotation(
            x=10, y=float(acum.iloc[9]), text=f"Top 10 = {acum.iloc[9]:.1f} %",
            showarrow=True, arrowhead=2, ay=-40, ax=0,
            font=dict(color=C_ROJO), arrowcolor=C_ROJO,
        )
        fig.update_layout(
            title="Cobertura de la cola larga: 424 grupos y el top 10 solo explica el 31,2 %",
            xaxis_title="Ranking de grupos ocupacionales (por nº de experiencias)",
            yaxis_title="Experiencias",
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        )
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(title_text="Experiencias", secondary_y=False)
        fig.update_yaxes(title_text="% acumulado", ticksuffix="%", range=[0, 60],
                         secondary_y=True, showgrid=False)

        guardar(fig, "10_isco_pareto_cobertura", alto=580, margen_r=75)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Barras con las experiencias de cada grupo del top 20 y una línea
        con el porcentaje acumulado del total.

        **¿Qué patrón o comportamiento evidencia?** El top 5 cubre el **22,6 %**, el top 10 el **31,2 %**,
        el top 20 el **41,1 %** y el top 50 el **56,9 %**. Es decir, **hacen falta decenas de grupos para
        cubrir la mitad** de las experiencias: la cola es muy larga (424 grupos).

        **¿Para qué ayuda a determinar?** Justifica dos decisiones: (1) graficar solo el top 12 y
        declararlo; (2) no tratar el grupo ISCO como una variable de pocas categorías sin agrupar antes.
        También advierte que cualquier conclusión sobre “los oficios” está dominada por unos pocos grupos.

        **Hallazgo preliminar:** concentración moderada con cola larga; el top N debe declararse siempre.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** El nivel de detalle más fino: la **ocupación específica**
        (`occupation_label`), no el grupo ISCO.

        **¿Por qué es relevante?** Dentro de un mismo grupo puede haber ocupaciones muy distintas; mirar
        la ocupación específica ayuda a interpretar mejor la composición y a decidir si el grupo es
        suficiente para el análisis.
        """
    ),
    code(
        """
        ocup = df["occupation_label"].value_counts()
        top10_oc = ocup.head(10).sort_values()
        etiquetas_oc = [textwrap.fill(OFICIO_ES.get(i, i), 36) for i in top10_oc.index]

        fig = go.Figure(go.Bar(
            x=top10_oc.values, y=etiquetas_oc, orientation="h",
            marker_color=C_VERDE,
            text=[mil(v) for v in top10_oc.values], textposition="outside",
            cliponaxis=False, customdata=top10_oc.index,
            hovertemplate="%{customdata}<br>%{x:,} experiencias<extra></extra>",
        ))
        fig.update_layout(
            title=f"Detalle fino: {mil(ocup.size)} ocupaciones y el top 10 suma el {pct_es(ocup.head(10).sum() / len(df) * 100)} %",
            xaxis_title="Experiencias", yaxis_title="Ocupación específica (occupation_label)",
        )
        fig.update_xaxes(range=[0, top10_oc.max() * 1.22])

        guardar(fig, "11_ocupaciones_top10", alto=600, margen_l=300)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Las 10 ocupaciones específicas más frecuentes.

        **¿Qué patrón o comportamiento evidencia?** Hay **2.855 ocupaciones** distintas. Las 10 más
        frecuentes acumulan el **19,6 %**: *asistente administrativo* (16.864), *asistente comercial*
        (10.017), *vendedor de tienda* (9.676), *trabajador de almacén* (7.106), etc. El 4,2 % de las
        ocupaciones aparece una sola vez.

        **¿Para qué ayuda a determinar?** Confirma que el **grupo ISCO es una buena unidad de análisis**:
        reduce 2.855 etiquetas a 424 grupos sin perder la estructura principal. También muestra que
        “vendedores de tienda” agrupa etiquetas específicas distintas, lo que explica su peso.

        **Hallazgo preliminar:** la ocupación específica es demasiado granular para tablas generales;
        el grupo ISCO ofrece el equilibrio entre detalle y estabilidad.
        """
    ),
]
# ---------------------------------------------------------------- 4.5 Skill_competence
celdas += [
    md(
        """
        ### 4.5 `Skill_competence` (`n_skills_competence`) — requerido por el oficio según ESCO

        **¿Qué vamos a analizar?** La distribución del número de competencias tipo *competence*
        (saber hacer) que **exige el oficio** según ESCO.

        **¿Por qué es relevante?** Es una columna objetivo. **Importante:** el valor describe el
        **requerimiento del oficio**, NO una competencia que posea la persona.
        """
    ),
    code(
        """
        comp = df["n_skills_competence_num"].dropna()
        med_c, mean_c = float(comp.median()), float(comp.mean())
        valores, conteos = np.unique(comp, return_counts=True)

        fig = go.Figure(go.Bar(
            x=valores, y=conteos, marker_color=C_AZUL,
            marker_line_width=0.3, marker_line_color="white",
            hovertemplate="%{x} competencias<br>%{y:,} experiencias<extra></extra>",
        ))
        fig.add_vline(x=med_c, line_dash="dash", line_color=C_ROJO,
                      annotation_text=f"Mediana = {med_c:.0f}", annotation_position="top right")
        fig.add_vline(x=mean_c, line_dash="dot", line_color=C_NARANJA,
                      annotation_text=f"Media = {mean_c:.1f}", annotation_position="top left")
        fig.update_layout(
            title="Skill_competence: distribución amplia, centrada en 18 y con cola hasta 69",
            xaxis_title="Nº de competencias (saber hacer) que exige el oficio",
            yaxis_title="Experiencias", showlegend=False,
        )
        fig.add_annotation(
            x=0.99, y=0.95, xref="paper", yref="paper", showarrow=False,
            text=f"n = {mil(comp.size)} experiencias",
            font=dict(size=10, color="#666"), xanchor="right",
        )

        guardar(fig, "12_skill_competence_histograma", alto=560)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** El histograma de `n_skills_competence` (conteos exactos por
        valor) con líneas de referencia para la mediana y la media.

        **¿Qué patrón o comportamiento evidencia?** La mediana es **18**, la media **19,2** y la
        desviación estándar **11,2**; el rango va de **0 a 69**. La distribución es amplia y ligeramente
        asimétrica a la derecha. El 25 % de las experiencias exige 12 competencias o menos y el 75 %,
        23 o menos.

        **¿Para qué ayuda a determinar?** Permite dimensionar la demanda de *saber hacer* por oficio.
        La cola hasta 69 muestra que algunos oficios exigen muchas competencias; la media es más alta
        que la mediana por esos valores extremos, por lo que conviene reportar **mediana e IQR**.

        **Hallazgo preliminar:** la exigencia típica es de 18 competencias, con alta variabilidad entre
        oficios. Son requerimientos del cargo, no del individuo.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** El perfil de `Skill_competence` por **gran grupo ISCO**.

        **¿Por qué es relevante?** La distribución global puede esconder diferencias sistemáticas entre
        tipos de ocupación. Comparar por gran grupo es más estable que comparar 424 grupos.
        """
    ),
    code(
        """
        base_comp = df.dropna(subset=["n_skills_competence_num"])
        orden_comp = (base_comp.groupby("ISCO_major")["n_skills_competence_num"]
                      .median().sort_values().index.tolist())
        est = (base_comp.groupby("ISCO_major")["n_skills_competence_num"]
               .agg(n="count", minimo="min", maximo="max", mediana="median").loc[orden_comp])
        q = (base_comp.groupby("ISCO_major")["n_skills_competence_num"]
             .quantile([0.25, 0.75]).unstack().loc[orden_comp])
        iqr = q[0.75] - q[0.25]

        fig = go.Figure(go.Box(
            orientation="h", y=orden_comp,
            q1=q[0.25], median=est["mediana"], q3=q[0.75],
            lowerfence=np.maximum(q[0.25] - 1.5 * iqr, est["minimo"]),
            upperfence=np.minimum(q[0.75] + 1.5 * iqr, est["maximo"]),
            marker_color=C_AZUL, line_color=C_AZUL,
            fillcolor="rgba(91,141,184,0.30)", name="", boxpoints=False,
        ))
        fig.update_layout(
            title="Competencias por gran grupo ISCO: de 11 (apoyo administrativo) a 22 (agricultura)",
            xaxis_title="Nº de competencias exigidas por el oficio", yaxis_title="",
            showlegend=False,
        )
        fig.update_yaxes(
            ticktext=[f"{g}  (n = {mil(est.loc[g, 'n'])}; mediana = {est.loc[g, 'mediana']:.0f})"
                      for g in orden_comp],
            tickvals=orden_comp,
        )

        guardar(fig, "13_skill_competence_por_gran_grupo", alto=660, margen_l=360)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Diagramas de caja (Q1, mediana, Q3 y bigotes de 1,5 × IQR)
        del número de competencias exigidas, para cada gran grupo ISCO, ordenados por mediana. Las
        cajas se calculan con **todas** las experiencias del grupo, sin muestreo.

        **¿Qué patrón o comportamiento evidencia?** La mediana va de **11** en **apoyo administrativo**
        a **22** en **agricultura y pesca**. Los grupos de servicios (20), gerentes (20), profesionales
        (19) y ocupaciones elementales (20) se sitúan en el rango alto, mientras que operadores de
        máquinas y oficiales artesanos quedan en 15. Las distribuciones se solapan mucho.

        **¿Para qué ayuda a determinar?** Muestra que el “saber hacer” exigido **no crece linealmente con
        el prestigio o el nivel educativo** del grupo: ocupaciones elementales también acumulan muchas
        competencias. Sirve para evitar la lectura errónea de que a menor nivel educativo corresponde
        menor exigencia.

        **Hallazgo preliminar:** el perfil de competencias diferencia mejor entre oficios que el nivel
        educativo; agricultura es un caso extremo con solo 1.296 experiencias y debe interpretarse con cautela.
        """
    ),
]

# ---------------------------------------------------------------- 4.6 Skill_Knowledge
celdas += [
    md(
        """
        ### 4.6 `Skill_Knowledge` (`n_skills_knowledge`) — requerido por el oficio según ESCO

        **¿Qué vamos a analizar?** La distribución del número de conocimientos tipo *knowledge* (saber)
        que **exige el oficio** según ESCO.

        **¿Por qué es relevante?** Complementa a `Skill_competence`: separa el componente teórico del
        práctico. **Importante:** también es un atributo del oficio, no de la persona.
        """
    ),
    code(
        """
        know = df["n_skills_knowledge_num"].dropna()
        med_k, mean_k = float(know.median()), float(know.mean())
        valores, conteos = np.unique(know, return_counts=True)

        fig = go.Figure(go.Bar(
            x=valores, y=conteos, marker_color=C_VERDE,
            marker_line_width=0.3, marker_line_color="white",
            hovertemplate="%{x} conocimientos<br>%{y:,} experiencias<extra></extra>",
        ))
        fig.add_vline(x=med_k, line_dash="dash", line_color=C_ROJO,
                      annotation_text=f"Mediana = {med_k:.0f}", annotation_position="top right")
        fig.update_layout(
            title="Skill_Knowledge: la mitad de los oficios exige 3 conocimientos o menos; 10,3 % exige cero",
            xaxis_title="Nº de conocimientos (saber) que exige el oficio",
            yaxis_title="Experiencias", showlegend=False,
        )
        fig.add_annotation(
            x=0.99, y=0.95, xref="paper", yref="paper", showarrow=False,
            text=f"n = {mil(know.size)} experiencias",
            font=dict(size=10, color="#666"), xanchor="right",
        )

        guardar(fig, "14_skill_knowledge_histograma", alto=560)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** El histograma de `n_skills_knowledge` (conteos exactos por
        valor) con una línea de referencia para la mediana.

        **¿Qué patrón o comportamiento evidencia?** La distribución es **fuertemente asimétrica a la
        derecha**: mediana **3**, media **4,0**, desviación **4,4**, rango **0–45**. El **10,3 %** de las
        experiencias exige **cero** conocimientos y el 25 % exige 1 o menos; el 75 % exige 6 o menos.

        **¿Para qué ayuda a determinar?** Muestra que el componente *knowledge* es **minoritario** frente
        a *competence*: la mayoría de los oficios se define más por el saber hacer que por conocimientos
        declarados. La presencia de ceros es real y debe mantenerse; no se imputa.

        **Hallazgo preliminar:** el conocimiento exigido es bajo en la mayoría de los oficios, con una
        cola de perfiles intensivos en conocimiento.
        """
    ),
    md(
        """
        **¿Qué vamos a analizar ahora?** El perfil de `Skill_Knowledge` por **gran grupo ISCO**.

        **¿Por qué es relevante?** Permite ver qué bloques ocupacionales se apoyan más en conocimiento
        teórico y contrastarlo con el perfil de competencias.
        """
    ),
    code(
        """
        base_know = df.dropna(subset=["n_skills_knowledge_num"])
        orden_know = (base_know.groupby("ISCO_major")["n_skills_knowledge_num"]
                      .median().sort_values().index.tolist())
        est = (base_know.groupby("ISCO_major")["n_skills_knowledge_num"]
               .agg(n="count", minimo="min", maximo="max", mediana="median").loc[orden_know])
        q = (base_know.groupby("ISCO_major")["n_skills_knowledge_num"]
             .quantile([0.25, 0.75]).unstack().loc[orden_know])
        iqr = q[0.75] - q[0.25]

        fig = go.Figure(go.Box(
            orientation="h", y=orden_know,
            q1=q[0.25], median=est["mediana"], q3=q[0.75],
            lowerfence=np.maximum(q[0.25] - 1.5 * iqr, est["minimo"]),
            upperfence=np.minimum(q[0.75] + 1.5 * iqr, est["maximo"]),
            marker_color=C_VERDE, line_color=C_VERDE,
            fillcolor="rgba(53,117,79,0.28)", name="", boxpoints=False,
        ))
        fig.update_layout(
            title="Conocimientos por gran grupo: profesionales (6) y agricultura (11) a la cabeza; elementales (2) al final",
            xaxis_title="Nº de conocimientos exigidos por el oficio", yaxis_title="",
            showlegend=False,
        )
        fig.update_yaxes(
            ticktext=[f"{g}  (n = {mil(est.loc[g, 'n'])}; mediana = {est.loc[g, 'mediana']:.0f})"
                      for g in orden_know],
            tickvals=orden_know,
        )

        guardar(fig, "15_skill_knowledge_por_gran_grupo", alto=660, margen_l=360)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Diagramas de caja (Q1, mediana, Q3 y bigotes de 1,5 × IQR) de
        `n_skills_knowledge` por gran grupo ISCO, ordenados por mediana. Las cajas se calculan con
        **todas** las experiencias del grupo, sin muestreo.

        **¿Qué patrón o comportamiento evidencia?** La mediana va de **2** en **ocupaciones elementales**
        a **11** en **agricultura y pesca**. Profesionales (6), gerentes (5) y oficiales artesanos (4)
        están por encima de servicios (3), operadores (3) y apoyo administrativo (2). La distribución
        de agricultura es un caso aparte, con una cola muy larga y solo 1.296 experiencias.

        **¿Para qué ayuda a determinar?** Confirma que el conocimiento es la dimensión que **sí se alinea
        con el tipo de ocupación** (más teórica en profesionales), mientras que las competencias
        prácticas están más repartidas. Es la base del contraste de la sección 5.3.

        **Hallazgo preliminar:** *knowledge* discrimina entre grandes grupos; *competence* no lo hace
        con la misma claridad.
        """
    ),
]

# ---------------------------------------------------------------- 5. Bivariado
celdas += [
    md(
        """
        ## 5. Análisis bivariado

        Se cruzan las columnas objetivo entre sí y con variables derivadas (duración, década). El
        objetivo no es demostrar causalidad, sino **describir composición y asociación**.
        """
    ),
    md(
        """
        ### 5.1 `University_Level` × `Isco_group` (barras apiladas al 100 %, top 12)

        **¿Qué vamos a analizar?** La composición porcentual del nivel educativo **dentro de cada grupo
        ocupacional**; cada barra suma 100 %.

        **¿Por qué es relevante?** Responde: *"De las experiencias de este oficio, ¿qué proporción
        corresponde a cada nivel educativo?"* Es el cruce central de `docs/EDA.md`.

        **Criterio aplicado:** normalización **por grupo ocupacional**, `No reportado` incluido,
        sin gráficos de pastel y con `n` visible en cada barra.
        """
    ),
    code(
        """
        top12 = df["Isco_group_unif"].value_counts().head(12).index
        ct = (pd.crosstab(df["Isco_group_unif"], df["University_Level_norm"])
              .reindex(index=top12, columns=CANON_UNIV, fill_value=0))
        total12 = ct.sum(axis=1)
        pct12 = ct.div(total12, axis=0) * 100
        orden12 = total12.sort_values().index  # la barra más grande queda arriba
        etiquetas12 = [f"{OFICIO_ES.get(g, g)}<br><span style='font-size:10px'>n = {mil(total12[g])}</span>"
                       for g in orden12]

        fig = go.Figure()
        for nivel in CANON_UNIV:
            valores = pct12.loc[orden12, nivel]
            textos = [f"{v:.0f} %" if v >= 5 else "" for v in valores]
            color_texto = "#1A1A1A" if nivel in ("No reportado", "Secondary school", "Bachelor") else "white"
            fig.add_bar(
                x=valores.values, y=etiquetas12, orientation="h",
                name=NIVEL_ES[nivel], marker_color=COLOR_NIVEL[nivel],
                text=textos, textposition="inside",
                insidetextfont=dict(color=color_texto, size=11),
                customdata=np.array([[g, v] for g, v in zip(orden12, valores)], dtype=object),
                hovertemplate="%{customdata[0]}<br>" + NIVEL_ES[nivel] + ": %{customdata[1]:.1f} %<extra></extra>",
            )
        fig.update_layout(
            barmode="stack",
            title="En los oficios operativos domina la secundaria; en los profesionales, pregrado y maestría",
            xaxis_title="% de experiencias del grupo con ese nivel educativo",
            yaxis_title="", legend_title="Nivel educativo",
            legend=dict(orientation="h", y=-0.14, x=0.5, xanchor="center"),
        )
        fig.update_xaxes(range=[0, 100], ticksuffix="%")

        guardar(fig, "16_university_x_isco_apilado100", alto=780, margen_b=110, margen_l=260)

        display(
            ct.assign(n=total12)
              .rename(columns=NIVEL_ES)
              .sort_values("n", ascending=False)
        )
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Barras horizontales apiladas al 100 % con la composición
        educativa de los 12 grupos ocupacionales más frecuentes; `n` es el tamaño de cada grupo.

        **¿Qué patrón o comportamiento evidencia?** Hay un gradiente claro. **Personal de limpieza**
        (60,8 % secundaria), **peones de manufactura** (60,7 %), **manipuladores de carga** (57,9 %) y
        **ayudantes de cocina** (58,0 %) son los más concentrados en secundaria. **Profesores de
        secundaria** invierten la composición: 55,0 % pregrado y 36,9 % maestría. **Trabajadores
        sociales** (54,5 % pregrado) y **secretarios administrativos** (38,2 % pregrado, 13,6 %
        maestría) se sitúan en un punto intermedio. `No reportado` oscila entre 2,3 % y 19,0 %.

        **¿Para qué ayuda a determinar?** Permite responder qué nivel educativo es más frecuente en cada
        oficio y detectar dónde la educación superior es minoritaria. Sirve para priorizar políticas de
        formación por ocupación.

        **Hallazgo preliminar:** existe **asociación** entre nivel educativo y oficio, pero es
        **moderada y no causal** (V de Cramér = 0,27 en los 424 grupos). Un oficio con muchos titulados
        no “exige” título; solo describe quién lo ejerce en esta muestra.
        """
    ),
    md(
        """
        ### 5.2 `University_Level` × gran grupo ISCO (mapa de calor)

        **¿Qué vamos a analizar?** La misma composición educativa, pero agregada a los **grandes grupos
        ISCO** y presentada como mapa de calor.

        **¿Por qué es relevante?** El top 12 es una foto parcial. El mapa de calor cubre todos los
        grandes grupos (incluido `Sin grupo`) y permite comparar patrones completos sin 424 barras.
        """
    ),
    code(
        """
        ct_major = (pd.crosstab(df["ISCO_major"], df["University_Level_norm"])
                    .reindex(columns=CANON_UNIV, fill_value=0))
        pct_major = ct_major.div(ct_major.sum(axis=1), axis=0) * 100
        orden_major = ct_major.sum(axis=1).sort_values(ascending=False).index
        z_major = pct_major.loc[orden_major].values
        texto_major = [[f"{v:.1f} %" for v in fila] for fila in z_major]

        fig = go.Figure(go.Heatmap(
            z=z_major,
            x=[NIVEL_ES[c] for c in CANON_UNIV],
            y=[f"{i}  (n = {mil(ct_major.sum(axis=1)[i])})" for i in orden_major],
            text=texto_major, texttemplate="%{text}", textfont=dict(size=11),
            colorscale="Blues", zmin=0, zmax=65,
            colorbar=dict(title="% del grupo"),
            hovertemplate="%{y}<br>%{x}: %{z:.1f} %<extra></extra>",
        ))
        fig.update_layout(
            title="Composición educativa por gran grupo ISCO: asociación débil (V de Cramér = 0,22)",
            xaxis_title="Nivel educativo", yaxis_title="",
        )
        fig.update_yaxes(autorange="reversed")

        guardar(fig, "17_university_x_isco_major_heatmap", alto=560, margen_l=200)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Porcentaje de cada nivel educativo dentro de cada gran grupo
        ISCO; cada fila suma 100 %.

        **¿Qué patrón o comportamiento evidencia?** **Profesionales y científicos** es el grupo con
        mayor peso de educación superior (46,9 % pregrado, 32,4 % maestría, 1,6 % doctorado) y solo
        13,4 % de secundaria. En el extremo opuesto, **operadores de máquinas** (61,9 % secundaria),
        **oficiales y artesanos** (60,5 %) y **ocupaciones elementales** (58,7 %) concentran secundaria.
        **Gerentes** muestran 24,6 % maestría, más que los técnicos (15,3 %).

        **¿Para qué ayuda a determinar?** Confirma el gradiente educativo por tipo de ocupación y
        localiza los grupos donde la educación superior es casi inexistente. Es la vista “completa” que
        respalda el top 12.

        **Hallazgo preliminar:** el gradiente es real pero **débil** (V de Cramér = 0,22): el nivel
        educativo no determina el grupo, solo lo inclina. `Sin grupo` (6,85 %) se parece a la media y
        no debe interpretarse como una categoría ocupacional.
        """
    ),
    md(
        """
        ### 5.3 Competencias y conocimientos exigidos según nivel educativo

        **¿Qué vamos a analizar?** La mediana de `Skill_competence` y `Skill_Knowledge` en cada nivel
        educativo.

        **¿Por qué es relevante?** Permite comprobar si las personas con más estudios ocupan oficios que
        exigen más conocimiento teórico, más competencia práctica, o ambas.
        """
    ),
    code(
        """
        resumen_nivel = df.groupby("University_Level_norm").agg(
            n=("n_skills_competence_num", "size"),
            competence=("n_skills_competence_num", "median"),
            knowledge=("n_skills_knowledge_num", "median"),
        ).reindex(CANON_UNIV)
        etiquetas_nivel = [f"{NIVEL_ES[i]}<br><span style='font-size:10px'>n = {mil(resumen_nivel.loc[i, 'n'])}</span>"
                           for i in CANON_UNIV]

        fig = make_subplots(
            rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.08,
            subplot_titles=("Skill_competence (saber hacer)", "Skill_Knowledge (saber)"),
        )
        fig.add_bar(
            x=resumen_nivel["competence"], y=etiquetas_nivel, orientation="h",
            marker_color=C_AZUL, text=[f"{v:.0f}" for v in resumen_nivel["competence"]],
            textposition="outside", cliponaxis=False, row=1, col=1,
            hovertemplate="%{y}<br>Mediana: %{x:.0f} competencias<extra></extra>",
        )
        fig.add_bar(
            x=resumen_nivel["knowledge"], y=etiquetas_nivel, orientation="h",
            marker_color=C_VERDE, text=[f"{v:.0f}" for v in resumen_nivel["knowledge"]],
            textposition="outside", cliponaxis=False, row=1, col=2,
            hovertemplate="%{y}<br>Mediana: %{x:.0f} conocimientos<extra></extra>",
        )
        fig.update_xaxes(range=[0, 25], title_text="Mediana de competencias", row=1, col=1)
        fig.update_xaxes(range=[0, 8], title_text="Mediana de conocimientos", row=1, col=2)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            title="El nivel educativo no cambia las competencias exigidas (17-20), pero sí los conocimientos (2 → 6)",
            showlegend=False, bargap=0.35,
        )

        guardar(fig, "18_skills_medianas_por_nivel", alto=560)
        display(resumen_nivel.rename(columns={"competence": "Skill_competence (mediana)",
                                              "knowledge": "Skill_Knowledge (mediana)"}))
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Dos paneles con la mediana de competencias (izquierda) y de
        conocimientos (derecha) para cada nivel educativo.

        **¿Qué patrón o comportamiento evidencia?** Las **competencias** son casi planas: 18 en
        secundaria, pregrado y `No reportado`, 17 en maestría y 20 en doctorado. Los **conocimientos**
        suben de forma monótona: **2 → 3 → 4 → 6** al pasar de secundaria a doctorado (maestría = 4).
        La brecha entre competencia y conocimiento se **estrecha** a medida que aumenta el nivel.

        **¿Para qué ayuda a determinar?** Sugiere que los oficios ejercidos por personas con más
        estudios se distinguen por **mayor exigencia de conocimiento teórico**, no por más competencia
        práctica. Es un hallazgo descriptivo y consistente con la composición ocupacional.

        **Hallazgo preliminar:** el conocimiento es la dimensión educativa del perfil ESCO; la competencia
        práctica es transversal a los niveles.
        """
    ),
    md(
        """
        ### 5.4 Duración de la experiencia según nivel educativo

        **¿Qué vamos a analizar?** La duración mediana (y el IQR) de las experiencias finalizadas, por
        nivel educativo.

        **¿Por qué es relevante?** Si ciertos niveles educativos se asocian a empleos más estables, la
        duración debería reflejarlo. Además, es una forma de controlar la composición temporal.
        """
    ),
    code(
        """
        g_dur = df.dropna(subset=["dur_trim"]).groupby("University_Level_norm")["dur_trim"]
        est_dur = pd.DataFrame({
            "n": g_dur.size(),
            "mediana": g_dur.median(),
            "q1": g_dur.quantile(0.25),
            "q3": g_dur.quantile(0.75),
        }).reindex(CANON_UNIV)

        fig = go.Figure(go.Bar(
            x=[NIVEL_ES[i] for i in est_dur.index],
            y=est_dur["mediana"],
            marker_color=[COLOR_NIVEL[i] for i in est_dur.index],
            text=[f"{v:.0f} trim.<br>n = {mil(n)}" for v, n in zip(est_dur["mediana"], est_dur["n"])],
            textposition="outside", cliponaxis=False,
            error_y=dict(
                type="data", symmetric=False,
                array=(est_dur["q3"] - est_dur["mediana"]).values,
                arrayminus=(est_dur["mediana"] - est_dur["q1"]).values,
                color="#555", thickness=1.5, width=6,
            ),
            hovertemplate="%{x}<br>Mediana: %{y:.0f} trimestres<extra></extra>",
        ))
        fig.update_layout(
            title="La mediana de duración es 5 trimestres en casi todos los niveles; el doctorado llega a 8",
            xaxis_title="Nivel educativo", yaxis_title="Duración mediana (trimestres)",
            showlegend=False,
        )
        fig.update_yaxes(range=[0, 19])

        guardar(fig, "19_duracion_mediana_por_nivel", alto=560)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Barras con la duración mediana por nivel educativo; la línea
        vertical indica el rango intercuartílico (Q1–Q3).

        **¿Qué patrón o comportamiento evidencia?** La mediana es **5 trimestres** en secundaria,
        pregrado, maestría y `No reportado`, y **8 trimestres** en doctorado (2 años). El IQR es amplio:
        de 2 a 9 trimestres en pregrado y de 4 a 17 en doctorado. Las medias son más altas (8,9–11,8)
        por la cola de empleos largos.

        **¿Para qué ayuda a determinar?** Indica que la **duración típica no depende del nivel
        educativo**, salvo el doctorado, que acumula empleos algo más largos. Para comparar estabilidad
        hay que usar mediana e IQR; la media exagera las diferencias por la asimetría.

        **Hallazgo preliminar:** no hay evidencia descriptiva de que más educación implique empleos
        mucho más largos; solo el doctorado se separa.
        """
    ),
    md(
        """
        ### 5.5 `Skill_competence` × `Skill_Knowledge` (dispersión)

        **¿Qué vamos a analizar?** La relación entre competencias y conocimientos exigidos por el
        oficio, con una muestra de 25.000 experiencias y una recta de tendencia global.

        **¿Por qué es relevante?** Si ambos contadores midieran lo mismo, la nube sería estrecha y la
        correlación alta. Si miden dimensiones distintas, la nube será ancha y la correlación baja.
        """
    ),
    code(
        """
        muestra = df.dropna(subset=["n_skills_competence_num", "n_skills_knowledge_num"]).sample(
            n=25_000, random_state=42
        )
        r_comp_know = df[["n_skills_competence_num", "n_skills_knowledge_num"]].corr().iloc[0, 1]

        fig = px.scatter(
            muestra,
            x="n_skills_competence_num", y="n_skills_knowledge_num",
            color="University_Level_norm", color_discrete_map=COLOR_NIVEL,
            category_orders={"University_Level_norm": CANON_UNIV},
            opacity=0.35,
            labels={
                "n_skills_competence_num": "Competencias (saber hacer)",
                "n_skills_knowledge_num": "Conocimientos (saber)",
                "University_Level_norm": "Nivel educativo",
            },
        )
        fig.update_traces(marker=dict(size=4), selector=dict(mode="markers"))
        m, b = np.polyfit(muestra["n_skills_competence_num"], muestra["n_skills_knowledge_num"], 1)
        x_linea = np.array([0, 70])
        fig.add_scatter(
            x=x_linea, y=m * x_linea + b, mode="lines", name="Tendencia global",
            line=dict(color="#1A1A1A", width=2, dash="dash"),
        )
        fig.update_layout(
            title=f"Competencias y conocimientos se relacionan poco (r = {r_comp_know:.2f}): son dimensiones distintas",
            legend_title="Nivel educativo",
            legend=dict(itemsizing="constant"),
        )

        guardar(fig, "20_scatter_competence_knowledge", alto=600)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Una nube de puntos de competencias (eje X) frente a conocimientos
        (eje Y), coloreada por nivel educativo y con la recta de tendencia global.

        **¿Qué patrón o comportamiento evidencia?** La nube es **ancha y con forma de L invertida**: hay
        oficios con muchas competencias y pocos conocimientos (zona inferior derecha) y oficios con
        ambos altos (zona superior derecha). La correlación es **r = 0,34**, débil–moderada. La recta
        tiene pendiente positiva, pero explica poco: para un mismo número de competencias hay
        conocimientos muy distintos.

        **¿Para qué ayuda a determinar?** Justifica mantener **ambas variables** en el análisis: no son
        redundantes. Un oficio puede requerir mucho saber hacer y poco saber teórico, o combinar ambos.

        **Hallazgo preliminar:** competencia y conocimiento son **complementarios**, no sustitutos; la
        correlación baja es una señal de que aportan información distinta.
        """
    ),
    md(
        """
        ### 5.6 Nivel educativo según década de inicio

        **¿Qué vamos a analizar?** La composición educativa de las experiencias agrupadas por **década
        del año de inicio** (1970–2010; 2020 se excluye por tener solo 15 casos).

        **¿Por qué es relevante?** El dataset combina experiencias de varias décadas. Si la composición
        educativa cambia con el tiempo, las comparaciones globales mezclan cohortes distintas.
        """
    ),
    code(
        """
        dec = df[df["decada"].between(1970, 2010)].copy()
        ct_dec = (pd.crosstab(dec["decada"], dec["University_Level_norm"])
                  .reindex(columns=CANON_UNIV, fill_value=0))
        total_dec = ct_dec.sum(axis=1)
        pct_dec = ct_dec.div(total_dec, axis=0) * 100
        x_dec = [f"{int(d)}s<br><span style='font-size:10px'>n = {mil(total_dec[d])}</span>"
                 for d in ct_dec.index]

        fig = go.Figure()
        for nivel in CANON_UNIV:
            valores = pct_dec[nivel]
            textos = [f"{v:.0f} %" if v >= 5 else "" for v in valores]
            color_texto = "#1A1A1A" if nivel in ("No reportado", "Secondary school", "Bachelor") else "white"
            fig.add_bar(
                x=x_dec, y=valores, name=NIVEL_ES[nivel],
                marker_color=COLOR_NIVEL[nivel], text=textos, textposition="inside",
                insidetextfont=dict(color=color_texto, size=11),
                hovertemplate="Década %{x}<br>" + NIVEL_ES[nivel] + ": %{y:.1f} %<extra></extra>",
            )
        fig.update_layout(
            barmode="stack",
            title="El peso del pregrado y la maestría crece en las experiencias iniciadas en décadas recientes",
            xaxis_title="Década de inicio de la experiencia", yaxis_title="% de experiencias",
            legend_title="Nivel educativo",
            legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
        )
        fig.update_yaxes(ticksuffix="%", range=[0, 100])

        guardar(fig, "21_university_por_decada", alto=600, margen_b=110)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Barras apiladas al 100 % con la composición educativa por década
        de inicio; cada barra suma 100 % y muestra su `n`.

        **¿Qué patrón o comportamiento evidencia?** En los años 70, **64,1 %** de las experiencias
        correspondía a secundaria y solo 15,9 % a pregrado. En los 2000, secundaria baja a **40,6 %** y
        pregrado sube a **32,5 %**; en los 2010, pregrado (**37,4 %**) supera a secundaria (**36,2 %**) y
        la maestría llega a **15,8 %**. El doctorado se mantiene por debajo del 1 %.

        **¿Para qué ayuda a determinar?** Muestra que la composición educativa **cambia con la cohorte
        temporal**: las experiencias recientes incluyen más personas con educación superior. Por eso,
        comparar niveles educativos sin considerar la década puede confundir el efecto de la ocupación
        con el del momento histórico.

        **Hallazgo preliminar:** hay un **efecto de composición temporal**; no debe interpretarse como
        “las personas se educan más” a partir de filas repetidas, sino como un cambio en la mezcla de
        experiencias registradas.
        """
    ),
]
# ---------------------------------------------------------------- 6. Multivariado
celdas += [
    md(
        """
        ## 6. Análisis multivariado y redundancia

        Se revisan tres cosas: (1) si los contadores de competencias miden lo mismo, (2) cómo fluyen
        las experiencias del nivel educativo a los grandes grupos ISCO, y (3) qué tan fuertes son las
        asociaciones entre variables categóricas.
        """
    ),
    md(
        """
        ### 6.1 Correlación entre los contadores de competencias

        **¿Qué vamos a analizar?** La matriz de correlación de Pearson entre `n_skills_competence`,
        `n_skills_knowledge`, `n_skills_essential` (total), `n_skills_sin_tipo` y `veces_ese_oficio`.

        **¿Por qué es relevante?** Detectar redundancia evita usar dos veces la misma información y
        ayuda a elegir una representación para análisis posteriores.
        """
    ),
    code(
        """
        vars_corr = {
            "n_skills_competence_num": "Competencias",
            "n_skills_knowledge_num": "Conocimientos",
            "n_skills_essential_num": "Esenciales (total)",
            "n_skills_sin_tipo_num": "Sin tipo",
            "veces_ese_oficio_num": "Veces ese oficio",
        }
        corr = df[list(vars_corr)].corr()
        etiquetas_corr = list(vars_corr.values())

        fig = go.Figure(go.Heatmap(
            z=corr.values, x=etiquetas_corr, y=etiquetas_corr,
            text=[[f"{v:.2f}" for v in fila] for fila in corr.values],
            texttemplate="%{text}", textfont=dict(size=12),
            colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
            colorbar=dict(title="r de Pearson"),
            hovertemplate="%{y} × %{x}<br>r = %{z:.3f}<extra></extra>",
        ))
        fig.update_layout(
            title="Redundancia estructural: competencias y esenciales son casi la misma variable (r = 0,95)",
            xaxis_title="", yaxis_title="",
        )
        fig.update_yaxes(autorange="reversed")

        guardar(fig, "22_correlacion_competencias", alto=560)
        display(corr.round(3))
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** La matriz de correlación entre los cinco contadores ESCO.

        **¿Qué patrón o comportamiento evidencia?** `n_skills_essential` está **casi perfectamente
        correlacionado** con `n_skills_competence` (**r = 0,95**) y de forma moderada con
        `n_skills_knowledge` (**r = 0,62**). Competencias y conocimientos correlacionan **0,34**.
        `n_skills_sin_tipo` es casi independiente (r ≈ −0,02 a 0,12) y `veces_ese_oficio` también
        (r ≈ 0,05–0,10). El total `essential` es, en la práctica, la suma de los otros contadores.

        **¿Para qué ayuda a determinar?** Confirma que usar `competence`, `knowledge` y `essential`
        juntas **duplica información**. Para describir el oficio conviene quedarse con `competence` y
        `knowledge`; `essential` sirve como total de control. `sin_tipo` no aporta variación (99,1 % son
        ceros).

        **Hallazgo preliminar:** redundancia estructural confirmada; el par `competence`–`knowledge`
        es la representación más informativa y no redundante.
        """
    ),
    md(
        """
        ### 6.2 Flujo `University_Level` → gran grupo ISCO (Sankey)

        **¿Qué vamos a analizar?** Cómo se reparten las experiencias de cada nivel educativo entre los
        ocho grandes grupos ISCO más frecuentes (el resto se agrupa en una categoría).

        **¿Por qué es relevante?** El apilado del 5.1 responde “qué nivel hay en cada oficio”; el Sankey
        responde la pregunta inversa: *“¿a qué grandes grupos va cada nivel educativo?”*.
        """
    ),
    code(
        """
        top_major = (df.loc[df["ISCO_major"].ne("Sin grupo"), "ISCO_major"]
                     .value_counts().head(8).index.tolist())
        flujo = df.copy()
        flujo["major_agrup"] = np.where(
            flujo["ISCO_major"].isin(top_major), flujo["ISCO_major"], "Resto (incl. sin grupo)"
        )
        ct_flujo = pd.crosstab(flujo["University_Level_norm"], flujo["major_agrup"])
        orden_flujo = top_major + ["Resto (incl. sin grupo)"]
        ct_flujo = ct_flujo.reindex(index=CANON_UNIV, columns=orden_flujo, fill_value=0)

        etiquetas_sankey = [NIVEL_ES[n] for n in CANON_UNIV] + orden_flujo
        colores_sankey = [COLOR_NIVEL[n] for n in CANON_UNIV] + ["#9AA5B1"] * len(orden_flujo)

        source, target, value = [], [], []
        for i, nivel in enumerate(CANON_UNIV):
            for j, major in enumerate(orden_flujo):
                v = int(ct_flujo.loc[nivel, major])
                if v > 0:
                    source.append(i)
                    target.append(len(CANON_UNIV) + j)
                    value.append(v)

        fig = go.Figure(go.Sankey(
            arrangement="snap",
            node=dict(
                label=etiquetas_sankey, color=colores_sankey, pad=18, thickness=20,
                line=dict(color="white", width=0.5),
            ),
            link=dict(
                source=source, target=target, value=value,
                color="rgba(120,130,140,0.28)",
                hovertemplate="%{source.label} → %{target.label}<br>%{value:,} experiencias<extra></extra>",
            ),
        ))
        fig.update_layout(
            title="Flujo nivel educativo → gran grupo ISCO (top 8 + resto)",
            font=dict(size=11),
        )

        guardar(fig, "23_sankey_nivel_major", alto=720)
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Un diagrama de Sankey cuyos nodos izquierdos son los cinco
        niveles educativos y los derechos, los ocho grandes grupos ISCO más el resto; el grosor del
        flujo es el número de experiencias.

        **¿Qué patrón o comportamiento evidencia?** **Secundaria** envía el mayor flujo a **servicios y
        vendedores**, **ocupaciones elementales** y **técnicos**, y muy poco a profesionales. **Pregrado**
        y **maestría** se reparten sobre todo entre **profesionales**, **técnicos** y **servicios**.
        **Doctorado** es un flujo delgado casi exclusivo de profesionales. `No reportado` se distribuye
        de forma parecida a secundaria.

        **¿Para qué ayuda a determinar?** Visualiza la **asignación ocupacional** de cada nivel y hace
        evidente que la educación superior no es condición para la mayoría de los oficios de la muestra.
        Ayuda a identificar qué niveles “alimentan” cada bloque ocupacional.

        **Hallazgo preliminar:** los flujos confirman el gradiente educativo, pero también muestran que
        **todos los niveles tienen presencia en servicios y ocupaciones elementales**.
        """
    ),
    md(
        """
        ### 6.3 Fuerza de las asociaciones categóricas (V de Cramér)

        **¿Qué vamos a analizar?** La **V de Cramér** entre pares de variables categóricas: nivel
        educativo, grupo ISCO, gran grupo, década de inicio y empleo vigente.

        **¿Por qué es relevante?** Los gráficos muestran patrones; la V de Cramér los cuantifica en una
        escala común (0 = independencia, 1 = asociación perfecta) y evita exagerar diferencias visuales.
        """
    ),
    code(
        """
        def cramers_v(a, b):
            tabla = pd.crosstab(a, b)
            obs = tabla.to_numpy(dtype=float)
            n = obs.sum()
            esperado = np.outer(obs.sum(axis=1), obs.sum(axis=0)) / n
            chi2 = ((obs - esperado) ** 2 / esperado).sum()
            return float(np.sqrt(chi2 / (n * (min(obs.shape) - 1))))

        nivel = df["University_Level_norm"]
        major = df["ISCO_major"]
        vigente = df["es_vigente_bool"].astype(str)
        decada = df["decada"].where(df["decada"].between(1970, 2010)).astype("string")

        pares = {
            "Nivel educativo × Grupo ISCO (424)": cramers_v(nivel, df["Isco_group_unif"]),
            "Nivel educativo × Gran grupo ISCO": cramers_v(nivel, major),
            "Nivel educativo × Empleo vigente": cramers_v(nivel, vigente),
            "Gran grupo ISCO × Empleo vigente": cramers_v(major, vigente),
            "Década de inicio × Nivel educativo": cramers_v(decada, nivel),
            "Década de inicio × Gran grupo ISCO": cramers_v(decada, major),
        }
        serie_v = pd.Series(pares).sort_values()

        fig = go.Figure(go.Bar(
            x=serie_v.values, y=serie_v.index, orientation="h",
            marker_color=C_AZUL,
            text=[f"{v:.3f}" for v in serie_v.values], textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>V de Cramér = %{x:.3f}<extra></extra>",
        ))
        for x, txt in [(0.1, "Débil"), (0.3, "Moderada"), (0.5, "Fuerte")]:
            fig.add_vline(x=x, line_dash="dot", line_color="#999",
                          annotation_text=txt, annotation_position="top")
        fig.update_layout(
            title="Todas las asociaciones categóricas son débiles (V de Cramér < 0,30)",
            xaxis_title="V de Cramér (0 = independencia, 1 = asociación perfecta)",
            yaxis_title="",
        )
        fig.update_xaxes(range=[0, 0.55])

        guardar(fig, "24_cramers_v_asociaciones", alto=520, margen_l=270)
        display(pd.DataFrame({"V de Cramér": serie_v.round(3)}))
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Barras horizontales con la V de Cramér de cada par de variables,
        con líneas de referencia para asociación débil (0,1), moderada (0,3) y fuerte (0,5).

        **¿Qué patrón o comportamiento evidencia?** La asociación más alta es **nivel educativo × grupo
        ISCO (424)** con **0,274**, seguida de **nivel × gran grupo** con **0,216**. Las asociaciones
        con **empleo vigente** son casi nulas (**0,009** y **0,020**), y las de **década** son muy
        débiles (**0,062** y **0,068**). Ninguna supera 0,30.

        **¿Para qué ayuda a determinar?** Confirma que el nivel educativo y el oficio están relacionados,
        pero **de forma débil**: ninguna variable “explica” a la otra. También descarta que los empleos
        vigentes se concentren en un nivel u oficio concreto, y que la década sea un factor dominante
        (aunque la composición educativa sí cambie, el tamaño del efecto es pequeño).

        **Hallazgo preliminar:** asociaciones débiles; los patrones visuales son tendencias, no reglas.
        Esto refuerza el carácter **descriptivo y no causal** del EDA.
        """
    ),
]

# ---------------------------------------------------------------- 7. Calidad
celdas += [
    md(
        """
        ## 7. Calidad de datos

        **¿Qué vamos a analizar?** La disponibilidad de cada columna objetivo, la cobertura ESCO y un
        resumen de nulos, duplicados y valores extremos.

        **¿Por qué es relevante?** Define el universo analizable y las limitaciones que deben declararse
        en el informe.
        """
    ),
    md(
        """
        ### 7.1 Disponibilidad de las columnas objetivo

        **¿Qué vamos a analizar?** El porcentaje de filas sin dato real y el porcentaje con un valor
        **declarado como desconocido** (`No reportado`) en cada columna objetivo.

        **¿Por qué es relevante?** Un nulo y un “no reportado” no son lo mismo: el segundo es una
        respuesta explícita. Mezclarlos sin decirlo distorsiona la interpretación.
        """
    ),
    code(
        """
        columnas_obj = {
            "Resume_id": "resume_id",
            "Period_Time": "Period_Time",
            "University_Level": "university_level",
            "Isco_group": "isco_group_label",
            "Skill_competence": "n_skills_competence",
            "Skill_Knowledge": "n_skills_knowledge",
        }
        disponibilidad = pd.DataFrame({
            "columna": list(columnas_obj),
            "nulo_%": [df[c].isna().mean() * 100 for c in columnas_obj.values()],
            "declarado_%": [
                (df["University_Level_norm"].eq("No reportado").mean() * 100)
                if col == "University_Level" else 0.0
                for col in columnas_obj
            ],
        })

        fig = go.Figure()
        fig.add_bar(
            x=disponibilidad["nulo_%"], y=disponibilidad["columna"], orientation="h",
            name="Nulo real (sin dato)", marker_color="#9AA5B1",
            text=[f"{v:.1f} %" if v >= 1 else "" for v in disponibilidad["nulo_%"]],
            textposition="outside", cliponaxis=False,
            hovertemplate="%{y}<br>Nulo real: %{x:.2f} %<extra></extra>",
        )
        fig.add_bar(
            x=disponibilidad["declarado_%"], y=disponibilidad["columna"], orientation="h",
            name="Declarado desconocido", marker_color=C_NARANJA,
            text=[f"{v:.1f} %" if v >= 1 else "" for v in disponibilidad["declarado_%"]],
            textposition="outside", cliponaxis=False,
            hovertemplate="%{y}<br>Declarado: %{x:.2f} %<extra></extra>",
        )
        fig.update_layout(
            barmode="stack",
            title="Ninguna columna objetivo supera 12 % de información no disponible",
            xaxis_title="% de experiencias", yaxis_title="Columna objetivo",
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        )
        fig.update_xaxes(range=[0, 22], ticksuffix="%")

        guardar(fig, "25_disponibilidad_columnas_objetivo", alto=520)
        display(disponibilidad.round(2))
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** Para cada columna objetivo, el porcentaje de nulos reales (gris)
        y de valores declarados como desconocidos (naranja).

        **¿Qué patrón o comportamiento evidencia?** `Resume_id` y `Period_Time` están **completos**.
        `University_Level` no tiene nulos, pero un **11,37 %** está declarado como `No reportado`.
        `Isco_group` tiene **6,85 %** de nulos y los dos contadores ESCO, **7,52 %** cada uno (los mismos
        28.304 registros sin clasificación). No hay ninguna columna con más de 12 % de información no
        disponible.

        **¿Para qué ayuda a determinar?** Delimita el universo: los cruces ocupacionales se calculan
        sobre el **93,15 %** de filas con grupo ISCO, y los análisis de competencias sobre el **92,48 %**
        con ESCO. `No reportado` educativo debe mantenerse en los denominadores porque es una categoría
        declarada, no un hueco.

        **Hallazgo preliminar:** calidad razonable, con pérdidas moderadas y bien localizadas.
        """
    ),
    md(
        """
        ### 7.2 Cobertura ESCO

        **¿Qué vamos a analizar?** La distribución de `saber_skills` (`ok` vs. `no_clasificado`) y su
        relación con la presencia de grupo ocupacional.

        **¿Por qué es relevante?** Las competencias solo tienen sentido cuando el oficio está clasificado
        por ESCO. Si la cobertura fuera baja, el análisis de competencias representaría a una minoría.
        """
    ),
    code(
        """
        cobertura = df["saber_skills"].value_counts()
        nombres_cob = {"ok": "Con oficio ESCO (ok)", "no_clasificado": "Sin clasificación ESCO"}

        fig = go.Figure(go.Bar(
            x=[nombres_cob.get(i, i) for i in cobertura.index],
            y=cobertura.values,
            marker_color=[C_VERDE, C_NARANJA],
            text=[f"{mil(v)}<br>{v / len(df) * 100:.2f} %" for v in cobertura.values],
            textposition="outside", cliponaxis=False,
            hovertemplate="%{x}<br>%{y:,} experiencias<extra></extra>",
        ))
        fig.update_layout(
            title="Cobertura ESCO: 92,5 % de las experiencias tiene oficio clasificado",
            xaxis_title="Estado de clasificación", yaxis_title="Experiencias", showlegend=False,
        )
        fig.update_yaxes(range=[0, cobertura.max() * 1.2])

        guardar(fig, "26_cobertura_esco", alto=540)

        sin_isco = int(df["isco_group_label"].isna().sum())
        rescatadas = int((df["saber_skills"].eq("no_clasificado") & df["isco_group_label"].notna()).sum())
        print(f"Filas sin grupo ISCO: {sin_isco:,}")
        print(f"Filas no_clasificado con grupo recuperado (es_rescatado): {rescatadas:,}")
        """
    ),
    md(
        """
        **¿Qué muestra este gráfico?** El número y porcentaje de experiencias con y sin clasificación
        ESCO.

        **¿Qué patrón o comportamiento evidencia?** **348.263 experiencias (92,48 %)** tienen oficio
        ESCO (`ok`); **28.304 (7,52 %)** están `no_clasificado`. De estas últimas, **2.499** sí tienen
        grupo ocupacional recuperado (`es_rescatado = True`), por lo que **25.805 (6,85 %)** quedan sin
        grupo ISCO.

        **¿Para qué ayuda a determinar?** Confirma que el análisis ocupacional y de competencias cubre a
        la gran mayoría de la muestra. También explica por qué los nulos de `Isco_group` (6,85 %) y de
        los contadores ESCO (7,52 %) **no coinciden**: hay 2.499 filas rescatadas con oficio pero sin
        competencias.

        **Hallazgo preliminar:** cobertura ESCO alta y consistente; las pérdidas están identificadas y
        cuantificadas.
        """
    ),
    md(
        """
        ### 7.3 Resumen de control de calidad

        **¿Qué vamos a revisar?** Duplicados exactos, valores extremos (regla IQR) y consistencia del
        grano. Esta tabla resume los chequeos que respaldan las limitaciones del informe.
        """
    ),
    code(
        """
        def outliers_iqr(serie):
            s = serie.dropna()
            q1, q3 = s.quantile([0.25, 0.75])
            iqr = q3 - q1
            fuera = (s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)
            return int(fuera.sum()), round(100 * fuera.mean(), 2)

        controles = []
        for nombre, col in [
            ("Skill_competence", "n_skills_competence_num"),
            ("Skill_Knowledge", "n_skills_knowledge_num"),
            ("n_skills_essential", "n_skills_essential_num"),
        ]:
            n_out, pct_out = outliers_iqr(df[col])
            controles.append({"control": f"Outliers IQR · {nombre}", "valor": f"{n_out:,} ({pct_out} %)"})

        controles += [
            {"control": "Filas duplicadas exactas", "valor": f"{int(df.duplicated().sum()):,}"},
            {"control": "Experiencias por persona (media)", "valor": f"{len(df) / df['resume_id'].nunique():.2f}"},
            {"control": "Personas con 1 sola experiencia", "valor": f"{(df['resume_id'].value_counts() == 1).sum():,} (6,15 %)"},
            {"control": "Empleos vigentes (censurados)", "valor": f"{int(df['es_vigente_bool'].sum()):,} (5,03 %)"},
            {"control": "Combinaciones únicas de Period_Time", "valor": f"{df['Period_Time'].nunique():,}"},
            {"control": "Grupos ISCO únicos", "valor": f"{df['Isco_group_unif'].nunique():,}"},
        ]
        display(pd.DataFrame(controles))
        """
    ),
    md(
        """
        **¿Qué muestra la tabla?** Un resumen de los chequeos de calidad ejecutados sobre el dataset.

        **¿Qué patrón o comportamiento evidencia?** **No hay filas duplicadas exactas**. Los valores
        extremos por IQR afectan al **4,61 %** de `Skill_competence`, al **2,01 %** de `Skill_Knowledge`
        y al **4,71 %** de `n_skills_essential`. Hay 18.956 empleos vigentes (5,03 %) y 6.229
        combinaciones distintas de `Period_Time`.

        **¿Para qué ayuda a determinar?** Indica que los datos están bien estructurados (sin duplicados),
        pero que los contadores tienen colas que conviene tratar con mediana/IQR o, si se modela, con
        transformación o winsorización. La censura de los vigentes y la granularidad temporal deben
        declararse.

        **Hallazgo preliminar:** dataset consistente; los principales riesgos son las colas de
        competencias y la censura temporal, no la duplicación.
        """
    ),
]

# ---------------------------------------------------------------- 8. Hallazgos
celdas += [
    md(
        """
        ## 8. Hallazgos, conclusiones y recomendaciones

        ### Hallazgos clave

        1. **Grano y concentración de personas.** Hay **376.567 experiencias** para **71.061 personas**
           (**5,3** por persona). El **6,15 %** tiene una sola experiencia, la mediana es **5** y el
           máximo **20**. El dataset describe **trayectorias**, no personas únicas.

        2. **Period_Time es de alta cardinalidad y está censurada.** Existen **6.229** combinaciones
           inicio-fin; el top 20 solo cubre el **23,4 %**. Los inicios se concentran entre 2000 y 2016
           (pico en **2012**) y en el **primer trimestre**. La duración mediana es **5 trimestres
           (1,25 años)**; el **66,4 %** dura exactamente 2, 5 o 9 trimestres por la rejilla trimestral.
           El **5,03 %** de los empleos sigue vigente y queda censurado.

        3. **Nivel educativo.** Predomina **Secundaria (39,3 %)**, seguida de **Pregrado (34,4 %)**,
           **Maestría (14,5 %)**, **No reportado (11,4 %)** y **Doctorado (0,4 %)**. En este archivo
           `No reportado` es una etiqueta literal, no un nulo.

        4. **Ocupaciones.** Hay **424 grupos ISCO** y **2.855 ocupaciones** específicas. El top 5 de
           grupos cubre el **22,6 %**, el top 10 el **31,2 %** y el top 50 el **56,9 %**: concentración
           moderada con **cola larga**. Servicios y vendedores (**20,3 %**), técnicos (**18,1 %**) y
           profesionales (**16,5 %**) son los bloques más grandes.

        5. **Educación × oficio.** El cruce muestra un gradiente: limpieza, manufactura y carga
           concentran secundaria (**57–61 %**), mientras profesores de secundaria (**55,0 % pregrado,
           36,9 % maestría**) y trabajadores sociales (**54,5 % pregrado**) se inclinan a educación
           superior. La asociación es **débil–moderada** (V de Cramér **0,274** con 424 grupos y
           **0,216** con grandes grupos), **no causal**.

        6. **Competencias vs. conocimientos (clave).** `Skill_competence` tiene mediana **18** (media
           19,2; rango 0–69) y `Skill_Knowledge` mediana **3** (media 4,0; rango 0–45, con **10,3 %**
           de ceros). **Ambas son exigencias del oficio según ESCO, no competencias de la persona.**
           Su correlación es **0,34**: miden dimensiones distintas.

        7. **El conocimiento discrimina; la competencia no.** La mediana de competencias es casi plana
           entre niveles educativos (17–20), mientras la de conocimientos sube **2 → 3 → 4 → 6** de
           secundaria a doctorado. Por gran grupo ISCO, la competencia va de **11** (apoyo
           administrativo) a **22** (agricultura) y el conocimiento de **2** (ocupaciones elementales)
           a **11** (agricultura).

        8. **Redundancia estructural.** `n_skills_essential` correlaciona **0,95** con
           `n_skills_competence` y **0,62** con `n_skills_knowledge`; es el total de los contadores.
           `n_skills_sin_tipo` es casi constante (99,1 % ceros). Para analizar, usar `competence` y
           `knowledge`; `essential` solo como control.

        9. **Tiempo y composición.** La composición educativa cambia por década: en los 70 la
           secundaria era **64,1 %** y el pregrado **15,9 %**; en los 2010 el pregrado (**37,4 %**)
           supera a la secundaria (**36,2 %**). Es un **efecto de composición temporal**, no una
           trayectoria individual.

        10. **Calidad.** **92,48 %** de las experiencias tiene oficio ESCO. Hay **6,85 %** sin grupo
            ISCO y **7,52 %** sin competencias; **2.499** filas rescatadas explican la diferencia. No
            hay duplicados exactos. Los valores extremos por IQR afectan a **2,0–4,7 %** de los
            contadores.

        ### ¿Qué respuestas se obtienen a las columnas objetivo?

        - `Resume_id`: no es un identificador único de fila; agrupa **trayectorias** con 5,3 experiencias
          en promedio.
        - `Period_Time`: se creó correctamente, pero su alta cardinalidad obliga a derivar **año,
          trimestre y duración** para analizarla.
        - `University_Level`: composición conocida, con **11,4 %** declarado como `No reportado`.
        - `Isco_group`/`ISCO_group`: unificados con `isco_group_label`; **424 grupos** y una cola larga
          que justifica el top N.
        - `Skill_competence`/`Skill_Knowledge`: caracterizadas como **requerimientos del oficio**, con
          perfiles diferenciados por gran grupo y por nivel educativo (sobre todo en conocimiento).

        ### Limitaciones

        - **Grano:** todo se calcula por **experiencia laboral**, no por persona.
        - **Competencias:** son **requerimientos del oficio (ESCO)**, no habilidades poseídas.
        - **Causalidad:** solo se describen **asociaciones y composiciones**; no se prueba que la
          educación “cause” el oficio ni viceversa.
        - **Archivo con outliers:** este notebook usa `empleos_limpio_con_competencias .csv`
          (376.567 filas). El proyecto también mantiene una variante `sin_outliers` (341.090 filas);
          los resultados pueden cambiar ligeramente con ella.
        - **Ausencias:** `No reportado` (11,4 %), `no_clasificado` (7,5 %) y sin grupo ISCO (6,9 %) se
          declaran y se mantienen visibles.
        - **Temporal:** los empleos vigentes están **censurados** y el registro está dominado por la
          rejilla trimestral.
        - **Geografía:** Flandes, Bélgica (JobHop v2); no se generaliza a otros mercados.

        ### Recomendaciones

        - Para análisis **por persona**, deduplicar/agregar por `resume_id` y declarar la regla.
        - Para tiempo, usar **año/trimestre de inicio y duración**; no usar `Period_Time` como categoría.
        - En cruces educación–ocupación, normalizar **por grupo** e incluir `No reportado`.
        - Elegir `Skill_competence` + `Skill_Knowledge` como representación; no sumar `essential` otra vez.
        - Reportar **medianas e IQR** en los contadores por sus colas; si se modela, evaluar
          transformación o winsorización.
        - Mantener el enfoque **descriptivo** y las reglas de honestidad visual de `docs/EDA.md`.
        """
    ),
]

# ---------------------------------------------------------------- 9. Reproducibilidad
celdas += [
    md(
        """
        ## 9. Reproducibilidad

        - **Dataset:** `data/03_processed/empleos_limpio_con_competencias .csv` (UTF-8, 376.567 × 23)
        - **Sesión scientific-eda:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`
        - **Journal (append-only):** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/journal.md`
        - **Estadísticas de respaldo:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/resumen_columnas_objetivo.json`
        - **Librerías:** todas se importan en la **primera celda de código** (`pandas`, `numpy`,
          `plotly`).
        - **Dependencias nuevas:** `plotly>=6.0` y `kaleido>=1.0` (exportación a WebP).
        - **Figuras interactivas:** `plots/figuras_plotly/*.html` (26 archivos; `plotly.min.js` se
          guarda una sola vez en la misma carpeta).
        - **Figuras estáticas:** `plots/figuras_plotly/*.webp` (26 archivos).
        - **Scripts (PEP723 + `uv run`):**
          - `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/estadisticas_columnas_objetivo.py`
          - `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/construir_notebook_plotly.py`

        ```bash
        cd C:\\Users\\ASUS\\Documents\\MINERIA2

        # 1) Estadísticas de respaldo
        uv run analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/estadisticas_columnas_objetivo.py

        # 2) Reconstruir el notebook (opcional; ya está versionado)
        uv run analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/construir_notebook_plotly.py

        # 3) Ejecutar y persistir las salidas interactivas
        uv run python -m nbconvert --to notebook --execute --inplace \\
          --ExecutePreprocessor.timeout=1800 notebooks/EDA_Columnas_Objetivo.ipynb
        ```

        > **Nota:** el notebook embebe `plotly.js` una vez para que las figuras funcionen sin internet.
        > Los HTML exportados usan `plotly.min.js` en la misma carpeta; si se mueven, hay que mover
        > también ese archivo.
        """
    ),
]

# --------------------------------------------------------------------------- guardar
nb = new_notebook(cells=celdas)
nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata["language_info"] = {
    "name": "python",
    "version": "3.13",
    "mimetype": "text/x-python",
    "file_extension": ".py",
}
nb.metadata["title"] = "EDA enfocado a las columnas objetivo - JobPath (Plotly)"

DESTINO.write_text(nbformat.writes(nb) + "\n", encoding="utf-8")
print(f"Notebook escrito: {DESTINO}")
print(f"Celdas: {len(celdas)} (markdown: {sum(c.cell_type == 'markdown' for c in celdas)}, "
      f"código: {sum(c.cell_type == 'code' for c in celdas)})")
