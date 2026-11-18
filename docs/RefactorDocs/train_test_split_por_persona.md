# Train / test por persona en JobPath

## Que se hizo

Los conjuntos `train` y `test` se construyeron con `GroupShuffleSplit` usando `resume_id` como grupo. Eso significa:

- el conjunto de prueba contiene **personas completas**, no filas aisladas;
- ninguna persona aparece en ambos conjuntos;
- el 20 % de personas se reserva para test y el 80 % para train;
- la semilla aleatoria es fija (`random_state = 42`);
- los escaladores, encoders y discretizadores se ajustan solo en train y despues transforman test.

## Por que se hace asi

Una persona tiene varias experiencias laborales. Si se divide por fila, empleos de la misma persona quedarian en train y test. Eso fuga informacion y hace que el resultado se vea mejor de lo que realmente es.

Por ejemplo, el nivel educativo, la trayectoria y los oficios de una persona se repetirian en ambos lados. El split por persona prueba si la preparacion del dato y los patrones encontrados se mantienen cuando aparecen personas nuevas.

## Como se verifica

- `shared_persons = 0`.
- `resume_id` no entra como feature en `X`.
- Las columnas de `X_train` y `X_test` son identicas.
- `mean/std/min/max` de las columnas escaladas se imprimen para train y se comparan con test.
- La prevalencia de `reincide` se reporta por conjunto para detectar desbalances visibles.

## Cuando no hace falta

En este proyecto la validacion formal acostumbra a usar este split para estabilidad. Pero la mineria es unsupervised, por lo que el objetivo principal sigue siendo descubrir patrones en todo el universo. El split es una salvaguarda metodologica, no un requisito del negocio.

## Conexion con el notebook

Ver `notebooks/refactor/3.0_transformacion.ipynb`, secciones 9 y 10: split por persona, validacion y exportacion de `X_train`, `X_test` por version.
PY