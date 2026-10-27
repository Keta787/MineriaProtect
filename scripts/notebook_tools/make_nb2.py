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

md('# EDA enfocado a las columnas objetivo - JobPath\n\n**Proyecto:** JobPath (Minería de Datos - UNIMINUTO Ibagué, 2026-2)\n\n**Dataset:** `data/03_processed/empleos_limpio_con_competencias .csv`\n\n**Sesión scientific-eda:** `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`\n\n**Fecha:** 2026-10-25\n\n**Objetivo:** Realizar EDA descriptivo enfocado exclusivamente a las columnas objetivo solicitadas, con explicación de cada gráfico (qué muestra, qué patrón evidencia, para qué ayuda a determinar).\n\n**Encoding:** UTF-8')

md('## Índice\n\n1. [Importación de librerías](#1-importación-de-librerías)\n2. [Contexto y Metodología](#2-contexto-y-metodología)\n3. [Carga de datos y preparación](#3-carga-de-datos-y-preparación)\n4. [Análisis Univariado por columna objetivo](#4-análisis-univariado-por-columna-objetivo)\n5. [Análisis Bivariado](#5-análisis-bivariado)\n6. [Análisis Multivariado y Redundancia](#6-análisis-multivariado-y-redundancia)\n7. [Calidad de Datos](#7-calidad-de-datos)\n8. [Hallazgos, Conclusiones y Recomendaciones](#8-hallazgos-conclusiones-y-recomendaciones)\n9. [Reproducibilidad](#9-reproducibilidad)')

md('## 1. Importación de librerías\n\n**Todas las librerías necesarias se cargan en esta única celda.**')
code('''# === TODAS LAS LIBRERIAS ===
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

print("Librerias cargadas correctamente")
''')

md('## 2. Contexto y Metodología\n\n- Se sigue estrictamente la skill scientific-eda.\n- Contexto primero, documentado en journal.md (append-only).\n- Scripts con PEP723 + uv run, figuras .webp\n- Encoding: UTF-8\n- Competencias (Skill_competence / Skill_Knowledge): son requerimientos del oficio segun ESCO, NO competencias de la persona.\n\n### Mapeo columnas objetivo\n\n| Solicitada | Real | Notas |\n|---|---|---|\n| Resume_id | resume_id | 1 fila = 1 experiencia laboral (no 1 persona) |\n| Period_Time | start_date - end_date | Creada. Si end_date == "Present", se conserva "Present" |\n| University_Level | university_level | NaN/vacio -> "No reportado". Traduccion solo visual |\n| Isco_group | isco_group_label (prioritario) / isco_group | Unificados. Se usa isco_group_label por legibilidad |\n| Skill_competence | n_skills_competence | Requerimiento por oficio (ESCO) |\n| Skill_Knowledge | n_skills_knowledge | Requerimiento por oficio (ESCO) |\n| ISCO_group | isco_group_label / isco_group | Unificado con Isco_group |')

md('## 3. Carga de datos y preparación\n\n### ¿Qué vamos a hacer?\nCargar `empleos_limpio_con_competencias .csv` con encoding UTF-8, crear Period_Time, normalizar University_Level a No reportado, unificar Isco_group.\n\n### ¿Por qué es relevante?\nGarantiza trazabilidad y honestidad con los datos.')
code('''root = Path.cwd()
for p in [root] + list(root.parents):
    if (p / "data").exists():
        root = p
        break

data_path = root / "data" / "03_processed" / "empleos_limpio_con_competencias .csv"
print("Cargando:", data_path)
df = pd.read_csv(data_path, encoding='utf-8', dtype=str, keep_default_na=False, na_values=[""])
print("Shape:", df.shape)

df["Period_Time"] = df["start_date"].astype(str) + " - " + df["end_date"].astype(str)

CANON_UNIV = ["No reportado", "Secondary school", "Bachelor", "Master", "PhD"]
df["University_Level_norm"] = df["university_level"].copy()
df.loc[df["University_Level_norm"].isna(), "University_Level_norm"] = "No reportado"
df.loc[df["University_Level_norm"].astype(str).str.strip() == "", "University_Level_norm"] = "No reportado"
df["University_Level_norm"] = df["University_Level_norm"].fillna("No reportado")

df["Isco_group_unif"] = df["isco_group_label"].fillna("SIN_GRUPO")

df["n_skills_competence_num"] = pd.to_numeric(df["n_skills_competence"], errors="coerce")
df["n_skills_knowledge_num"] = pd.to_numeric(df["n_skills_knowledge"], errors="coerce")
df["n_skills_essential_num"] = pd.to_numeric(df["n_skills_essential"], errors="coerce")

print("Preparacion completada")
df.head()
''')

md('## 4. Análisis Univariado por columna objetivo')
md('### 4.1 Resume_id (identificador de persona)')
code('''unique_resumes = df["resume_id"].nunique()
fig, ax = plt.subplots(figsize=(6,5))
ax.bar(["Filas (experiencias)", "Personas unicas (resume_id)"], [len(df), unique_resumes], color=['#5b8db8','#35754f'])
ax.set_title("Resume_id: experiencias vs personas unicas")
ax.set_ylabel("Conteo")
plt.tight_layout()
plt.show()
print(len(df), unique_resumes)
''')
md('### 4.2 Period_Time')
code('''fig, ax = plt.subplots(figsize=(10,6))
df["Period_Time"].value_counts().head(20).plot(kind="bar", ax=ax, color='#5b8db8')
ax.set_title("Top 20 Period_Time (start_date - end_date)")
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()
''')
md('### 4.3 University_Level')
code('''fig, ax = plt.subplots(figsize=(8,5))
vc = df["University_Level_norm"].value_counts().reindex(CANON_UNIV, fill_value=0)
vc.plot(kind="bar", ax=ax, color=["#9e9e9e","#f4a259","#5b8db8","#35754f","#7a2626"])
ax.set_title("Distribucion de University_Level (normalizado)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
''')
md('### 4.4 Isco_group / ISCO_group (unificados)')
code('''fig, ax = plt.subplots(figsize=(10,6))
df["Isco_group_unif"].value_counts().head(15).plot(kind="barh", ax=ax, color='#5b8db8')
ax.set_title("Top 15 Grupos Ocupacionales (isco_group_label)")
plt.tight_layout()
plt.show()
''')
md('### 4.5 Skill_competence (n_skills_competence) - REQUERIDO POR OFICIO')
code('''fig, ax = plt.subplots(figsize=(8,5))
df["n_skills_competence_num"].dropna().plot(kind="hist", bins=30, ax=ax, alpha=0.7, color='#5b8db8')
ax.set_title("Skill_competence (requerido por oficio)")
plt.tight_layout()
plt.show()
''')
md('### 4.6 Skill_Knowledge (n_skills_knowledge) - REQUERIDO POR OFICIO')
code('''fig, ax = plt.subplots(figsize=(8,5))
df["n_skills_knowledge_num"].dropna().plot(kind="hist", bins=30, ax=ax, alpha=0.7, color='#35754f')
ax.set_title("Skill_Knowledge (requerido por oficio)")
plt.tight_layout()
plt.show()
''')

md('## 5. Análisis Bivariado')
md('### 5.1 University_Level x Isco_group (Barras apiladas 100% por grupo ocupacional)')
code('''NIVEL_ES = {"No reportado":"No reportado", "Secondary school":"Secundaria", "Bachelor":"Pregrado", "Master":"Maestria", "PhD":"Doctorado"}
colores = ["#C8C8C8","#E39A50","#5B8DB8","#35754F","#7A2626"]
top12 = df["Isco_group_unif"].value_counts().head(12).index
sub = df[df["Isco_group_unif"].isin(top12)].copy()
ct = pd.crosstab(sub["Isco_group_unif"], sub["University_Level_norm"])
ct = ct.reindex(columns=CANON_UNIV, fill_value=0)
pct = ct.div(ct.sum(axis=1), axis=0)*100
pct = pct.loc[pct.sum(axis=1).sort_values(ascending=True).index]
pct_es = pct.rename(columns=NIVEL_ES)
fig, ax = plt.subplots(figsize=(14,9))
left = np.zeros(len(pct_es))
for col,c in zip(pct_es.columns, colores):
    ax.barh(pct_es.index, pct_es[col], left=left, color=c, label=col)
    left += pct_es[col].values
ax.set_xlim(0,100)
ax.set_title("University_Level x Isco_group (Top 12) - Composicion % por grupo ocupacional")
ax.set_xlabel("% de empleos del grupo con ese nivel educativo")
ax.legend(title="Nivel educativo", bbox_to_anchor=(1.01,1), loc="upper left")
plt.tight_layout()
plt.show()
''')
md('### 5.2 Skill_competence x Isco_group / Skill_Knowledge x Isco_group')
code('''top12 = df["Isco_group_unif"].value_counts().head(12).index
sub = df[df["Isco_group_unif"].isin(top12)]
sub.groupby("Isco_group_unif")[["n_skills_competence_num","n_skills_knowledge_num"]].median().sort_values("n_skills_competence_num", ascending=False)
''')

md('## 6. Análisis Multivariado y Redundancia')
code('''numc = df[["n_skills_competence_num","n_skills_knowledge_num","n_skills_essential_num"]].copy()
corr = numc.corr()
fig, ax = plt.subplots(figsize=(6,5))
sns.heatmap(corr, annot=True, cmap="Blues", fmt=".2f", ax=ax)
ax.set_title("Correlacion entre competencias requeridas por oficio")
plt.tight_layout()
plt.show()
''')

md('## 7. Calidad de Datos')
code('''print(df["saber_skills"].value_counts(dropna=False))
print("Filas sin isco_group_label:", df["isco_group_label"].isna().sum())
print("Personas unicas:", df["resume_id"].nunique(), "| Filas:", len(df))
print("isco_group unicos:", df["isco_group"].nunique(), "| isco_group_label unicos:", df["isco_group_label"].nunique())
''')

md('## 8. Hallazgos, Conclusiones y Recomendaciones\n\n- 1 fila = 1 experiencia. Hay mas experiencias que personas unicas.\n- Se usa isco_group_label por legibilidad (duplicado con isco_group).\n- Period_Time creado. University_Level normalizado a No reportado.\n- Cruce por grupo ocupacional (100% por barra). Sin causalidad.\n- Skill_competence/Skill_Knowledge son requerimientos del oficio (ESCO), no de la persona.\n- Hay redundancia con n_skills_essential.\n- Mayoría cubierto por ESCO, hay no_clasificado y pluriempleo.')

md('## 9. Reproducibilidad\n\n- Dataset: `data/03_processed/empleos_limpio_con_competencias .csv` (UTF-8)\n- Todas las librerias en primera celda de codigo\n- Sesion: `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/`\n- Journal: `analysis/2026-10-25T16-00-00-eda-columnas-objetivo/journal.md`')

out = Path('notebooks/EDA_Columnas_Objetivo.ipynb')
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
print('OK')
