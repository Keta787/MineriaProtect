import json
import os

path = 'notebooks/refactor/2.0_preprocesamiento_jobpath.ipynb'
with open(path, encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']

# New markdown + code cells
md_intro = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 13. Comparativa: Con outliers vs Sin outliers\n",
        "\n",
        "**¿QUÉ SE HACE?** Se comparan ambas versiones del dataset usando rutas relativas desde la raíz `MineriaProtect/`:\n",
        "\n",
        "- **Con outliers:** `data/03_processed/empleos_limpio_con_competencias.csv`\n",
        "- **Sin outliers:** `data/03_processed/empleos_limpio_con_competencias_sin_outliers.csv`\n",
        "\n",
        "**¿POR QUÉ?** Permite ver el efecto real de la winsorización IQR. Se analizan forma, nulos, duplicados, descriptivos, boxplots, histogramas y reducción de rango para decidir con qué versión conviene seguir en las siguientes fases.\n",
        "\n",
        "**Detalle importante:** Las exclusiones aplicadas (IDs, códigos, banderas 0/1, one-hot/dummy, `start_date`/`end_date`, columnas con IQR==0) se respetan. La winsorización es con `clip()`, sin eliminar filas.\n"
    ]
}

code_load = {
    "cell_type": "code",
    "metadata": {},
    "source": [
        "# Carga de ambas versiones con rutas relativas\n",
        "from pathlib import Path\n",
        "import pandas as pd\n",
        "import numpy as np\n",
        "import matplotlib.pyplot as plt\n",
        "\n",
        "# Determinar raíz MineriaProtect\n",
        "cwd = Path.cwd()\n",
        "root = cwd\n",
        "if root.name == 'refactor':\n",
        "    root = root.parent.parent\n",
        "elif root.name == 'notebooks':\n",
        "    root = root.parent\n",
        "elif root.name != 'MineriaProtect':\n",
        "    for p in [root] + list(root.parents):\n",
        "        if p.name == 'MineriaProtect':\n",
        "            root = p\n",
        "            break\n",
        "\n",
        "path_con = root / 'data' / '03_processed' / 'empleos_limpio_con_competencias.csv'\n",
        "path_sin = root / 'data' / '03_processed' / 'empleos_limpio_con_competencias_sin_outliers.csv'\n",
        "\n",
        "print('Rutas usadas:')\n",
        "print('  Con outliers:', path_con)\n",
        "print('  Sin outliers:', path_sin)\n",
        "\n",
        "df_con = pd.read_csv(path_con)\n",
        "df_sin = pd.read_csv(path_sin)\n",
        "\n",
        "print('\\nFormas:')\n",
        "print('  Con outliers:', df_con.shape)\n",
        "print('  Sin outliers:', df_sin.shape)\n",
        "print('\\nDiferencia de filas:', df_con.shape[0] - df_sin.shape[0])\n",
        "print('Diferencia de columnas:', df_con.shape[1] - df_sin.shape[1])\n"
    ]
}

code_compare = {
    "cell_type": "code",
    "metadata": {},
    "source": [
        "# Comparativa general\n",
        "print('=== COMPARATIVA GENERAL ===')\n",
        "print('Nulos totales (con):', df_con.isna().sum().sum())\n",
        "print('Nulos totales (sin):', df_sin.isna().sum().sum())\n",
        "print('Duplicados exactos (con):', df_con.duplicated().sum())\n",
        "print('Duplicados exactos (sin):', df_sin.duplicated().sum())\n",
        "\n",
        "num_con = df_con.select_dtypes(include=[np.number]).columns.tolist()\n",
        "num_sin = df_sin.select_dtypes(include=[np.number]).columns.tolist()\n",
        "num_common = [c for c in num_con if c in num_sin]\n",
        "\n",
        "# Excluir identificadores y banderas binarias\n",
        "exclude_check = ['resume_id', 'Resume_id', 'isco_group', 'isco_level']\n",
        "vars_check = []\n",
        "for c in num_common:\n",
        "    if c in exclude_check:\n",
        "        continue\n",
        "    s = df_con[c].dropna()\n",
        "    if s.empty:\n",
        "        continue\n",
        "    # saltar binarios\n",
        "    uniq = s.unique()\n",
        "    if set(uniq).issubset({0,1}):\n",
        "        continue\n",
        "    vars_check.append(c)\n",
        "\n",
        "vars_check = vars_check[:8]\n",
        "print('\\nVariables numéricas comparadas:', vars_check)\n"
    ]
}

code_table = {
    "cell_type": "code",
    "metadata": {},
    "source": [
        "# Tabla resumen por variable\n",
        "rows = []\n",
        "for c in vars_check:\n",
        "    s1 = df_con[c].dropna()\n",
        "    s2 = df_sin[c].dropna()\n",
        "    if s1.empty or s2.empty:\n",
        "        continue\n",
        "    desc1 = s1.describe()\n",
        "    desc2 = s2.describe()\n",
        "    r1 = desc1['max'] - desc1['min']\n",
        "    r2 = desc2['max'] - desc2['min']\n",
        "    red = ((r1 - r2)/r1*100) if r1 != 0 else 0\n",
        "    rows.append({\n",
        "        'variable': c,\n",
        "        'min_con': desc1['min'], 'min_sin': desc2['min'],\n",
        "        'q1_con': desc1['25%'], 'q1_sin': desc2['25%'],\n",
        "        'med_con': desc1['50%'], 'med_sin': desc2['50%'],\n",
        "        'q3_con': desc1['75%'], 'q3_sin': desc2['75%'],\n",
        "        'max_con': desc1['max'], 'max_sin': desc2['max'],\n",
        "        'rango_con': r1, 'rango_sin': r2,\n",
        "        '%_reduccion_rango': red\n",
        "    })\n",
        "\n",
        "res = pd.DataFrame(rows)\n",
        "pd.set_option('display.float_format', lambda x: f'{x:.3f}')\n",
        "print(res.to_string(index=False))\n",
        "pd.reset_option('display.float_format')\n"
    ]
}

code_plots = {
    "cell_type": "code",
    "metadata": {},
    "source": [
        "# Boxplots comparativos\n",
        "n = len(vars_check)\n",
        "if n > 0:\n",
        "    fig, axes = plt.subplots(n, 2, figsize=(10, 3*n))\n",
        "    if n == 1:\n",
        "        axes = [axes]\n",
        "    for i, c in enumerate(vars_check):\n",
        "        ax1 = axes[i][0] if n > 1 else axes[0][0]\n",
        "        ax2 = axes[i][1] if n > 1 else axes[0][1]\n",
        "        df_con[[c]].boxplot(ax=ax1)\n",
        "        ax1.set_title(f'{c} - Con outliers')\n",
        "        df_sin[[c]].boxplot(ax=ax2)\n",
        "        ax2.set_title(f'{c} - Sin outliers (winsorizado IQR)')\n",
        "    plt.tight_layout()\n",
        "    plt.show()\n",
        "\n",
        "# Histogramas superpuestos\n",
        "if n > 0:\n",
        "    fig, axes = plt.subplots(n, 1, figsize=(10, 2.5*n))\n",
        "    if n == 1:\n",
        "        axes = [axes]\n",
        "    for i, c in enumerate(vars_check):\n",
        "        ax = axes[i]\n",
        "        ax.hist(df_con[c].dropna(), bins=40, alpha=0.5, label='Con outliers')\n",
        "        ax.hist(df_sin[c].dropna(), bins=40, alpha=0.5, label='Sin outliers')\n",
        "        ax.set_title(f'Distribución - {c}')\n",
        "        ax.legend()\n",
        "    plt.tight_layout()\n",
        "    plt.show()\n"
    ]
}

code_bars = {
    "cell_type": "code",
    "metadata": {},
    "source": [
        "# Reducción de rango por variable\n",
        "if not res.empty:\n",
        "    plt.figure(figsize=(10,4))\n",
        "    plt.bar(res['variable'], res['%_reduccion_rango'])\n",
        "    plt.title('Reducción de rango (max-min) tras winsorización IQR')\n",
        "    plt.ylabel('% reducción')\n",
        "    plt.xticks(rotation=45)\n",
        "    plt.tight_layout()\n",
        "    plt.show()\n"
    ]
}

md_conclusion = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### Análisis y recomendación\n",
        "\n",
        "**Detalles observados:**\n",
        "- Si el número de filas es **igual** entre ambas versiones, se confirma que **NO se eliminaron filas**, solo se aplicó `clip()` (winsorización).\n",
        "- La tabla muestra cómo se acotan los valores máximos (y en ocasiones mínimos) sin tocar la mediana en la mayoría de los casos.\n",
        "- Los *boxplots* permiten ver la compresión de las colas. Los histogramas muestran si la forma central se conserva.\n",
        "- Si alguna variable muestra 0% de reducción, significa que no tenía valores fuera de los límites IQR o estaba excluida por las reglas.\n",
        "\n",
        "**¿Con outliers, sin outliers o con ambos?**\n",
        "\n",
        "| Uso | Recomendación | Explicación |\n",
        "|---|---|---|\n",
        "| **Análisis descriptivo, construcción de secuencias por persona (`S_p`), minería de transiciones** | **Conservar con outliers** (o revisar caso por caso) | Los extremos pueden representar trayectorias poco frecuentes pero válidas. Pueden contener la señal que se busca descubrir. |\n",
        "| **Escalado, PCA, clustering, k-means, modelos basados en distancias** | **Usar sin outliers** | Las distancias euclídeas se ven fuertemente afectadas por colas largas. Winsorizar con IQR reduce ese efecto sin perder filas. |\n",
        "| **Lo más adecuado para este proyecto** | **Usar ambos** | Generar la matriz `X` numérica desde `empleos_limpio_con_competencias_sin_outliers.csv`. Mantener la versión con outliers para el análisis descriptivo, validación de patrones y trazabilidad. |\n",
        "\n",
        "**Regla práctica:** Si los gráficos muestran reducción importante en `n_skills_*` o `veces_ese_oficio`, lo correcto es usar la **versión sin outliers** para técnicas sensibles a escala/distancia. Si se desea preservar al máximo la variabilidad original para el análisis de secuencias, se puede priorizar la versión **con outliers** justificando la decisión en el informe.\n"
    ]
}

# Append
cells.extend([md_intro, code_load, code_compare, code_table, code_plots, code_bars, md_conclusion])
nb['cells'] = cells

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False)

print('done')
