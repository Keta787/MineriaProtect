import sys
sys.path.insert(0,'notebooks/refactor')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.dummy import DummyClassifier
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from lib import categorias

BASE = Path = __import__('pathlib').Path
BASE_DIR = BASE('.')
DATA = BASE_DIR / 'data' / '03_processed' / 'empleos_limpio_con_competencias .csv'
OUT_IMG = BASE_DIR / 'arbol_fuga_completo.png'
OUT_TXT = BASE_DIR / 'arbol_fuga_export_completo.txt'
OUT_CSV1 = BASE_DIR / 'arbol_fuga_comparacion_depth_completo.csv'
OUT_CSV2 = BASE_DIR / 'arbol_fuga_feature_importances.csv'
OUT_CSV3 = BASE_DIR / 'arbol_fuga_metricas.csv'
OUT_CSV4 = BASE_DIR / 'arbol_fuga_4preguntas.csv'

print('Loading...')
df = pd.read_csv(DATA)
df['y'] = (df['veces_ese_oficio'] >= 2).astype(int)
df['isco_mayor'] = categorias.isco_mayor(df)
X = pd.get_dummies(df[['isco_mayor']], columns=['isco_mayor'])
y = df['y']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# Baseline
dummy = DummyClassifier(strategy='most_frequent', random_state=42)
dummy.fit(X_train, y_train)
y_pred_dummy = dummy.predict(X_test)
print('=== BASELINE (most_frequent) ===')
print('Accuracy:', accuracy_score(y_test, y_pred_dummy))
print(confusion_matrix(y_test, y_pred_dummy))
print(classification_report(y_test, y_pred_dummy))

# Compare depths
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
res_df.to_csv(OUT_CSV1, index=False)
print(res_df)

# Train depth 4
arbol = DecisionTreeClassifier(max_depth=4, random_state=42)
arbol.fit(X_train, y_train)
y_pred_arbol = arbol.predict(X_test)
print('\n=== ARBOL max_depth=4 ===')
print('Train:', arbol.score(X_train,y_train), 'Test:', arbol.score(X_test,y_test), 'Leaves:', arbol.get_n_leaves())
print('Confusion matrix:')
print(confusion_matrix(y_test, y_pred_arbol))
print(classification_report(y_test, y_pred_arbol))

# Metrics
metricas = []
metricas.append({'modelo':'Baseline_most_frequent', 'accuracy': accuracy_score(y_test,y_pred_dummy)})
metricas.append({'modelo':'DecisionTree_max_depth4', 'accuracy': accuracy_score(y_test,y_pred_arbol)})
pd.DataFrame(metricas).to_csv(OUT_CSV3, index=False)

# Feature importances
imp = pd.DataFrame({'feature': X.columns, 'importance': arbol.feature_importances_}).sort_values('importance', ascending=False)
imp.to_csv(OUT_CSV2, index=False)
print(imp)

# Plot
plt.figure(figsize=(22,14))
plot_tree(arbol, feature_names=list(X.columns), class_names=['Primera vez','Reincide'], filled=True, rounded=True, proportion=True)
plt.tight_layout()
plt.savefig(OUT_IMG, dpi=150)
plt.close()
print('Saved', OUT_IMG)

# Export text
txt = export_text(arbol, feature_names=list(X.columns))
with open(OUT_TXT, 'w', encoding='utf-8') as f:
    f.write(txt)
print('Saved', OUT_TXT)
print(txt)
