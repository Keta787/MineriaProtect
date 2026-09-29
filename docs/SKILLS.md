# SKILLS — las competencias ESCO dentro de `empleos`

Qué son las seis columnas de competencias del dataset integrado, qué significan, qué se puede
sacar de ellas y qué no. Este documento es la referencia del tema; para el detalle de por qué se
tomó cada decisión de diseño, ver las secciones de decisiones del `README.md`. La auditoría de la rama (`docs/AUDITORIA_RAMA_PRUEBA.md`) está **fuera de git** y documenta una versión anterior del pipeline (era `train`, 1.506.445 filas); sirve como contexto, no como fuente de verdad.

Las cifras de este documento son de la rama vigente (**test + val**: 376.567 experiencias,
71.061 personas) y se verificaron corriendo el pipeline completo.

> **De dónde sale cada perfil.** Las cifras de las §2 y §7 se midieron sobre
> `empleos_limpio.csv` con el bloque de la §12, no salieron de una sesión de EDA. Conviene decirlo
> porque el cuaderno `2.0_EDA_y_seleccion.ipynb` —el único EDA del repo— **se ejecutó el 2026-09-15,
> antes** de que las seis columnas se integraran, y su salida guardada ni las menciona. Sus
> comentarios sobre la taxonomía tampoco incluyen los archivos de `01_raw/SKILLS/`. Si se quiere un
> EDA que cubra las competencias, hay que reejecutar `2.0`; hoy no lo hay.

---

## 1. De dónde viene

La fuente es el puente de relaciones de ESCO v1.2.1: `occupationSkillRelations_en`, que dice qué
competencias **exige un cargo**. No dice qué sabe ninguna persona. La diferencia importa y está en
§3.

| Dato | Valor |
|---|---|
| Relaciones totales en la fuente | 126.051 |
| Relaciones `essential` (las que usa el pipeline) | **67.600** |
| Oficios con al menos una competencia esencial | 3.039 |
| Distribución por tipo | 51.155 `skill/competence` · 16.406 `knowledge` · **39 sin `skillType`** |
| Archivo crudo | `data/01_raw/SKILLS/occupationSkillRelations_en.csv` |
| Archivo limpio (el que lee el pipeline) | `data/02_interim/SKILLS/occupationSkillRelations_en_limpio.csv` |
| Diccionario de competencias (no entra al integrado) | `data/02_interim/SKILLS/skills_en_limpio.csv` |

Las skills viven en carpetas hermanas de ESCO (`ESCO/` y `SKILLS/`) en `01_raw` y `02_interim`,
porque se limpian aparte. `limpiar_datos.py` las descubre con `rglob("*")` y conserva la subcarpeta,
así que la separación no costó ningún cambio en el script.

### El cruce que hay que hacer (y es fácil no hacer)

El puente no usa el código de ocupación, sino el `conceptUri`, que es un UUID:

```
occupationSkillRelations_en.occupationUri  ─┐
                                            ├─→  occupation_code
occupations_en.conceptUri                 ─┘
```

Sin ese salto el merge devuelve **0 filas sin ningún error visible**. Por eso está resuelto en un
solo lugar del código: `indicadores.cargar_relaciones()`.

---

## 2. Las seis columnas

| Columna | Tipo | Qué afirma | Cifras (test+val) |
|---|---|---|---|
| `saber_skills` | texto | `ok` / `no_clasificado`: si hay oficio al que atribuir competencias | `ok` 348.263 (92,5 %) · `no_clasificado` 28.304 (7,5 %) |
| `n_skills_essential` | número | Total de competencias esenciales del oficio | 4 a 99 · mediana 20 · media 23,3 · sd 13,3 · 78 valores distintos |
| `n_skills_competence` | número | Cuántas de esas son *saber hacer* | 0 a 69 · mediana 18 · media 19,2 · sd 11,2 · 68 valores distintos |
| `n_skills_knowledge` | número | Cuántas son *saber* | 0 a 45 · mediana 3 · media 4,0 · sd 4,4 · 37 valores distintos |
| `n_skills_sin_tipo` | número | Las relaciones que la fuente entrega sin `skillType` | >0 en el 0,84 % de las filas |
| `veces_ese_oficio` | número | Cuántas experiencias tiene esta persona en **este** oficio | 1 a 19 · mediana 1 · 16 valores distintos |

La asimetría entre las dos columnas de tipo es el dato más importante de la tabla: `competence` tiene
mediana 18 y `knowledge` mediana 3, o sea que el «saber hacer» domina por 6 a 1. Volveremos sobre esto
en la §7, porque es justo lo que hace que la dimensión de tipo sirva.

`n_skills_competence + n_skills_knowledge + n_skills_sin_tipo = n_skills_essential`, verificado por
un assert en cada corrida del pipeline.

> **Dos medianas, no una.** La mediana **19** es entre oficios; la mediana **20** es entre filas de
> experiencia. No son el mismo número: pesando por filas, los oficios más comunes pesan más.

---

## 3. Lo que estas columnas NO dicen

**ESCO describe lo que exige un cargo, no lo que sabe un individuo.** El dato de "qué sabe esta
persona" no existe en ninguna fuente del proyecto. Lo que hay es una **atribución**: se le asigna a
la persona el contenido del oficio que ocupaba.

La consecuencia práctica es que **dentro de un oficio no hay variación**: a los 19 choferes de bus
del caso `resume_id 83474` les corresponde la misma exacta lista de 33 competencias. Un hombre y una
mujer, ambos taxistas, con 33 competencias cada uno. Las columnas describen el **puesto**, no a la
**gente**.

Por eso toda lectura debe redactarse así:

| Se puede decir | No se puede decir |
|---|---|
| «El cargo de taxista exige 33 competencias esenciales» | «Esta persona sabe 33 cosas» |
| «El 92,5 % de las experiencias tiene oficio clasificado» | «El 92,5 % de las personas tiene habilidades» |
| «Esta persona volvió 19 veces a este cargo» | «Esta persona tiene 19 veces más experiencia» |

La única de las seis columnas que **sí** describe a una persona es `veces_ese_oficio` (§6).

---

## 4. Vacío ≠ 0

Cuando no hay oficio clasificado, los cuatro contadores quedan **vacíos** y `saber_skills` vale
`no_clasificado`. Nunca `0`.

No es un detalle de formato. Un `0` afirmaría que el cargo **no exige ninguna competencia**, lo cual
es falso. El vacío afirma que **no sabemos cuál era el cargo**. Son afirmaciones opuestas: una
describe el puesto, la otra describe nuestro conocimiento del dato. Mezclarlas produce conclusiones
inventadas sobre 28.304 filas (7,5 % del dataset).

Hay tres asserts que impiden que se mezclen:

```
Skills: contador descuadrado vs saber_skills      0   OK   # vacío <=> no_clasificado
Skills: contador en 0 (debe ser vacio)            0   OK   # el 0 está prohibido
Skills: competence+knowledge+sin_tipo != total    0   OK   # la suma cierra
```

`rescatado` (2.499 filas) cae en `no_clasificado` porque ESCO solo publica relaciones de competencia a
nivel de **ocupación**, no de grupo ISCO: aunque sepamos el área, no hay con qué contar.

---

## 5. Por qué son contadores y no filas

Esta es la decisión central. La primera implementación produjo `personas_skills.csv` con
**8.100.598 filas** (persona × experiencia × competencia) y 1,2 GB.

Llevar eso a `empleos` significa cambiar su grano, y el grano **es** su contrato: 1 fila = 1
experiencia, con PK única. Al expandir:

| | actual (contadores) | si fueran filas |
|---|---|---|
| filas | 376.567 | 8.100.598 (×21,5) |
| duplicados por PK `(resume_id, matched_code, start_date, end_date)` | 0 | **7.752.335** |
| filas que `dividir_por_outliers.py` borraría | 35.477 | **~763.170** |
| asserts de `limpiar_empleos.py` | 10/10 | 0/10 |

El renglón del medio es el que más daño hace: las 35.477 filas de cola larga son **las mismas 35.477**,
contadas 21 veces. El pipeline reportaría haber eliminado 763.170 paradójicamente sin borrar una sola
experiencia nueva.

Con contadores, `empleos.csv` pasa de 11 a **17 columnas** y las filas siguen siendo **376.567**.
El pipeline entero (`limpiar_empleos.py`, `dividir_por_outliers.py`) corre sin cambios
estructurales.

### El caso que la PK no ve

La fila «duplicados por PK: 0» de la tabla de arriba es cierta, pero la clave con la que se mide
—`(resume_id, matched_code, start_date, end_date)`— está elegida de tal modo que **no puede detectar
este problema**. Cambiando `matched_code` por `occupation_code` aparecen **52 grupos · 105 filas · 51
personas** con el mismo `resume_id`, el mismo `start_date` y el mismo `end_date` registrados dos veces:

```
100849 | Q1 2012 -> Q1 2013 | matched_code=3412.4.9 | emparejado=rescatado | es_unknown=False
100849 | Q1 2012 -> Q1 2013 | matched_code=unknown  | emparejado=unknown  | es_unknown=True
```

Es el **mismo periodo con dos desenlaces contradictorios**: o el puesto se empareja con un código o
no se empareja; ambas cosas a la vez no puede ser. Ocurre en 50 de los 52 grupos; en los 2 restantes
las dos filas son `rescatado` con distinto `isco_group`. Un grupo tiene 3 filas, los otros 51 tienen 2.

Lo que arrastra:

- `es_unknown_ocupacion` son **25.755** filas con periodo único, no 25.805.
- `es_rescatado` son **2.444**, no 2.499.

Ambas cifras del dataset están infladas en 50 y 55 filas respectivamente: el desdoblamiento del
`matched_code` ocurrió **antes** de que existiera `occupation_code`, que es la columna que hoy
permitiría verlo.

**No hay que arreglarlo para minar, y conviene saber por qué:** 0 de las 105 filas son
`saber_skills = 'ok'`, así que **ninguna llega a la `X`** (ni en `4.0` ni en `4.1`). El sesgo vive
solo en las cifras agregadas de este documento, no en el modelo. Aun así, si alguien cuenta
`es_unknown_ocupacion` para reportar «cuántas experiencias no se pudieron clasificar», la respuesta
honesta es 25.755.

Detalle que vuelve el hallazgo confuso de medir: si se busca el duplicado con
`["resume_id", "occupation_code", "start_date", "end_date"]` **sin rellenar los nulos**, `pandas`
compara `NaN` contra `NaN` como si fueran iguales y reporta **53** duplicados, cifra que no significa
nada. El conteo honesto exige tratar el vacío como su propio valor (`fillna("SIN_CODE")`), y recién
ahí aparece el fenómeno real de 52 grupos.

### Solo `essential`

De 126.051 relaciones se usan 67.600. Las `optional` son habilidades de nivelación, no el piso del
cargo: sumarlas volvería el conteo interpretable pero menos informativo, porque un cargo con
muchas opcionales y pocas esenciales se vería igual de exigente que uno al revés.

---

## 6. `veces_ese_oficio`: la reincidencia medida en vez de repetida

Quien repite el mismo cargo 19 veces tiene 19 filas —una por experiencia, con sus fechas— y
`veces_ese_oficio = 19` en todas. Sus competencias no se repiten dentro de cada fila.

Sin esa columna el conteo sería ambiguo entre dos cosas muy distintas: *«un cargo muy demandante»*
(muchas competencias) y *«muchos periodos en el mismo cargo»* (muchas filas iguales). El número de
competencias no las distingue.

```
veces_ese_oficio = 1      242.013 filas  (64,3 %)
                  >= 2     106.250 filas  |  32.400 personas
                  >= 3      44.992 filas  |  11.309 personas
                  >= 5      10.840 filas  |   1.825 personas
                  >= 10        512 filas  |      46 personas
                  = 19          19 filas  |       1 persona
```

**28,2 % del dataset son reincidencia, en 32.400 personas.** Es una cuarta parte de la información
de la tabla, y antes estaba escondida dentro de la repetición.

Además es la única columna de las seis que aporta una señal **conductual**: `es_vigente` dice «este
trabajo sigue abierto»; `veces_ese_oficio` dice «esta persona ya estuvo aquí». Preguntas distintas,
y solo una tenía respuesta.

---

## 7. Las seis columnas no son seis variables

Esto es lo que más conviene tener claro antes de construir la `X`.

### `n_skills_essential` no aporta información nueva

Es una **función determinista de `occupation_code`**: de 2.855 oficios, **0** tienen más de un valor
distinto. No hay nada en `occupation_label` que esta columna no sepa ya.

Lo que aporta es **codificación**: un número donde antes había 2.855 etiquetas. Eso es todo. Pero no
es trivial, porque resuelve *por debajo* del grupo ISCO:

- η² del grupo ISCO sobre `n_skills_essential` = **0,613** → el grupo explica 61 %, el 39 % restante
  está dentro del grupo.
- sd dentro del grupo = 4,3 · sd entre grupos = 11,3.
- **348 de 424** grupos contienen más de un oficio.

Es decir: reemplaza 2.855 etiquetas por un número que conserva resolución fina. El trade-off es real
y conviene decidirlo a conciencia, no heredarlo.

### Los tres contadores son la misma variable partida

`competence` y `knowledge` suman `essential`. No son tres variables sino una, repartida. Correlación
entre ambas: **0,34**.

Y el reparto está muy desbalanceado:

```
ratio  n_skills_competence / n_skills_essential
  mínimo 0,00   mediana 0,85   máximo 1,00   sd 0,128
  oficios con "hacer" dominando (> 0,5):  2.670 de 2.855
  oficios con "saber"  dominando (< 0,5):    137 de 2.855
```

Solo 137 oficios invierten el patrón, pero son los que hacen útil la dimensión:

| Código | Oficio | `essential` | hacer | saber | ratio |
|---|---|---|---|---|---|
| `3118.3.5` | computer-aided design operator | 49 | 6 | 43 | 0,12 |
| `2149.5` | bioengineer | 16 | 4 | 12 | 0,25 |
| `9621.2` | hotel porter | 6 | 7 | 0 | 1,00 |
| `9333.5` | rail intermodal equipment operator | 17 | 17 | 0 | 1,00 |

Un puesto de railway o de portero es puro «hacer»; uno de bioingeniería es casi puro «saber». Con
solo `n_skills_essential`, esos cuatro se verían casi iguales (49, 16, 6, 17 → ninguno se
distingue por *qué* exige, solo por *cuánto*).

### `n_skills_sin_tipo` es ruido como variable

Vale >0 en el **0,84 %** de las filas. Existe por aritmética: 39 de las 67.600 relaciones llegan sin
`skillType`, y sin ese bucket la suma no cerraría contra el total en 31.484 filas. Es un parche
aritmético, no un atributo del cargo.

---

## 8. Los nombres: la tabla `competencias_por_oficio.csv`

Los nombres de las competencias **sí están en el pipeline**, pero no dentro de `empleos_limpio.csv`:
viven en una tabla aparte, `data/03_processed/competencias_por_oficio.csv`, con **una fila por (oficio,
competencia)**. La produce `src/limpieza/generar_competencias.py`.

### Por qué una tabla y no una columna

Por el motivo de la §5 (los nombres son largos: 659 caracteres de promedio) y por uno propio: las
competencias son un atributo del **oficio**, no de la persona. Hay **3.039 oficios** para 71.061
personas y 376.567 experiencias, así que escribirlas en cada fila las repetiría unas 376.000 veces
(+230 MB). En su propia tabla se escriben **una vez por oficio** y se unen con un cruce N:1 por
`occupation_code`, que ya existe en los tres CSV del pipeline. **No hizo falta modificar ninguno.**

### La forma de la tabla

```
occupation_code | occupation_label         | habilidad_nombre                | habilidad_tipo
9111.1          | domestic cleaner         | cleaning techniques             | knowledge
9111.1          | domestic cleaner         | remove dust                    | skill/competence
9111.1          | domestic cleaner         | make the beds                  | skill/competence
...
```

| | |
|---|---|
| Filas | **67.600** (1 por par oficio × competencia) |
| Oficios | **3.039** |
| Habilidades distintas | **11.378** |
| Peso | 5,02 MiB |

**"1 fila = 1 competencia" es la regla de guardado, no la de lectura.** Para mostrar el perfil de un
cargo se agrupa por `occupation_code` y sale una línea con todas sus competencias; eso hace
`perfil_persona()`. Un cargo con 20 competencias ocupa 20 filas en el CSV y se muestra como una sola
línea de 20 nombres.

**Por qué no la forma ancha** (3.039 filas con los nombres dentro de un texto delimitado): permite
preguntar *«¿qué oficios exigen `welding techniques`?»* o *«¿qué hay en común entre horneador y
welder?»* con un `groupby`, en vez de partir texto en 3.039 filas cada vez. Eso es justamente la
pregunta de investigación, y cuesta 3 MB más.

### La tabla es un superconjunto del dataset

La tabla describe a **ESCO** (3.039 oficios); JobHop solo usa **2.855**. Los 184 oficios restantes
(3.693 competencias) no aparecen en ninguna fila de `empleos_limpio.csv` y están a propósito, para
poder ampliar sin volver a la fuente. No es una discrepancia.

### Las dos fuentes de verdad, vigiladas

`n_skills_essential` **se conserva** en los CSV del pipeline (está dentro de la `X` de `4.0`/`4.1` y no
cuesta nada), pero deja de ser un dato independiente: es una **caché desnormalizada** de esta tabla.
`generar_competencias.py` lo verifica en cada corrida, y lo verifica **por los cuatro contadores**:

```
n_skills_essential     reproduce todos los tipos    oficios que no cuadran: 0
n_skills_competence    reproduce skill/competence   oficios que no cuadran: 0
n_skills_knowledge     reproduce knowledge          oficios que no cuadran: 0
n_skills_sin_tipo      reproduce sin_tipo           oficios que no cuadran: 0
```

El contraste se restringe a los 2.855 oficios que JobHop usa. Comparar también los otros 184 daría
`NaN != NaN` y 184 falsos positivos — la trampa documentada en la §12, pero al revés.

Esto no elimina la redundancia: la convierte en una **red de seguridad**. Si el puente ESCO se
rompe, el pipeline corta con diagnóstico en vez de dejar dos números distintos circulando.

### Cómo usarla

```python
import indicadores as I

comp = I.cargar_competencias()                       # 67.600 × 4, la tabla normalizada
I.competencias_por_oficio(comp)                      # {occupation_code: [nombres]}
I.perfil_persona(empleos, comp, "100013")            # trayectoria con las competencias de cada cargo
I.salto_competencias(empleos, comp)                  # (detalle, resumen) del Jaccard entre contratos

# El camino viejo sigue vivo y da el mismo resultado:
rel = I.cargar_relaciones()                          # lee el puente ESCO crudo
I.skills_de_ocupacion(rel, "8331.1")                 # las competencias de UN cargo
I.skills_de_persona(empleos, rel)                    # las de TODAS las experiencias de una persona
I.resumen_competencias(empleos)                      # una fila por oficio, con los contadores
```

`cargar_competencias()` es la vía preferida: el archivo existe, el salto `code` → `occupationUri` ya
está hecho y validado, y no depende de que la fuente ESCO siga donde estaba.
`cargar_relaciones()` se conserva como lectura directa de la fuente y como referencia de contraste.

**Sobre el reparto de las competencias**, que no se había medido: las 11.378 habilidades son muy
específicas y su distribución es de cola larga. Sobre los 67.600 pares, las **10** habilidades más
frecuentes cubren el **3,3 %**, las **100** cubren el **17,2 %** y las **1.000** el **56,0 %**: hace
falta llegar a un cuarto de las habilidades para cubrir la mitad de los pares. No son un puñado de
"habilidades generales" sino miles de competencias específicas de cada puesto — lo que refuerza que
la unidad útil de análisis sea el **oficio** y no un "perfil de competencias" promedio.

### El salto entre contratos

`salto_competencias()` mide el **índice de Jaccard** entre las competencias que exigían dos contratos
consecutivos de una misma persona (`|A ∩ B| / |A ∪ B|`). Sobre 249.323 transiciones: **mediana 0,00** y
**53,5 %** sin compartir **ni una sola** competencia. Es decir, más de la mitad de los cambios de
oficio no tocan el conjunto de competencias exigidas.

Dos criterios, ambos iguales a los de `transiciones_consecutivas` para que los dos indicadores de
transición del proyecto sean comparables:

- Se eliminan los periodos repetidos exactos (misma persona, mismo inicio, mismo fin). Ojo: de los
  15.290 grupos repetidos solo **2.127** tienen un único cargo (ahí sí es duplicado); los otros
  **13.163** son cargos **distintos en el mismo periodo**, o sea pluriempleo simultáneo. Un trabajo
  simultáneo no es una transición.
- Un periodo **sin oficio clasificado rompe la cadena**: no se salta para emparejar los trabajos de los
  lados. Si alguien tiene un hueco de tres años cuyo cargo desconocemos, no se puede afirmar que pasó
  directamente de A a B.

Como dentro de un oficio no hay variación (§3), este indicador mide **cuánto cambian los requisitos
entre dos puestos**, no cuánto cambian las capacidades de una persona.

---

## 9. Cómo usarlas

**Como features, dos:**

```python
n_skills_essential    # demanda del oficio
veces_ese_oficio      # reincidencia de la persona
```

**`saber_skills` como filtro, nunca como variable.** Sacá las 28.304 filas `no_clasificado` y seguí.
No le asignes un número de relleno: el vacío ya dice lo que hay que saber, y un 0 sería una
afirmación falsa sobre el 7,5 % del dataset.

Esta selección de dos features es la que quedó implementada en la fase de transformación (código en `src/transformacion/`, evidencia en los cuadernos de la sesión 4, ver §10), junto con el binario de reincidencia.

**Si te interesa el contraste saber / saber hacer, usa el ratio, no los conteos:**

```python
ratio_saber_hacer = n_skills_competence / n_skills_essential
```

El ratio es insensible al tamaño del cargo, así que separa mejor. Un `n_skills_knowledge` alto puede
significar «oficio exigente» o «oficio con muchas competencias de un solo tipo»; el ratio distingue
los dos casos.

**`n_skills_sin_tipo`: fuera del modelo.** Déjalo en el CSV, donde cumple su función aritmética, y
no lo lleves a la `X`.

**Ojo con la redundancia.** Como `n_skills_essential` es determinista de `occupation_code`, si tu
modelo ya incluye `occupation_label` o `isco_group_label` one-hot, la información ya está ahí: la
variable no agrega señal, solo costo. Elige una de las dos formas. La ventaja de quedarse con el
número es comparabilidad y escalado; la de quedarse con la etiqueta es no perder la identidad del
oficio.

**Son dos redundancias distintas, y conviene no mezclarlas.** La de **almacenamiento** (el número
está en el CSV y además en la tabla de la §8) ya se resolvió: se conserva porque no cuesta nada, y se
vigila con un assert en cada corrida. La de **análisis** (si el número entra o no en la `X` como
variable) sigue abierta y es una decisión de modelado, no de datos: depende de si se va a usar la
identidad del oficio como etiqueta one-hot o su exigencia como número, y no de cómo se guarde.

**Y una advertencia metodológica**, si esto llega a un informe: como el conteo es por oficio y no
por persona, un análisis de «personas con más habilidades» está mal construido desde el inicio. Lo
que sí se puede afirmar es sobre **puestos**: «quienes pasan de ingeniería a otra área suben de una
demanda media de 18 a 32 competencias», y eso es un hallazgo legítimo y útil.

---

## 10. Las skills en la transformación (`4.0` / `4.1`)

**Estado: HECHO.** La sección **2.5** de ambos cuadernos las incorpora a la `X`; el cálculo vive
en `src/transformacion/`, que es lo que ambos ejecutan. Esta sección
explica cómo y qué costó, porque las dos decisiones no son obvias.

### Qué entra y qué no

| Columna | ¿Entra a la `X`? | Por qué |
|---|---|---|
| `n_skills_essential` | sí, con `RobustScaler` | La demanda de competencias del oficio |
| `veces_ese_oficio` | sí, con `RobustScaler` | La reincidencia, en magnitud (2 ≠ 19) |
| `reincide` (= `veces > 1`) | sí, **sin escalar** | El mismo dato como 0/1, que es estable para el escalador |
| `n_skills_competence` | no | Es `essential` repartido, no información nueva |
| `n_skills_knowledge` | no | Ídem |
| `n_skills_sin_tipo` | no | Es aritmética, no un atributo del cargo |
| `saber_skills` | no | Es un filtro, no una variable |

El binario **no se escala** por la misma regla que el cuaderno ya aplicaba a las dummies y a las
banderas: un 0/1 no gana nada con un escalador. Y `n_skills_essential` se incluye **aun siendo
redundante con el one-hot de `occupation_code`**, porque en un modelo con distancia euclídea una
variable numérica densa ordena a los vecinos de forma que 2.855 columnas dispersas no.

### El costo: 7,5 % de las filas salen de la `X`

`n_skills_essential` es `NaN` en las filas sin oficio clasificado, y `sklearn` no admite `NaN` en un
escalador. Como el proyecto no imputa, la salida es dropearlas, y la pérdida se declara en el
cuaderno en vez de esconderla:

| | `4.0` (con cola larga) | `4.1` (sin cola larga) |
|---|---|---|
| filas antes | 376.567 | 341.090 |
| filas que salen de la `X` | 28.304 (7,52 %) | 26.186 (7,68 %) |
| filas usable para la `X` | **348.263** | **314.904** |
| personas | 71.061 → 70.397 | 69.182 → 68.338 |

Las que salen son exactamente las de `emparejado = 'unknown'` (25.805 / 23.886) más las de
`emparejado = 'rescatado'` (2.499 / 2.300). Estas últimas sí tienen `occupation_code`: ESCO publica
relaciones a nivel de ocupación, no de grupo ISCO, así que del código recuperado no hay nada que
contar. Por eso el vacío ≠ 0 de la §4 importa acá también: si esas filas hubieran entrado con un 0
de relleno, el modelo habría aprendido que «un puesto sin competencias» es una categoría real.

> Los cuatro números de arriba son los del dataset completo. Corregidos por el desdoblamiento de
> periodos de la §5 serían 25.755 y 2.444. La diferencia no cambia ninguna de las dos filas de la
> tabla, porque el drop es por `saber_skills`, no por bandera: las 105 filas en cuestión ya están
> fuera de la `X` por ser `no_clasificado`.

### El efecto secundario del drop: columnas que colapsan y banderas constantes

Este es el punto que hay que tener presente antes de minerar, y no aparece en los cuadernos.

**a) Dos banderas quedan constantes.** `es_unknown_ocupacion` y `es_rescatado` se llevan en la `X`
como columnas, pero **el drop de la §2.5 las deja en un solo valor**:

```
es_unknown_ocupacion   en la X (4.0): ['False']        -> 1 valor
es_rescatado           en la X (4.0): ['False']        -> 1 valor
es_vigente             en la X (4.0): ['False', 'True'] -> 2 valores
```

No es un defecto del drop: es su consecuencia lógica. Las filas que llevan esas banderas en `True`
son **exactamente** las que se van, así que las columnas quedan con ancho cero. Meter dos features
constantes en un KNN o en k-means no rompe nada, pero tampoco aporta nada y **engaña a cualquier
lectura de importancia de variables**: un modelo que les dé un peso distinto de cero está usando una
constante.

**b) El one-hot de `emparejado` se reduce a una columna.** Por la misma causa, `get_dummies` deja de
devolver tres columnas y devuelve una:

```
celda 21 de 4.0:  emparejado -> 1 columnas  ['emparejado_ok']
```

La tabla de codificación de la celda 4 y el comentario de la celda 33 siguen describiendo
`emparejado` como «3 columnas» y `emparejado_ok / _unknown / _rescatado`. Describen el dataset
**anterior** al drop. El código hace bien la cuenta y la imprime; lo que quedó desactualizado es el
texto alrededor.

Las verificaciones finales de los cuadernos no detectan ni (a) ni (b) porque solo comprueban dtypes y
nulos, y tanto una columna de ceros como una dummy única están sanas en ambos respectos.

Comprobación de una línea para (a):

```python
for c in ("es_unknown_ocupacion", "es_rescatado"):
    assert e.loc[e["saber_skills"].eq("ok"), c].nunique() == 1, f"{c} varía dentro de la X"
```

Y para (b):

```python
pd.get_dummies(df_s["emparejado"]).shape[1]     # 1, no 3
```

**Decisión pendiente, no resuelta en el repo:** si se conservan, conviene registrarlas como
**constantes** y no como features. Si se dropean las dos banderas constantes, `X_final` baja de 2.327
a 2.325 columnas en `4.0` (y `emparejado_ok` es, por su parte, redundante con
`occupation_code`, como ya se dice en la §9).

### El escalamiento, que era la parte no obvia

Agregadas **sin** escalar, las skills rompen la métrica. Medido sobre la submuestra de 50.000 filas
de `4.0` (300 parejas aleatorias), aporte de cada columna a la distancia euclídea:

| Escenario | `start_ord` | `end_ord` | `dur_q` | `univ_ord` | `n_skills` | `veces` |
|---|---|---|---|---|---|---|
| **Sin skills** (lo que había) | 20,12 % | 21,64 % | **56,56 %** | 1,68 % | — | — |
| Skills **sin escalar** | 42,94 % | 38,00 % | 10,78 % | 0,03 % | 8,19 % | **0,05 %** |
| Skills **con `RobustScaler`** (producción) | 12,09 % | 13,54 % | 32,51 % | 0,66 % | **17,68 %** | **19,74 %** |

Dos cosas que la tabla deja claras y que no se ven en la §5:

1. **`veces_ese_oficio` sin escalar vale 0,05 %.** No es «una variable que aporta poco»: es una
   variable **anulada** por el escalamiento de otra. Con `RobustScaler` pasa a 19,74 %.
2. **Sin las skills, `univ_ord` ya estaba en 0,03 %** y con ellas en producción sigue en 0,66 %.
   Ese es un efecto lateral conocido de mezclar IQR con rango total, ya documentado como deuda
   abierta en la sección 4.2 de los cuadernos. Las skills no lo crearon ni lo empeoraron.

En `4.1` el panorama es el mismo con otros números (fechas 83,75 % sin escalar; `n_skills` de 8,76 %
a 14,24 % con `Robust`).

### Qué pasó con el PCA

El audit de correlación ahora corre sobre **6** numéricas en vez de 4, y la conclusión no cambió:
hacen falta **4 de 6** componentes para el 80 % de la varianza y la sexta no aporta nada. PCA
sigue sin aplicar y sigue fuera de la `X` final.

Lo interesante es **por qué** no comprime, y las competencias lo hacen visible: la correlación de
`n_skills_essential` contra `start_ord` es **0,046** en `4.0` y **0,038** en `4.1`. Son casi
ortogonales. Las fechas y la duración son una dependencia lineal entre sí; las competencias
describen el *puesto*, no el *cuándo*. Son dimensiones que no se solapan, que es exactamente la
condición para que un PCA no sirva.

### Cómo se verifica

Los dos checks de la 2.5 —que no haya ningún `0` y que el vacío coincida exacto con
`saber_skills == 'no_clasificado'`— se calculan **antes** del drop, en
`transformacion.universo_con_competencias` (`src/transformacion/`); la celda 2.5 de los
cuadernos los imprime ya medidos (`info["ceros"]`, `info["vacio_exacto"]`). El cálculo se movió
al módulo al extraer la transformación de los cuadernos, y conviene decirlo porque la versión
anterior de esta línea decía que el check vivía en la celda.

La celda de la `X` final, en cambio, sí sigue comprobando en el cuaderno que no queden nulos ni
dtypes no numéricos: `X_final` queda en (50.000 × 2.327) en `4.0` y (50.000 × 2.328) en `4.1`,
con 0 nulos y 0 columnas no numéricas en ambos.

---

## 11. Reproducirlo

Las skills entran en la fase de integración, antes de cualquier limpieza. La tabla de competencias se
genera después de la integración, porque se contrasta contra sus contadores. El orden importa:

```bash
python src/limpieza/limpiar_datos.py         # crea data/02_interim/SKILLS/ (el puente limpio)
python src/limpieza/integrar_empleos.py      # + 6 columnas → empleos.csv   (376.567 × 17)
python src/limpieza/generar_competencias.py  # tabla de competencias        (67.600 × 4)
python src/limpieza/limpiar_empleos.py       # + 3 banderas → *_limpio.csv  (376.567 × 20)
python src/limpieza/dividir_por_outliers.py  # sin cola larga              (341.090 × 20)
```

Los cinco scripts son deterministas: sin aleatoriedad, sin fechas, sin orden dependiente del
entorno. Correrlos dos veces da el mismo archivo byte a byte.

> **La transformación no es un sexto script.** Desde que el código salió de los cuadernos a
> `src/transformacion/` (librería, sin `__main__`), la fase 4 se reproduce abriendo
> `notebooks/4.0_transformacion.ipynb` o `4.1_transformacion_sin_outliers.ipynb` y ejecutándolos:
> los cuadernos importan el módulo y **imprimen**, el módulo **devuelve**. No se ejecuta con
> `python` y no deja archivos: la `X` no se persiste (50.000 × ~2.327 en denso son ~116 MB, y
> el curso no pide el `.csv`), así que la evidencia de esa fase es la salida guardada del
> cuaderno, no un derivado en `data/`. Los dos cuadernos se conservan y difieren solo en
> `VERSION`.

En esa fase la aleatoriedad sí existe y por eso está atada: un único `RandomState` compartido
(`rng = np.random.RandomState(T.SEED_MUESTRA)`) se crea en la celda de configuración y se pasa
después a `submuestra()` y a `auditoria_pca()`, en ese orden, para que el consumo coincida con el
de la versión anterior. Y el `KBinsDiscretizer` de la 2.4 va con `subsample=None` a propósito: en
sklearn 1.9.1 `fit` hace `resample(..., random_state=None)` sobre una submuestra de 200.000 filas,
así que con 376.567 filas los bordes salían distintos en cada corrida (regla D5 incumplida). Ese
bloque es exploratorio y no entra en la `X`, pero sus bordes estaban citados en el cuaderno.

> La excepción son los CSV de bitácora en `logs/`, que llevan una marca de tiempo ISO y por eso sí
> cambian en cada corrida. La afirmación es sobre los datos, no sobre los logs. Verificado por hash:
> reserializar `empleos_limpio_sin_outliers.csv` desde `empleos_limpio.csv` reproduce el SHA-256 del
> archivo en disco.

| Archivo | Filas | Columnas | Tamaño |
|---|---|---|---|
| `data/03_processed/empleos.csv` | 376.567 | 17 | 47,9 MiB |
| `data/03_processed/competencias_por_oficio.csv` | 67.600 | 4 | 5,02 MiB |
| `data/03_processed/empleos_limpio.csv` | 376.567 | 20 | 54,8 MiB |
| `data/03_processed/empleos_limpio_sin_outliers.csv` | 341.090 | 20 | 49,5 MiB |

(En MiB, no en MB decimales: los mismos archivos miden 5,3 / 50,2 / 57,4 / 51,9 MB. Vale la pena
decirlo porque `ls -h` y `stat` usan bases distintas y las cifras parecen no cuadrar.)

Los contadores se guardan **como texto** en el CSV, porque el proyecto lee todo con `dtype=str`
(regla para no perder los ceros a la izquierda de los códigos ESCO: `0110` no puede colisionar con
`110`). Para usarlos como número hay que hacer `pd.to_numeric` explícitamente.

---

## 12. Verificación

`limpiar_empleos.py` corre 10 umbrales, 4 de ellos sobre las competencias, y falla ruidosamente si
alguno se descuadra. Además, `integrar_empleos.py` imprime el bloque `CANON PARA limpiar_empleos.py`
con las cifras verificadas en cada corrida.

La tabla de competencias de la §8 añade un cuarto control, que es el que ata las dos fuentes de
verdad: `generar_competencias.py` **no escribe nada** hasta que contar sus filas por oficio reproduce
los cuatro contadores de `empleos.csv`, oficio por oficio (0 discrepancias en los 2.855). Además
exige que no haya ni un par (oficio, competencia) repetido, porque sin eso el conteo por oficio
dejaría de equivaler al conteo de competencias distintas y el contraste compararía dos cosas
distintas.

Para una revisión completa del dataset:

```python
e = pd.read_csv("data/03_processed/empleos_limpio.csv", dtype=str,
                keep_default_na=False, na_values=[""])
num = lambda c: pd.to_numeric(e[c], errors="coerce")
ok = e["saber_skills"].eq("ok")
total = num("n_skills_essential")

# el vacío y el flag tienen que coincidir exactamente
(total.isna() == ~ok).all()                        # True
total.eq(0).sum() == 0                             # True

# y la suma de los buckets tiene que cerrar contra el total
buckets = num("n_skills_competence") + num("n_skills_knowledge") + num("n_skills_sin_tipo")
buckets.isna().loc[~total.notna()].all()           # True: sin dato, los 3 también
buckets.eq(total).loc[total.notna()].all()          # True: 348.263 de 348.263

# las banderas quedan constantes dentro de la X (ver §10)
[e.loc[ok, c].nunique() for c in ("es_unknown_ocupacion", "es_rescatado")]   # [1, 1]

# y los periodos desdobles de la §5, contados con el vacío como valor propio
v = e.copy()
v["occupation_code"] = v["occupation_code"].fillna("SIN_CODE")
PK = ["resume_id", "occupation_code", "start_date", "end_date"]
v.duplicated(subset=PK, keep=False).sum()           # 105, en 52 grupos y 51 personas

# la tabla de la §8 reproduce los contadores, por los cuatro
c = pd.read_csv("data/03_processed/competencias_por_oficio.csv", dtype=str,
                keep_default_na=False, na_values=[""])
conteo = c.groupby(["occupation_code", "habilidad_tipo"]).size().unstack(fill_value=0)
conteo["n_skills_essential"] = conteo.sum(axis=1)
usados = (e.loc[ok, ["occupation_code", "n_skills_essential"]]
          .drop_duplicates("occupation_code")
          .set_index("occupation_code")["n_skills_essential"]
          .pipe(pd.to_numeric))
(usados == conteo.loc[usados.index, "n_skills_essential"]).all()          # True
c.duplicated(subset=["occupation_code", "habilidad_nombre"]).sum()       # 0
```

> Detalle de pandas al reproducir esto: **`NaN != NaN` es `True`**, así que cualquier comparación de
> igualdad entre columnas de contadores tiene que restringirse a las filas con dato. Sin ese filtro
> la cuenta da 28.304 filas «que no cuadran» cuando en realidad cuadran todas — y es exactamente el
> falso positivo que dio durante la implementación. El assert del pipeline ya lo hace así.
>
> Y al revés: al contar duplicados, `NaN` **sí** se considera igual a `NaN`, que es lo que produce
> los 53 sin sentido de la §5. Las dos trampas son el mismo comportamiento de `pandas`, aplicado en
> direcciones opuestas.
