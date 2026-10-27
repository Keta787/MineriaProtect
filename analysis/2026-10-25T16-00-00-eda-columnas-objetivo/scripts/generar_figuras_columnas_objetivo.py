# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2.2.0",
#   "matplotlib>=3.8.0",
#   "numpy>=1.26.0",
#   "seaborn>=0.13.0",
# ]
# ///

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import seaborn as sns
import textwrap

# root
cwd = Path.cwd()
root = cwd
for _ in range(10):
    if (root / "data").exists():
        break
    root = root.parent

session = root / "analysis" / "2026-10-25T16-00-00-eda-columnas-objetivo"
plots = session / "plots"
plots.mkdir(parents=True, exist_ok=True)

data_path = root / "data" / "03_processed" / "empleos_con_competencias_limpio_sin_outliers.csv"
df = pd.read_csv(data_path, dtype=str, encoding="utf-8", keep_default_na=False, na_values=[""])

# Preparacion
df["Period_Time"] = df["start_date"].astype(str) + " - " + df["end_date"].astype(str)

# University_Level normalizar
CANON_UNIV = ["No reportado", "Secondary school", "Bachelor", "Master", "PhD"]
df["University_Level_norm"] = df["university_level"].copy()
df.loc[df["University_Level_norm"].isna(), "University_Level_norm"] = "No reportado"
df.loc[df["University_Level_norm"].astype(str).str.strip() == "", "University_Level_norm"] = "No reportado"
df["University_Level_norm"] = df["University_Level_norm"].fillna("No reportado")

# Isco group unificado
df["Isco_group_unif"] = df["isco_group_label"].fillna("SIN_GRUPO")

# Guardar csv preparado para notebook
prep = session / "empleos_preparado_columnas_objetivo.csv"
df.to_csv(prep, index=False)
print("PREP:", prep, df.shape)

# 1) University_Level
fig, ax = plt.subplots(figsize=(8,5))
vc = df["University_Level_norm"].value_counts().reindex(CANON_UNIV, fill_value=0)
vc.plot(kind="bar", ax=ax, color=["#9e9e9e","#f4a259","#5b8db8","#35754f","#7a2626"])
ax.set_title("Distribución de University_Level (normalizado)")
ax.set_ylabel("Frecuencia")
ax.set_xlabel("Nivel educativo")
plt.xticks(rotation=45)
plt.tight_layout()
fig.savefig(plots / "01_univariado_university_level.webp", format="webp")
plt.close()

# 2) Isco_group_top15
fig, ax = plt.subplots(figsize=(10,6))
top15 = df["Isco_group_unif"].value_counts().head(15)
top15.plot(kind="barh", ax=ax)
ax.set_title("Top 15 Grupos Ocupacionales (isco_group_label)")
ax.set_xlabel("Frecuencia")
plt.tight_layout()
fig.savefig(plots / "02_univariado_isco_top15.webp", format="webp")
plt.close()

# 3) Skill_competence
fig, ax = plt.subplots(figsize=(8,5))
df["n_skills_competence_num"] = pd.to_numeric(df["n_skills_competence"], errors="coerce")
df["n_skills_competence_num"].dropna().plot(kind="hist", bins=30, ax=ax, alpha=0.7)
ax.set_title("Distribución de Skill_competence (n_skills_competence) - Requerido por oficio")
ax.set_xlabel("Nº competencias tipo competence")
plt.tight_layout()
fig.savefig(plots / "03_univariado_skill_competence_hist.webp", format="webp")
plt.close()

# 4) Skill_knowledge
fig, ax = plt.subplots(figsize=(8,5))
df["n_skills_knowledge_num"] = pd.to_numeric(df["n_skills_knowledge"], errors="coerce")
df["n_skills_knowledge_num"].dropna().plot(kind="hist", bins=30, ax=ax, alpha=0.7)
ax.set_title("Distribución de Skill_Knowledge (n_skills_knowledge) - Requerido por oficio")
ax.set_xlabel("Nº competencias tipo knowledge")
plt.tight_layout()
fig.savefig(plots / "04_univariado_skill_knowledge_hist.webp", format="webp")
plt.close()

# 5) Period_Time top20
fig, ax = plt.subplots(figsize=(10,6))
df["Period_Time"].value_counts().head(20).plot(kind="bar", ax=ax)
ax.set_title("Top 20 Period_Time (start_date - end_date)")
ax.set_ylabel("Frecuencia")
plt.xticks(rotation=90)
plt.tight_layout()
fig.savefig(plots / "05_univariado_period_time_top20.webp", format="webp")
plt.close()

# 6) Resume_id unicos vs filas
unique_resumes = df["resume_id"].nunique()
fig, ax = plt.subplots(figsize=(6,5))
ax.bar(["Filas (experiencias)", "Personas únicas (resume_id)"], [len(df), unique_resumes])
ax.set_title("Resume_id: experiencias vs personas únicas")
ax.set_ylabel("Conteo")
plt.tight_layout()
fig.savefig(plots / "06_univariado_resume_id.webp", format="webp")
plt.close()

# 7) Bivariado University_Level x Isco_group (apilado 100%, top12)
top12 = df["Isco_group_unif"].value_counts().head(12).index
sub = df[df["Isco_group_unif"].isin(top12)].copy()
ct = pd.crosstab(sub["Isco_group_unif"], sub["University_Level_norm"])
ct = ct.reindex(columns=CANON_UNIV, fill_value=0)
pct = ct.div(ct.sum(axis=1), axis=0)*100
pct = pct.loc[pct.sum(axis=1).sort_values(ascending=True).index]

NIVEL_ES = {"No reportado":"No reportado","Secondary school":"Secundaria","Bachelor":"Pregrado","Master":"Maestría","PhD":"Doctorado"}
pct_es = pct.rename(columns=NIVEL_ES)
colores = ["#C8C8C8","#E39A50","#5B8DB8","#35754F","#7A2626"]

fig, ax = plt.subplots(figsize=(14,9))
left = np.zeros(len(pct_es))
for col,c in zip(pct_es.columns, colores):
    ax.barh(pct_es.index, pct_es[col], left=left, color=c, label=col)
    left += pct_es[col].values
ax.set_xlim(0,100)
ax.set_title("University_Level x Isco_group (Top 12) - Composición % por grupo ocupacional")
ax.set_xlabel("% de empleos del grupo con ese nivel educativo")
ax.legend(title="Nivel educativo", bbox_to_anchor=(1.01,1), loc="upper left")
plt.tight_layout()
fig.savefig(plots / "07_bivariado_university_x_isco_stacked100.webp", format="webp")
plt.close()

# 8) Correlacion competencias
numc = df[["n_skills_competence_num","n_skills_knowledge_num"]].copy()
numc["n_skills_essential_num"] = pd.to_numeric(df["n_skills_essential"], errors="coerce")
corr = numc.corr()
fig, ax = plt.subplots(figsize=(6,5))
sns.heatmap(corr, annot=True, cmap="Blues", fmt=".2f", ax=ax)
ax.set_title("Correlación entre competencias requeridas por oficio")
plt.tight_layout()
fig.savefig(plots / "08_multivariado_correlacion_competencias.webp", format="webp")
plt.close()

print("DONE")
