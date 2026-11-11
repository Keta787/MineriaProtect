# Guía para ejecutar los cuadernos del proyecto (explicada sin tecnicismos)

**Qué es esta guía.** Los "cuadernos" (archivos `.ipynb`) son documentos que
mezclan texto y código. Al abrirlos y pulsar "ejecutar", el código se pone a
funcionar y va mostrando resultados. Esta guía explica, en lenguaje normal, en
qué orden se ejecutan, qué archivos tocan y cómo hacerlo sin borrar ni estropear
nada.

---

## 1. La idea en una frase

El proyecto funciona como una **cadena de cocina**:

1. Se limpian los datos (cuaderno **2.0**).
2. Se preparan en formato numérico para el análisis (cuaderno **3.0**).
3. Se hacen dos diagnósticos rápidos de control (cuadernos **4.0** y **4.1**).
4. Se explora y se describe lo que hay (cuaderno **5.0**, el EDA).

Cada paso **usa lo que dejó el anterior**. Por eso el orden importa: si se
ejecuta el 5.0 sin haber ejecutado el 3.0, no encuentra los archivos que
necesita y falla.

```
2.0  →  3.0  →  4.0 / 4.1  →  5.0
limpiar  preparar  controlar   explorar
```

Los cuadernos 4.0 y 4.1 son opcionales: solo leen y no cambian nada. El 5.0 sí
los necesita si quieres ver las dos figuras que hablan de ellos (G23 y la tabla
G24).

---

## 2. Qué hace cada cuaderno y qué archivos toca

| Cuaderno | Qué hace, en palabras simples | ¿Toca archivos? | ¿Es peligroso? |
|---|---|---|---|
| **1.0** | Es un documento de texto con el planteamiento del trabajo. No se ejecuta. | No | No |
| **2.0** | Limpia el archivo de datos: revisa duplicados, valores vacíos y valores extremos. | **Sí**: reescribe `data\03_processed\empleos_limpio_con_competencias_sin_outliers.csv` | **Sí.** Lo reescribe sin preguntar |
| **3.0** | Convierte los datos limpios en tablas numéricas listas para analizar. Es el paso más largo. | **Sí**: reescribe los 8 archivos de `data\04_transformed` (unos 3,8 GB) y 2 archivos de configuración | **Sí.** También sin preguntar |
| **4.0** | Diagnóstico de control sobre una muestra de 10.000 filas. | No, solo lee | No |
| **4.1** | El mismo diagnóstico sobre una muestra de 50.000 filas. | No, solo lee | No |
| **5.0** | Explora los datos y genera las 28 figuras y la tabla del reparto train/test. | **Sí**, pero solo dentro de `reports\eda_jobpath\` | No. No toca `data\` |

**Conclusión práctica:** si solo quieres volver a ver el análisis y las figuras,
ejecuta **únicamente el 5.0**. Es el único que no puede estropear los datos.

---

## 3. Antes de empezar: guarda una copia

Esto es lo más importante de toda la guía. Como los cuadernos 2.0 y 3.0
sobrescriben archivos sin avisar, hay que hacer una copia antes. Es como
guardar una copia de un documento antes de editarlo.

### Paso a paso

1. Abre la carpeta del proyecto: `C:\Users\User\Documents\JobPath\MineriaProtect`.
2. Haz clic derecho en la barra de direcciones de la ventana, escribe
   `powershell` y pulsa Enter. Se abre una ventana negra donde se escriben
   órdenes.
3. Copia y pega estos cuatro bloques, uno detrás de otro, y pulsa Enter después
   de cada uno:

```powershell
cd C:\Users\User\Documents\JobPath\MineriaProtect
```

```powershell
$fecha = Get-Date -Format 'yyyy-MM-dd_HH-mm'
New-Item -ItemType Directory -Force "backup\$fecha" | Out-Null
```

```powershell
Copy-Item data\03_processed   "backup\$fecha\03_processed"   -Recurse
Copy-Item data\04_transformed "backup\$fecha\04_transformed" -Recurse
```

```powershell
Get-ChildItem data\03_processed,data\04_transformed -Recurse -File |
    Get-FileHash -Algorithm SHA256 |
    Export-Csv "backup\$fecha\huellas.csv" -NoTypeInformation
```

**Qué hace cada bloque, en simple:**

- El primero te sitúa en la carpeta del proyecto.
- El segundo crea una carpeta con la fecha y la hora de hoy dentro de `backup\`.
- El tercero copia las dos carpetas de datos (unos 4,4 GB; puede tardar varios
  minutos).
- El cuarto guarda una "huella digital" de cada archivo (un código que cambia si
  el archivo cambia). Sirve para comprobar después, sin abrirlos, si algo se
  modificó.

> Si algo va mal más adelante, con esa carpeta `backup\...` se recupera todo
> (ver el apartado 6).

---

## 4. Cómo ejecutar los cuadernos

Hay dos maneras. La primera es la más fácil y la recomendada si no tienes
costumbre.

### Opción A · Con el programa Jupyter (recomendada)

1. Abre la ventana de PowerShell en la carpeta del proyecto (como en el paso 1
   de arriba) y escribe:

   ```powershell
   jupyter notebook
   ```

   Se abrirá una página en el navegador con la lista de archivos.

2. Entra en la carpeta `notebooks`, luego en `refactor`.
3. Haz clic en el cuaderno que quieras abrir (por ejemplo
   `5.0_EDA_jobpath.ipynb`).
4. En el menú de arriba elige **Kernel → Restart & Run All** (o **Cell → Run
   All**). Eso significa "reinicia y ejecuta todo de principio a fin".
5. Espera. Verás cómo van apareciendo los resultados debajo de cada bloque de
   código. **No cierres la pestaña ni pulses nada mientras trabaja.**
6. Cuando termine, guarda con **Ctrl + S**.

Repite lo mismo con los cuadernos en el orden del apartado 1.

### Opción B · Con una orden (para ejecutar la cadena entera)

`nbconvert` es un programa que ejecuta un cuaderno de principio a fin sin
abrirlo. Se usa así, un bloque por cuaderno y **en este orden**:

```powershell
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 notebooks\refactor\2.0_preprocesamiento_jobpath.ipynb
```

```powershell
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=7200 notebooks\refactor\3.0_transformacion.ipynb
```

```powershell
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 notebooks\refactor\4.0_PCA.ipynb
```

```powershell
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 notebooks\refactor\4.1_PCA_completo.ipynb
```

```powershell
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 notebooks\refactor\5.0_EDA_jobpath.ipynb
```

Traducción de la orden: "ejecuta este cuaderno, guárdalo con los resultados y
dale hasta 60 minutos de margen antes de rendirte". El número del final son los
segundos de espera máxima; el 3.0 lleva 7200 porque es el más lento.

**Solo el análisis:**

```powershell
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 notebooks\refactor\5.0_EDA_jobpath.ipynb
```

---

## 5. Cómo saber que salió bien

Al terminar, comprueba estas cosas. Si coinciden, todo está correcto.

**Los datos transformados (después de 3.0).** Copia y pega:

```powershell
python -c "
import pandas as pd
from pathlib import Path
base = Path('data/04_transformed')
for v in ('con_outliers', 'sin_outliers'):
    for s in ('train', 'test'):
        x = pd.read_csv(base / v / s / f'X_{s}.csv', nrows=0)
        y = pd.read_csv(base / v / s / f'y_{s}.csv')
        print(v, s, 'columnas', x.shape[1], '| filas', len(y), '| casos 1', int(y.iloc[:, 0].sum()))
"
```

Debe aparecer:

| Versión | Conjunto | Columnas | Filas | Casos con valor 1 |
|---|---|---|---|---|
| con_outliers | train | 2.839 | 278.987 | 85.147 |
| con_outliers | test | 2.839 | 69.276 | 21.103 |
| sin_outliers | train | 2.839 | 278.987 | 85.147 |
| sin_outliers | test | 2.839 | 69.276 | 21.103 |

Las dos versiones tienen que dar **exactamente lo mismo** en filas y en casos
con valor 1. Solo cambian algunos valores extremos, no el número de filas.

**Las figuras (después de 5.0).**

```powershell
(Get-ChildItem reports\eda_jobpath\figures\*.png).Count
```

Debe decir **28**. Y dentro del cuaderno 5.0, al final, las tres últimas
comprobaciones tienen que decir **True**:

```
Todos los insumos intactos: True
Todas las figuras presentes: True
Todos los cruces con target en train: True
```

Eso significa: "los archivos de partida no se modificaron", "están las 28
figuras" y "no se usó el conjunto de prueba para sacar conclusiones".

---

## 6. Si algo sale mal: volver atrás

No pasa nada, para eso está la copia. En la misma ventana de PowerShell:

```powershell
Copy-Item "backup\LA-FECHA-QUE-APARECE\03_processed\*"   data\03_processed   -Force
Copy-Item "backup\LA-FECHA-QUE-APARECE\04_transformed\*" data\04_transformed -Force -Recurse
```

Sustituye `LA-FECHA-QUE-APARECE` por el nombre real de la carpeta dentro de
`backup\` (por ejemplo `2026-11-11_10-30`). Eso devuelve los datos a como
estaban antes de empezar.

---

## 7. Señales de alarma y qué hacer

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Un bloque de código se queda con un asterisco `*` mucho rato | Está trabajando (el 3.0 tarda) | Esperar. No cerrar ni reiniciar |
| Un mensaje rojo con `FileNotFoundError` | Falta un archivo porque el paso anterior no se ejecutó | Ejecutar el cuaderno anterior y repetir |
| Un mensaje rojo con `MemoryError` | El ordenador se quedó sin memoria | Cerrar otras aplicaciones y repetir; el 3.0 es el que más consume |
| En el 3.0, la segunda celda no muestra nada | Es normal: solo carga la configuración | No hacer nada |
| El 5.0 dice `False` en alguna comprobación | Algo se modificó o falta una figura | Revisar si se ejecutó el 3.0 y volver a lanzar el 5.0 |
| Cambian el número de filas | Se activó una opción que no debía | Restaurar la copia del apartado 6 |

---

## 8. Reglas de oro (para no romper nada)

1. **No borres** `data\03_processed\empleos_limpio_con_competencias.csv`. Es el
   archivo de partida y ningún cuaderno lo vuelve a crear.
2. **No actives** las casillas de los cuadernos 2.0 que dicen "solo ejecutar si
   aprueba" (`APPROVE_KEY_DUPLICATES`, `APPROVE_CATEGORY_NORMALIZATION`).
   Cambian cuántas filas hay y todo lo demás deja de cuadrar.
3. **No cambies el orden de las columnas** ni los nombres de los archivos de
   `data\04_transformed`: el 5.0 los busca por su nombre exacto.
4. **No toques el texto que imprimen los cuadernos 4.0 y 4.1.** El 5.0 lee esas
   frases para construir dos figuras; si cambian, falla.
5. **No subas la carpeta `backup\` al repositorio.** Son gigas de copia.
6. Si dudas, ejecuta solo el **5.0**: no modifica datos.

---

## 9. Resumen en tres líneas

- Para ver el análisis: ejecuta solo el **5.0**.
- Para rehacer todo: copia de seguridad → **2.0 → 3.0 → 4.0 → 4.1 → 5.0**.
- Si algo falla: restaura la carpeta de `backup\` y vuelve a intentarlo.
