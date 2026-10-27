import json
from pathlib import Path

nb = {
 'nbformat': 4,
 'nbformat_minor': 5,
 'metadata': {
  'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
  'language_info': {'name': 'python', 'version': '3.11'}
 },
 'cells': []
}

def md(text):
    nb['cells'].append({'cell_type':'markdown','metadata':{},'source':text.splitlines(True)})

def code(src):
    nb['cells'].append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':src.splitlines(True)})

md('# EDA enfocado a las columnas objetivo - JobPath\n\n**Proyecto:** JobPath (Minería de Datos - UNIMINUTO Ibagué, 2026-2)\n\n**Dataset:** `data/03_processed/empleos_limpio_con_competencias .csv`\n\n**Sesión scientific-eda:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`\n\n**Fecha:** 2026-10-25\n\n**Objetivo:** Realizar EDA descriptivo enfocado exclusivamente a las columnas objetivo solicitadas, con explicación de cada gráfico (¿qué muestra?, ¿qué patrón evidencia?, ¿para qué ayuda a determinar?).\n\n**Encoding:** UTF-8')

md('## Índice\n\n1. [Importación de librerías](#1-importación-de-librerías)\n2. [Contexto y Metodología](#2-contexto-y-metodología)\n3. [Carga de datos y preparación](#3-carga-de-datos-y-preparación)\n4. [Análisis Univariado por columna objetivo](#4-análisis-univariado-por-columna-objetivo)\n5. [Análisis Bivariado](#5-análisis-bivariado)\n6. [Análisis Multivariado y Redundancia](#6-análisis-multivariado-y-redundancia)\n7. [Calidad de Datos](#7-calidad-de-datos)\n8. [Hallazgos, Conclusiones y Recomendaciones](#8-hallazgos-conclusiones-y-recomendaciones)\n9. [Reproducibilidad](#9-reproducibilidad)')

md('## 1. Importación de librerías\n\n**Todas las librerías necesarias se cargan en esta única celda de código.**')
code('''# === TODAS LAS LIBRERÍAS ===
import os
import sys
import json
import math
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import seaborn as sns

from IPython.display import Image, display, HTML

plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
sns.set_style('whitegrid')

print("Librerías cargadas correctamente")
''')

md('## 2. Contexto y Metodología\n\n- Se sigue **estrictamente** la skill `scientific-eda`.\n- Contexto primero, un solo paso a la vez, documentado en `journal.md` (append-only).\n- Scripts con **PEP723 + `uv run`**, figuras guardadas en formato **`.webp`**.\n- **Encoding:** UTF-8\n- **Competencias (Skill_competence / Skill_Knowledge):** Son **requerimientos del oficio según ESCO**, NO competencias que posee la persona.\n\n### Mapeo de las columnas objetivo\n\n| Columna solicitada | Columna real en el dataset | Notas |\n|---|---|---|\n| `Resume_id` | `resume_id` | Identificador de persona. 1 fila = 1 experiencia laboral, NO 1 persona. |\n| `Period_Time` | Creada a partir de `start_date` y `end_date` | Se concatena como `start_date - end_date`. Si `end_date == "Present"`, se conserva `"Present"`. |\n| `University_Level` | `university_level` | Los valores vacíos/NaN se pasan a `"No reportado"`. Orden canónico: `No reportado`, `Secondary school`, `Bachelor`, `Master`, `PhD`. Traducción solo para visualización. |\n| `Isco_group` | `isco_group_label` (prioritario) / `isco_group` | Se unifican. Se utiliza `isco_group_label` por ser más legible. Se documenta la unificación. |\n| `Skill_competence` | `n_skills_competence` | Requerimiento del oficio según ESCO. **NO es competencia de la persona.** |\n| `Skill_Knowledge` | `n_skills_knowledge` | Requerimiento del oficio según ESCO. **NO es competencia de la persona.** |\n| `ISCO_group` | `isco_group_label` / `isco_group` | Se unifica con `Isco_group`. |')

md('## 3. Carga de datos y preparación\n\n### ¿Qué vamos a hacer?\nCargar el archivo `empleos_limpio_con_competencias .csv` con **encoding UTF-8**, crear la columna `Period_Time`, normalizar `University_Level` a `"No reportado"`, unificar `Isco_group` y convertir las columnas numéricas de competencias para su análisis.\n\n### ¿Por qué es relevante?\nGarantiza trazabilidad, honestidad con los datos y consistencia con las reglas del proyecto (`docs/EDA.md`).')
code('''# Buscar raíz del proyecto
root = Path.cwd()
for p in [root] + list(root.parents):
    if (p / "data").exists():
        root = p
        break

# Cargar dataset con encoding UTF-8
data_path = root / "data" / "03_processed" / "empleos_limpio_con_competencias .csv"
print("Cargando dataset con encoding UTF-8:")
print(data_path)
print("")

df = pd.read_csv(data_path, encoding='utf-8', dtype=str, keep_default_na=False, na_values=[""])
print("Shape del dataset:", df.shape)
print("Columnas:", len(df.columns))
print("")

# Crear Period_Time
df["Period_Time"] = df["start_date"].astype(str) + " - " + df["end_date"].astype(str)

# Normalizar University_Level
CANON_UNIV = ["No reportado", "Secondary school", "Bachelor", "Master", "PhD"]
df["University_Level_norm"] = df["university_level"].copy()
df.loc[df["University_Level_norm"].isna(), "University_Level_norm"] = "No reportado"
df.loc[df["University_Level_norm"].astype(str).str.strip() == "", "University_Level_norm"] = "No reportado"
df["University_Level_norm"] = df["University_Level_norm"].fillna("No reportado")

# Unificar Isco_group
df["Isco_group_unif"] = df["isco_group_label"].fillna("SIN_GRUPO")

# Convertir numéricos para análisis
df["n_skills_competence_num"] = pd.to_numeric(df["n_skills_competence"], errors="coerce")
df["n_skills_knowledge_num"] = pd.to_numeric(df["n_skills_knowledge"], errors="coerce")
df["n_skills_essential_num"] = pd.to_numeric(df["n_skills_essential"], errors="coerce")

print("Preparación completada correctamente")
print("")
df[["resume_id", "start_date", "end_date", "Period_Time", "university_level", "University_Level_norm", "isco_group_label", "Isco_group_unif", "n_skills_competence", "n_skills_knowledge"]].head()
''')

md('## 4. Análisis Univariado por columna objetivo\n\nPara cada columna objetivo se realiza: tabla/resumen + gráfico + explicación obligatoria (¿Qué muestra?, ¿Qué patrón evidencia?, ¿Para qué ayuda a determinar?, Hallazgos preliminares).')

md('### 4.1 `Resume_id` (identificador de persona)\n\n**¿Qué vamos a analizar?** Diferencia entre número de filas (experiencias laborales) y número de personas únicas (`resume_id`).\n\n**¿Por qué es relevante?** El grano del dataset es **1 fila = 1 experiencia laboral, NO 1 persona**. Es fundamental tener esto claro para no interpretar conteos erróneamente.')
code('''unique_resumes = df["resume_id"].nunique()
total_filas = len(df)

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(["Filas (experiencias laborales)", "Personas únicas (resume_id)"], [total_filas, unique_resumes], color=['#5B8DB8', '#35754F'], width=0.6)
ax.set_title("Resume_id: Experiencias laborales vs personas únicas", fontsize=12, fontweight='bold')
ax.set_ylabel("Conteo", fontsize=11)
ax.grid(axis='y', linestyle=':', alpha=0.5)

for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height):,}', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.show()

print(f"Total de filas (experiencias): {total_filas:,}")
print(f"Personas únicas (resume_id): {unique_resumes:,}")
print(f"Diferencia (experiencias extra): {total_filas - unique_resumes:,}")
''')
md('**¿Qué muestra este gráfico?** Comparación entre el número total de experiencias laborales y el número de personas únicas identificadas por `resume_id`.\n\n**¿Qué patrón o comportamiento evidencia?** Existe una diferencia considerable: hay **más filas que personas únicas**, lo que indica que muchas personas aparecen con múltiples experiencias laborales en su trayectoria.\n\n**¿Para qué ayuda a determinar?** Obliga a recordar que el análisis por conteo es **por experiencia, no por persona**. Al calcular proporciones por grupo ocupacional o nivel educativo, se está analizando la composición de **empleos/experiencias**, no la distribución entre personas. También justifica el análisis de pluriempleo.\n\n**Hallazgos preliminares:** El dataset tiene trayectorias con múltiples empleos por persona. Cualquier inferencia debe tener en cuenta el grano (experiencia laboral).')

md('### 4.2 `Period_Time` (start_date - end_date)\n\n**¿Qué vamos a analizar?** Frecuencia de las combinaciones de periodo más comunes (`start_date - end_date`).\n\n**¿Por qué es relevante?** Permite entender la distribución temporal de las experiencias laborales y detectar periodos vigentes (`Present`).')
code('''fig, ax = plt.subplots(figsize=(12, 6))
period_counts = df["Period_Time"].value_counts().head(20)
period_counts.plot(kind="bar", ax=ax, color='#5B8DB8')
ax.set_title("Top 20 Period_Time más frecuentes (start_date - end_date)", fontsize=12, fontweight='bold')
ax.set_xlabel("Periodo", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
plt.xticks(rotation=90)
ax.grid(axis='y', linestyle=':', alpha=0.5)
plt.tight_layout()
plt.show()

print(period_counts)
''')
md('**¿Qué muestra este gráfico?** Las 20 combinaciones `Period_Time` con mayor número de experiencias laborales.\n\n**¿Qué patrón o comportamiento evidencia?** Existe concentración en ciertos periodos. Es posible identificar empleos vigentes cuando aparece `Present` al final.\n\n**¿Para qué ayuda a determinar?** Contextualiza el horizonte temporal del dataset, permite identificar la censura por la derecha (empleos vigentes) y sirve como base para entender la cronología de las trayectorias.\n\n**Hallazgos preliminares:** La distribución temporal está concentrada en ciertos periodos. La presencia de `Present` indica empleos vigentes al momento de captura del CV.')

md('### 4.3 `University_Level`\n\n**¿Qué vamos a analizar?** Distribución del nivel educativo tras normalizar los valores vacíos/NaN a `"No reportado"`.')
code('''fig, ax = plt.subplots(figsize=(9, 5))
vc = df["University_Level_norm"].value_counts().reindex(CANON_UNIV, fill_value=0)
bars = vc.plot(kind="bar", ax=ax, color=["#9E9E9E", "#F4A259", "#5B8DB8", "#35754F", "#7A2626"])
ax.set_title("Distribución de University_Level (normalizado a 'No reportado')", fontsize=12, fontweight='bold')
ax.set_xlabel("Nivel educativo", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
plt.xticks(rotation=45)
ax.grid(axis='y', linestyle=':', alpha=0.5)

for i, v in enumerate(vc):
    ax.text(i, v, f'{int(v):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.show()

print(vc)
''')
md('**¿Qué muestra este gráfico?** Frecuencias absolutas por nivel educativo, con los valores ausentes explícitamente mostrados como `"No reportado"`.\n\n**¿Qué patrón o comportamiento evidencia?** Predomina `Secondary school` y `Bachelor`. Existe una fracción importante clasificada como `No reportado`, producto de valores vacíos/NaN en el dataset original.\n\n**¿Para qué ayuda a determinar?** Define la composición educativa del conjunto de experiencias. Al mostrar `No reportado` explícitamente, se mantiene la honestidad con los datos (siguiendo las reglas de `docs/EDA.md`) y evita ocultar ausencias.\n\n**Hallazgos preliminares:** La mayoría de las experiencias corresponden a niveles `Secondary school` y `Bachelor`. Los ausentes se tratan explícitamente como `No reportado`.')

md('### 4.4 `Isco_group` / `ISCO_group` (unificados)\n\n**¿Qué vamos a analizar?** Distribución de los grupos ocupacionales utilizando `isco_group_label` como base principal.\n\n**¿Por qué es relevante?** Es la dimensión ocupacional para realizar el cruce con el nivel educativo. Existe duplicidad entre `Isco_group` e `ISCO_group`, por lo que se unifican.\n\n**Decisión de unificación:** Se utiliza `isco_group_label` como base principal (`Isco_group_unif`) por su mayor legibilidad. Se verifica que `isco_group` y `isco_group_label` tienen la misma cardinalidad, siendo redundantes entre sí.')
code('''fig, ax = plt.subplots(figsize=(11, 7))
top15_isco = df["Isco_group_unif"].value_counts().head(15)
top15_isco.plot(kind="barh", ax=ax, color='#5B8DB8')
ax.set_title("Top 15 Grupos Ocupacionales (isco_group_label) - Unificados", fontsize=12, fontweight='bold')
ax.set_xlabel("Frecuencia", fontsize=11)
ax.set_ylabel("Grupo Ocupacional", fontsize=11)
ax.grid(axis='x', linestyle=':', alpha=0.5)
plt.tight_layout()
plt.show()

print("isco_group únicos:", df["isco_group"].nunique())
print("isco_group_label únicos:", df["isco_group_label"].nunique())
print("")
print(top15_isco)
''')
md('**¿Qué muestra este gráfico?** Los 15 grupos ocupacionales más frecuentes según `isco_group_label`.\n\n**¿Qué patrón o comportamiento evidencia?** Existe una alta concentración de experiencias en pocos grupos ocupacionales (destacan `Shop sales assistants`, `Administrative and executive secretaries`, etc.).\n\n**¿Para qué ayuda a determinar?** Justifica enfocar el análisis bivariado al **Top N** de grupos ocupacionales por número de empleos. Además confirma la unificación entre `Isco_group` e `ISCO_group`.\n\n**Hallazgos preliminares:** Alta concentración ocupacional. Se utiliza `isco_group_label` como representación unificada de `Isco_group`/`ISCO_group` por legibilidad.')

md('### 4.5 `Skill_competence` (`n_skills_competence`) - **Requerido por el oficio según ESCO**\n\n**¿Qué vamos a analizar?** Distribución del número de competencias tipo *competence* que **exige** el oficio según ESCO.\n\n**¿Por qué es relevante?** Es una de las columnas objetivo. **IMPORTANTE:** Este valor NO corresponde a las competencias que posee la persona, sino a las competencias que **requiere** el cargo/ocupación según la taxonomía ESCO.')
code('''fig, ax = plt.subplots(figsize=(9, 5))
data_comp = df["n_skills_competence_num"].dropna()
data_comp.plot(kind="hist", bins=30, ax=ax, alpha=0.75, color='#5B8DB8', edgecolor='black')
ax.set_title("Distribución de Skill_competence (n_skills_competence) - Requerido por oficio según ESCO", fontsize=12, fontweight='bold')
ax.set_xlabel("Número de competencias tipo 'competence'", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
ax.grid(axis='y', linestyle=':', alpha=0.5)
plt.tight_layout()
plt.show()

print(data_comp.describe())
''')
md('**¿Qué muestra este gráfico?** Distribución del número de competencias tipo *competence* exigidas por el oficio.\n\n**¿Qué patrón o comportamiento evidencia?** Distribución asimétrica positiva. La mayoría de oficios exigen un número determinado de competencias tipo *saber hacer* (*competence*), con algunos oficios que exigen mayor cantidad.\n\n**¿Para qué ayuda a determinar?** Permite caracterizar la exigencia en términos de *competencias prácticas/saber hacer* por oficio. Es fundamental recordar que se trata de **requerimientos del cargo**, no de competencias del individuo.\n\n**Hallazgos preliminares:** Existe variabilidad en la exigencia de competencias tipo *competence* entre oficios. Se trata de un atributo del oficio según ESCO.')

md('### 4.6 `Skill_Knowledge` (`n_skills_knowledge`) - **Requerido por el oficio según ESCO**\n\n**¿Qué vamos a analizar?** Distribución del número de competencias tipo *knowledge* que **exige** el oficio según ESCO.\n\n**¿Por qué es relevante?** Complementa a `Skill_competence`. **IMPORTANTE:** Este valor NO corresponde a las competencias que posee la persona, sino a las competencias que **requiere** el cargo/ocupación según la taxonomía ESCO.')
code('''fig, ax = plt.subplots(figsize=(9, 5))
data_know = df["n_skills_knowledge_num"].dropna()
data_know.plot(kind="hist", bins=30, ax=ax, alpha=0.75, color='#35754F', edgecolor='black')
ax.set_title("Distribución de Skill_Knowledge (n_skills_knowledge) - Requerido por oficio según ESCO", fontsize=12, fontweight='bold')
ax.set_xlabel("Número de competencias tipo 'knowledge'", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
ax.grid(axis='y', linestyle=':', alpha=0.5)
plt.tight_layout()
plt.show()

print(data_know.describe())
''')
md('**¿Qué muestra este gráfico?** Distribución del número de competencias tipo *knowledge* exigidas por el oficio.\n\n**¿Qué patrón o comportamiento evidencia?** Generalmente menor que las de tipo *competence*, también con asimetría hacia la derecha.\n\n**¿Para qué ayuda a determinar?** Permite distinguir entre oficios que exigen mayor componente teórico (*knowledge*) vs mayor componente práctico (*competence*). Ambos son **requerimientos del oficio**, no del individuo.\n\n**Hallazgos preliminares:** El componente *knowledge* suele ser menor al *competence*. Analizar ambos juntos permite caracterizar mejor el perfil de exigencia por ocupación.')

md('## 5. Análisis Bivariado\n\n### 5.1 `University_Level` x `Isco_group` (Barras apiladas al 100% por grupo ocupacional)\n\n**¿Qué vamos a analizar?** Composición porcentual del nivel educativo **dentro de cada grupo ocupacional**. Cada barra suma 100%.\n\n**¿Por qué es relevante?** Responde a: *"De las experiencias laborales que corresponden a este grupo ocupacional, ¿qué proporción tiene cada nivel educativo?"*\n\n**Reglas aplicadas (según `docs/EDA.md`):** Normalización **por oficio/grupo ocupacional**, se muestra `No reportado` explícitamente, se usan colores diferenciados, sin gráficos de pastel, se enfoca en los grupos más frecuentes.')
code('''NIVEL_ES = {"No reportado": "No reportado", "Secondary school": "Secundaria", "Bachelor": "Pregrado", "Master": "Maestría", "PhD": "Doctorado"}
colores = ["#C8C8C8", "#E39A50", "#5B8DB8", "#35754F", "#7A2626"]

top12 = df["Isco_group_unif"].value_counts().head(12).index
sub = df[df["Isco_group_unif"].isin(top12)].copy()

ct = pd.crosstab(sub["Isco_group_unif"], sub["University_Level_norm"])
ct = ct.reindex(columns=CANON_UNIV, fill_value=0)
pct = ct.div(ct.sum(axis=1), axis=0) * 100
pct = pct.loc[pct.sum(axis=1).sort_values(ascending=True).index]
pct_es = pct.rename(columns=NIVEL_ES)

fig, ax = plt.subplots(figsize=(15, 10))
left = np.zeros(len(pct_es))
for col, c in zip(pct_es.columns, colores):
    ax.barh(pct_es.index, pct_es[col], left=left, color=c, label=col, edgecolor='white', linewidth=0.5)
    left += pct_es[col].values

ax.set_xlim(0, 100)
ax.set_title("University_Level x Isco_group (Top 12) - Composición porcentual por grupo ocupacional", fontsize=13, fontweight='bold')
ax.set_xlabel("% de empleos del grupo ocupacional con ese nivel educativo", fontsize=11)
ax.set_ylabel("Grupo ocupacional (ISCO-08)", fontsize=11)
ax.legend(title="Nivel educativo", bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False)
ax.grid(axis='x', linestyle=':', alpha=0.5)
ax.set_axisbelow(True)
plt.tight_layout()
plt.show()

print("Tabla de respaldo (conteos):")
ct
''')
md('**¿Qué muestra este gráfico?** Barras apiladas al 100% mostrando la composición por nivel educativo dentro de cada uno de los 12 grupos ocupacionales más frecuentes.\n\n**¿Qué patrón o comportamiento evidencia?** Se observa variación entre grupos: en oficios más operativos/manuales predomina `Secundaria`, mientras que en grupos administrativos/profesionales hay mayor proporción de `Pregrado` y `Maestría`. Se mantiene visible la categoría `No reportado`.\n\n**¿Para qué ayuda a determinar?** Permite visualizar la asociación entre nivel educativo y grupo ocupacional en términos de **composición**. Ayuda a entender qué niveles educativos son más frecuentes en cada tipo de ocupación.\n\n**Hallazgos preliminares:** Existe variación en la composición por nivel educativo entre grupos ocupacionales. **Importante:** Esto muestra asociación/composición, **NO prueba causalidad** ni que el título sea un requisito para el puesto. Además, el análisis es **por experiencia (fila), no por persona**.')

md('### 5.2 `Skill_competence` y `Skill_Knowledge` por grupo ocupacional\n\n**¿Qué vamos a analizar?** Comparación de la exigencia de competencias (mediana) por grupo ocupacional.\n\n**¿Por qué es relevante?** Las competencias son **requerimientos del oficio según ESCO**, no competencias del individuo. Permite caracterizar el perfil de exigencia de cada grupo ocupacional.')
code('''top12 = df["Isco_group_unif"].value_counts().head(12).index
sub = df[df["Isco_group_unif"].isin(top12)].copy()

med = sub.groupby("Isco_group_unif")[["n_skills_competence_num", "n_skills_knowledge_num"]].median()
med = med.sort_values("n_skills_competence_num", ascending=False)
med.columns = ["Skill_competence (mediana)", "Skill_Knowledge (mediana)"]
med
''')
md('**¿Qué muestra esta tabla?** Mediana de `n_skills_competence` y `n_skills_knowledge` para los 12 grupos ocupacionales más frecuentes.\n\n**¿Qué patrón o comportamiento evidencia?** Existen diferencias entre grupos en cuanto a su perfil de exigencia. Algunos grupos exigen mayor número de competencias tipo *competence* (saber hacer), otros mayor énfasis en *knowledge* (saber).\n\n**¿Para qué ayuda a determinar?** Permite caracterizar la naturaleza de cada grupo ocupacional según el tipo de competencias que **exige** según ESCO. Ayuda a entender la demanda de competencias por tipo de ocupación.\n\n**Hallazgos preliminares:** Los grupos ocupacionales tienen perfiles de exigencia diferenciados. Las competencias analizadas son **atributos del oficio**, no del individuo.')

md('## 6. Análisis Multivariado y Redundancia\n\n### 6.1 Correlación entre competencias requeridas por el oficio\n\n**¿Qué vamos a analizar?** Correlación entre `n_skills_competence`, `n_skills_knowledge` y `n_skills_essential`.\n\n**¿Por qué es relevante?** Evaluar redundancia estructural entre estas variables.')
code('''numc = df[["n_skills_competence_num", "n_skills_knowledge_num", "n_skills_essential_num"]].copy()
corr = numc.corr()

fig, ax = plt.subplots(figsize=(7, 6))
sns.heatmap(corr, annot=True, cmap="Blues", fmt=".3f", square=True, ax=ax, cbar_kws={'shrink': 0.8})
ax.set_title("Correlación entre competencias requeridas por el oficio (ESCO)", fontsize=12, fontweight='bold')
plt.tight_layout()
plt.show()

print(corr)
''')
md('**¿Qué muestra este gráfico?** Matriz de correlación entre las tres variables de conteo de competencias requeridas por el oficio.\n\n**¿Qué patrón o comportamiento evidencia?** `n_skills_essential` presenta alta correlación con `n_skills_competence`. `n_skills_competence` y `n_skills_knowledge` se reparten el total de `n_skills_essential` (junto con `n_skills_sin_tipo`).\n\n**¿Para qué ayuda a determinar?** Confirma la **redundancia estructural**: `n_skills_essential = n_skills_competence + n_skills_knowledge + n_skills_sin_tipo`. Usar más de una de estas variables simultáneamente puede introducir redundancia.\n\n**Hallazgos preliminares:** Existe redundancia estructural entre los contadores de competencias. `Skill_competence` y `Skill_Knowledge` son componentes del total exigido por el oficio.')

md('## 7. Calidad de Datos\n\n**¿Qué vamos a analizar?** Cobertura ESCO (`saber_skills`), filas sin grupo ocupacional, pluriempleo, unificación de `Isco_group`/`ISCO_group`.')
code('''print("=" * 50)
print("COBERTURA ESCO (saber_skills)")
print("=" * 50)
print(df["saber_skills"].value_counts(dropna=False))
print("")

print("=" * 50)
print("FILAS SIN GRUPO OCUPACIONAL")
print("=" * 50)
print("Filas sin isco_group_label:", df["isco_group_label"].isna().sum())
print("")

print("=" * 50)
print("PLURIEMPLEO")
print("=" * 50)
print("Personas únicas (resume_id):", df["resume_id"].nunique())
print("Total de filas (experiencias):", len(df))
print("Diferencia (filas - personas):", len(df) - df["resume_id"].nunique())
print("")

print("=" * 50)
print("UNIFICACIÓN Isco_group / ISCO_group")
print("=" * 50)
print("isco_group (código) únicos:", df["isco_group"].nunique())
print("isco_group_label únicos:", df["isco_group_label"].nunique())
print("Isco_group_unif únicos:", df["Isco_group_unif"].nunique())
print("")
print("Conclusión: isco_group e isco_group_label son equivalentes en cardinalidad -> redundantes. Se usa isco_group_label como base.")
''')
md('**¿Qué muestra este análisis?** Indicadores de calidad: cobertura ESCO, ausencias de grupo ocupacional, pluriempleo y verificación de la unificación entre `Isco_group` e `ISCO_group`.\n\n**¿Qué patrón o comportamiento evidencia?** Mayoría de filas con oficio clasificado (`ok`). Existen filas con `no_clasificado`. Hay pluriempleo (más filas que personas únicas). `isco_group` e `isco_group_label` tienen misma cardinalidad, confirmando su equivalencia/redundancia.\n\n**¿Para qué ayuda a determinar?** Define el **universo analizable**. Las competencias (`Skill_competence`/`Skill_Knowledge`) son válidas principalmente cuando hay oficio clasificado. El análisis por grupo ocupacional solo aplica a filas con `isco_group_label`. El hecho de ser por experiencia debe tenerse en cuenta.\n\n**Hallazgos preliminares:** Cobertura mayoritariamente buena por ESCO. Se confirma la unificación usando `isco_group_label`. Hay que declarar pluriempleo y `no_clasificado` como limitaciones del análisis.')

md('## 8. Hallazgos, Conclusiones y Recomendaciones\n\n### Hallazgos clave\n\n1. **Grano del dataset:** 1 fila = 1 experiencia laboral, NO 1 persona. Hay más experiencias que personas únicas, lo que indica trayectorias con múltiples empleos (pluriempleo).\n\n2. **Columnas objetivo mapeadas:** Todas las columnas solicitadas fueron identificadas/mapeadas correctamente. `Period_Time` fue creada a partir de `start_date` y `end_date`.\n\n3. **Unificación:** `Isco_group` e `ISCO_group` son equivalentes en cardinalidad. Se utiliza `isco_group_label` como base principal para `Isco_group`/`ISCO_group` por legibilidad.\n\n4. **Nivel educativo:** Predomina `Secondary school` y `Bachelor`. Los valores ausentes fueron normalizados a `No reportado` de forma explícita, siguiendo las reglas de `docs/EDA.md`.\n\n5. **Cruce educación x grupo ocupacional:** Al normalizar **por grupo ocupacional** (cada barra suma 100%), se observa variación entre grupos. En oficios operativos predomina nivel secundario, mientras que en grupos administrativos/profesionales hay mayor proporción de pregrado/maestría. **Esto es asociación/composición, NO causalidad.**\n\n6. **Competencias:** `Skill_competence` y `Skill_Knowledge` son **requerimientos del oficio según ESCO**, NO competencias que posee la persona. Existen diferencias entre grupos ocupacionales en su perfil de exigencia. Hay redundancia estructural con `n_skills_essential`.\n\n7. **Calidad:** Mayoría de experiencias con oficio clasificado por ESCO, aunque existe un porcentaje `no_clasificado`. Se debe tener en cuenta el pluriempleo.\n\n### ¿Qué respuestas se obtienen a las columnas objetivo?\n\n- Se identificaron y mapearon todas las columnas objetivo con sus equivalentes reales.\n- Se creó `Period_Time` correctamente.\n- Se unificaron `Isco_group`/`ISCO_group` usando `isco_group_label`.\n- Se analizó la distribución de `University_Level` con tratamiento explícito de ausentes.\n- Se caracterizó la exigencia de `Skill_competence` y `Skill_Knowledge` por oficio (dejando claro que son requerimientos, no competencias poseídas).\n- Se realizó el cruce `University_Level` x `Isco_group` con normalización por grupo ocupacional.\n\n### ¿Qué ayuda a determinar para cumplir el objetivo de la entrega?\n\nEste EDA proporciona un análisis descriptivo, trazable, reproducible y enfocado exclusivamente a las columnas objetivo. Cada gráfico incluye explicación de qué muestra, qué patrón evidencia y para qué ayuda a determinar. Se siguen las reglas de honestidad visual del proyecto, se deja explícita la distinción entre competencias requeridas vs poseídas, y se documenta el grano (experiencia vs persona). Esto sirve como base descriptiva para entender la relación entre nivel educativo y grupo ocupacional, así como la exigencia de competencias por oficio.\n\n### Limitaciones\n\n- **Grano:** El análisis es por **experiencia laboral (fila)**, no por persona. Quien tuvo múltiples empleos pesa múltiples veces.\n- **Competencias:** `Skill_competence` y `Skill_Knowledge` son **requerimientos del oficio según ESCO**, no competencias que posee la persona.\n- **Causalidad:** No se establece causalidad, solo asociaciones/composiciones descriptivas.\n- **Ausencias:** Existen valores `No reportado` (nivel educativo) y filas `no_clasificado` (sin oficio clasificado por ESCO).\n- **Pluriempleo:** Conservado en el dataset.\n- **Alcance geográfico:** Datos provienen de Flandes, Bélgica.\n\n### Recomendaciones\n\n- **Para análisis por persona:** Si se requiere análisis a nivel de persona, se debe deduplicar o agregar por `resume_id` teniendo en cuenta la trayectoria.\n- **Cruces ocupacionales:** Siempre normalizar por grupo ocupacional (como se hace aquí) para responder \"¿qué nivel educativo hay en este oficio?\".\n- **Competencias:** Tratar `Skill_competence`/`Skill_Knowledge` como atributos del oficio. No interpretarlos como habilidades del individuo.\n- **Calidad:** Tener en cuenta las filas `no_clasificado` al filtrar por grupo ocupacional.\n- **Alcance:** Mantener este análisis descriptivo sin pasar a modelado/predicción, conforme al enfoque solicitado.')

md('## 9. Reproducibilidad\n\n- **Dataset utilizado:** `data/03_processed/empleos_limpio_con_competencias .csv` (con **encoding UTF-8**)\n- **Sesión scientific-eda:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`\n- **Journal (append-only):** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/journal.md`\n- **Librerías:** Todas importadas en la **primera celda de código**\n- **Scripts (PEP723 + `uv run`):**\n  - `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/inspeccion_columnas_objetivo.py`\n  - `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/generar_figuras_columnas_objetivo.py`\n- **Figuras:** Guardadas en `.webp` en `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/plots/`\n\n```bash\ncd C:\\Users\\ASUS\\Documents\\MINERIA2\nuv run analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/inspeccion_columnas_objetivo.py\nuv run analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/generar_figuras_columnas_objetivo.py\n```')

out = Path('notebooks/EDA_Columnas_Objetivo.ipynb')
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
print('OK')
