import json
from pathlib import Path

nb_path = Path('notebooks/EDA_Columnas_Objetivo.ipynb')
with open(nb_path, 'r', encoding='utf-8', errors='ignore') as f:
    nb = json.load(f)

replacements = {
    '�': 'í',
    'Maestria': 'Maestría',
    'nicas': 'únicas',
    'unicas': 'únicas',
    'Correlacion': 'Correlación',
    'Composicion': 'Composición',
    'Librerias': 'Librerías',
    'segun': 'según',
    'vacio': 'vacío',
    'Composicion %': 'Composición %',
}

for cell in nb['cells']:
    if 'source' in cell:
        new_src = []
        for line in cell['source']:
            for old, new in replacements.items():
                if old in line:
                    line = line.replace(old, new)
            new_src.append(line)
        cell['source'] = new_src

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print('Done')
