# Scripts ejecutables

Esta carpeta contiene los puntos de entrada que leen y escriben archivos del
proyecto. La lógica reutilizable permanece en `src/`.

## Pipeline de datos

Los pasos de limpieza y preparación están en
[`pipeline/limpieza/`](./pipeline/limpieza/):

```text
scripts/pipeline/limpieza/
├── limpiar_datos.py
├── integrar_empleos.py
├── generar_competencias.py
├── unificar_competencias_empleos.py
├── limpiar_empleos.py
├── limpiar_empleos_con_competencias.py
├── dividir_por_outliers.py
└── dividir_competencias_por_outliers.py
```

Se ejecutan desde la raíz del repositorio. Por ejemplo:

```powershell
python scripts/pipeline/limpieza/limpiar_datos.py
```

## Otros scripts

- [`arbol_reincidencia/`](./arbol_reincidencia/) contiene el entrenamiento de
  los modelos de reincidencia.
- [`notebook_tools/`](./notebook_tools/) contiene utilidades de mantenimiento
  para construir o reparar notebooks; no forma parte del pipeline de datos.

