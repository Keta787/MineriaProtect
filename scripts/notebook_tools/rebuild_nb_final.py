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
    nb['cells'].append({'cell_type': 'markdown', 'metadata': {}, 'source': text.splitlines(True)})

def code(src):
    nb['cells'].append({'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': src.splitlines(True)})

# 1. PORTADA
md('# EDA enfocado a las columnas objetivo - JobPath\n\n'
   '**Proyecto:** JobPath (Minería de Datos - UNIMINUTO Ibagué, 2026-2)\n\n'
   '**Dataset:** `data/03_processed/empleos_limpio_con_competencias .csv`\n\n'
   '**Sesión scientific-eda:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`\n\n'
   '**Fecha:** 2026-10-25\n\n'
   '**Objetivo:** Realizar un EDA descriptivo enfocado exclusivamente a las columnas objetivo solicitadas, mostrando cada gráfico con su explicación: ¿qué muestra?, ¿qué patrón evidencia? y ¿para qué ayuda a determinar?\n\n'
   '**Codificación:** UTF-8')

# 2. ÍNDICE
md('## Índice\n\n'
   '1. [Importación de librerías](#1-importación-de-librerías)\n'
   '2. [Contexto y metodología](#2-contexto-y-metodología)\n'
   '3. [Carga de datos y preparación](#3-carga-de-datos-y-preparación)\n'
   '4. [Análisis univariado por columna objetivo](#4-análisis-univariado-por-columna-objetivo)\n'
   '5. [Análisis bivariado](#5-análisis-bivariado)\n'
   '6. [Análisis multivariado y redundancia](#6-análisis-multivariado-y-redundancia)\n'
   '7. [Calidad de datos](#7-calidad-de-datos)\n'
   '8. [Hallazgos, conclusiones y recomendaciones](#8-hallazgos-conclusiones-y-recomendaciones)\n'
   '9. [Reproducibilidad](#9-reproducibilidad)')

# 3. PRIMERA CELDA - TODAS LAS LIBRERÍAS
md('## 1. Importación de librerías\n\n**Todas las librerías necesarias se importan en esta única celda de código.**')
code('''# === TODAS LAS LIBRERÍAS NECESARIAS ===
import os
import sys
import json
import math
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

import seaborn as sns

from IPython.display import Image, display, HTML

# Configuración visual
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.grid'] = True
sns.set_style('whitegrid')

print("Librerías cargadas correctamente")
print("Versión de pandas:", pd.__version__)
''')

# 4. CONTEXTO
md('## 2. Contexto y metodología\n\n'
   '- Se sigue **estrictamente** la skill `scientific-eda`.\n'
   '- Contexto primero, un solo paso a la vez y todo documentado en `journal.md` (append-only).\n'
   '- Scripts con **PEP723 + `uv run`**, figuras guardadas en formato **`.webp`**.\n'
   '- **Codificación:** UTF-8\n'
   '- **Importante:** Las columnas `Skill_competence` y `Skill_Knowledge` corresponden a **competencias que EXIGE el oficio según ESCO**, **NO** a competencias que posee la persona.\n\n'
   '### Mapeo de las columnas objetivo\n\n'
   '| Columna solicitada | Columna real en el dataset | Notas |\n'
   '|-------------------|-----------------------------|-------|\n'
   '| `Resume_id` | `resume_id` | Identificador de persona. 1 fila = 1 experiencia laboral, NO 1 persona. |\n'
   '| `Period_Time` | Creada desde `start_date` y `end_date` | Concatenación `start_date - end_date`. Si `end_date == "Present"`, se conserva `"Present"`. |\n'
   '| `University_Level` | `university_level` | Valores vacíos/NaN se normalizan a `"No reportado"`. Orden: `No reportado`, `Secondary school`, `Bachelor`, `Master`, `PhD`. Solo traducción visual. |\n'
   '| `Isco_group` | `isco_group_label` (prioritario) / `isco_group` | Unificados. Se utiliza `isco_group_label` por legibilidad. |\n'
   '| `Skill_competence` | `n_skills_competence` | **Requerimiento del oficio según ESCO. NO es competencia de la persona.** |\n'
   '| `Skill_Knowledge` | `n_skills_knowledge` | **Requerimiento del oficio según ESCO. NO es competencia de la persona.** |\n'
   '| `ISCO_group` | `isco_group_label` / `isco_group` | Unificado con `Isco_group`. |')

# 5. CARGA Y PREPARACIÓN
md('## 3. Carga de datos y preparación\n\n'
   '### ¿Qué vamos a hacer?\n'
   'Cargar el archivo `empleos_limpio_con_competencias .csv` con **encoding UTF-8**, crear `Period_Time`, normalizar `University_Level` a `"No reportado"`, unificar `Isco_group`/`ISCO_group` con `isco_group_label` y preparar las variables numéricas de competencias para el análisis.\n\n'
   '### ¿Por qué es relevante?\n'
   'Garantiza trazabilidad, consistencia con las reglas del proyecto y una base limpia para el EDA enfocado a las columnas objetivo.')
code('''# Buscar raíz del proyecto
root = Path.cwd()
for p in [root] + list(root.parents):
    if (p / "data").exists():
        root = p
        break

# Cargar dataset con encoding UTF-8
data_path = root / "data" / "03_processed" / "empleos_limpio_con_competencias .csv"
print("Ruta del dataset:")
print(data_path)
print()

df = pd.read_csv(data_path, encoding='utf-8', dtype=str, keep_default_na=False, na_values=[""])
print("Dimensiones del dataset:", df.shape)
print("Total de columnas:", len(df.columns))
print()

# Crear columna Period_Time
df["Period_Time"] = df["start_date"].astype(str).str.strip() + " - " + df["end_date"].astype(str).str.strip()

# Normalizar University_Level
CANON_UNIV = ["No reportado", "Secondary school", "Bachelor", "Master", "PhD"]
df["University_Level_norm"] = df["university_level"].astype(str).str.strip()
df.loc[df["University_Level_norm"].isin(["", "nan", "None", "NaN"]), "University_Level_norm"] = "No reportado"
df["University_Level_norm"] = df["University_Level_norm"].fillna("No reportado")

# Unificar Isco_group / ISCO_group
df["Isco_group_unif"] = df["isco_group_label"].astype(str).str.strip()
df.loc[df["Isco_group_unif"].isin(["", "nan", "None", "NaN"]), "Isco_group_unif"] = "SIN_GRUPO"

# Preparar variables numéricas de competencias (requerimientos por oficio)
df["n_skills_competence_num"] = pd.to_numeric(df["n_skills_competence"], errors="coerce")
df["n_skills_knowledge_num"] = pd.to_numeric(df["n_skills_knowledge"], errors="coerce")
df["n_skills_essential_num"] = pd.to_numeric(df["n_skills_essential"], errors="coerce")
df["n_skills_sin_tipo_num"] = pd.to_numeric(df["n_skills_sin_tipo"], errors="coerce")
df["veces_ese_oficio_num"] = pd.to_numeric(df["veces_ese_oficio"], errors="coerce")

print("Preparación completada exitosamente")
print()
df[["resume_id", "start_date", "end_date", "Period_Time", "university_level", "University_Level_norm", 
    "isco_group", "isco_group_label", "Isco_group_unif", "n_skills_competence", "n_skills_knowledge"]].head()
''')

# 6. UNIVARIADO
md('## 4. Análisis univariado por columna objetivo\n\nPara cada una de las columnas objetivo se presenta el análisis con su respectiva explicación obligatoria.')
md('### 4.1 `Resume_id` (identificador de persona)\n\n**¿Qué vamos a analizar?** Diferencia entre el total de filas (experiencias laborales) y las personas únicas identificadas por `resume_id`.\n\n**¿Por qué es relevante?** El grano del dataset es **1 fila = 1 experiencia laboral, NO 1 persona**. Este punto es fundamental para interpretar correctamente los resultados.')
code('''unique_resumes = df["resume_id"].nunique()
total_filas = len(df)

fig, ax = plt.subplots(figsize=(7,5))
bars = ax.bar(["Filas (experiencias laborales)", "Personas únicas (resume_id)"], 
              [total_filas, unique_resumes], color=['#5B8DB8', '#35754F'], width=0.55)
ax.set_title("Resume_id: Experiencias laborales vs personas únicas", fontsize=12, fontweight='bold')
ax.set_ylabel("Cantidad", fontsize=11)
ax.grid(axis='y', linestyle=':', alpha=0.6)

for bar in bars:
    h = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., h, f"{int(h):,}", ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.show()

print(f"Total de filas (experiencias): {total_filas:,}")
print(f"Personas únicas: {unique_resumes:,}")
print(f"Diferencia: {total_filas - unique_resumes:,} experiencias adicionales por pluriempleo/trayectorias")
''')
md('**¿Qué muestra este gráfico?** La comparación entre el número total de experiencias laborales y el número de personas únicas.\n\n**¿Qué patrón o comportamiento evidencia?** Hay más filas que personas únicas, lo que indica que existen personas con múltiples experiencias laborales a lo largo de su trayectoria.\n\n**¿Para qué ayuda a determinar?** Obliga a recordar el grano del análisis. Cualquier proporción calculada es **por experiencia**, no por persona. Además, justifica tener en cuenta el pluriempleo al interpretar los resultados.\n\n**Hallazgos preliminares:** Existen trayectorias con múltiples empleos. El análisis debe realizarse teniendo presente que una misma persona puede contribuir con varias filas.')

md('### 4.2 `Period_Time` (`start_date - end_date`)\n\n**¿Qué vamos a analizar?** Frecuencia de las 20 combinaciones más comunes de `Period_Time`.\n\n**¿Por qué es relevante?** Permite identificar la distribución temporal de las experiencias y la presencia de empleos vigentes (`Present`).')
code('''fig, ax = plt.subplots(figsize=(12,6))
top_period = df["Period_Time"].value_counts().head(20)
top_period.plot(kind='bar', ax=ax, color='#5B8DB8')
ax.set_title("Top 20 Period_Time más frecuentes", fontsize=12, fontweight='bold')
ax.set_xlabel("Periodo (start_date - end_date)", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
plt.xticks(rotation=90)
ax.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.show()

top_period
''')
md('**¿Qué muestra este gráfico?** Las 20 combinaciones `Period_Time` con mayor número de experiencias laborales.\n\n**¿Qué patrón o comportamiento evidencia?** Se observa concentración en ciertos periodos. Algunos registros muestran `end_date = Present`, lo cual indica empleos vigentes al momento de la captura.\n\n**¿Para qué ayuda a determinar?** Contextualiza el horizonte temporal, permite identificar la censura por la derecha y entender cuándo se concentran las experiencias en el dataset.\n\n**Hallazgos preliminares:** Distribución temporal concentrada con presencia de empleos vigentes.')

md('### 4.3 `University_Level`\n\n**¿Qué vamos a analizar?** Distribución del nivel educativo tras normalizar valores vacíos o NaN a `"No reportado"`.\n\n**¿Por qué es relevante?** Es clave para el cruce con los grupos ocupacionales.')
code('''fig, ax = plt.subplots(figsize=(9,5))
vc_univ = df["University_Level_norm"].value_counts().reindex(CANON_UNIV, fill_value=0)
bars = vc_univ.plot(kind='bar', ax=ax, color=["#9E9E9E", "#F4A259", "#5B8DB8", "#35754F", "#7A2626"])
ax.set_title("Distribución de University_Level (normalizado a 'No reportado')", fontsize=12, fontweight='bold')
ax.set_xlabel("Nivel educativo", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
plt.xticks(rotation=45)
ax.grid(axis='y', linestyle=':', alpha=0.6)

for i,v in enumerate(vc_univ):
    ax.text(i, v, f"{int(v):,}", ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.show()

vc_univ
''')
md('**¿Qué muestra este gráfico?** Frecuencias por nivel educativo con la categoría `"No reportado"` explícitamente mostrada.\n\n**¿Qué patrón o comportamiento evidencia?** Predominan `Secondary school` y `Bachelor`. Existe una proporción importante de `No reportado` correspondiente a valores ausentes.\n\n**¿Para qué ayuda a determinar?** Define la composición educativa del conjunto de experiencias laborales. Mostrar `No reportado` explícitamente mantiene la honestidad con los datos.\n\n**Hallazgos preliminares:** Mayoría en `Secondary school` y `Bachelor`. Los ausentes se tratan de forma explícita y no se ocultan.')

md('### 4.4 `Isco_group` / `ISCO_group` (unificados con `isco_group_label`)\n\n**¿Qué vamos a analizar?** Distribución de los grupos ocupacionales más frecuentes.\n\n**¿Por qué es relevante?** Es la dimensión ocupacional para el cruce con `University_Level`.\n\n**Decisión de unificación:** Se utiliza `isco_group_label` como base principal (`Isco_group_unif`), ya que `isco_group` (código) y `isco_group_label` son equivalentes en cardinalidad.')
code('''fig, ax = plt.subplots(figsize=(11,7))
top15 = df["Isco_group_unif"].value_counts().head(15)
top15.plot(kind='barh', ax=ax, color='#5B8DB8')
ax.set_title("Top 15 Grupos Ocupacionales (unificados con isco_group_label)", fontsize=12, fontweight='bold')
ax.set_xlabel("Frecuencia", fontsize=11)
ax.set_ylabel("Grupo ocupacional", fontsize=11)
ax.grid(axis='x', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.show()

print("isco_group únicos:", df["isco_group"].nunique())
print("isco_group_label únicos:", df["isco_group_label"].nunique())
print("Isco_group_unif únicos:", df["Isco_group_unif"].nunique())
''')
md('**¿Qué muestra este gráfico?** Los 15 grupos ocupacionales con mayor número de experiencias laborales.\n\n**¿Qué patrón o comportamiento evidencia?** Alta concentración en pocos grupos ocupacionales.\n\n**¿Para qué ayuda a determinar?** Justifica enfocar el cruce bivariado en el Top N. Confirma que `Isco_group` e `ISCO_group` son redundantes y se unifican correctamente con `isco_group_label`.\n\n**Hallazgos preliminares:** Concentración ocupacional clara. Se mantiene `isco_group_label` como representación unificada.')

md('### 4.5 `Skill_competence` (`n_skills_competence`) - Requerido por el oficio según ESCO\n\n**¿Qué vamos a analizar?** Distribución del número de competencias tipo *competence* que **exige** el oficio según ESCO.\n\n**¿Por qué es relevante?** Es una columna objetivo. **IMPORTANTE:** Este valor es un **requerimiento del oficio**, NO una competencia que posee la persona.')
code('''fig, ax = plt.subplots(figsize=(9,5))
data_sc = df["n_skills_competence_num"].dropna()
data_sc.plot(kind='hist', bins=30, ax=ax, alpha=0.8, color='#5B8DB8', edgecolor='black')
ax.set_title("Skill_competence (n_skills_competence) - Requerido por el oficio según ESCO", fontsize=12, fontweight='bold')
ax.set_xlabel("Número de competencias tipo 'competence'", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
ax.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.show()

data_sc.describe()
''')
md('**¿Qué muestra este gráfico?** Histograma de `n_skills_competence` (competencias tipo *competence* exigidas por el oficio).\n\n**¿Qué patrón o comportamiento evidencia?** Distribución asimétrica positiva. La exigencia varía entre oficios.\n\n**¿Para qué ayuda a determinar?** Permite conocer la demanda en *saber hacer* por tipo de ocupación. Se debe tener siempre presente que son **requerimientos del cargo**, no del individuo.\n\n**Hallazgos preliminares:** Existe variabilidad en la exigencia de competencias tipo *competence* entre oficios.')

md('### 4.6 `Skill_Knowledge` (`n_skills_knowledge`) - Requerido por el oficio según ESCO\n\n**¿Qué vamos a analizar?** Distribución del número de competencias tipo *knowledge* que **exige** el oficio según ESCO.\n\n**¿Por qué es relevante?** Complementa a `Skill_competence`. **IMPORTANTE:** Este valor es un **requerimiento del oficio**, NO una competencia que posee la persona.')
code('''fig, ax = plt.subplots(figsize=(9,5))
data_sk = df["n_skills_knowledge_num"].dropna()
data_sk.plot(kind='hist', bins=30, ax=ax, alpha=0.8, color='#35754F', edgecolor='black')
ax.set_title("Skill_Knowledge (n_skills_knowledge) - Requerido por el oficio según ESCO", fontsize=12, fontweight='bold')
ax.set_xlabel("Número de competencias tipo 'knowledge'", fontsize=11)
ax.set_ylabel("Frecuencia", fontsize=11)
ax.grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.show()

data_sk.describe()
''')
md('**¿Qué muestra este gráfico?** Histograma de `n_skills_knowledge` (competencias tipo *knowledge* exigidas por el oficio).\n\n**¿Qué patrón o comportamiento evidencia?** Generalmente menor cantidad que *competence*, con distribución asimétrica.\n\n**¿Para qué ayuda a determinar?** Permite diferenciar el énfasis teórico (*knowledge*) vs práctico (*competence*) por ocupación. Ambos son **requerimientos del oficio**, no competencias del individuo.\n\n**Hallazgos preliminares:** El componente *knowledge* es complementario al *competence* y permite caracterizar mejor el perfil de exigencia por grupo ocupacional.')

# 7. BIVARIADO
md('## 5. Análisis bivariado\n\n### 5.1 `University_Level` x `Isco_group` (barras apiladas al 100% por grupo ocupacional)\n\n**¿Qué vamos a analizar?** Composición porcentual del nivel educativo **dentro de cada grupo ocupacional**. Cada barra suma 100%.\n\n**¿Por qué es relevante?** Responde: *"De las experiencias laborales de este grupo ocupacional, ¿qué proporción corresponde a cada nivel educativo?"*\n\n**Criterio aplicado:** Normalización **por grupo ocupacional**, se incluye `No reportado` explícitamente, sin gráficos de pastel, siguiendo las recomendaciones de `docs/EDA.md`.')
code('''NIVEL_ES = {"No reportado": "No reportado", "Secondary school": "Secundaria", 
            "Bachelor": "Pregrado", "Master": "Maestría", "PhD": "Doctorado"}
COLORES = ["#C8C8C8", "#F4A259", "#5B8DB8", "#35754F", "#7A2626"]

top12 = df["Isco_group_unif"].value_counts().head(12).index
sub = df[df["Isco_group_unif"].isin(top12)].copy()

ct = pd.crosstab(sub["Isco_group_unif"], sub["University_Level_norm"])
ct = ct.reindex(columns=CANON_UNIV, fill_value=0)
pct = ct.div(ct.sum(axis=1), axis=0) * 100
pct = pct.sort_values(by="Secondary school", ascending=True)
pct_es = pct.rename(columns=NIVEL_ES)

fig, ax = plt.subplots(figsize=(15, 10))
left = np.zeros(len(pct_es))
for col, c in zip(pct_es.columns, COLORES):
    ax.barh(pct_es.index, pct_es[col], left=left, color=c, label=col, edgecolor='white', linewidth=0.6)
    left += pct_es[col].values

ax.set_xlim(0, 100)
ax.set_title("University_Level x Isco_group (Top 12) - Composición porcentual por grupo ocupacional", fontsize=13, fontweight='bold')
ax.set_xlabel("% de empleos del grupo ocupacional con ese nivel educativo", fontsize=11)
ax.set_ylabel("Grupo ocupacional (isco_group_label)", fontsize=11)
ax.legend(title="Nivel educativo", bbox_to_anchor=(1.01, 1), loc='upper left', frameon=False)
ax.grid(axis='x', linestyle=':', alpha=0.6)
ax.set_axisbelow(True)
plt.tight_layout()
plt.show()

ct
''')
md('**¿Qué muestra este gráfico?** Barras apiladas al 100% con la composición por nivel educativo dentro de cada uno de los 12 grupos ocupacionales más frecuentes.\n\n**¿Qué patrón o comportamiento evidencia?** Se aprecia variación entre grupos. Los oficios más operativos presentan mayor proporción de `Secundaria` y `No reportado`, mientras que los grupos administrativos y profesionales muestran mayor peso de `Pregrado` y `Maestría`.\n\n**¿Para qué ayuda a determinar?** Permite visualizar la asociación entre nivel educativo y grupo ocupacional en términos de **composición**. Ayuda a responder qué nivel educativo es más frecuente en cada ocupación.\n\n**Hallazgos preliminares:** Existe variación clara entre grupos. **Importante:** Esto refleja **asociación/composición**, **NO causalidad** ni que el título sea requisito obligatorio. El análisis es **por experiencia laboral (fila), no por persona**.')

md('### 5.2 `Skill_competence` y `Skill_Knowledge` por grupo ocupacional (mediana)\n\n**¿Qué vamos a analizar?** Mediana del número de competencias tipo *competence* y *knowledge* exigidas por cada grupo ocupacional.\n\n**¿Por qué es relevante?** Permite comparar el perfil de exigencia entre ocupaciones. Recuerde: son **requerimientos del oficio según ESCO**, no competencias del individuo.')
code('''top12 = df["Isco_group_unif"].value_counts().head(12).index
sub_b = df[df["Isco_group_unif"].isin(top12)].copy()
med_sk = sub_b.groupby("Isco_group_unif")[["n_skills_competence_num", "n_skills_knowledge_num"]].median()
med_sk.columns = ["Skill_competence (mediana) - Requerido por oficio", "Skill_Knowledge (mediana) - Requerido por oficio"]
med_sk = med_sk.sort_values("Skill_competence (mediana) - Requerido por oficio", ascending=False)
med_sk
''')
md('**¿Qué muestra esta tabla?** Mediana de competencias exigidas por el oficio para los 12 grupos ocupacionales más frecuentes.\n\n**¿Qué patrón o comportamiento evidencia?** Se observan diferencias entre grupos en su perfil de exigencia. Algunos exigen mayor número de competencias tipo *competence* (saber hacer), otros muestran distinto equilibrio con *knowledge* (saber).\n\n**¿Para qué ayuda a determinar?** Permite caracterizar la naturaleza de cada ocupación según qué tipo de competencias **exige** ESCO. Útil para entender la demanda de competencias por tipo de grupo ocupacional.\n\n**Hallazgos preliminares:** Los perfiles de exigencia son diferenciados entre grupos. Ambas variables son **atributos del oficio**, no del trabajador.')

# 8. MULTIVARIADO
md('## 6. Análisis multivariado y redundancia\n\n### 6.1 Correlación entre competencias requeridas por el oficio\n\n**¿Qué vamos a analizar?** Relación entre `n_skills_competence`, `n_skills_knowledge` y `n_skills_essential`.\n\n**¿Por qué es relevante?** Detectar redundancia estructural entre estos contadores.')
code('''num_corr = df[["n_skills_competence_num", "n_skills_knowledge_num", "n_skills_essential_num"]].dropna()
corr_mat = num_corr.corr()

fig, ax = plt.subplots(figsize=(7,6))
sns.heatmap(corr_mat, annot=True, cmap='Blues', fmt='.3f', square=True, ax=ax, cbar_kws={'shrink':0.8})
ax.set_title("Correlación entre competencias requeridas por el oficio (ESCO)", fontsize=12, fontweight='bold')
plt.tight_layout()
plt.show()

corr_mat
''')
md('**¿Qué muestra este gráfico?** Matriz de correlación entre los contadores de competencias exigidas por el oficio.\n\n**¿Qué patrón o comportamiento evidencia?** `n_skills_essential` muestra alta correlación con `n_skills_competence`. Además, `n_skills_competence` + `n_skills_knowledge` + `n_skills_sin_tipo` conforman el total `n_skills_essential`.\n\n**¿Para qué ayuda a determinar?** Confirma **redundancia estructural**. Si se usan varias de estas variables juntas, se estaría contando la misma información. Es importante elegir una representación adecuada.\n\n**Hallazgos preliminares:** Existe redundancia entre los contadores. `Skill_competence` y `Skill_Knowledge` son componentes del total exigido por el oficio.')

# 9. CALIDAD
md('## 7. Calidad de datos\n\n**¿Qué vamos a analizar?** Cobertura ESCO, filas sin grupo ocupacional, pluriempleo y unificación entre `Isco_group` e `ISCO_group`.\n\n**¿Por qué es relevante?** Define el universo analizable y las limitaciones del estudio.')
code('''print("="*55)
print("COBERTURA ESCO - saber_skills")
print("="*55)
print(df["saber_skills"].value_counts(dropna=False))
print()

print("="*55)
print("FILAS SIN GRUPO OCUPACIONAL")
print("="*55)
print("Filas sin isco_group_label:", df["isco_group_label"].isna().sum())
print("Filas con SIN_GRUPO en Isco_group_unif:", (df["Isco_group_unif"]=="SIN_GRUPO").sum())
print()

print("="*55)
print("PLURIEMPLEO")
print("="*55)
print("Personas únicas (resume_id):", f"{df['resume_id'].nunique():,}")
print("Total de filas (experiencias):", f"{len(df):,}")
print("Diferencia (filas - personas):", f"{len(df) - df['resume_id'].nunique():,}")
print()

print("="*55)
print("UNIFICACIÓN Isco_group / ISCO_group")
print("="*55)
print("isco_group (código) únicos:", df["isco_group"].nunique())
print("isco_group_label únicos:", df["isco_group_label"].nunique())
print("Isco_group_unif únicos:", df["Isco_group_unif"].nunique())
print()
print("Conclusión: Se utiliza isco_group_label como base unificada por legibilidad.")
''')
md('**¿Qué muestra este análisis?** Indicadores clave de calidad del dataset.\n\n**¿Qué patrón o comportamiento evidencia?** Mayoría con oficio clasificado por ESCO (`ok`). Existen filas sin grupo ocupacional y con `no_clasificado`. Hay pluriempleo (más experiencias que personas). `isco_group` e `isco_group_label` son redundantes entre sí.\n\n**¿Para qué ayuda a determinar?** Define el universo analizable para el cruce por grupo ocupacional. Las competencias son válidas fundamentalmente cuando existe clasificación por oficio. Debe tenerse en cuenta el grano (experiencia vs persona).\n\n**Hallazgos preliminares:** Buena cobertura mayoritaria por ESCO. Se confirma la unificación con `isco_group_label`. Pluriempleo y ausencias deben declararse como limitaciones.')

# 10. HALLAZGOS
md('## 8. Hallazgos, conclusiones y recomendaciones\n\n### Hallazgos clave\n\n1. **Grano correcto:** 1 fila = 1 experiencia laboral, no 1 persona. Hay más experiencias que personas únicas, lo que evidencia trayectorias con múltiples empleos.\n\n2. **Columnas objetivo:** Todas las columnas solicitadas fueron identificadas/mapeadas. `Period_Time` fue creada correctamente desde `start_date - end_date`.\n\n3. **Unificación:** `Isco_group` e `ISCO_group` son equivalentes. Se utiliza `isco_group_label` como base unificada por mayor legibilidad.\n\n4. **Nivel educativo:** Predomina `Secondary school` y `Bachelor`. Los valores ausentes se normalizaron explícitamente a `No reportado`, siguiendo `docs/EDA.md`.\n\n5. **Cruce educación x grupo ocupacional:** Al normalizar **por grupo ocupacional** (100% por barra), se observa variación entre grupos. Oficios operativos muestran mayor peso de `Secundaria`, mientras que grupos administrativos/profesionales mayor peso de `Pregrado/Maestría`. **Solo asociación/composición, sin causalidad.**\n\n6. **Competencias (clave):** `Skill_competence` y `Skill_Knowledge` son **requerimientos del oficio según ESCO**, **NO** competencias que posee la persona. Existen diferencias entre grupos ocupacionales en su perfil de exigencia. Hay redundancia estructural con `n_skills_essential`.\n\n7. **Calidad:** Mayoría con oficio clasificado por ESCO. Existen casos `no_clasificado` y pluriempleo que deben tenerse en cuenta.\n\n### ¿Qué respuestas se obtienen a las columnas objetivo?\n\n- Se mapearon correctamente todas las columnas solicitadas.\n- Se creó `Period_Time` y se aplicó el tratamiento a `University_Level`.\n- Se unificaron `Isco_group`/`ISCO_group`.\n- Se analizó la distribución por grupo ocupacional y el cruce con nivel educativo (normalizado por grupo).\n- Se caracterizó `Skill_competence` y `Skill_Knowledge` dejando claro que son **requerimientos del oficio**, no del individuo.\n\n### ¿Qué ayuda a determinar para cumplir el objetivo de la entrega?\n\nEste notebook entrega un EDA descriptivo, trazable, reproducible y enfocado exclusivamente a las columnas objetivo. Cada gráfico incluye su explicación. Se respeta el grano (experiencia vs persona), se aplica normalización correcta en el cruce, se aclara la naturaleza de las competencias y se siguen las reglas de honestidad visual del proyecto.\n\n### Limitaciones\n\n- **Grano:** Análisis por **experiencia laboral**, no por persona.\n- **Competencias:** Son **requerimientos del oficio (ESCO)**, no competencias poseídas por el individuo.\n- **Causalidad:** Solo se describen asociaciones/composiciones, no relaciones causales.\n- **Ausencias:** Presencia de `No reportado` y filas `no_clasificado`.\n- **Pluriempleo:** Conservado en el dataset.\n- **Alcance geográfico:** Flandes, Bélgica.\n\n### Recomendaciones\n\n- Para análisis a nivel persona, considerar agregación/deduplicación por `resume_id` respetando la trayectoria.\n- En cruces ocupación-nivel educativo, usar siempre normalización **por grupo ocupacional**.\n- Tratar `Skill_competence`/`Skill_Knowledge` como atributos del oficio.\n- Tener en cuenta las filas `no_clasificado` al filtrar por grupo ocupacional.\n- Mantener el enfoque descriptivo, fuera de alcance de modelado/predicción en esta entrega.')

# 11. REPRODUCIBILIDAD
md('## 9. Reproducibilidad\n\n'
   '- **Dataset:** `data/03_processed/empleos_limpio_con_competencias .csv` (codificación **UTF-8**)\n'
   '- **Sesión scientific-eda:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`\n'
   '- **Journal (append-only):** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/journal.md`\n'
   '- **Librerías:** Todas importadas en la **primera celda de código**\n'
   '- **Scripts (PEP723 + `uv run`):**\n'
   '  - `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/inspeccion_columnas_objetivo.py`\n'
   '  - `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/generar_figuras_columnas_objetivo.py`\n'
   '- **Figuras:** `.webp` en `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/plots/`\n\n'
   '```bash\n'
   'cd C:\\Users\\ASUS\\Documents\\MINERIA2\n'
   'uv run analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/inspeccion_columnas_objetivo.py\n'
   'uv run analysis/2026-10-25T16-00-00-eda-columnas-objetivo/scripts/generar_figuras_columnas_objetivo.py\n'
   '```')

out = Path('notebooks/EDA_Columnas_Objetivo.ipynb')
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('Notebook regenerado correctamente:', out)
print('Sin caracteres corruptos, con todas las librerías en la primera celda, usando el dataset correcto y con explicación en cada gráfico.')
