import sys
sys.path.insert(0,'notebooks/refactor')
import pandas as pd
from sklearn.model_selection import train_test_split
from lib import categorias

df = pd.read_csv('data/03_processed/empleos_limpio_con_competencias .csv')
df['y'] = (df['veces_ese_oficio'] >= 2).astype(int)
df['isco_mayor'] = categorias.isco_mayor(df)
X = pd.get_dummies(df[['isco_mayor']], columns=['isco_mayor'])
y = df['y']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# Q1
mask_q1_left = X_train['isco_mayor_5'] <= 0.5  # no group 5
mask_q1_right = X_train['isco_mayor_5'] > 0.5  # yes group 5
print('Q1: ¿Pertenece al grupo ISCO 5 (Service and sales workers)? isco_mayor_5 <= 0.50 => NO')
print(f'Rama NO (izq): {mask_q1_left.sum()} clientes, tasa reinc={y_train[mask_q1_left].mean():.3f}')
print(f'Rama SÍ (der): {mask_q1_right.sum()} clientes, tasa reinc={y_train[mask_q1_right].mean():.3f}')

# Q2 follows left branch (no group 5)
X2 = X_train[mask_q1_left]
y2 = y_train[mask_q1_left]
mask_q2_left = X2['isco_mayor_3'] <= 0.5  # no group 3
mask_q2_right = X2['isco_mayor_3'] > 0.5 # yes group 3
print('\nQ2 (sigue rama NO grupo 5): ¿Pertenece al grupo ISCO 3? isco_mayor_3 <= 0.50 => NO')
print(f'Rama NO: {mask_q2_left.sum()} clientes, tasa reinc={y2[mask_q2_left].mean():.3f}')
print(f'Rama SÍ: {mask_q2_right.sum()} clientes, tasa reinc={y2[mask_q2_right].mean():.3f}')

# Q3 follows left of Q2
X3 = X2[mask_q2_left]
y3 = y2[mask_q2_left]
mask_q3_left = X3['isco_mayor_9'] <= 0.5
mask_q3_right = X3['isco_mayor_9'] > 0.5
print('\nQ3 (sigue NO5, NO3): ¿Pertenece al grupo ISCO 9? isco_mayor_9 <= 0.50 => NO')
print(f'Rama NO: {mask_q3_left.sum()} clientes, tasa reinc={y3[mask_q3_left].mean():.3f}')
print(f'Rama SÍ: {mask_q3_right.sum()} clientes, tasa reinc={y3[mask_q3_right].mean():.3f}')

# Q4 follows left of Q3
X4 = X3[mask_q3_left]
y4 = y3[mask_q3_left]
mask_q4_left = X4['isco_mayor_2'] <= 0.5
mask_q4_right = X4['isco_mayor_2'] > 0.5
print('\nQ4 (sigue NO5, NO3, NO9): ¿Pertenece al grupo ISCO 2? isco_mayor_2 <= 0.50 => NO')
print(f'Rama NO: {mask_q4_left.sum()} clientes, tasa reinc={y4[mask_q4_left].mean():.3f}')
print(f'Rama SÍ: {mask_q4_right.sum()} clientes, tasa reinc={y4[mask_q4_right].mean():.3f}')
