import sys
sys.path.insert(0,'notebooks/refactor')
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from lib import categorias

df = pd.read_csv('data/03_processed/empleos_limpio_con_competencias .csv')
df['y'] = (df['veces_ese_oficio'] >= 2).astype(int)
df['isco_mayor'] = categorias.isco_mayor(df)
X = pd.get_dummies(df[['isco_mayor']], columns=['isco_mayor'])
y = df['y']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

col5 = X_train.columns.get_loc('isco_mayor_5')
mask_left = X_train.iloc[:, col5] <= 0.5
mask_right = X_train.iloc[:, col5] > 0.5
print('Pregunta 1: isco_mayor_5 <= 0.50')
print('Left (<=0.5, no group 5):', mask_left.sum(), 'tasa reinc:', y_train[mask_left].mean())
print('Right (>0.5, yes group 5):', mask_right.sum(), 'tasa reinc:', y_train[mask_right].mean())

# Go down left branch further
# Question 2 on left: isco_mayor_3 <= 0.50
Xl = X_train[mask_left]
yl = y_train[mask_left]
col3 = Xl.columns.get_loc('isco_mayor_3')
m2_left = Xl.iloc[:, col3] <= 0.5  # no group 3
m2_right = Xl.iloc[:, col3] > 0.5 # yes group 3
print('\nPregunta 2 (rama izquierda): isco_mayor_3 <= 0.50')
print('Izq:', m2_left.sum(), 'tasa:', yl[m2_left].mean())
print('Der:', m2_right.sum(), 'tasa:', yl[m2_right].mean())
