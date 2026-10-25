import sys
sys.path.insert(0,'notebooks/refactor')
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from lib import categorias

df = pd.read_csv('data/03_processed/empleos_limpio_con_competencias .csv')
df['y'] = (df['veces_ese_oficio'] >= 2).astype(int)
df['isco_mayor'] = categorias.isco_mayor(df)
X = pd.get_dummies(df[['isco_mayor']], columns=['isco_mayor'])
y = df['y']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

tasa_global = y_train.mean()
print('Tasa global train:', tasa_global)

# Mapeo
isco_map = {1:'Managers',2:'Professionals',3:'Technicians and associate professionals',4:'Clerical support workers',5:'Service and sales workers',6:'Skilled agricultural, forestry and fishery workers',7:'Craft and related trades workers',8:'Plant and machine operators and assemblers',9:'Elementary occupations'}

filas = []

# Q1
mask_q1_left = X_train['isco_mayor_5'] <= 0.5  # NO grupo 5
mask_q1_right = X_train['isco_mayor_5'] > 0.5 # SI grupo 5
filas.append({
    '#':1,
    'Pregunta': '¿Pertenece al grupo ISCO 5 (Service and sales workers)?',
    'Regla árbol (export_text)': 'isco_mayor_5 <= 0.50 => NO',
    'Rama': 'Izq = NO pertenece a ISCO 5 | Der = SÍ pertenece a ISCO 5',
    'Clientes (train)': int(mask_q1_left.sum()) if True else None,
    'Tasa reincidencia rama IZQ': f"{y_train[mask_q1_left].mean():.3f}",
    'Tasa reincidencia rama DER': f"{y_train[mask_q1_right].mean():.3f}",
    'Lift rama DER / global': f"{y_train[mask_q1_right].mean()/tasa_global:.3f}",
    'Ganancia/intuición': 'Mayor separación: grupo 5 eleva la tasa respecto al global'
})

# Q2
X2 = X_train[mask_q1_left]; y2 = y_train[mask_q1_left]
mask_q2_left = X2['isco_mayor_3'] <= 0.5
mask_q2_right = X2['isco_mayor_3'] > 0.5
filas.append({
    '#':2,
    'Pregunta': '¿Pertenece al grupo ISCO 3 (Technicians and associate professionals)? (sigue rama NO grupo 5)',
    'Regla árbol (export_text)': 'isco_mayor_3 <= 0.50 => NO',
    'Rama': 'Izq = NO pertenece a ISCO 3 | Der = SÍ pertenece a ISCO 3',
    'Clientes (train)': int(mask_q2_left.sum()),
    'Tasa reincidencia rama IZQ': f"{y2[mask_q2_left].mean():.3f}",
    'Tasa reincidencia rama DER': f"{y2[mask_q2_right].mean():.3f}",
    'Lift rama DER / global': f"{y2[mask_q2_right].mean()/tasa_global:.3f}",
    'Ganancia/intuición': 'Dentro de NO grupo 5, grupo 3 aumenta la tasa'
})

# Q3
X3 = X2[mask_q2_left]; y3 = y2[mask_q2_left]
mask_q3_left = X3['isco_mayor_9'] <= 0.5
mask_q3_right = X3['isco_mayor_9'] > 0.5
filas.append({
    '#':3,
    'Pregunta': '¿Pertenece al grupo ISCO 9 (Elementary occupations)? (sigue NO5, NO3)',
    'Regla árbol (export_text)': 'isco_mayor_9 <= 0.50 => NO',
    'Rama': 'Izq = NO pertenece a ISCO 9 | Der = SÍ pertenece a ISCO 9',
    'Clientes (train)': int(mask_q3_left.sum()),
    'Tasa reincidencia rama IZQ': f"{y3[mask_q3_left].mean():.3f}",
    'Tasa reincidencia rama DER': f"{y3[mask_q3_right].mean():.3f}",
    'Lift rama DER / global': f"{y3[mask_q3_right].mean()/tasa_global:.3f}",
    'Ganancia/intuición': 'Grupo 9 eleva la tasa en esta subpoblación'
})

# Q4
X4 = X3[mask_q3_left]; y4 = y3[mask_q3_left]
mask_q4_left = X4['isco_mayor_2'] <= 0.5
mask_q4_right = X4['isco_mayor_2'] > 0.5
filas.append({
    '#':4,
    'Pregunta': '¿Pertenece al grupo ISCO 2 (Professionals)? (sigue NO5, NO3, NO9)',
    'Regla árbol (export_text)': 'isco_mayor_2 <= 0.50 => NO',
    'Rama': 'Izq = NO pertenece a ISCO 2 | Der = SÍ pertenece a ISCO 2',
    'Clientes (train)': int(mask_q4_left.sum()),
    'Tasa reincidencia rama IZQ': f"{y4[mask_q4_left].mean():.3f}",
    'Tasa reincidencia rama DER': f"{y4[mask_q4_right].mean():.3f}",
    'Lift rama DER / global': f"{y4[mask_q4_right].mean()/tasa_global:.3f}",
    'Ganancia/intuición': 'Grupo 2 también muestra mayor propensión'
})

res = pd.DataFrame(filas)
res.to_csv('arbol_fuga_4preguntas_completo.csv', index=False)
print(res.to_string())
print('\n\nGuardado: arbol_fuga_4preguntas_completo.csv')
