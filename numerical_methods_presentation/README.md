# Numerical Methods Presentation — JobPath (`MineriaProtect`)

Presentación interactiva unificada (**100 % offline**, con KaTeX empaquetado localmente) que contrasta los dos métodos centrales del curso —**Regresión Lineal por Mínimos Cuadrados (MCO)** e **Interpolación Polinomial de Lagrange**— aplicados a la duración laboral de empleos cerrados (`~es_vigente`, regla `MR-09`) sobre **JobHop v2** + **ESCO v1.2.1 / ISCO-08**.

## Contenido de la carpeta

| Ruta | Descripción |
|---|---|
| `index.html` | **Presentación HTML Unificada (`16` diapositivas):** contexto JobPath, mapa rápido de las 4 capas de `data/` aplicado a los 2 casos, catálogo interactivo de las 12 reglas `MR-01`–`MR-12`, fórmulas explicadas símbolo por símbolo con revelado progresivo (clic / tecla `.`), 2 simuladores JS con gráficos SVG en vivo, tablas CSV verificadas, síntesis cara a cara MCO vs. Lagrange y cierre minimalista. |
| `case_01_RL04_annual_drift_extrapolation/` | **Caso 1 (`IDEA-RL-04` · MCO):** presentación individual (`8` diapositivas), figura 150 DPI, tablas CSV verificadas, explicación y guía fácil. |
| `case_02_LG01_survival_and_runge/` | **Caso 2 (`IDEA-LG-01` · Lagrange):** presentación individual (`8` diapositivas), figuras 150 DPI (`P₃` y Fenómeno de Runge), tablas CSV verificadas, explicación y guía fácil. |
| `assets/katex/` | Paquete local **KaTeX 0.16.11** (`katex.min.css`, `katex.min.js`, `contrib/auto-render.min.js` + `20` fuentes `.woff2`) para renderizado matemático 100 % offline. |
| `EVALUACION_PRESENTACION_UNIFICADA.md` | Auditoría pedagógica y técnica de 6 ejes (`100 / 100 · Nota 5.00 / 5.0`). |

## Cómo visualizarla

- **En local:** clona el repositorio y abre `numerical_methods_presentation/index.html` en cualquier navegador moderno (Chrome, Edge, Firefox). No requiere servidor ni conexión a internet.
- **En GitHub Pages:** habilita *Settings → Pages* apuntando a la rama correspondiente y accede a `/numerical_methods_presentation/`.

## Atajos de teclado

- `←` / `→` o `Espacio`: cambiar de diapositiva
- `.` (punto) o clic en cualquier símbolo: revelado / enfoque paso a paso en diapositivas de fórmulas
- `F`: pantalla completa
- `Esc`: cerrar zoom de gráficas o salir del modo enfoque
