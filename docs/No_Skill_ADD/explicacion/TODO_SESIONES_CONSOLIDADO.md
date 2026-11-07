
# contexto_sesion1.md

# SesiÃ³n 1 Â· QuÃ© es minerÃ­a de datos

> **Para quÃ© sirve este documento.** Explica la sesiÃ³n 1 del curso (*IntroducciÃ³n a la MinerÃ­a
> de Datos*) aplicada a **MinerÃ­aProtect**. EstÃ¡ escrito para alguien que ya tiene los datos
> pero **no programador**.
>
> **No es un manual de cÃ³digo.** No vas a aprender Python aquÃ­. Vas a entender **quÃ© preguntas
> responde y por quÃ© se tardÃ³ **tres sesiones solo en preparar los
> datos** y por quÃ© el proyecto **no va a predecir nada**.
>
> **Las cifras son las vigentes** (las del `README.md` a septiembre de 2026). Si alguna vez
> oyes un nÃºmero como "1.506.445 filas" o "174.036 nulos", ese es de una versiÃ³n anterior
> del proyecto que ya no se usa.

---

## 1. La idea

MinerÃ­a de datos **no es correr un programa que adivina el futuro**. Casi siempre es lo
contrario: es **leer algo que ya estÃ¡ escrito** y encontrar una estructura que nadie habÃ­a
notado.

Tres ejemplos de "cosas que ya estaban escritas":

- Las tarjetas de un banco dicen que un grupo de clientes tiene una media de edad de 40 aÃ±os y
  el otro, la mitad. Nadie lo habÃ­a mirado, pero llevaba aÃ±os escrito en los registros.
- Un defecto de pieza en una fÃ¡brica ocurre a las 14:20, cuando el turno acaba. EstÃ¡ en la
  hora de todos los registros.
- Un hospital sabe a quÃ© hora llegan las admisiones masivas: a las 9, cuando empiezan los turnos.

**El patrÃ³n no se agrega. Se descubre.** Esa es la diferencia con un reporte, que solo
cuenta cosas que ya se sabÃ­an.

**Y hay una advertencia que se repite en toda la sesiÃ³n:** la calidad de la respuesta depende
casi por completo de la calidad de los datos. Si los datos estÃ¡n mal, el algoritmo ejecuta sin
error y devuelve una respuesta **equivocada con apariencia de respuesta**. Nadie se avisa.

---

## 2. Cuatro palabras que hay que saber

| Palabra | QuÃ© es, en serio |
|---|---|
| **Dataset** | El archivo con los datos. AquÃ­: la lista de experiencias laborales de 71.061 personas. |
| **Variable** | Una caracterÃ­stica que se le anota a cada fila. "OcupaciÃ³n", "fecha de inicio", "nivel educativo". |
| **PatrÃ³n** | Una regularidad que se repite. "Las personas que empiezan en Seller ahora estÃ¡n en Manager el 70 % de las veces." |
| **Algoritmo** | Una receta fija que, aplicada a los datos, devuelve algo. Un Ã¡rbol de decisiÃ³n, un K-means, una regresiÃ³n. |

**Sobre el algoritmo:** es la parte fÃ¡cil. Todos los algoritmos se descargan, se instalan y se
ejecutan. Lo difÃ­cil â€”y lo que ocupa el 80 % del trabajoâ€” es tener datos decentes.

---

## 3. En el curso: las seis etapas (KDD)

El curso presenta el **KDD** (*Knowledge Discovery in Databases*, descubrimiento de
conocimiento en bases de datos) como un proceso de **seis pasos**, siempre en el mismo orden:

```plaintext
1. SELECCIÃ“N      â†’ Â¿de dÃ³nde saco los datos?
2. PREPROCESAMIENTO â†’ vienen sucios, hay que limpiarlos
3. TRANSFORMACIÃ“N  â†’ hay que volverlos nÃºmeros
4. MINERÃA         â†’ aquÃ­ sÃ­ corro el algoritmo          â† el 20 %
5. INTERPRETACIÃ“N  â†’ Â¿quÃ© significa lo que saliÃ³?
6. CONOCIMIENTO    â†’ Â¿quÃ© hago con esto maÃ±ana?
```

**El punto que el profesor mÃ¡s repite, y que conviene interiorizar:**

> **La minerÃ­a de datos propiamente dicha es solo 1 de las 6 etapas.**

El error mÃ¡s comÃºn â€”y el mÃ¡s caro conceptualmenteâ€” es creer que "minerÃ­a de datos" significa
"aplicar un Ã¡rbol de decisiÃ³n". Significa **las seis cosas**. Y las cinco primeras no tienen
nada de difÃ­cil: son escuchar y usar lÃ³gica de negocio.

**La regla prÃ¡ctica que resume toda la sesiÃ³n:**

> **80 % del esfuerzo es preparar los datos. 20 % es modelar.**

MinerÃ­aProtect lleva tres sesiones en esa parte del 80 %. No es que el proyecto vaya lento: es
que la etapa va primero.

---

## 4. CRISP-DM: el mismo camino, con nombres de industria

El curso tambiÃ©n menciona **CRISP-DM**, un estÃ¡ndar usado en la empresa. No es otra teorÃ­a
distinta: es **el mismo camino con nombres mÃ¡s precisos**, y aÃ±ade dos cosas Ãºtiles.

| | KDD (6 etapas) | CRISP-DM (6 fases) |
|---|---|---|
| Empezar por los datos | SelecciÃ³n | Entendimiento del negocio |
| Ver quÃ© hay | SelecciÃ³n | Entendimiento de los datos |
| Arreglar | Preprocesamiento | PreparaciÃ³n |
| Convertir a nÃºmeros | TransformaciÃ³n | TransformaciÃ³n |
| Correr el modelo | MinerÃ­a | Modelado |
| Ver si sirve | InterpretaciÃ³n | EvaluaciÃ³n |
| Usarlo | Conocimiento | Despliegue |

**Lo que CRISP-DM agrega y KDD no dice:**

1. **Empieza por el negocio, no por los datos.** Antes de mirar una sola fila hay que
   responder: Â¿esto le sirve a alguien? KDD arranca en "selecciÃ³n"; CRISP-DM arranca en
   "comprensiÃ³n del negocio".
2. **Se puede volver atrÃ¡s.** El camino no es una lÃ­nea recta. KDD tampoco lo dice, pero
   CRISP-DM lo pone explÃ­cito: la minerÃ­a va despuÃ©s de la preparaciÃ³n.

---

## 5. En MinerÃ­aProtect: el acta de constituciÃ³n

El proyecto sÃ­ se hizo esta sesiÃ³n. El resultado estÃ¡ en
`notebooks/1.0_comprension_negocio.md`, que es el documento donde se decidiÃ³ **quÃ©** se va a
investigar y **por quÃ©**. Es literalmente el primer entregable.

### 5.1 El escenario de aplicaciÃ³n

> **Un observatorio laboral de formaciones educativas.** O sea: el problema de **conectar lo
> que una persona estudia con lo que efectivamente llega a trabajar.**

Tres personas a las que le importa:

- **Instituciones educativas** â€” saber si las carreras que forman sirven.
- **Egresados** â€” decidir a quÃ© atenerse.
- **Tomadores de decisiÃ³n pÃºblicos** â€” diseÃ±ar la polÃ­tica de formaciÃ³n.

### 5.2 Las preguntas, en dos idiomas

| | |
|---|---|
| **Pregunta de negocio** (sin tecnicismos) | Â¿QuÃ© patrones aparecen en la trayectoria laboral de una persona a lo largo de su vida, y quÃ© relaciÃ³n tiene esa trayectoria con lo que estudiÃ³? |
| **Pregunta tÃ©cnica** (con tecnicismos) | Dado un historial de empleos *(desde, hasta, ocupaciÃ³n)* por persona, Â¿quÃ© secuencias y transiciones ocupacionales son frecuentes y estables? |
| **Objetivo** | Descubrir y caracterizar **patrones de transiciÃ³n ocupacional** en trayectorias post-formaciÃ³n. |

La misma pregunta, dos veces: una para el rector y otra para el que programa.

### 5.3 La decisiÃ³n mÃ¡s importante: esto NO es predicciÃ³n

AquÃ­ el proyecto hizo algo que casi nadie hace y que conviene entender bien:

> **Tarea de minerÃ­a: *descubrimiento* (no supervisada).**
> **Quedan descartadas las tareas supervisadas** (clasificaciÃ³n, regresiÃ³n, predicciÃ³n).

Â¿QuÃ© significa eso? En un problema **supervisado** hay una columna que dice la respuesta
("este cliente se fue", "este empleado fue ascendido") y el modelo aprende a acertar esa columna
a partir de las otras. En un problema **no supervisado** **no existe esa columna**: no hay
respuesta correcta que adivinar. Solo se busca estructura.

**Por quÃ© MinerÃ­aProtect descartÃ³ la predicciÃ³n:**

- Nadie pidiÃ³ "dime si esta persona va a cambiar de empleo". Nadie pidiÃ³ eso.
- Si existiera la columna "cambiÃ³ de empleo", el proyecto serÃ­a de predicciÃ³n. No lo es.
- La pregunta es **"Â¿quÃ© transiciones ocurren y con quÃ© frecuencia?"** â€” y esa pregunta se
  responde **contando patrones**, no entrenando un modelo.

**Esto es la lecciÃ³n de la sesiÃ³n 1 aplicada:** el curso explica que la minerÃ­a es la etapa 4
de 6, y MinerÃ­aProtect tomÃ³ la decisiÃ³n de **empezar por las etapas 1 a 3 y quedarse en la
etapa 3** â€” porque las respuestas de las etapas 1 y 2 (limpieza) ya son el entregable de las
sesiones 2 y 3.

### 5.4 Las fuentes: dos sÃ­, una descartada

| Fuente | QuÃ© aporta | DecisiÃ³n |
|---|---|---|
| **JobHop v2** | Historial de empleos por persona, con fechas trimestrales. Da el identificador de persona, que es lo que permite armar secuencias. | **Usada** |
| **ESCO v1.2.1** (ComisiÃ³n Europea) | Convierte el cÃ³digo de ocupaciÃ³n en un cÃ³digo estandarizado, para poder comparar. | **Usada** |
| **OLE Colombia** (Observatorio Laboral) | Historiales ocupacionales de personas. | **Descartada** â€” no publica trayectorias con fechas a nivel de persona |

**Por quÃ© se descartÃ³ OLE:** sin fechas, no hay secuencias. Y el proyecto necesita secuencias
(trazos en el tiempo), no solo un listado de trabajos. **Se descartÃ³ por una razÃ³n
estructural, no porque fuera mala fuente.**

### 5.5 La advertencia importante: los datos son de BÃ©lgica

> Los patrones de este proyecto salen de **Flandes, BÃ©lgica**. **Son mÃ©todo, no son
> aplicables a Colombia sin precauciÃ³n en la interpretaciÃ³n.**

Este es un punto que a veces incomoda y que vale la pena tener claro. El proyecto **usa el
mÃ©todo** (cÃ³mo se construye una trayectoria laboral, cÃ³mo se limpian datos, cÃ³mo se
transforman) con datos reales. Pero un patrÃ³n que sale de BÃ©lgica **no significa
automÃ¡ticamente que ocurra igual en Colombia** â€” el mercado laboral colombiano es otro.

**Lo que sÃ­ se puede trasladar:** el mÃ©todo, la forma de limpiar, la forma de transformar.
**Lo que hay que mirar con lupa:** cualquier conclusiÃ³n sobre "las personas hacen tal cosa".

### 5.6 Los tres criterios de Ã©xito

Como el proyecto **no es predictivo**, no hay "accuracy" ni puntaje. El Ã©xito se mide con
tres cosas, y las tres importan por igual:

1. **Patrones identificables y repetidos.** Se deben encontrar transiciones que **se repitan**
   varias veces, no anÃ©cdotas sueltas.
2. **Datos limpios, trazables y reproducibles.** Cada nÃºmero del informe se puede regenerar
   con los scripts. Nada escrito a mano.
3. **Resultados interpretables.** Alguien no tÃ©cnico entiende quÃ© se encontrÃ³.

El punto 2 es el que mÃ¡s se cuida en el proyecto, y es la razÃ³n de que exista todo lo que se
vio en la sesiÃ³n 3: bitÃ¡cora, scripts deterministas, archivos que nunca se editan a mano.

---

## 6. Lo que el curso pide y aquÃ­ no aplica

| Lo que pide el curso | Por quÃ© aquÃ­ no aplica |
|---|---|
| Aplicar un modelo y medir su exactitud | El proyecto no es predictivo: no hay columna objetivo que adivinar. |
| Usar el dataset de ejemplo (TelecomUNO) | MinerÃ­aProtect usa datos reales de Belgium (JobHop v2 + ESCO). |
| Buscar el "cliente que se va" | AquÃ­ se buscan "trayectorias y transiciones", no "clientes en riesgo". |
| Inventar un problema de negocio | El problema ya estÃ¡ definido: observatorio de formaciones educativas. |

---

## 7. QuÃ© ya estÃ¡ hecho

- âœ… Acta de constituciÃ³n analÃ­tica firmada: `notebooks/1.0_comprension_negocio.md`
- âœ… Pregunta de negocio, tÃ©cnica y objetivo, definidos
- âœ… Fuentes seleccionadas (2 usadas, 1 descartada con razÃ³n)
- âœ… Tarea de minerÃ­a decidida: **descubrimiento, no predicciÃ³n**
- âœ… Criterios de Ã©xito definidos

**Esta sesiÃ³n ya no se vuelve a tocar.** Es el documento que fija el rumbo.

---

## 8. Lo que sigue

```plaintext
SesiÃ³n 1  â†’  Â¿de dÃ³nde salen los datos?          (acta)         âœ” hecho
SesiÃ³n 2  â†’  cÃ³mo se cargan y se juntan         (EDA)          âœ” hecho
SesiÃ³n 3  â†’  limpiar los datos                  (pipeline)     âœ” hecho
SesiÃ³n 4  â†’  volverlos nÃºmeros                  (transformar)  âœ” hecho
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SesiÃ³n 5  â†’  mirarlos con calma                 (EDA)
SesiÃ³n 7+ â†’  aplicar la tÃ©cnica de minerÃ­a      (modelos)
```

Cada sesiÃ³n es una etapa del camino de la secciÃ³n 3. El proyecto lleva cuatro etapas
completadas. Lo que sigue es **la primera vez que se corre un algoritmo de verdad** â€” y
recuerda: esa es la etapa 4 de 6, la Ãºltima que se hace, no la primera.

---

## 9. Errores frecuentes

| âŒ Error | âœ… Correcto |
|---|---|
| Empezar por el modelo | Primero el acta: Â¿esto le sirve a alguien? |
| Confundir "minerÃ­a" con "un algoritmo" | MinerÃ­a son las 6 etapas, no solo la 4 |
| Confundir mining con "reporte" | Un reporte cuenta lo que ya se sabe; la minerÃ­a descubre lo que no |
| Prometer un 90 % de exactitud sin pregunta de negocio | Primero la pregunta, despuÃ©s el modelo |
| Tratar los datos de BÃ©lgica como si fueran de Colombia | El mÃ©todo se traslada, las conclusiones hay que mirarlas con lupa |
| Decidir "voy a predecir" sin que nadie lo pida | El proyecto se define por su pregunta, no al revÃ©s |

---

## En una frase

**La minerÃ­a de datos no es adivinar el futuro: es leer algo que ya estÃ¡ escrito y encontrar
la estructura que nadie habÃ­a visto. Y en MinerÃ­aProtect, esa estructura todavÃ­a no se ha
buscado: primero se limpiÃ³ y se transformÃ³, que es exactamente lo que la sesiÃ³n 1 dice que
hay que hacer.**



# contexto_sesion2.md

# SesiÃ³n 2 Â· Fuentes y formatos de datos

> **Para quÃ© sirve este documento.** Explica la sesiÃ³n 2 del curso (*Fuentes y Tipos de
> Datos*) aplicada a **MinerÃ­aProtect**. EstÃ¡ escrito para alguien que ya tiene los datos pero
> **no programador**.
>
> **No es un manual de cÃ³digo.** AquÃ­ se entiende de dÃ³nde salen los datos, en quÃ© formato
> vienen, cÃ³mo se cargan y por quÃ© el proyecto usa dos fuentes y descartÃ³ una.
>
> **Las cifras son las vigentes** (las del `README.md` a septiembre de 2026). Si alguna vez
> oyes un nÃºmero como "1.506.445 filas" o "174.036 nulos", ese es de una versiÃ³n anterior
> del proyecto que ya no se usa.

---

## 1. La idea

Los datos **no estÃ¡n dentro de tu proyecto**. EstÃ¡n en otro lado: en una pÃ¡gina web, en un
archivo que alguien publica, en una base de datos pÃºblica. El trabajo de esta sesiÃ³n es
**ir a buscarlos, entender cÃ³mo vienen y meterlos al proyecto sin romperlos**.

Tres cosas que hay que tener claras antes de empezar:

1. **Cada fuente tiene su formato.** Un archivo de texto separado por comas no es lo mismo
   que una base de datos ni que una pÃ¡gina web que responde preguntas. Cada formato se lee
   de una manera distinta.
2. **Cargar mal no avisa.** Si lees un archivo de la forma equivocada, el programa **no da
   error**: te devuelve algo que parece un archivo y estÃ¡ mal. Ejemplo real de este
   proyecto: si se leen los cÃ³digos como nÃºmero, el cÃ³digo `0043` se vuelve `43`, y ese
   cÃ³digo ya no existe en ninguna fuente.
3. **Las fuentes se combinan.** Ninguna fuente sirve sola. El proyecto toma una que dice
   *dÃ³nde trabajar* y otra que dice *cÃ³mo se llama ese trabajo*, y las une.

---

## 2. Cuatro formatos que hay que conocer

| Formato | QuÃ© es | Ejemplo |
|---|---|---|
| **CSV** | Un archivo de texto donde cada fila es un registro y las columnas van separadas por comas. Se abre con el bloc de notas. | `ocupaciones_en.csv` |
| **JSON** | Un archivo de texto donde la informaciÃ³n va con llaves y comillas, para que quede anidada. | `ventas.json` |
| **Base de datos (SQL)** | Un archivo que guarda informaciÃ³n en **tablas** y permite hacer preguntas con un lenguaje propio (SQL: "dame las filas donde..."). | `ventas.db` |
| **API** | No es un archivo: es una direcciÃ³n web a la que se le pregunta y contesta. La respuesta cambia si cambian los datos de origen. | La API de ESCO |

**Por quÃ© importa la diferencia entre CSV y base de datos:** en un CSV, cada quien tiene su
propio archivo y las cuentas dejan de cuadrar cuando hay muchos. En una base de datos, todos
preguntan al mismo lugar. El cuaderno de la sesiÃ³n del curso lo dice asÃ­: con 50 sedes, el
CSV se rompe; la base de datos no.

**MinerÃ­aProtect no usa base de datos propia, pero sÃ­ usa una API pÃºblica** (mÃ¡s abajo).

---

## 3. En el curso: una tienda pequeÃ±a

El curso usa un ejemplo de una tienda con 12 ventas, guardado al mismo tiempo en los tres
formatos (CSV, JSON y base de datos) para compararlos. El cuaderno de la sesiÃ³n saca cinco
conclusiones:

1. Un CSV se puede convertir a JSON y volver a leer. Las dimensiones se conservan: 12 filas
   y 7 columnas.
2. Un JSON se puede meter en una base de datos y consultarlo. La base de datos puede
   devolver solo las ventas de una sede.
3. **Los tres formatos conservan la estructura del tiempo.** Al convertirlos, la columna de
   fecha queda igual en los tres. Esto permite analizar la evoluciÃ³n temporal sin importar
   de dÃ³nde venga el dato.
4. **Preguntar en el cÃ³digo o en la base de datos da el mismo resultado.** El total de
   ingresos por categorÃ­a es el mismo se calcule donde se calcule.
5. **Para 50 sedes, la recomendaciÃ³n es una base de datos**, no archivos CSV.

**Lo que la sesiÃ³n realmente enseÃ±a con ese ejemplo:** el formato es el envase, no el contenido.
La informaciÃ³n es la misma; lo que cambia es cuÃ¡nto cuesta moverla y cuÃ¡nto se complica
cuando deja de caber en una sola mÃ¡quina.

---

## 4. En MinerÃ­aProtect: dos fuentes, una descartada

El acta de la sesiÃ³n 1 ya habÃ­a reservado **al menos dos fuentes pÃºblicas**. Estas son las
tres evaluadas:

| Fuente | QuÃ© aporta | DecisiÃ³n |
|---|---|---|
| **JobHop v2** | Historial de empleos por persona, con fecha de inicio y de fin. Da el identificador de persona, que es lo que permite armar la lÃ­nea de tiempo de su carrera. | **Usada** (principal) |
| **ESCO v1.2.1** (ComisiÃ³n Europea) | Convierte un cÃ³digo de ocupaciÃ³n en un nombre y le da una jerarquÃ­a estÃ¡ndar. TambiÃ©n aporta quÃ© competencias exige cada oficio. | **Usada** (enriquecimiento) |
| **OLE Colombia** (Observatorio Laboral) | Historiales ocupacionales de personas. | **Descartada** |

### 4.1 Por quÃ© se descartÃ³ OLE

No porque sea mala fuente, sino por una razÃ³n muy concreta: **no publica trayectorias con
fechas a nivel de persona**. El proyecto necesita saber *en quÃ© orden* una persona fue
cambiando de trabajo y *cuÃ¡ndo*. Sin fechas no hay lÃ­nea de tiempo, y sin lÃ­nea de tiempo no
hay secuencia. Una fuente sin la informaciÃ³n que necesitas no sirve, por muy buena que sea.

### 4.2 JobHop v2: por quÃ© solo la mitad

JobHop v2 viene en tres archivos (llamados *particiones*): `train`, `test` y `val`. Son datos
de la misma naturaleza, pero con distinto propÃ³sito para el aprendizaje automÃ¡tico.

El proyecto **usa `test` + `val` y descarta `train`**. Motivo: `train` es unas cinco veces
mÃ¡s grande y hace el trabajo lento sin aportar informaciÃ³n nueva para este caso.

| ParticiÃ³n | Datos crudos | DespuÃ©s de limpiar | Â¿Se usa? |
|---|---|---|---|
| `train` | 1.594.827 | 1.506.445 | No |
| `test` | 198.877 | 188.061 | **SÃ­** |
| `val` | 199.587 | 188.506 | **SÃ­** |
| **Total usado** | | **376.567** | |

> **Aviso importante:** 1.506.445 es el tamaÃ±o de la particiÃ³n que **no** se usa. Si algÃºn
> dÃ­a se escucha ese nÃºmero, se estÃ¡ hablando de la particiÃ³n descartada, no del proyecto.

**Las 376.567 filas son 71.061 personas.** Es decir: cada persona tiene, en promedio, unas
cinco experiencias laborales registradas.

### 4.3 ESCO: el archivo que le pone nombre a los cÃ³digos

JobHop dice "esta persona trabajÃ³ en el cÃ³digo `0110.10`", pero ese cÃ³digo no significa nada
por sÃ­ solo. ESCO traduce: "`0110.10` es *directivo de empresa*, del Ã¡rea *legisladores y
directivos*".

El paquete ESCO son cuatro archivos:

| Archivo | QuÃ© da | Limpieza aplicada |
|---|---|---|
| `occupations_en.csv` | CÃ³digo â†’ nombre de ocupaciÃ³n + grupo | 3.043 â†’ **3.039** (se quitan 4 cÃ³digos repetidos) |
| `ISCOGroups_en.csv` | La jerarquÃ­a del Ã¡rea (nivel, etiqueta) | 619 filas, 8 â†’ **7** columnas (se quita una que estaba vacÃ­a en el 100 %) |
| `skills_en.csv` | La ficha de cada competencia | 13.960 â†’ **13.939** (se quitan 21 repetidos) |
| `occupationSkillRelations_en.csv` | QuÃ© competencias exige cada oficio | 126.051 â†’ **126.051** (no se quita nada) |

**FÃ­jate en el detalle de la Ãºltima fila:** el archivo de competencias se conserva completo,
incluidas las relaciones a las que la fuente no les da tipo. Esos casos van a su propia
columna para que nada se pierda, en vez de descartarse.

### 4.4 CuÃ¡ntas veces se pudo poner nombre a una ocupaciÃ³n

DespuÃ©s de unir las dos fuentes, cada cÃ³digo de JobHop se busca en ESCO. El resultado:

| Resultado del cruce | QuÃ© significa | CuÃ¡ntas filas |
|---|---|---|
| **`ok`** | El cÃ³digo existe tal cual en ESCO | 348.263 |
| **`rescatado`** | El cÃ³digo exacto no estaba, pero sÃ­ uno que empieza igual (el grupo de 4 dÃ­gitos) | 2.499 |
| **`unknown`** | No se pudo identificar la ocupaciÃ³n | 25.805 |

En total: **2.855 de 2.873 cÃ³digos distintos** tienen nombre (el **93,1 %** de las filas).

**El 6,9 % que queda sin identificar no se tira.** Se conserva con una bandera que dice
"esto no lo supimos identificar". Es preferible saber que no se sabe, que inventar.

---

## 5. CÃ³mo se cargan: la "carga defensiva"

Cargar datos es la acciÃ³n de meter un archivo en el programa. **Carga defensiva** significa
cargar de la manera que menos pueda salir mal, aunque el archivo traiga sorpresas.

La regla mÃ¡s importante del proyecto estÃ¡ en el `README.md`:

> **Todos los archivos se leen como texto** (`dtype=str`), nunca como nÃºmero, para conservar
> los ceros a la izquierda de los cÃ³digos.

**Por quÃ© esto importa tanto:** ESCO e ISCO usan cÃ³digos como `0043` o `0110.10`. El cero de
adelante **es parte del cÃ³digo**, no un relleno.

- Si se lee como texto: `0043` se queda `0043`, y el cruce con la otra fuente funciona.
- Si se lee como nÃºmero: `0043` se vuelve `43`, y ese cÃ³digo no existe en ninguna parte.

**El programa no avisa.** El archivo carga, la tabla se ve normal, y lo que falla son 2.855
cruces que se quedan sin pareja. Por eso el proyecto lo tiene escrito como regla, y no como
buena intenciÃ³n.

---

## 6. Los tres scripts de carga, y por quÃ© el orden importa

Cargar y unir son dos pasos distintos, y por eso hay tres archivos:

| Script | QuÃ© hace | De dÃ³nde a dÃ³nde |
|---|---|---|
| `limpiar_datos.py` | Limpia cada fuente por separado | `data/01_raw/` â†’ `data/02_interim/` |
| `integrar_empleos.py` | Une `test` + `val` de JobHop y le cruza ESCO | fuentes â†’ `empleos.csv` |
| `generar_competencias.py` | Arma la tabla de quÃ© competencias exige cada oficio | ESCO â†’ `competencias_por_oficio.csv` |

**Y hay un detalle de orden que parece casual pero no lo es:** `generar_competencias.py`
tiene que correr **despuÃ©s** de `integrar_empleos.py`, porque su trabajo de validaciÃ³n
consiste en comprobar que los contadores que genera coincidan con los que ya estÃ¡n en
`empleos.csv`. Para eso, el archivo tiene que existir.

Y si por algÃºn motivo el archivo no estuviera, el script **no falla en silencio**: genera la
tabla igual y **avisa en pantalla** que la comprobaciÃ³n se saltÃ³. Esa es la diferencia entre
un programa que miente y uno que avisa.

---

## 7. La API de ESCO: la fuente "en vivo"

El curso pide al menos una fuente que sea una **API o una base de datos pÃºblica**, y el
proyecto cumple con la de ESCO: `data.europa.eu/esco/api`.

Una API no es un archivo: es una direcciÃ³n a la que se le pregunta y contesta. La diferencia
es que **la respuesta se actualiza sola**, sin que nadie vuelva a descargar nada.

El cuaderno `2.0` hace la consulta en vivo sobre una competencia real del conjunto de datos y
muestra la respuesta. Y si la red del lugar donde se estÃ¡ no llega al dominio, **en vez de
fallar muestra un mensaje con las direcciones oficiales**. Otra vez: avisa, no miente.

---

## 8. El detalle de las competencias: contadores, no nombres

JobHop y ESCO permiten calcular, para cada oficio, **cuÃ¡ntas competencias esenciales exige**.
El proyecto lo aprovecha y lo agrega a la tabla principal como seis columnas.

**La decisiÃ³n de diseÃ±o mÃ¡s importante de toda esta sesiÃ³n:** esas seis columnas llevan
**contadores, no nombres**.

- **Contador:** "este oficio exige 20 competencias esenciales". Un nÃºmero.
- **Nombres:** "este oficio exige estas 20 competencias". Una lista.

Si se metieran los nombres, cada una de las 376.567 filas se multiplicarÃ­a por el nÃºmero de
competencias: el archivo pasarÃ­a de unos cientos de megabytes a mÃ¡s de 200, y ademÃ¡s cada
persona aparecerÃ­a repetidas veces, rompiendo la estructura del archivo.

**Entonces, Â¿dÃ³nde estÃ¡n los nombres?** En una tabla aparte,
`competencias_por_oficio.csv`, con **una fila por par (oficio, competencia)**: 67.600 filas,
3.039 oficios y 11.378 habilidades distintas. Se une con el resto por el cÃ³digo de
ocupaciÃ³n, que ya existe en todas partes, asÃ­ que el cruce **no multiplica nada**.

> **Advertencia de lectura, la mÃ¡s importante de esta sesiÃ³n.** Estas columnas dicen **cuÃ¡ntas
> competencias exige el cargo que esta persona ejercÃ­a**. **No dicen quÃ© sabe la persona.** El
> dato de las habilidades de un individuo no existe en ninguna fuente, y el proyecto lo
> atribuye por el puesto que ocupaba. La forma correcta de decirlo siempre es *"este cargo
> exige N competencias"*, nunca *"esta persona sabe N cosas"*.

El detalle completo de las seis columnas estÃ¡ en `docs/SKILLS.md`.

---

## 9. Lo que el curso pide y aquÃ­ no aplica

| Lo que pide el curso | Por quÃ© aquÃ­ no aplica |
|---|---|
| Cargar un CSV de una tienda con 12 ventas | El proyecto usa datos reales: 376.567 experiencias de 71.061 personas. |
| Usar una base de datos SQLite para 50 sedes | El proyecto trabaja con archivos CSV, pero **sÃ­** consulta una API pÃºblica real. |
| Meter todo en un JSON y sacarlo | El proyecto no necesita JSON: la informaciÃ³n es plana, y CSV es mÃ¡s directo. |
| Comparar los ingresos por categorÃ­a | El proyecto no tiene ingresos: tiene ocupaciones, fechas y competencias. |

---

## 10. QuÃ© ya estÃ¡ hecho

- âœ… Dos fuentes pÃºblicas descargadas y verificadas (JobHop v2 + ESCO)
- âœ… Una fuente evaluada y descartada con razÃ³n documentada (OLE Colombia)
- âœ… Fuentes limpiadas una por una (`limpiar_datos.py`)
- âœ… UniÃ³n hecha y validada (`integrar_empleos.py`)
- âœ… Tabla de competencias generada y contrastada contra la fuente (`generar_competencias.py`)
- âœ… Carga defensiva aplicada: todo se lee como texto
- âœ… Consulta real a la API de ESCO, con aviso si la red no llega
- âœ… Cuaderno con toda la evidencia: `notebooks/2.0_EDA_y_seleccion.ipynb`

**Resultado:** `data/03_processed/empleos.csv`, con **376.567 filas y 17 columnas**, de
**71.061 personas**. AdemÃ¡s `competencias_por_oficio.csv` con 67.600 filas.

---

## 11. Lo que sigue

```plaintext
Fuentes crudas (01_raw)          7 archivos, nunca se tocan
        â”‚  limpiar_datos.py
        â–¼
Fuentes limpias (02_interim)     versiÃ³n arreglada de cada una
        â”‚  integrar_empleos.py
        â–¼
Integrado (03_processed)          376.567 x 17  â† el archivo que entra a la sesiÃ³n 3
        â”‚  limpiar_empleos.py
        â–¼
Limpio                           376.567 x 20  â† el archivo que entra a la sesiÃ³n 4
```

La sesiÃ³n 3 empieza donde termina esta: con un archivo ya unido, ya limpio de errores
obvios, y listo para el diagnÃ³stico fino.

---

## 12. Errores frecuentes

| âŒ Error | âœ… Correcto |
|---|---|
| Leer los cÃ³digos como nÃºmero | Leerlos como texto, o se pierden los ceros de adelante |
| Usar la particiÃ³n `train` completa | El proyecto usa `test` + `val`; `train` es 5 veces mÃ¡s grande y no aporta |
| Meter los nombres de las competencias en la tabla principal | Van como contadores; los nombres en una tabla aparte |
| Decir "esta persona sabe 20 cosas" | Decir "este cargo exige 20 competencias" |
| Correr los scripts en cualquier orden | En el orden del `README.md`, o la validaciÃ³n no encuentra con quÃ© compararse |
| Si la API no responde, seguir como si nada | Avisar. El proyecto avisa en pantalla |
| Tocar los archivos de `data/01_raw/` | Son las fuentes: **jamÃ¡s** se modifican. Todo se deriva de ellas |

---

## En una frase

**Los datos no estaban en el proyecto: hay que buscarlos, entender en quÃ© formato vienen y
cargarlos sin romperlos. MinerÃ­aProtect tomÃ³ dos fuentes pÃºblicas, descartÃ³ una porque no
tenÃ­a fechas, y todo se lee "como texto" para que los ceros de los cÃ³digos no
desaparezcan en el camino.**



# contexto_sesion3.md

# SesiÃ³n 3 Â· Limpieza de datos

> **Para quÃ© sirve este documento.** Explica la sesiÃ³n 3 del curso (*Limpieza de datos*)
> aplicada a **MinerÃ­aProtect**, el proyecto propio. EstÃ¡ escrito para alguien que ya tiene
> los datos pero **no programador**: cada concepto se explica en palabras antes de mostrar
> cÃ³mo quedÃ³ en el proyecto.
>
> **No es un manual de cÃ³digo.** No vas a aprender Python aquÃ­. Vas a entender **quÃ© se
> decidiÃ³ tirar, quÃ© se decidiÃ³ conservar y por quÃ©** â€” que es la parte que de verdad importa.
>
> **Las cifras son las vigentes** (las del `README.md` a septiembre de 2026). Si alguna vez
> oyes un nÃºmero como "1.506.445 filas" o "174.036 nulos", ese es de una versiÃ³n anterior
> del proyecto que ya no se usa.

---

## 1. La idea

Hay una forma de pensar que separa a quien limpia datos de quien solo los toca.

**Limpiar datos no es hacerlos lindos. Es evitar que el anÃ¡lisis despuÃ©s mienta.**

Un dato faltante no es un problema que se arregla: es una pregunta sobre la realidad que
nadie respondiÃ³. Una duraciÃ³n de 40 aÃ±os no es un error: es una persona que no se moviÃ³ en
cuarenta aÃ±os. El trabajo de la limpieza es **distinguir el ruido de la informaciÃ³n**, y
casi siempre la respuesta correcta es *conservar y marcar*, no *borrar*.

Esa es la idea de esta sesiÃ³n, y es exactamente lo que hace el proyecto.

---

## 2. Cinco palabras que hay que saber

No hace falta saber programar para leer esto. Solo estas cinco:

| Palabra | QuÃ© es, en serio |
|---|---|
| **CSV** | Un archivo de texto donde los datos estÃ¡n en filas separadas por comas. Se puede abrir con un bloc de notas. Es el formato mÃ¡s simple que existe para tabular datos. |
| **Fila** | Una persona, un evento, un registro. "Esta persona estuvo en este trabajo entre estas fechas." |
| **Columna** | Un atributo. "OcupaciÃ³n", "fecha de inicio", "nivel educativo". |
| **Script** | Un archivo de texto con instrucciones paso a paso. En vez de que alguien revise 376.567 filas a mano, el script lo hace siempre igual, y maÃ±ana tambiÃ©n. |
| **Bandera** | Una columna nueva que dice sÃ­ o no. No reemplaza nada: **se le aÃ±ade al lado** para que la informaciÃ³n importante no se pierda. |

Todo lo demÃ¡s que aparezca aquÃ­ estÃ¡ explicado en el momento en que aparece.

---

## 3. En el curso: el caso TelecomUNO

El curso usa una empresa ficticia, **TelecomUNO**, con un archivo de clientes. El dataset
viene **sucio a propÃ³sito** â€” el profesor lo preparÃ³ asÃ­ para que hubiera algo que limpiar.

TenÃ­a 2.460 filas y le sobraban por lo menos cinco cosas:

| Problema | QuÃ© era |
|---|---|
| **Datos faltantes** | 441 celdas vacÃ­as repartidas en tres columnas |
| **Filas repetidas** | 60 personas aparecÃ­an dos veces |
| **Nombres distintos para lo mismo** | "BÃ¡sico", "basico", "BÃSICO", "Basico "â€¦ 11 formas de escribir 3 planes |
| **NÃºmeros imposibles** | edades de 0 y de 220 aÃ±os; facturaciones negativas |
| **Valores disparatados** | alguien que consumÃ­a 616 GB en un mes |

Al final de la sesiÃ³n el archivo queda asÃ­:

```
2.460 filas  â†’  2.400 filas
12 columnas  â†’  12 columnas
441 nulos    â†’  0 nulos
```

Es decir: **tirÃ³ filas y rellenÃ³ huecos.** Esa es la limpieza que se suele imaginar, y es la
que el curso evalÃºa.

---

## 4. En MinerÃ­aProtect: los mismos conceptos, otra realidad

El proyecto tiene la misma estructura â€”personas con su historial laboralâ€” pero el problema es
distinto. AquÃ­ no hay basura que se genera: hay **hechos que parecen errores y no lo son**.

| | TelecomUNO (curso) | MinerÃ­aProtect (proyecto) |
|---|---|---|
| Archivo de entrada | 2.460 Ã— 12 | 376.567 Ã— 17 |
| Archivo de salida | 2.400 Ã— 12 | **376.567 Ã— 20** |
| **Filas eliminadas** | **60** | **0** |
| **Columnas agregadas** | 0 | **3** |
| Datos faltantes | 441 celdas dispersas | 42.807, todas en la misma columna |
| Filas repetidas | 60 | 0 |
| Valor extremo raro | 616 GB en un mes | una carrera de 40 aÃ±os |

**Lee la tabla con calma: el pipeline entra con 376.567 filas y sale con 376.567.**
No se borra ni una sola. Lo Ãºnico que hace es **aÃ±adir tres columnas**.

Eso no significa que no hubo limpieza. Significa que la limpieza ya se hizo antes, en el
momento en que se unieron las fuentes. Cuando el archivo llega a esta etapa ya estÃ¡
estructuralmente bien. Lo que queda son cosas que no se pueden borrar porque son verdad.

---

## 5. Los conceptos, uno por uno

### 5.1 Datos faltantes: importan mÃ¡s *por quÃ©* que cuÃ¡ntos

Cuando falta un dato siempre hay que preguntarse **por quÃ© falta**. No es lo mismo:

- Falta porque **nadie lo anotÃ³** â†’ el dato no significa nada, se puede ignorar.
- Falta porque **la persona no tiene ese dato** â†’ es informaciÃ³n vÃ¡lida.
- Falta porque **el sistema no lo guardÃ³** â†’ informaciÃ³n que existe pero se perdiÃ³.

La cifra sola no sirve. En el proyecto hay 42.807 celdas sin nivel educativo. Una celda dice
"no sabemos el nivel educativo de esta experiencia" â€” y eso ya es una afirmaciÃ³n. La
decisiÃ³n no fue inventar un nivel, fue **registrar la ausencia como una categorÃ­a propia**.

### 5.2 Los tres tipos de dato faltante (MCAR, MAR, MNAR)

Es el concepto central de la sesiÃ³n y vale la pena entenderlo de verdad.

- **MCAR** â€” *faltante completamente al azar.* No tiene nada que ver con nada. Ejemplo: un
  sensor que se cayÃ³ ese dÃ­a. Se puede descartar sin miedo.
- **MAR** â€” *faltante al azar.* Falta por una razÃ³n que **sÃ­** conocemos. Ejemplo: falta la
  fecha de fin solo en los empleos que **siguen vigentes** â€” claro, si el empleo no ha
  terminado, no hay fecha de fin.
- **MNAR** â€” *faltante no al azar.* Falta por una razÃ³n **que estÃ¡ justo en el dato que
  falta**. Ejemplo: en una encuesta de ingresos, quienes ganan menos responden menos. El
  dato falta *porque* del valor que falta.

**Por quÃ© importa:** con MCAR y MAR se puede rellenar con el valor mÃ¡s comÃºn. Con MNAR, rellenar
con el valor mÃ¡s comÃºn **fabrica datos que no existen** y ademÃ¡s sesga todo lo demÃ¡s.

### 5.3 Rellenar (imputar) vs. marcar (bandera)

Las dos formas de tratar un hueco:

| | Rellenar | Marcar |
|---|---|---|
| QuÃ© hace | Ponle un valor inventado | Ponle "no lo sÃ©" como categorÃ­a propia |
| Gana | El archivo queda completo | No se inventa nada |
| Pierde | Se fabrican datos que nadie vivio | El archivo tiene una categorÃ­a mÃ¡s |

El proyecto **no rellena nada**. Usa la segunda. Por eso el archivo sale con 20 columnas en
vez de 17.

### 5.4 Filas repetidas: no es lo mismo "repetida" que "parecida"

Hay dos preguntas distintas y se contestan distinto:

1. **Â¿Es la misma fila dos veces?** â†’ se borra una. En el proyecto: **0 casos**.
2. **Â¿Es la misma persona dos veces?** â†’ puede ser verdad, no es un error. En el proyecto:
   hay 18.749 personas con lo que se llama **clave corta** â€” misma persona, mismas fechas,
   pero con dos ocupaciones distintas.

Ese segundo caso es **pluriempleo**: alguien que tuvo dos trabajos a la vez. Es informaciÃ³n
valiosa sobre el mercado laboral. Si se borrara, estarÃ­as borrando el hecho de que hay
personas con dos empleos.

### 5.5 Valores extremos: el dato raro puede ser el mÃ¡s verdadero

Este es el punto que mÃ¡s se confunde, y el proyecto lo maneja de forma distinta al curso.

La estadÃ­stica detecta valores "raros" con reglas automÃ¡ticas. Las reglas sirven para
**seÃ±alar**, nunca para **decidir**. Cada vez que una regla marca un valor raro hay que
preguntarse: *Â¿esto es un error de captura o es alguien con un caso especial?*

El caso del proyecto lo deja clarÃ­simo:

- La regla estadÃ­stica dice: *una duraciÃ³n de mÃ¡s de **24,5 trimestres** (unos 6 aÃ±os) es un
  valor extremo.*
- Pero el trabajo mÃ¡s largo del dataset dura **160 trimestres = 40 aÃ±os**.
- Â¿Un empleado que se quedÃ³ 40 aÃ±os en un lugar es un error? No. Es la persona mÃ¡s estable
  de todo el archivo.

**35.477 filas** quedan fuera de ese umbral. **Ninguna se borrÃ³.** Todas se conservaron.

Y se hizo una segunda cosa: se creÃ³ un archivo aparte, `empleos_limpio_sin_outliers.csv`, que
sÃ­ quita esa cola larga, para poder comparar los dos escenarios. **No se decide
destruyendo; se decide teniendo las dos versiones y viendo la diferencia.**

### 5.6 CÃ³mo se calcula el umbral (IQR)

Sin detalles matemÃ¡ticos: se toman las duraciones, se ordena de menor a mayor, se calcula un
rango "normal" que cubre la mitad de los datos, y se considera raro lo que se sale de Ã©l
hacia arriba. En el proyecto ese lÃ­mite quedÃ³ en 24,5 trimestres.

Un detalle que conviene ver: **un umbral calculado sobre la mitad central de los datos
ignora que la cuarta parte de la poblaciÃ³n dura mÃ¡s de 6 aÃ±os.** Por eso una regla
estadÃ­stica automÃ¡tica, aplicada sola, produce un "error" en una de cada cinco filas. Las
reglas sirven para mirar, no para borrar.

---

## 6. CÃ³mo estÃ¡ organizado el pipeline

El archivo `scripts/pipeline/limpieza/limpiar_empleos.py` hace el trabajo en **siete pasos**, siempre en
el mismo orden:

| Paso | QuÃ© hace | Por quÃ© en ese orden |
|---|---|---|
| 1 Â· DiagnÃ³stico | Mide el archivo antes de tocarlo | No puedes saber si mejoraste algo si no sabes cÃ³mo estaba |
| 2 Â· Duplicados | Verifica que no haya repetidas | Primero lo que rompe la llave del archivo |
| 3 Â· CategorÃ­as | Revisa que los valores posibles sean los esperados | Antes de rellenar, hay que saber quÃ© categorÃ­as hay |
| 4 Â· Faltantes | Crea las 3 banderas | Agregar informaciÃ³n, nunca quitarla |
| 5 Â· Outliers | Mide y **registra** la cola larga | Se mide antes de decidir |
| 6 Â· ValidaciÃ³n | Comprueba 10 reglas contra nÃºmeros fijos | Si algo no cuadra, el script se detiene |
| 7 Â· Exportar | Escribe el resultado y **verifica que el original no cambiÃ³** | La regla de oro: el archivo de entrada jamÃ¡s se toca |

**Lo importante del paso 6:** el script lleva dentro los nÃºmeros exactos que deberÃ­a encontrar
(376.567 filas, 71.061 personas, 0 duplicadosâ€¦). Si un dÃ­a el resultado es 376.568, el
script **se detiene y avisa**, en vez de seguir adelante con un nÃºmero que nadie revisÃ³.
Eso es lo que hace que los datos sean confiables.

---

## 7. Lo que tu pipeline NO hizo, y por quÃ©

Esta es la parte que vale la pena estudiar, porque es la diferencia entre un curso y un
proyecto real.

| No lo hizo | Por quÃ© |
|---|---|
| **No borrÃ³ ninguna fila** | No habÃ­a nada que borrar. Las 376.567 entran y salen. |
| **No rellenÃ³ ningÃºn dato faltante** | Rellenar 42.807 niveles educativos habrÃ­a inventado la formaciÃ³n de miles de personas. PrefiriÃ³ decir "no lo sÃ©". |
| **No quitÃ³ las carreras largas** | 40 aÃ±os en un empleo no son un error. Quitarlas habrÃ­a eliminado a las personas mÃ¡s estables del archivo y el modelo habrÃ­a aprendido que nadie se queda. |
| **No borrÃ³ las claves cortas** | Esas 18.749 personas tenÃ­an dos empleos a la vez. Es informaciÃ³n, no duplicado. |

**Todo lo que hizo fue aÃ±adir 3 columnas:**

| Columna nueva | QuÃ© dice |
|---|---|
| `es_vigente` | Esta persona **sigue** en ese trabajo (no tiene fecha de fin) |
| `es_unknown_ocupacion` | El sistema no pudo identificar a quÃ© oficio corresponde |
| `es_rescatado` | La ocupaciÃ³n se pudo deducir de otra fuente |

**La diferencia de fondo:** la limpieza del curso *quita*. La limpieza de este proyecto
*agrega*. En vez de responder "Â¿quÃ© borro?", responde "Â¿quÃ© informaciÃ³n estaba escondida
aquÃ­ y conviene sacar a la luz?".

---

## 8. Lo que el curso pide y aquÃ­ NO aplica

Esta secciÃ³n es una convenciÃ³n del proyecto: cuando el ejercicio del curso no se puede
aplicar tal cual, se dice cuÃ¡l es el motivo. Sin esto, alguien compararÃ­a la guÃ­a del
profesor con el proyecto y pensarÃ­a que estÃ¡ mal hecho.

| Lo que pide el curso | Por quÃ© aquÃ­ no aplica |
|---|---|
| **Borrar filas duplicadas** | Ya no hay. 0 duplicados exactos y 0 por llave natural. La limpieza se hizo antes, al integrar las fuentes. |
| **Rellenar datos faltantes con el valor mÃ¡s comÃºn** | AquÃ­ eso fabricarÃ­a datos. El proyecto crea la categorÃ­a "no reportado" en vez de rellenar. |
| **Quitar los valores extremos** | Se conservaron, y ademÃ¡s se creÃ³ una segunda versiÃ³n sin ellos para poder comparar. |
| **Dejar el archivo con el mismo nÃºmero de filas** | AquÃ­ es al revÃ©s: las filas son las mismas pero **se suman 3 columnas**. |

**Y un caso curioso:** el curso busca el texto literal `"None"` dentro de una columna para
detectar datos faltantes. En la versiÃ³n actual del proyecto ese texto **ya no existe**
(0 apariciones): todo lo que falta son celdas realmente vacÃ­as. Antes eran 174.036; hoy, 0.
Es un buen ejemplo de que un mismo archivo de cÃ³digo puede tener que cambiar aunque nada
del mÃ©todo haya cambiado.

---

## 9. QuÃ© ya estÃ¡ hecho

Esto no es un plan de trabajo: **ya estÃ¡ hecho y verificado.**

- âœ… Fuentes limpias (`limpiar_datos.py`)
- âœ… IntegraciÃ³n de las fuentes (`integrar_empleos.py`)
- âœ… Pipeline de 7 fases sobre el archivo integrado (`limpiar_empleos.py`)
- âœ… VersiÃ³n alternativa sin la cola larga (`dividir_por_outliers.py`)
- âœ… ValidaciÃ³n final: **10 de 10 reglas verificadas**
- âœ… Cuaderno que lo reproduce todo con la evidencia impresa: `notebooks/3.0_preprocesamiento.ipynb`

**Resultado:** `empleos_limpio.csv`, con **376.567 filas Ã— 20 columnas**, de **71.061 personas**.

La limpieza estÃ¡ **terminada al 100 %**.

---

## 10. Lo que sigue

La sesiÃ³n 4 es la continuaciÃ³n directa: ya no se limpian datos, se los **transforma** para
que un modelo pueda entenderlos.

```plaintext
Archivo limpio (376.567 Ã— 20, con textos y fechas)
              â”‚
              â”‚  â† sesiÃ³n 4: se convierte todo a nÃºmeros
              â–¼
Matriz de caracterÃ­sticas (X) â€” solo nÃºmeros, misma informaciÃ³n
              â”‚
              â–¼
Listo para los modelos de las sesiones 7-9
```

Los pasos de la sesiÃ³n 4: convertir categorÃ­as en nÃºmeros (one-hot), **escalar** para que
nada domine por estar en grande, y reducir dimensiones si hay demasiadas.

Y despuÃ©s, el paso que la limpieza dejÃ³ preparado: **armar las secuencias por persona**,
que es el verdadero objetivo del proyecto â€” no es "una fila por persona", sino **la lÃ­nea de
tiempo de su carrera**.

---

## 11. Errores frecuentes

Los que se repiten cuando alguien retoca este pipeline:

| âŒ Error | âœ… Correcto |
|---|---|
| Borrar la cola larga de duraciones | Se conserva y se compara aparte |
| Rellenar los niveles educativos con "el mÃ¡s comÃºn" | Crear la categorÃ­a "no reportado" |
| Tratar las claves cortas como duplicados | Son pluriempleo: informaciÃ³n real |
| Editar `empleos.csv` a mano | Es la entrada canÃ³nica y **jamÃ¡s** se modifica; todo se deriva de ella |
| Cargar los cÃ³digos con nÃºmeros | Hay que leerlos como texto, o se pierden los ceros iniciales (`0043` se vuelve `43`) |
| Cambiar una cifra sin actualizar el script | El script tiene los nÃºmeros esperados dentro: si cambias uno sin el otro, se detiene |

---

## En una frase

**El curso enseÃ±a a tirar datos; MinerÃ­aProtect enseÃ±a a no tirar nada** â€” y a poner
banderas donde el curso pondrÃ­a huecos, porque un dato raro puede ser la persona mÃ¡s
interesante del archivo.



# contexto_sesion4.md

# SesiÃ³n 4 Â· TransformaciÃ³n y reducciÃ³n de datos

> **Para quÃ© sirve este documento.** Explica la sesiÃ³n 4 del curso (*TransformaciÃ³n y
> ReducciÃ³n de Datos*) aplicada a **MinerÃ­aProtect**. EstÃ¡ escrito para alguien que ya tiene
> los datos pero **no programador**.
>
> **No es un manual de cÃ³digo.** AquÃ­ se entiende por quÃ© hay que convertir los datos en
> nÃºmeros, por quÃ© hay que ponerlos todos en la misma escala, y quÃ© pasa si no se hace. Es
> la sesiÃ³n donde se ve, de forma dramÃ¡tica, **que un error de escala arruina todo el
> anÃ¡lisis**.
>
> **Las cifras son las vigentes** (las del `README.md` a septiembre de 2026). Si alguna vez
> oyes un nÃºmero como "1.506.445 filas" o "174.036 nulos", ese es de una versiÃ³n anterior
> del proyecto que ya no se usa.

---

## 1. La idea

La sesiÃ³n 3 terminÃ³ con un archivo limpio: 376.567 filas, 20 columnas, sin datos faltantes.
Todo listo. **Y sin embargo, todavÃ­a no se puede analizar nada.**

Â¿Por quÃ©? Porque el archivo todavÃ­a tiene cosas que un algoritmo no sabe manejar:

- **Texto.** "Directivo de empresa" no es un nÃºmero. No se puede comparar con "Cocinero"
  buscando cuÃ¡l es mayor.
- **Fechas.** Una fecha de inicio y una fecha de fin no son un valor: son dos cosas que
  juntas producen una duraciÃ³n.
- **Columnas con Units distintas.** El nÃºmero de competencias va de 4 a 99. El aÃ±o de inicio
  va de 1990 a 2026. La duraciÃ³n va de 1 a 160 trimestres.

**La transformaciÃ³n de datos es convertir todo eso en nÃºmeros que sÃ­ se puedan comparar**, sin
perder ni un bit de la informaciÃ³n original. No es una etapa distinta de la limpieza: es la
Ãºltima parte de la preparaciÃ³n.

**La idea mÃ¡s importante de toda la sesiÃ³n, y la que mÃ¡s caro sale si se olvida:**

> Cuando dos columnas viven en escalas distintas, **la mÃ¡s grande se apodera de todas las
> comparaciones**. No porque tenga mÃ¡s importancia, sino porque sus nÃºmeros son mÃ¡s grandes.

---

## 2. Cuatro palabras que hay que saber

| Palabra | QuÃ© es, en serio |
|---|---|
| **Escalar** | Poner varias columnas en la misma escala, para que sean comparables. |
| **One-hot** | Convertir una categorÃ­a en varias columnas de sÃ­/no. "Oficio = cocinero" se vuelve una columna con 1 si lo es y 0 si no. |
| **Ordinal** | Convertir una categorÃ­a que **sÃ­ tiene orden** en un nÃºmero que respeta ese orden. |
| **Distancia** | CÃ³mo se mide quÃ© tan lejos estÃ¡n dos cosas. Es lo que usan los algoritmos para agrupar. |

---

## 3. En el curso: por quÃ© hay que escalar

El curso lo demuestra con un caso demoledor. Toma dos clientes de una operadora, calcula
"cuÃ¡nto se parecen" usando las columnas numÃ©ricas, y la distancia le da:

```
42.550,3
```

Es una distancia enorme. Pero ese nÃºmero casi no significa nada: **estÃ¡ dominado por la
columna de facturaciÃ³n**, que tiene valores en las decenas de miles de miles, mientras que la
columna de minutos de llamada anda por decenas.

DespuÃ©s de poner todo en la misma escala, la distancia entre esos mismos dos clientes baja a:

```
0,829
```

**No es que los clientes se hayan vuelto mÃ¡s parecidos.** Es que la pregunta dejÃ³ de estar
contaminada por la columna mÃ¡s grande. La distancia "0,829" sÃ­ significa algo; la distancia
"42.550,3" no.

### 3.1 El orden correcto, que el curso repite como regla

```plaintext
Limpiar  â†’  Codificar  â†’  Escalar  â†’  (PCA)  â†’  Modelar
```

Este orden **no es una sugerencia, es una regla**. Y tambiÃ©n al revÃ©s:

- No se escala antes de limpiar: se escala basura.
- No se modela antes de escalar: el modelo agrupa por la columna equivocada.
- No se codifica despuÃ©s de escalar: una columna de texto no se puede escalar.

### 3.2 Los tres escaladores y cuÃ¡ndo se usa cada uno

| Escalador | QuÃ© hace | CuÃ¡ndo |
|---|---|---|
| **MinMax** | Cada valor se convierte a un nÃºmero entre 0 y 1. | Cuando el rango estÃ¡ acotado y no hay valores extremos. |
| **Standard** | Se resta el promedio y se divide por la desviaciÃ³n. Queda centrado en 0. | Cuando los datos se reparten parejo. |
| **Robust** | Se centra usando la **mediana** en vez del promedio. | **Cuando hay valores extremos** â€” y no los elimina, los deja de torcer la medida. |

**Robust existe por una razÃ³n concreta:** el promedio lo mueven unos pocos valores extremos.
La mediana no. Si una fila tiene 160 trimestres y todas las demÃ¡s andan por 2, el promedio se
sube, pero la mediana se queda donde estÃ¡.

**Y hay una tensiÃ³n real en el curso:** la sesiÃ³n 3 pide conservar la cola larga de duraciones
porque son personas reales, y luego la sesiÃ³n 4 dice que hay que usar el escalador robusto
porque hay valores extremos. **Las dos cosas son ciertas al mismo tiempo**, y por eso
`Robust` es el que corresponde: no borra los valores raros, solo deja que no contaminen la
escala.

---

## 4. En MinerÃ­aProtect: dos versiones, y por quÃ©

La transformaciÃ³n se hizo **dos veces**, sobre dos archivos distintos:

| Cuaderno | Sobre quÃ© archivo | Resultado |
|---|---|---|
| `4.0_transformacion.ipynb` | El limpio completo (376.567 filas) | La versiÃ³n con la cola larga conservada |
| `4.1_transformacion_sin_outliers.ipynb` | El limpio **sin** la cola larga (341.090 filas) | La versiÃ³n comparable |

**La razÃ³n de tener las dos** estÃ¡ en `dividir_por_outliers.py`. En la sesiÃ³n 3 se decidiÃ³
**conservar** las carreras de hasta 40 aÃ±os porque son personas reales. Pero para elegir la
tÃ©cnica de minerÃ­a hace falta saber **cuÃ¡nto cambia el resultado** si esas carreras estÃ¡n o
no. Por eso el script corta el archivo en dos: uno con todo, otro sin la cola larga, y permite
cruzar los dos y medir el impacto.

**Conservar y comparar. No decidir a ciegas ni destruir a ciegas.** Es el mismo criterio de la
sesiÃ³n 3, aplicado a una decisiÃ³n que aÃºn no estÃ¡ tomada.

---

## 5. El paso 1: de texto a nÃºmeros

### 5.1 La ocupaciÃ³n: una-hot, porque no tiene orden

La columna `occupation_code` tiene **2.855 valores distintos**. Â¿CÃ³mo se convierte eso a
nÃºmeros?

**La respuesta: NO se convierte.** Se expande. Por cada ocupaciÃ³n se crea una columna que
vale 1 si esa fila es esa ocupaciÃ³n, y 0 si no.

```plaintext
Si la ocupaciÃ³n es "0110.10" (directivo de empresa):

  occupation_0110.10 = 1
  occupation_0110.11 = 0
  occupation_0110.12 = 0
  ... y asÃ­ para las otras 2.854
```

**Â¿Por quÃ© no se le asigna un nÃºmero del 1 al 2.855?** Porque **no hay ningÃºn orden entre las
ocupaciones**. Si "cocinero" fuera 5 y "director" fuera 900, el algoritmo leerÃ­a eso como
"director estÃ¡ mucho mÃ¡s cerca de cocinero que de panadero", y no tiene ningÃºn sentido. Es
el error clÃ¡sico de codificar categorÃ­as con nÃºmeros sin darse cuenta.

**El precio que se paga:** una columna se convierte en mÃ¡s de dos mil. En el cuaderno, que
trabaja sobre una **submuestra de 50.000 filas** (para que el cuaderno no se demore horas), el
resultado son **2.316 columnas de ocupaciÃ³n**. Sobre el archivo completo serÃ­an unas 2.800,
porque los 50.000 ejemplos no alcanzan a cubrir los 2.855 oficios que hay.

Por eso el cuaderno tiene una secciÃ³n que se llama literalmente **"auditorÃ­a de redundancia"**:
antes de expandir, se revisa si todas esas categorÃ­as sirven o si algunas sobran.

### 5.2 El nivel educativo: ordinal, porque sÃ­ tiene orden

| Columna | Tipo | RazÃ³n |
|---|---|---|
| `occupation_code` | **One-hot** (una columna por oficio) | No hay jerarquÃ­a entre oficios |
| `university_level` | **Ordinal** (una sola columna) | Hay jerarquÃ­a real: bÃ¡sico < medio < alto < universitario |
| `emparejado` | **Una sola columna** (`emparejado_ok`) | Dice si el cÃ³digo se emparejÃ³ tal cual o hubo que rescatarlo. Las otras 3 seÃ±ales ya estÃ¡n en las banderas |
| `esco_level` | **Se descarta** | Es una constante: el mismo valor en todas las filas. No aporta nada |

**Sobre `esco_level`:** una columna donde todas las filas dicen lo mismo no dice nada. Es
ruido con forma de dato, y por eso el cuaderno la elimina. Es un ejemplo de que **no toda
columna merece entrar**, aunque exista.

### 5.3 Las fechas: el curso y su mÃ©todo

Las fechas se manejan de tres formas, y el cuaderno las muestra:

- **Como nÃºmero de trimestre.** 2020-Q3 se convierte en un nÃºmero. Es la base de la
  secuencia.
- **Como duraciÃ³n.** `dur_q = trimestre_final - trimestre_inicial`. ("Esta persona estuvo
  5 trimestres en este trabajo.")
- **Como rangos (KBins).** Este es **el mÃ©todo literal del curso**: se agrupan las fechas en
  pocas franjas en vez de dejar cada fecha suelta. Menos columnas, menos ruido.

**Un detalle importante que el cuaderno anota:** como la duraciÃ³n se calcula **restando** el
inicio del final, hay informaciÃ³n que se repite por tres lados. Si cambias la fecha de fin,
cambian tres columnas a la vez. Por eso estÃ¡ la auditorÃ­a de redundancia.

---

## 6. El paso 2: poner todo en la misma escala

AquÃ­ estÃ¡ el corazÃ³n de la sesiÃ³n. El proyecto tomÃ³ **una decisiÃ³n distinta para cada
columna**, y el cuaderno lo justifica una por una.

| Columna | Escalador | RazÃ³n |
|---|---|---|
| `start_ord`, `end_ord`, `dur_q` (trimestres) | **Robust** | Tienen la cola larga de las carreras de hasta 40 aÃ±os |
| `n_skills_essential` (4 a 99) | **Robust** | DistribuciÃ³n asimÃ©trica, con gente que tiene oficios muy exigentes |
| `veces_ese_oficio` (1 a 19) | **Robust** | Casi todos valen 1; unos pocos valen 19. El promedio la arruinarÃ­a |
| `university_level` | **MinMax** | Rango acotado y limpio: queda entre 0 y 1 |
| `reincide` (sÃ­/no) | **Sin escalar** | Ya es 0 o 1. Escalarlo serÃ­a una operaciÃ³n sobre sÃ­ misma |

**La Ãºltima fila es la que hay que entender:** escalar una columna que ya estÃ¡ entre 0 y 1 no
tiene sentido. Es como preguntar cuÃ¡ntos metros mide un metro.

### 6.1 Y la prueba de que se hizo bien

Un escalador no se aplica a ciegas: **se comprueba que hizo lo que tenÃ­a que hacer.**

- Con **Robust**, la mediana de cada columna debe quedar en **0**. Resultado: `[0.0, 0.0, 0.0]`. âœ“
- Con **MinMax**, el mÃ­nimo y el mÃ¡ximo deben quedar en **0** y **1**. Resultado: `(0.0, 1.0)`. âœ“
- `reincide` debe seguir siendo 0 o 1. Resultado: `[0, 1]`. âœ“

**Esto es lo que distingue un pipeline de verdad de uno que solo corre:** el resultado se
comprueba contra lo que deberÃ­a ser. Si maÃ±ana cambia algo y la mediana ya no da 0, el
cuaderno lo muestra.

### 6.2 La demostraciÃ³n que hay que ver

El cuaderno hace la misma prueba que el curso, y el resultado es aÃºn mÃ¡s claro. Toma **siete
columnas sin escalar** y calcula cuÃ¡nto aporta cada una a la distancia entre dos personas
cualesquiera:

| Columna | Aporte a la distancia |
|---|---|
| Trimestre de inicio | **42,94 %** |
| Trimestre de fin | **38,00 %** |
| DuraciÃ³n | 10,78 % |
| Competencias del cargo | 8,19 % |
| Las otras tres | 0,05 % Â· 0,03 % Â· 0,01 % |

**Las dos fechas aportan el 80,9 % de la distancia. Las otras cinco columnas, el 19,1 %.**

Y el cuaderno escribe la conclusiÃ³n en una lÃ­nea:

> **Sin escala, KNN y k-means agruparÃ­an por CALENDARIO, no por carrera.**

PiÃ©nsalo: el algoritmo que todavÃ­a no se ha aplicado **ya sabemos que interpretarÃ­a mal los
datos**. No agruparÃ­a personas con trayectorias similares: agruparÃ­a gente que trabajÃ³ en los
mismos aÃ±os. Como el mercado de trabajo cambia con las dÃ©cadas, eso es un error gravÃ­simo.

**Este es el motivo por el que escalar no es opcional, un detalle de estilo ni una buena
prÃ¡ctica. Es la diferencia entre un anÃ¡lisis que significa algo y uno que no.**

---

## 7. El paso 3: la auditorÃ­a de redundancia y la pregunta por PCA

### 7.1 Â¿Y PCA?

El curso enseÃ±a PCA como el paso opcional entre escalar y modelar. El cuaderno lo aplica, y
antes de aplicarlo **se pregunta si tiene sentido**.

Resultado: a PCA entran **6 columnas numÃ©ricas**. Las miles de columnas del one-hot de
ocupaciÃ³n **no entran**, porque son indicadores de sÃ­/no y no tienen sentido en un anÃ¡lisis de
componentes.

**Y con 6 columnas, PCA aporta poco.** La reducciÃ³n de dimensiÃ³n tiene sentido cuando hay
cientos de columnas que describen lo mismo. Con seis, casi no hay nada que comprimir. La
respuesta del cuaderno es midir, imprimir la varianza explicada, y **dejar la decisiÃ³n
documentada** en vez de aplicarla por costumbre.

**Esa es la postura correcta ante cualquier tÃ©cnica: no se aplica porque el curso la enseÃ±a,
sino porque los datos la necesitan.**

### 7.2 El problema de la redundancia que sÃ­ importa

Como `dur_q` se calcula restando el inicio del final, **tres columnas guardan parte de la
misma informaciÃ³n**. Cambiar la fecha de fin cambia las tres.

Eso no es un error: es una propiedad de los datos que hay que conocer y dejar escrita. El
cuaderno tiene una secciÃ³n entera (`1.1 VerificaciÃ³n de los descartes`) dedicada a esto. Un
anÃ¡lisis serio no esconde lo que no sabe de sus propias columnas.

---

## 8. El punto incÃ³modo: 28.304 filas que quedan fuera

La transformaciÃ³n tiene un costo, y el proyecto lo documenta en vez de esconderlo.

El problema estÃ¡ en las competencias. Cuando **no se pudo identificar la ocupaciÃ³n** de una
fila, sus contadores de competencias **quedan vacÃ­os** â€” y vacÃ­os, nunca cero. Y hay una
razÃ³n de fondo para no ponerles cero:

> Un 0 affirmarÃ­a que **ese cargo no exige ninguna competencia**, lo cual es falso. No sabemos
> quÃ© cargo es; no sabemos quÃ© exige.

El problema es que la librerÃ­a de modelos **no acepta huecos**: si hay un vacÃ­o, se niega a
trabajar. Las dos reglas chocan, y hay que romper una.

**Lo que hizo el proyecto:** romper la regla de "no dejar filas fuera" y quedarse con las
que sÃ­ se pueden transformar. El resultado:

| | Filas | Porcentaje |
|---|---|---|
| Entrada | 376.567 | 100 % |
| **Salida** | **348.263** | 92,5 % |
| Descartadas | 28.304 | 7,5 % |

**Y lo importante: se comprobÃ³ que las filas descartadas son exactamente las mismas que
tienen la ocupaciÃ³n sin identificar.** La coincidencia es exacta. Eso significa que no se
perdiÃ³ nada por accidente: se descartÃ³ **precisamente** lo que no se podÃ­a transformar, y
solo eso.

**Lo que habrÃ­a que decir en un informe:** la transformaciÃ³n trabaja con el 92,5 % de las
filas, y ese 92,5 % es todo lo que tiene ocupaciÃ³n identificada. La conclusiÃ³n sobre el
universo es "esto aplica a las experiencias con ocupaciÃ³n reconocida".

---

## 9. El resultado final

```plaintext
ARCHIVO LIMPIO
376.567 filas x 20 columnas   |   71.061 personas
        â”‚
        â”‚  quitar 28.304 filas sin ocupaciÃ³n identificada  (-7,5 %)
        â–¼
348.263 filas que sÃ­ se pueden transformar
        â”‚  codificar   ocupaciÃ³n â†’ una columna por oficio  (one-hot)
        â”‚              nivel edu â†’ 1 columna                (ordinal)
        â”‚              banderas es_* â†’ 3 columnas
        â”‚  escalar     Robust  â†’ 5 columnas numÃ©ricas
        â”‚              MinMax  â†’ nivel educativo
        â”‚              sin tocar â†’ reincide
        â–¼
MATRIZ DE CARACTERÃSTICAS (X)
Todo nÃºmero, sin nulos
Sobre la submuestra de 50.000 filas: 2.327 columnas
(2.316 de ocupaciÃ³n + 11 de lo demÃ¡s)
        â”‚
        â–¼
Lista para los modelos de las sesiones 7-9
```

**Las verificaciones que tiene que pasar** (y pasa):

- Sin nulos
- Sin columnas de texto: todo es nÃºmero
- Mediana en 0 en las columnas Robust, en 0 y 1 en la MinMax
- AuditorÃ­a de outliers y de varianza de PCA imprimidas en vivo

**Y el dato de las reincidencias**, que se calcula de paso: **106.250 filas (30,5 %)**
corresponden a alguien que repite el mismo oficio. Son **32.400 personas**. Es decir, **casi
una de cada tres filas del archivo es de alguien que ya habÃ­a estado en ese mismo cargo.**

Ese es el tipo de hallazgo que la sesiÃ³n 3 hizo posible: no se borraron las repeticiones, se
contaron.

---

## 10. Lo que el curso pide y aquÃ­ no aplica

| Lo que pide el curso | Por quÃ© aquÃ­ no aplica |
|---|---|
| Escalar las 11 columnas de TelecomUNO | AquÃ­ se escala **una por una y con una razÃ³n distinta para cada una**. |
| Aplicar PCA porque es el paso del mÃ©todo | Se pregunta primero si sirve. Con 6 columnas numÃ©ricas, aporta poco. Se mide y se documenta. |
| Dejar todas las filas | AquÃ­ salen fuera 28.304, y se comprueba que son exactamente las que no se pueden transformar. |
| Codificar la ocupaciÃ³n como nÃºmero | AquÃ­ es una columna por oficio, porque son 2.855 oficios sin jerarquÃ­a entre ellos |
| Usar el mismo escalador para todo | El proyecto usa tres distintos, cada uno con su justificaciÃ³n. |

---

## 11. QuÃ© ya estÃ¡ hecho

- âœ… AnÃ¡lisis de redundancia previo a expandir
- âœ… CodificaciÃ³n one-hot de la ocupaciÃ³n (una columna por oficio)
- âœ… CodificaciÃ³n ordinal del nivel educativo
- âœ… Columnas constantes detectadas y descartadas
- âœ… Escalado con tres mÃ©todos distintos, uno por tipo de columna
- âœ… Escalado verificado (medianas en 0, rangos en 0-1)
- âœ… AuditorÃ­a de quÃ© aporta cada columna a la distancia (el 80,9 %)
- âœ… PCA auditado, con la varianza explicada a la vista
- âœ… Las 28.304 filas descartadas, con la coincidencia verificada
- âœ… **Dos versiones completas** para comparar el efecto de la cola larga

**Archivos:** `notebooks/4.0_transformacion.ipynb` y `4.1_transformacion_sin_outliers.ipynb`.

**Resultado: la transformaciÃ³n estÃ¡ terminada.** La matriz de caracterÃ­sticas estÃ¡ lista para
que en las sesiones siguientes se le apliquen los modelos.

---

## 12. Lo que sigue

```plaintext
Archivo limpio
      â”‚  â† sesiÃ³n 4 (esta)
      â–¼
Matriz de caracterÃ­sticas (X)      348.263 filas, miles de columnas, solo nÃºmeros
      â”‚
      â”‚  â† sesiÃ³n 5: mirarla con calma (EDA)
      â”‚  â† sesiones 7-9: aplicarle un modelo
      â–¼
Patrones de transiciÃ³n ocupacional    â† el objetivo del proyecto
```

Y antes de llegar a los modelos hay un paso que el proyecto tiene pendiente y que es el
siguiente de verdad: **armar las secuencias por persona**. Porque el objetivo no es
"analizar una fila", es "analizar la lÃ­nea de tiempo de una carrera". Y una fila suelta, sin
la fila anterior de la misma persona, no dice nada.

---

## 13. Errores frecuentes

| âŒ Error | âœ… Correcto |
|---|---|
| No escalar, porque "las columnas ya estÃ¡n en nÃºmeros" | Escalar no es opcional. Sin eso, el 80,9 % de la distancia lo deciden las fechas |
| Usar el mismo escalador para todas las columnas | Una decisiÃ³n por columna, con su razÃ³n escrita |
| Codificar la ocupaciÃ³n con nÃºmeros del 1 al 2.855 | One-hot: no hay jerarquÃ­a entre oficios |
| Aplicar PCA porque el curso lo enseÃ±a | Preguntar primero si los datos lo necesitan |
| Poner 0 en los contadores de competencias de las filas sin ocupaciÃ³n | VacÃ­o, no cero. Un 0 afirma algo falso |
| Escalar `reincide`, que ya es 0 o 1 | No hace falta: escalar un 0 o un 1 es no hacer nada |
| Dejar una columna constante en la matriz | No dice nada. Se descarta |
| No documentar el 7,5 % que se descartÃ³ | Un informe honesto dice quÃ© quedÃ³ fuera y por quÃ© |

---

## En una frase

**Transformar los datos es volverlos comparables sin perder nada. Y el motivo por el que
esta sesiÃ³n importa mÃ¡s de lo que parece es una cifra concreta: sin escalar, el 80,9 % de
la distancia entre dos personas lo deciden las dos fechas â€” el algoritmo agruparÃ­a por
calendario en vez de por carrera.**



# presentacion.md

# SesiÃ³n 5 Â· AnÃ¡lisis Exploratorio de Datos (EDA)

*MinerÃ­a de Datos Â· UNIMINUTO IbaguÃ© Â· 2026-2*

## 1. Cuatro datasets idÃ©nticos... hasta que los grafica

## 2. Objetivos de aprendizaje

- Calcular e interpretar medidas de tendencia central, dispersiÃ³n y forma, eligiendo la apropiada segÃºn la distribuciÃ³n.
- Construir histogramas, boxplots, barras, dispersiÃ³n, mapas de calor y matrices de dispersiÃ³n con matplotlib, leyendo patrones y outliers.
- Interpretar el coeficiente de Pearson y distinguir correlaciÃ³n de causalidad con ejemplos.
- Redactar hallazgos accionables en la estructura estÃ¡ndar del informe EDA que exige el curso.

## 3. Ruta de la sesiÃ³n (Agenda)

## 4. ConexiÃ³n con sesiones anteriores Â¿pero conocemos los datos?

- Sesiones 2â€“4: cargamos, limpiamos y transformamos TelecomUNO. Sabemos que ESTÃ bien; aÃºn no sabemos QUÃ‰ dice.
- El EDA es la fase Entendimiento de los datos de CRISP-DM en estado puro y cierra el material del Avance 1.
- Hoy trabajamos con DOS datasets: telecom_clientes_limpio.csv y un nuevo vecino ibaguereÃ±o.

## 5. Â¿QuÃ© es el AnÃ¡lisis Exploratorio de Datos (EDA)?

## 6. Medidas descriptivas, tres preguntas

## 7. CorrelaciÃ³n de Pearson: fuerza y direcciÃ³n

- Ventas de helado â†‘ con ahogamientos â†‘... porque AMBOS suben en verano (variable confusora)
- MÃ¡s bomberos en el incendio â†” mÃ¡s daÃ±os: la gravedad causa ambos
- En nuestros datos: Ã¡reaâ†”arriendo r=0,62 (causal plausible); antigÃ¼edadâ†”arriendo r=âˆ’0,20 (dÃ©bil, requiere contexto)

## 8. Dataset: inmuebles_arriendo_ibague.csv

- Barrios incluidos: Multicentro, CÃ¡diz, PicaleÃ±a, Ciudad JardÃ­n, La Pola, Santa Helena, Alfonso LÃ³pez, Venecia, JordÃ¡n y CalambÃ­o, con tarifas por mÂ² distintas.
- Problemas inyectados: 10 nulos en arriendo, 8 en baÃ±os, 6 en antigÃ¼edad; 6 mansiones Ã—3,2 y 4 precios imposibles de $90.000.
- Semilla 42: cada estudiante regenera EXACTAMENTE el mismo archivo.
- Ruta: sesion5/datasets/ . Generador: generador_inmuebles.py .

## 9. Histograma: la forma de la distribuciÃ³n

- Agrupa los valores en intervalos (bins) y cuenta cuÃ¡ntos caen en cada uno: la "silueta" de la variable.
- Lectura aquÃ­: masa principal entre ~150 y ~300 mil COP, con cola derecha larga: los outliers estiran el grÃ¡fico.
- LÃ­nea roja (media 249 mil) queda a la derecha de la verde (mediana 238 mil): firma de asimetrÃ­a positiva.
- Tip: pocos bins ocultan picos; demasiados inventan ruido. 30 es buen punto de partida.

## 10. Boxplot: anatomÃ­a de cinco nÃºmeros + outliers

- Caja: el IQR, el 50% central de los datos (Q1=189 mil a Q3=291 mil). LÃ­nea: mediana.
- Bigotes: hasta 1,5Ã—IQR desde los cuartiles. Todo punto fuera del bigote se dibuja como cÃ­rculo: outlier visual.
- Lectura aquÃ­: lÃ­mite superior 444 mil y 19 puntos detectados por IQR: mansiones y errores conviven en esa nube.
- SÃºper poder: comparar grupos lado a lado (boxplot de arriendo POR BARRIO en su tarea).

## 11. Barras: contar categorÃ­as sin engaÃ±os

- Equivalente al countplot de seaborn: df["barrio"].value_counts().barh() .
- Lectura: Multicentro (112) y CÃ¡diz (104) concentran oferta; CalambÃ­o (40) es nicho. Amoblado: minorÃ­a (~29%).
- Orden SIEMPRE por frecuencia o por valor, jamÃ¡s alfabÃ©tico "porque sÃ­": el orden ya es informaciÃ³n.
- Para precio por barrio, mejor la MEDIANA: CalambÃ­o media 162 vs mediana 165 mil (los outliers distorsionan la media).

## 12. DispersiÃ³n + recta de tendencia

- Cada punto es un inmueble: Ã¡rea (x) contra arriendo (y). La recta roja ajusta por mÃ­nimos cuadrados (equivalente al regplot de seaborn).
- Lectura: r = 0,62 fuerte positivo; pendiente â‰ˆ 3 mil COP adicionales por cada mÂ² construido.
- Salta a la vista el cÃºmulo de puntos arriba-derecha (mansiones) y la franja inferior ($90.000): el describe() los escondÃ­a entre promedios; el grÃ¡fico los exhibe.
- Eso es EDA en estado puro: hipÃ³tesis visibles ANTES de cualquier modelo.

## 13. Heatmap de correlaciones y matriz de dispersiÃ³n

- Heatmap: toda la matriz de Pearson en un vistazo; rojo positivo, azul negativo.
- Lecturas clave: habitacionesâ†”banos 0,75 y habitacionesâ†”Ã¡rea 0,69 (redundancia potencial); Ã¡reaâ†”arriendo 0,62; antigÃ¼edadâ†”arriendo âˆ’0,20.
- Variables redundantes anticipan problemas de multicolinealidad en modelos lineales (lo retomaremos en regresiÃ³n).
- Matriz de dispersiÃ³n ( fig_matriz_dispersion.png ): todos los scatter cruzados + histogramas en diagonal; versiÃ³n matplotlib del pairplot de seaborn (opcional instalarla para estÃ©tica extra).

## Un grÃ¡fico es un argumento

- Ejes etiquetados CON UNIDADES ("miles de COP", "mÂ²")
- TÃ­tulo que declara el hallazgo, no el tipo de grÃ¡fico ("El Ã¡rea explica el 38% del arriendo")
- Barras arrancan en cero; anotaciones directas sobre el dato clave
- Paleta consistente y accesible (verificable en escala de grises)
- Pastel 3D: distorsiona Ã¡reas y es ilegible (ademÃ¡s, pastel solo con &lt; 5 categorÃ­as)
- Truncar el eje Y de barras para exagerar diferencias minÃºsculas
- Doble eje Y disfrazando correlaciones forzadas
- Colormap arcoÃ­ris para variables continuas: inventa fronteras falsas

## 15. Las tablas que imprime eda_inmuebles.py

- Gradiente claro norte-caribeâ†’sur: la ubicaciÃ³n vale hasta 117 mil COP mensuales entre extremos.
- El script tambiÃ©n cruza TelecomUNO: fuga 23% en plan Basico vs 13% Premium.

## 16. Cuando mirar antes de modelar evitÃ³ desastres

## 17. Ejercicio en clase: informe EDA de TelecomUNO

- (5 min) Univariado: describe() de las numÃ©ricas + skew de facturacion_mensual y gb_datos. Identifiquen las 2 asimetrÃ­as mÃ¡s marcadas.
- (8 min) Histograma y boxplot de facturacion_mensual; cuantifiquen los outliers con IQR (no solo "se ven raros").
- (7 min) Barras de ciudad y tipo_plan + tabla de tasa de fuga por segmento con pd.crosstab(normalize="index") .
- (8 min) DispersiÃ³n antiguedad_meses vs facturacion_mensual + heatmap de correlaciones numÃ©ricas. Â¿Alguna relaciÃ³n sorprendente?
- (7 min) Redacten 3 hallazgos en formato: hallazgo + evidencia (cifra/grÃ¡fico) + acciÃ³n sugerida para el negocio.

## 18. Criterios de Ã©xito del informe?

- Todo grÃ¡fico con tÃ­tulo-hallazgo, ejes y unidades completos
- Outliers CUANTIFICADOS con IQR, no solo seÃ±alados visualmente
- Mediana usada para reportar variables asimÃ©tricas
- Los 3 hallazgos conectan evidencia estadÃ­stica con acciÃ³n de negocio
- Graficar sin revisar tipos (fechas/categorÃ­as como texto)
- Concluir causalidad desde una correlaciÃ³n ("las quejas CAUSAN fuga")
- Describir el grÃ¡fico en vez de interpretarlo ("aquÃ­ hay barras azules...")
- Pastel con 10 categorÃ­as o efecto 3D decorativo

## 19. Informe de laboratorio

- Inicio: presenta tablas y grÃ¡ficos bÃ¡sicos con apoyo de la plantilla.
- Progreso: interpreta la mayorÃ­a de grÃ¡ficos y cuantifica algunos outliers.
- Esperado: informe completo, interpretaciones correctas y hallazgos accionables.
- Excepcional: ademÃ¡s, propone nuevas variables o segmentos y valida sus hipÃ³tesis con datos.

## 20. Trabajo independiente

- Lectura (2 h): plantilla de anÃ¡lisis exploratorio del curso + Han, Kamber &amp; Pei, secciÃ³n 2.2 (resÃºmenes descriptivos). Revise la galerÃ­a de matplotlib y guarde 2 ejemplos Ãºtiles.
- PrÃ¡ctica (2 h): extienda eda_inmuebles.py : agregue boxplot de arriendo por barrio y un grÃ¡fico propio suyo (con tÃ­tulo-hallazgo). Guarde ambas figuras.
- Proyecto (2 h): complete el borrador COMPLETO del informe EDA de su dataset con la estructura de 6 secciones exigida.

## 21. Errores comunes

## 22. Cierre

- EDA = escuchar los datos antes de modelar: univariado, bivariado y multivariado.
- Tendencia central, dispersiÃ³n y forma responden preguntas distintas; con asimetrÃ­a, la mediana manda.
- Pearson mide asociaciÃ³n lineal; correlaciÃ³n jamÃ¡s prueba causalidad.
- La galerÃ­a mÃ­nima: histograma, boxplot, barras, dispersiÃ³n, heatmap y matriz de dispersiÃ³n, todos generados con matplotlib puro.
- Con este cierre, el material tÃ©cnico del Avance 1 estÃ¡ completo.




