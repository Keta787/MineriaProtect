# ESTÁNDAR DE CALIDAD Y BUENAS PRÁCTICAS DE CÓDIGO

## Propósito

Documento maestro de referencia para crear, revisar, corregir o refactorizar código de forma consistente. La calidad se evalúa por corrección, claridad, mantenibilidad y comportamiento, no por la cantidad de clases, funciones o patrones utilizados.

---

## Jerarquía de reglas

Aplicar las reglas en este orden; ante conflicto prevalece la de mayor prioridad:

1. Corrección funcional.
2. Preservación del comportamiento existente (ver **E2**).
3. Integridad y seguridad de los datos.
4. Claridad.
5. Mantenibilidad.
6. Estructura y modularidad.
7. Rendimiento.
8. Convenciones de estilo.

No aplicar una regla mecánicamente si produce código menos claro, menos correcto o más complejo. Cuando una excepción sea necesaria, indicarla explícitamente.

---

# A. Estructura y estilo

## A1. Nomenclatura

Seguir la convención idiomática del lenguaje utilizado. Para Python:

- Funciones, variables y módulos: `snake_case`
- Clases: `PascalCase`
- Constantes: `UPPER_SNAKE_CASE`

No mezclar convenciones dentro del mismo proyecto. No utilizar `camelCase` en Python salvo que exista una convención externa ya establecida que deba conservarse.

> **Excepción del proyecto (MineriaProtect):** en `libros/Diagnostico_Limpieza_Empleos.ipynb` se conservan nombres `camelCase` en español (`calcularDuracionTrimestres`, `contarGruposDuplicados`) por ser los nombres de las funciones requeridas por el entregable de la sesión 3. Es una excepción **explícita y documentada** de ese entregable; el código del proyecto (`script/`) sigue `snake_case`.

Los nombres deben ser descriptivos y representar su propósito. Evitar nombres ambiguos (`x`, `data2`, `temp`, `aux`, `obj`, `thing`) cuando exista una alternativa más clara.

## A2. Estructura del código

Organizar el código de forma lógica. Para módulos Python, preferir:

1. Imports
2. Constantes y configuración
3. Clases
4. Funciones auxiliares
5. Funciones principales
6. Punto de entrada, cuando exista

Mantener separadas las responsabilidades de: configuración, carga, transformación, validación, análisis y exportación. No colocar toda la lógica en una única función, bloque o celda (ver **D3** para notebooks).

## A3. Funciones: responsabilidad y complejidad

Cada función debe tener una responsabilidad principal claramente identificable. Puede realizar varias operaciones internas si todas forman parte de la misma responsabilidad; dividir cuando existan responsabilidades independientes, lógica excesivamente compleja o etapas que se entiendan mejor por separado.

- Ninguna función debería superar aproximadamente 100 líneas salvo justificación clara. El límite no es rígido: una función corta también requiere refactorización si su lógica es compleja.
- Revisar también: cantidad de condiciones, anidamiento, caminos de ejecución, dependencia de estado externo.
- Preferir, cuando corresponda: condiciones tempranas, retornos tempranos, funciones auxiliares y expresiones claras.
- No dividir artificialmente una función solo para cumplir un límite, ni alargarla para alcanzar un mínimo (ver **A7**).

Ejemplo de mala separación:

```python
hacer_todo()  # carga, limpia, calcula estadísticas, genera gráficos y exporta
```

Preferir responsabilidades separadas cuando realmente sean independientes: `cargar_datos()`, `limpiar_datos()`, `calcular_estadisticas()`, `generar_graficos()`, `exportar_resultados()`.

## A4. Clases

Utilizar clases cuando aporten valor real: estado que deba encapsularse, comportamiento asociado a una entidad, reutilización de una estructura coherente, configuración compartida o una responsabilidad que se beneficie del encapsulamiento.

No crear clases únicamente por regla de estilo o "usar POO". Si una solución con funciones y módulos es más clara, utilizarla (ver **A7**).

### A4.1 Métodos

Organizar los métodos lógicamente: constructor/inicialización, métodos públicos principales, métodos auxiliares internos y métodos de validación o soporte. Los métodos deben actuar sobre la responsabilidad de su clase. Evitar clases que solo agrupen funciones sin aportar estado, encapsulamiento o comportamiento relacionado.

## A5. SOLID

Aplicar cada principio solo cuando mejore la estructura real del sistema:

- **S — Single Responsibility:** una clase o función con una responsabilidad identificable.
- **O — Open/Closed:** evitar diseños que obliguen a modificar continuamente una pieza central cuando una extensión limpia sea posible.
- **L — Liskov Substitution:** con herencia, las clases derivadas deben respetar el comportamiento esperado de la base.
- **I — Interface Segregation:** evitar interfaces o abstracciones demasiado grandes para sus consumidores.
- **D — Dependency Inversion:** aplicarlo cuando reducir el acoplamiento aporte una ventaja real.

No introducir abstracciones, interfaces, patrones o capas solo para "cumplir SOLID" (ver **A7**). La simplicidad tiene prioridad cuando la complejidad adicional no aporta valor.

## A6. Abstracción y simplicidad

Regla general (aplicable a clases, funciones, interfaces, patrones y constantes): la abstracción debe mejorar el diseño, no ocultarlo ni demostrar técnica.

- Evitar duplicación de lógica cuando exista reutilización real, represente una responsabilidad independiente, mejore la legibilidad o reduzca complejidad.
- No crear abstracciones únicamente porque dos fragmentos se parecen superficialmente. Dos copias similares pueden ser aceptables; la tercera repetición justifica extraer.
- No dividir código artificialmente solo para aparentar modularidad.
- No convertir cada literal pequeño en una constante innecesaria.

Las secciones **A4**, **A5** y **A3** se rigen por esta regla.

## A7. Imports

Mantener los imports limpios y mínimos: no importar lo innecesario, evitar duplicados y `from modulo import *`, agruparlos de forma coherente y eliminar dependencias que ya no se usan. No agregar una biblioteca nueva cuando la funcionalidad ya pueda resolverse con las dependencias existentes.

## A8. Tipado

Utilizar type hints cuando mejoren la comprensión, la detección de errores, el contrato o la mantenibilidad. Priorizar las funciones públicas, reutilizables o con parámetros/retornos no evidentes.

```python
def cargar_datos(ruta: str) -> pd.DataFrame:
    ...
```

No añadir anotaciones artificiales únicamente por cumplir una regla.

## A9. Documentación del código

- Escribir *docstrings* breves en **español** para funciones y clases públicas o reutilizables: qué hace, qué recibe y qué devuelve; mencionar convenciones no obvias (p.ej. "duración inclusiva") y el motivo de decisiones relevantes.
- Los comentarios en línea se reservan para aclarar el **porqué** (limitaciones, decisiones, datos del negocio), no para repetir el **qué** ya visible en el código.
- La documentación de cada bloque debe explicar qué hace y **por qué existe** (criterio "Documentación" del curso); en pipelines de limpieza, registrar el antes/después y el criterio aplicado (bitácora o tabla de trazabilidad).

---

# B. Datos y procesamiento

## B1. Bucles, vectorización y procesamiento de datos

Un `for` dentro de otro `for` no está prohibido de forma absoluta, pero debe considerarse una señal para revisar la implementación. Antes de aceptarlo, evaluar: operaciones vectorizadas, funciones de biblioteca, estructuras de datos adecuadas, `groupby`, `merge`, `join`, agregaciones, `transform` y `map` cuando corresponda. Considerar también su complejidad temporal.

Para Pandas/NumPy:

- Evitar recorrer fila por fila cuando exista una alternativa vectorizada clara.
- No utilizar `iterrows()` sin justificación técnica; si la iteración por filas es realmente necesaria, evaluar `itertuples()`.
- No utilizar bucles manuales para operaciones que la biblioteca realiza de forma más clara o eficiente.
- No extraer un bucle a otra función únicamente para ocultar que es un bucle anidado.

## B2. Recursividad

No utilizar recursividad como sustituto de un bucle. Solo utilizarla cuando el problema tenga una estructura naturalmente recursiva: árboles, estructuras jerárquicas, recorridos recursivos o algoritmos definidos así. Para procesamiento normal de datos, preferir iteración u operaciones de biblioteca.

## B3. Valores mágicos y configuración

Evitar valores de negocio o configuración escritos en múltiples lugares; centralizar rutas, nombres de archivos, columnas críticas, parámetros de negocio, límites y configuraciones reutilizadas.

```python
ANIO_CORTE = 2026

if anio > ANIO_CORTE:
```

Aplicar solo cuando el valor tenga significado de negocio, configuración o reutilización; no convertir cada literal pequeño en una constante (ver **A6**).

## B4. Efectos secundarios y estado mutable

- Las funciones deben evitar modificar silenciosamente objetos externos; preferir efectos explícitos: `df_limpio = limpiar_datos(df)`.
- Especial cuidado con DataFrames, listas, diccionarios, objetos compartidos y estado global.
- No utilizar objetos mutables como valores por defecto (`def procesar_datos(datos=[]):` es incorrecto); preferir inmutables o inicialización interna.
- Evitar atributos de clase mutables compartidos accidentalmente entre instancias.
- En Pandas, trabajar sobre copias (`df.copy()`) y evitar el patrón que dispara `SettingWithCopyWarning`.

## B5. Reglas de negocio y lógica técnica

Separar conceptualmente *qué* debe hacer el sistema de *cómo* se implementa. Toda decisión de negocio o dominio debe poder identificarse y justificarse; no aplicar transformaciones "porque parecían necesarias".

```python
df = df[df["university_level"] != "None"]
```

Debe existir una regla de negocio o una decisión documentada que explique esta operación. Especialmente en datos:

- Conservar la semántica; no convertir categorías significativas en valores nulos sin justificación.
- No eliminar información sin justificación; documentar transformaciones relevantes.
- Registrar estrategias de imputación (qué se imputó y por qué) y, cuando la ausencia sea informativa, considerar columnas indicadoras *missing/imputed*.
- No sustituir indiscriminadamente los nulos por `0`, pues el cero suele ser significativo.

## B6. Integridad de los datos

- No modificar los datos originales salvo autorización explícita; trabajar sobre copias o derivados manteniendo diferenciados originales, integrados y limpios.
- Validar antes y después de transformaciones importantes: dimensiones, columnas, tipos, valores faltantes y duplicados; comprobar pérdida o multiplicación inesperada de registros.
- Al leer datos, especificar parámetros explícitos (`encoding`, `sep`, `dtype`, `parse_dates`) en lugar de confiar en inferencias por defecto.
- Estandarizar nombres de columnas y tipos temprano (sin espacios, minúsculas con guiones bajos, dtypes adecuados como `category` para cardinalidad baja).
- Antes de un `merge`/`join`, validar claves duplicadas para evitar explosión de filas; tras el merge, comprobar dimensiones.
- Loggear o registrar cuántas filas se descartan, imputan o modifican en cada etapa, de modo que una caída inesperada de registros sea visible.
- Una transformación importante debe poder explicarse y validarse; verificar claves únicas al final cuando corresponda.

## B7. Notebooks

Cuando el código esté en un cuaderno Jupyter, organizar las celdas de forma lógica: contexto, imports, configuración, carga de datos, funciones auxiliares, procesamiento, validaciones, resultados y exportación.

Evitar: imports repetidos, configuración dispersa, procesamiento duplicado, funciones gigantes y celdas con demasiadas responsabilidades independientes. Separar razonablemente procesamiento, validación, visualización y exportación. Validar que el cuaderno sea reproducible de arriba a abajo.

---

# C. Robustez

## C1. Manejo de errores

- Capturar excepciones específicas (`except FileNotFoundError:`) en lugar de `except:`.
- No usar `except: pass` ni convertir silenciosamente un error real en un valor aparentemente válido.
- No usar `try/except` para esconder problemas que deberían corregirse; si un error debe propagarse, dejar que se propague.
- Al transformar una excepción, conservar información útil del error original.
- Los mensajes de error deben incluir contexto suficiente para diagnosticar desde un log (operación, entrada afectada u origen).
- No ignorar valores de retorno que informan fallos; un error silencioso es difícil de rastrear.

## C2. Logging y salida

En scripts y procesos reproducibles, usar `logging` para eventos importantes, advertencias, errores e información de diagnóstico. En notebooks exploratorios, `print()`/`display()` son apropiados para presentar resultados. No usar mensajes de consola como sustituto de un sistema de registro cuando el proyecto requiera trazabilidad.

> **Excepción del proyecto (MineriaProtect):** en entregables académicos de minería de datos, los `print()`/`display()` que el pipeline emite como **bitácora y evidencia** (diagnóstico, decisiones tomadas, validación final) constituyen el entregable en sí, según el criterio "Documentación" del curso. Se permite su uso intencional y estructurado en scripts y notebooks; quedan prohibidos los prints de depuración residuales.

## C3. Manejo de recursos

Liberar siempre los recursos adquiridos, preferentemente con `with` (archivos, conexiones, cursors, handles). No abrir recursos sin cerrarlos; en datos, evitar cargar datasets completos en memoria cuando la tarea permita procesamiento en chunks o paginación.

## C4. Rendimiento

- Evitar consultas u operaciones de I/O dentro de bucles (patrón N+1).
- No repetir cálculos costosos que puedan calcularse una vez y pasarse por referencia.
- Las llamadas de red deben tener timeout.
- Para conjuntos grandes, procesar en chunks o paginando, sin cargar resultados ilimitados en memoria.
- Optimizar solo cuando sea necesario; la optimización prematura no sustituye a la claridad (ver **A6** y la regla final **E5**).

## C5. Seguridad

- Validar toda entrada externa (parámetros HTTP, archivos, formularios, APIs, variables de entorno) antes de usarla en consultas, operaciones de archivo o llamadas externas. Esto previene inyección SQL, XSS y path traversal.
- No incrustar secretos (claves, tokens, credenciales) en el código, comentarios, pruebas ni logs; provienen de variables de entorno o gestores de secretos.
- No exponer detalles internos (stack traces, nombres de esquemas o rutas) en mensajes mostrados al usuario.
- Las comprobaciones de autenticación/autorización deben residir en el servidor, no solo ocultarse en el cliente.
- Toda dependencia nueva debe revisarse: ¿está mantenida?, ¿tiene vulnerabilidades conocidas?; documentar el motivo de incorporarla.

---

# D. Verificación y entrega

## D1. Pruebas

El código nuevo debe ser comprobable: funciones con entradas y salidas claras facilitan las pruebas. Al escribir o revisar pruebas:

- Cubrir el camino feliz, casos límite y al menos un caso de fallo.
- Verificar comportamiento y no detalles de implementación (una prueba que se rompe sin cambiar comportamiento prueba la implementación, no la función).
- Aislar dependencias externas (bases de datos, APIs) con mocks para que las pruebas sean rápidas, deterministas y estables.
- Las pruebas deben ser independientes entre sí y libres de estados compartidos que generen flakiness.

> **Reconocimiento "Excepcional" (curso Minería de Datos):** en los entregables del curso, los **`assert` por fase embebidos en el pipeline** cuentan como *pruebas automáticas* (nivel Excepcional de la escalera de logro): deben comparar contra cantidades/valores verificados de la fuente, fallar con un mensaje claro y ejecutarse en cada corrida. No se exige una suite de pruebas separada (pytest) para estos entregables.

## D2. Verificación según el tipo de cambio

La cantidad de verificación depende del riesgo del cambio:

- **Cambio pequeño:** revisión estática (sintaxis, nombres, referencias, consistencia).
- **Cambio estructural:** revisión estática + validación de componentes afectados, imports y referencias.
- **Cambio funcional:** ejecución y validación del comportamiento afectado + pruebas.
- **Cambio en datos:** número de registros, columnas, tipos, nulos, duplicados, reglas de negocio y resultados antes/después.

No ejecutar innecesariamente todo el proyecto para verificar un cambio local.

> **Regla de integridad:** solo declarar como realizada una comprobación que realmente se ejecutó. No afirmar que una prueba fue realizada si no se corrió.

## D3. Herramientas y automatización

- Delegar las comprobaciones mecánicas (formato, orden de imports, variables sin usar, estilo) a linters y formatters del ecosistema (p.ej. `ruff`, `black`, `mypy`; `ESLint`/`Prettier` en JS) en lugar de resolverlas a mano en la revisión.
- No discutir estilo en la revisión si una herramienta puede aplicarlo automáticamente.
- Ejecutar los checks básicos en CI antes de la revisión humana, de modo que la revisión se concentre en lógica, comportamiento y decisiones.
- Estas herramientas y el CI son **opcionales**: recomendadas cuando el proyecto las adopte; no son un requisito de los entregables evaluados del curso (la verificación exigida es la de **D2**).

## D4. Control de versiones

- Realizar commits pequeños y enfocados en una única responsabilidad, con mensajes descriptivos.
- No versionar secretos, credenciales ni artefactos generados.
- En revisiones (PR), mantener el alcance limitado a un solo objetivo; documentar qué cambió, por qué, qué debe revisarse y qué queda fuera de alcance.

## D5. Reproducibilidad

Regla de oro del curso (criterio "Reproducibilidad", 10 %): **rutas relativas + requisitos declarados + semillas fijas si hay aleatoriedad**.

- Usar rutas **relativas al proyecto**; nunca rutas absolutas de la máquina local. En notebooks, resolver la raíz del proyecto buscando hacia arriba la carpeta `data/`.
- Declarar las dependencias del código (p.ej. `script/requirements/requirements.txt`) y documentar el comando de instalación y de ejecución en el `README`.
- Fijar semillas (`random.seed`, `np.random.seed`) **solo cuando el proceso use aleatoriedad**; si no hay fuente aleatoria, no introducir semillas artificialmente.
- El original de los datos es intocable: nunca sobrescribirlo; toda transformación escribe una salida nueva y documentada.
- Cualquier decisión de negocio que afecte el resultado (rango temporal, umbrales, banderas) debe vivir en un único punto de configuración o estar documentada en la bitácora.

---

# E. Contexto y modo de uso

## E1. Preservación del contexto

Antes de modificar código: leer el código existente, entender su propósito, identificar dependencias, reglas de negocio y restricciones, y detectar qué comportamiento debe conservarse. No refactorizar basándose en fragmentos aislados si el contexto disponible es insuficiente.

No inventar requisitos, resultados, datos, comportamientos, dependencias ni reglas de negocio. Si falta información necesaria para decidir correctamente, indicarlo.

## E2. Preservación del comportamiento

Al refactorizar, preservar el comportamiento observable, las reglas de negocio, las interfaces existentes y los resultados, salvo que el cambio funcional sea intencional.

No cambiar el algoritmo o la lógica funcional simplemente porque otra implementación parezca "más limpia". Si para mejorar la estructura es necesario cambiar el comportamiento: identificar el cambio, explicarlo, no aplicarlo silenciosamente y solicitar autorización cuando el contexto lo requiera.

## E3. Protocolo de conflictos

Cuando existan instrucciones contradictorias:

1. Aplicar la jerarquía de reglas definida al inicio.
2. Priorizar las restricciones explícitas del proyecto.
3. Priorizar la corrección funcional.
4. Señalar la contradicción.
5. Aplicar una solución conservadora si no cambia el comportamiento.

No resolver conflictos importantes mediante suposiciones silenciosas ni asumir decisiones cuando el contexto no sea suficiente.

---

## E4. Modos de uso y formato de salida

Este documento es una referencia; debe ser invocado con un **modo de uso** para tareas puntuales, sin re-enviar todo el estándar en cada turno.

### Referencia
Usar como estándar general al crear o modificar código.

### Revisión
Analizar el código y detectar incumplimientos **sin modificarlo**.

### Refactorización
Analizar primero y modificar después, preservando el comportamiento (ver **E2**).

### Corrección puntual
Aplicar únicamente la regla solicitada y las correcciones necesarias relacionadas, sin refactorización general. Ejemplo:

```
CORREGIR:
archivo: script/limpieza/limpiar_empleos.py
problema: función superior a 100 líneas
objetivo: reducir complejidad sin cambiar comportamiento
```

### Formato mínimo de respuesta

Para tareas de análisis o modificación, responder de forma estructurada usando solo las secciones que correspondan:

```
## Estado
APROBADO | REQUIERE CAMBIOS

## Hallazgos
| Prioridad | Archivo | Línea | Regla | Problema | Recomendación |
|---:|---|---|---|---|---|

## Cambios realizados
...

## Comportamiento preservado
...

## Excepciones o decisiones
...

## Verificación
- Sintaxis:
- Lint/análisis estático:
- Tests:
- Ejecución:
- Validación de datos:
```

- Clasificar hallazgos como CRÍTICO, ALTO, MEDIO o BAJO.
- No inventar números de línea; si no pueden determinarse, indicarlo.
- En el apartado Verificación, aplicar la regla de integridad de **D2**: solo marcar como realizada una comprobación efectivamente ejecutada.
- No añadir explicaciones extensas que no aporten a la tarea.

---

## E5. Regla final

No optimizar por cumplir la mayor cantidad de reglas. Optimizar por producir código: correcto → claro → mantenible → verificable → simple → eficiente cuando sea necesario.

Las reglas son una guía de calidad, no un objetivo en sí mismas. Si una regla aplicada literalmente empeora el código, explicar la excepción y conservar la solución técnicamente más adecuada (ver **A6**).