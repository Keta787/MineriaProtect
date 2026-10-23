# SOLID aplicado al refactor

Este documento explica cómo se organizó `notebooks/refactor/` y por qué.
No describe el dataset: para eso está `2.0_seleccion_dataset.ipynb` y, más
adelante, `5.0_EDA.ipynb`.

## Idea de fondo

Los cuadernos **orquestan**; el paquete `lib/` **calcula**. Un cuaderno no
debería contener lógica de negocio (parsear trimestres, decidir una bandera,
calcular límites de Tukey) porque esa lógica se repite, se desactualiza y no se
puede probar. En `lib/` cada regla vive una sola vez.

Reglas del paquete:

1. **Ninguna función imprime.** Devuelve datos; el cuaderno decide cómo mostrarlos.
2. **Ninguna función escribe archivos.** Los CSV son de solo lectura.
3. **Ninguna función adivina.** Si falta un dato obligatorio, lanza excepción.
4. **Las validaciones fallan fuerte.** Un `assert` que se cae es mejor que una cifra falsa en el informe.

## Estructura

```
notebooks/refactor/
├── SOLID.md                  # este documento
├── lib/
│   ├── config.py             # rutas y fuentes
│   ├── columnas.py           # diccionario de las 23 columnas
│   ├── carga.py              # lectura e inventario
│   ├── periodo.py            # Period_Time, ordinales, duración
│   ├── competencias.py       # banderas ESCO y validaciones
│   └── calidad.py            # vacíos, duplicados, outliers
├── 2.0_seleccion_dataset.ipynb
├── 3.0_preprocesamiento.ipynb
├── 4.0_transformacion.ipynb
├── 4.3_PCA.ipynb
└── 5.0_EDA.ipynb
```

## Los cinco principios, con ejemplos reales

| Principio | Cómo se aplica aquí | Ejemplo concreto |
|---|---|---|
| **S** · Responsabilidad única | Un módulo por pregunta. Cambiar la regla de banderas no toca el parseo de fechas. | `periodo.py` solo entiende `start_date`/`end_date`; `competencias.py` solo banderas. |
| **O** · Abierto/cerrado | Agregar una métrica no obliga a editar las existentes. | `calidad.resumen_outliers()` recibe una lista de columnas; sumar `veces_ese_oficio` no cambia la función. |
| **L** · Sustitución de Liskov | Las dos fuentes (`con_outliers`, `sin_outliers`) son intercambiables. | `carga.leer(fuente)` funciona con cualquiera de las dos sin ramas `if`. |
| **I** · Segregación de interfaces | Funciones pequeñas en vez de una clase con veinte métodos. | `crear_period_time`, `duracion_observada` y `duracion_a_corte` se usan por separado. |
| **D** · Inversión de dependencias | El cuaderno depende de funciones con nombre, no de pandas suelto. | El cuaderno llama `periodo.validar(df)`, no reimplementa el regex. |

## Por qué `config.Fuente` es un dato y no una ruta suelta

Una ruta suelta obliga a repetir el criterio en cada cuaderno. `Fuente` lleva
nombre, ruta y criterio en un solo objeto; si mañana cambia el archivo, se
cambia una vez y los cinco cuadernos siguen funcionando.

## Riesgos identificados y mitigaciones

Esta sección responde a un riesgo real detectado al auditar el dataset: la
instrucción original pedía marcar como "Sin Clasificar" toda lista vacía. Eso
produce **59.155** filas marcadas cuando la verdad es **26.186**.

| # | Riesgo | Qué lo provoca | Mitigación implementada |
|---|---|---|---|
| 1 | **Falso positivo "sin clasificar"** | Derivar la bandera del vacío de `skills`/`knowledge` | La bandera se deriva de `saber_skills` (`competencias.sin_oficio`); `validar()` lo impone |
| 2 | Bandera binaria ambigua | Un `False` no distingue "no exige" de "no aplica" | Dos banderas de **tres valores**, con `sin_clasificar` explícito |
| 3 | Doble conteo en el informe | Sumar 26.186 + 32.967 como si fueran lo mismo | `cruce_banderas()` muestra que son hechos distintos; van en secciones distintas |
| 4 | Fuga temporal | Usar `Period_Time` como predictor | Solo se usa para EDA y para calcular duración; nunca entra a `X` |
| 5 | Borrado silencioso de outliers | Confundir "ocultar" con "eliminar" | `calidad.ocultar()` recorta solo la serie que se grafica; el DataFrame no cambia |
| 6 | Instrucción ambigua del `.txt` | Nombra `skill_knowledge` / `skill_competence`, que no existen como tales | El diccionario (`columnas.py`) declara los nombres reales y su rol |

### Cómo se comprueba

- `competencias.validar()` corre en `3.0` y se cae si las banderas mienten.
- `competencias.auditar_falso_positivo()` imprime los tres conteos (correcto, ingenuo, falsos positivos) para que la diferencia quede a la vista.
- `competencias.validar_contadores()` comprueba que cada contador sea el largo de su lista.

## Cómo ejecutar

Desde `notebooks/refactor/`:

```bash
jupyter nbconvert --to notebook --execute --inplace 2.0_seleccion_dataset.ipynb
```

O abrir el cuaderno con Jupyter y ejecutar todas las celdas. No requiere
dependencias nuevas: pandas, numpy, matplotlib y scikit-learn ya están en
`requirements.txt`.
