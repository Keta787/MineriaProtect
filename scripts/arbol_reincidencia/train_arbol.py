from pathlib import Path
import sys
sys.path.insert(0, 'notebooks/refactor')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from lib import categorias

BASE = Path('.')
DATA = BASE / 'data' / '03_processed' / 'empleos_limpio_con_competencias .csv'
OUT_IMG = BASE / 'arbol_fuga.png'
OUT_TXT = BASE / 'arbol_fuga_export.txt'
OUT_CSV = BASE / 'arbol_fuga_comparacion_depth.csv'

print('Loading...')
df = pd.read_csv(DATA)
print('Shape:', df.shape)

df['y'] = (df['veces_ese_oficio'] >= 2).astype(int)
print(df['y'].value_counts(normalize=True))

df['isco_mayor'] = categorias.isco_mayor(df)
X = pd.get_dummies(df[['isco_mayor']], columns=['isco_mayor'])
y = df['y']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
print('Train:', X_train.shape, 'Test:', X_test.shape)

depths = [2,3,4,5,8,None]
res = []
for d in depths:
    clf = DecisionTreeClassifier(max_depth=d, random_state=42)
    clf.fit(X_train, y_train)
    res.append({
        'max_depth': str(d),
        'train_acc': clf.score(X_train,y_train),
        'test_acc': clf.score(X_test,y_test),
        'n_leaves': clf.get_n_leaves()
    })
res_df = pd.DataFrame(res)
print(res_df)
res_df.to_csv(OUT_CSV, index=False)

arbol = DecisionTreeClassifier(max_depth=4, random_state=42)
arbol.fit(X_train, y_train)
print('Depth4 train:', arbol.score(X_train,y_train), 'test:', arbol.score(X_test,y_test), 'leaves:', arbol.get_n_leaves())

plt.figure(figsize=(20,12))
plot_tree(arbol, feature_names=list(X.columns), class_names=['Primera vez','Reincide'], filled=True, rounded=True, proportion=True)
plt.tight_layout()
plt.savefig(OUT_IMG, dpi=150)
plt.close()
print('Saved', OUT_IMG)

txt = export_text(arbol, feature_names=list(X.columns))
with open(OUT_TXT, 'w', encoding='utf-8') as f:
    f.write(txt)
print('Saved', OUT_TXT)
print(txt[:800])
