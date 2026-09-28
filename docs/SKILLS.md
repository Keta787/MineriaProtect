# SKILLS — las competencias ESCO dentro de `empleos`

Qué son las seis columnas de competencias del dataset integrado, qué significan, qué se puede
sacar de ellas y qué no. Este documento es la referencia del tema; para el detalle de por qué se
tomó cada decisión de diseño, ver `docs/AUDITORIA_RAMA_PRUEBA.md` §5.6.

Las cifras de este documento son de la rama vigente (**test + val**: 376.567 experiencias,
71.061 personas) y se verificaron corriendo el pipeline completo.

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
| `n_skills_essential` | número | Total de competencias esenciales del oficio | 4 a 99 · mediana 20 · media 23,3 · sd 13,3 |
| `n_skills_competence` | número | Cuántas de esas son *saber hacer* | — |
| `n_skills_knowledge` | número | Cuántas son *saber* | — |
| `n_skills_sin_tipo` | número | Las relaciones que la fuente entrega sin `skillType` | >0 en el 0,84 % de las filas |
| `veces_ese_oficio` | número | Cuántas experiencias tiene esta persona en **este** oficio | 1 a 19 · mediana 1 · 16 valores distintos |

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

## 8. Los nombres no están en el pipeline

Solo hay contadores. Los nombres de las competencias se recuperan bajo demanda desde la fuente, con
tres funciones de `src/filtro/indicadores.py`:

```python
import indicadores as I

rel = I.cargar_relaciones()                       # 67.600 pares / 3.039 oficios, con occupation_code
I.skills_de_ocupacion(rel, "8331.1")             # las competencias de UN cargo
I.skills_de_persona(empleos, rel)                 # las de TODAS las experiencias de una persona
I.resumen_competencias(empleos)                   # una fila por oficio, con los contadores
```

La razón de que estén fuera del pipeline es la de §5: los nombres son largos (659 caracteres
promedio), y meterlos como columna agregada añadiría 230 MB al dataset principal sin ganar nada que
el merge no dé en un segundo.

`skills_de_persona()` devuelve **una fila por (`resume_id`, `skill_label`)**: el caso del taxista de
19 veces da **33 skills únicas**, no 19 × 33 = 627. La repetición ya está en `veces_ese_oficio`.

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

Esta selección de dos features es la que quedó implementada en los cuadernos de la sesión 4 (ver §10), junto con el binario de reincidencia.

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

**Y una advertencia metodológica**, si esto llega a un informe: como el conteo es por oficio y no
por persona, un análisis de «personas con más habilidades» está mal construido desde el inicio. Lo
que sí se puede afirmar es sobre **puestos**: «quienes pasan de ingeniería a otra área suben de una
demanda media de 18 a 32 competencias», y eso es un hallazgo legítimo y útil.

---

## 10. Las skills en la transformación (`4.0` / `4.1`)

**Estado: HECHO.** La sección **2.5** de ambos cuadernos las incorpora a la `X`. Esta sección
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

Las dos celdas de la 2.5 comprueban, antes de dropear, que no haya ningún `0` y que el vacío
coincida exacto con `saber_skills == 'no_clasificado'`. Y la celda de la `X` final sigue
comprobando que no queden nulos ni dtypes no numéricos: `X_final` queda en
(50.000 × 2.327) en `4.0` y (50.000 × 2.328) en `4.1`, con 0 nulos.

---

## 11. Reproducirlo

Las skills entran en la fase de integración, antes de cualquier limpieza. El orden importa:

```bash
python src/limpieza/limpiar_datos.py         # crea data/02_interim/SKILLS/ (el puente limpio)
python src/limpieza/integrar_empleos.py      # + 6 columnas → empleos.csv   (376.567 × 17)
python src/limpieza/limpiar_empleos.py       # + 3 banderas → *_limpio.csv  (376.567 × 20)
python src/limpieza/dividir_por_outliers.py  # sin cola larga              (341.090 × 20)
```

Los cuatro scripts son deterministas: sin aleatoriedad, sin fechas, sin orden dependiente del
entorno. Correrlos dos veces da el mismo archivo byte a byte.

| Archivo | Filas | Columnas | Tamaño |
|---|---|---|---|
| `data/03_processed/empleos.csv` | 376.567 | 17 | 47,9 MB |
| `data/03_processed/empleos_limpio.csv` | 376.567 | 20 | 54,8 MB |
| `data/03_processed/empleos_limpio_sin_outliers.csv` | 341.090 | 20 | 49,5 MB |

Los contadores se guardan **como texto** en el CSV, porque el proyecto lee todo con `dtype=str`
(regla para no perder los ceros a la izquierda de los códigos ESCO: `0110` no puede colisionar con
`110`). Para usarlos como número hay que hacer `pd.to_numeric` explícitamente.

---

## 12. Verificación

`limpiar_empleos.py` corre 10 umbrales, 4 de ellos sobre las competencias, y falla ruidosamente si
alguno se descuadra. Además, `integrar_empleos.py` imprime el bloque `CANON PARA limpiar_empleos.py`
con las cifras verificadas en cada corrida.

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
```

> Detalle de pandas al reproducir esto: **`NaN != NaN` es `True`**, así que cualquier comparación de
> igualdad entre columnas de contadores tiene que restringirse a las filas con dato. Sin ese filtro
> la cuenta da 28.304 filas «que no cuadran» cuando en realidad cuadran todas — y es exactamente el
> falso positivo que dio durante la implementación. El assert del pipeline ya lo hace así.
