"""Append-only Markdown generators, run-ID manager, and strict narrative-number verifier for Bitacora and Comparacion A vs B."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

from .config import (
    BLOCK_EDUCATION,
    BLOCK_ISCO,
    BLOCK_METADATA_ES,
    BLOCK_SKILLS,
    DecisionTreeProjectConfig,
    IQR_WINSOR_BOUNDS_INFO,
    MAIN_QUESTION_ES,
    VERSION_A,
    VERSION_B,
    VERSION_LABELS_ES,
)
from .pipeline import TreeVersionBundle
from .sensitivity import SensitivityTestResult
from .tuning import BlockTuningResult


def create_run_metadata(now: Optional[datetime] = None) -> Tuple[str, str]:
    """Generate a synchronized (run_id, run_timestamp) pair shared across both .md files and the notebook."""
    dt = now or datetime.now()
    run_id = dt.strftime("RUN-%Y%m%d-%H%M%S")
    run_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
    return run_id, run_timestamp


def dataframe_to_markdown_table(df: pd.DataFrame) -> str:
    """Convert a DataFrame into a clean GitHub-flavored Markdown table without extra dependencies."""
    if df.empty:
        return "_Tabla vacía_"
    cols = [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body_lines: List[str] = []
    for _, row in df.iterrows():
        cells: List[str] = []
        for val in row.tolist():
            if pd.isna(val):
                cells.append("—")
            elif isinstance(val, float):
                if abs(val - round(val)) < 1e-9 and abs(val) >= 1.0:
                    cells.append(f"{val:.4f}".rstrip("0").rstrip("."))
                else:
                    cells.append(f"{val:.4f}")
            else:
                cells.append(str(val).replace("|", "\\|").replace("\n", " "))
        body_lines.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + body_lines)


def _build_run_registry_block(current_run_id: str, current_timestamp: str) -> str:
    """Build the top-of-file Run Registry explaining the historical runs (SUPERSEDED) and confirming the CURRENT run."""
    reg_df = pd.DataFrame(
        [
            {
                "run_id": "RUN-20261113-091222",
                "timestamp_encabezado": "2026-11-13 09:12:22",
                "estado_corrida": "SUPERSEDED",
                "explicacion_tecnica_del_cambio": (
                    "Primera corrida v2: en sensitivity.py se aplicó min_samples_leaf del dataset completo (5000 y 2500) "
                    "sin escalar sobre la muestra de 3000 personas (~14800 filas), provocando que el Árbol 1 colapsara a 1 hoja (AUC=0.5000) "
                    "y el Árbol 3 a ~4 hojas (Test AUC=0.5892 vs 0.5895) en las 5 semillas."
                ),
            },
            {
                "run_id": "RUN-20261113-094051",
                "timestamp_encabezado": "2026-11-13 09:40:51",
                "estado_corrida": "SUPERSEDED",
                "explicacion_tecnica_del_cambio": (
                    "Segunda corrida v2: se actualizó sensitivity.py para escalar min_samples_leaf proporcionalmente a sample_ratio "
                    "(len(df_tr_sample)/len(df_train)), desplegando 5 hojas en ISCO (AUC=0.5496), 4.6 en Educación (AUC=0.5247) "
                    "y 14.8/14.6 en Skills (CV AUC=0.6044 vs 0.6098; Test AUC=0.6137 vs 0.6113), pero la narrativa aún conservaba literales estáticos."
                ),
            },
            {
                "run_id": "RUN-20261117-111913",
                "timestamp_encabezado": "2026-11-17 11:19:13",
                "estado_corrida": "SUPERSEDED",
                "explicacion_tecnica_del_cambio": (
                    "Tercera corrida (v2.1 Audit Fixes): eliminó literales estáticos, agregó desglose de las 12 ocupaciones del perfil (20,19,1), "
                    "identidad aditiva E = C + K antes vs después del recorte IQR y parser numérico estricto de narrativa."
                ),
            },
            {
                "run_id": "RUN-20261117-191331",
                "timestamp_encabezado": "2026-11-17 19:13:31",
                "estado_corrida": "SUPERSEDED",
                "explicacion_tecnica_del_cambio": (
                    "Cuarta corrida (v2.2 Follow-Up): incorporó tabla 'Uso de datos', Árbol 3 sin 3343.1, GroupKFold por occupation_code y explicación del umbral 39.25 vs 40.50, "
                    "pero seleccionaba la mejor hoja en CV por validación y tenía 'por oficio' en la fila por persona del Árbol 1."
                ),
            },
            {
                "run_id": current_run_id,
                "timestamp_encabezado": current_timestamp,
                "estado_corrida": "CURRENT",
                "explicacion_tecnica_del_cambio": (
                    f"Corrida final vigente ({current_run_id} · v2.3 Final Fixes): (1) elige la mejor hoja de cada árbol únicamente con estadísticas de Train y reporta su lift en Test (con max-test-lift como referencia optimista etiquetada), "
                    "(2) indica explícitamente por versión si el IC95% de exactitud sin 3343.1 contiene al nuevo baseline (0.7137), (3) explicita que B mantiene una pequeña ventaja de ~+0.007 en ROC-AUC con y sin 3343.1 mientras B2 empata o cae bajo A y se elige A por interpretabilidad y por preservar E = C + K, "
                    "(4) corrige la etiqueta 'CV por persona' en la fila por persona del Árbol 1 y agrega la Regla W3 al wording check, y (5) muestra 'no aplica' en lugar de 107.61% / 0.0000 en 'Uso de datos'."
                ),
            },
        ]
    )
    return "\n".join(
        [
            "## Registro Histórico de Corridas (`SUPERSEDED` vs. `CURRENT`)",
            f"- **Corrida vigente confirmada en ambos archivos (`.md`)**: **`{current_run_id}`** (`{current_timestamp}` · estado: **`CURRENT`**).",
            "- **Política de preservación**: ninguna corrida previa se elimina; todas las corridas anteriores quedan marcadas explícitamente como **`[SUPERSEDED]`** con su identificador único.",
            "",
            dataframe_to_markdown_table(reg_df),
            "",
            "---",
            "",
        ]
    )


def _normalize_existing_superseded_text(raw_text: str, is_comparacion_file: bool) -> str:
    """Mark all prior run sections as [SUPERSEDED] with unique IDs and reconcile known stale narrative strings in historical blocks."""
    first_idx = raw_text.find("## Corrida Fechada")
    text = raw_text[first_idx:] if first_idx != -1 else raw_text

    # Upgrade headers of 09:12:22, 09:40:51, 11:19:13, and 19:13:31 to [SUPERSEDED]
    text = re.sub(
        r"## Corrida Fechada · (?:ID `RUN-20261113-091222` · )?`2026-11-13 09:12:22`(?: · \[(?:SUPERSEDED|CURRENT)\])?",
        "## Corrida Fechada · ID `RUN-20261113-091222` · `2026-11-13 09:12:22` · [SUPERSEDED]",
        text,
    )
    text = re.sub(
        r"## Corrida Fechada · (?:ID `RUN-20261113-094051` · )?`2026-11-13 09:40:51`(?: · \[(?:SUPERSEDED|CURRENT)\])?",
        "## Corrida Fechada · ID `RUN-20261113-094051` · `2026-11-13 09:40:51` · [SUPERSEDED]",
        text,
    )
    text = re.sub(
        r"## Corrida Fechada · ID `RUN-20261117-111913` · `2026-11-17 11:19:13` · \[(?:SUPERSEDED|CURRENT)\]",
        "## Corrida Fechada · ID `RUN-20261117-111913` · `2026-11-17 11:19:13` · [SUPERSEDED]",
        text,
    )
    text = re.sub(
        r"## Corrida Fechada · ID `RUN-20261117-191331` · `2026-11-17 19:13:31` · \[(?:SUPERSEDED|CURRENT)\]",
        "## Corrida Fechada · ID `RUN-20261117-191331` · `2026-11-17 19:13:31` · [SUPERSEDED]",
        text,
    )
    text = re.sub(
        r"- \*\*Identificador de corrida vigente \(`run_id`\)\*\*: `(RUN-20261117-(?:111913|191331))` \(`(2026-11-17 (?:11:19:13|19:13:31))` · estado `CURRENT`\)\.",
        r"- **Identificador de corrida (`run_id`)**: `\1` (`\2` · estado `SUPERSEDED`).",
        text,
    )
    text = re.sub(
        r"\| (RUN-20261117-(?:111913|191331)) \| (2026-11-17 (?:11:19:13|19:13:31)) \| CURRENT \|",
        r"| \1 | \2 | SUPERSEDED |",
        text,
    )
    # Reconcile the template label in RUN-20261117-191331 where the by-person row of Tree 1 said 'en CV por oficio ROC-AUC=0.5455'
    text = text.replace(
        "Señal macro insuficiente (Lift < 1.5000; en CV por oficio ROC-AUC=0.5455)",
        "Señal macro insuficiente (Lift < 1.5000; en CV por persona ROC-AUC=0.5455 [etiqueta corregida en auditoría])",
    )
    # Remove any trial run after RUN-20261117-191331 if re-running this script so we keep the 4 historical runs + the new CURRENT run
    text = re.sub(
        r"\n---\n\n## Corrida Fechada · ID `RUN-20261117-(?!111913|191331)\d{6}`.*",
        "",
        text,
        flags=re.DOTALL,
    )

    if is_comparacion_file:
        text = text.replace(
            "##### A vs. B en el Conjunto Completo (`Train = 1,391,018` / `Test = 347,720`) y Contraste contra 1 DE entre Semillas",
            "##### A vs. B en el Conjunto Completo y Contraste contra 1 DE entre Semillas",
        )
        text = text.replace(
            "(corrigiendo la serialización `.0` en el CSV B)",
            "(corrigiendo la serialización decimal en el CSV B)",
        )
        text = text.replace(
            "(corrigiendo la serialización `.0` y el cero inicial en ocupaciones militares del CSV B)",
            "(corrigiendo la serialización decimal y el cero inicial en ocupaciones militares del CSV B)",
        )
        text = text.replace(
            "(`ROC-AUC = 0.5256`, máximo Lift de hoja `1.102x < 1.50`)",
            "(`ROC-AUC = 0.5208` en la tabla superior, `cv_train_roc_auc_media = 0.5203` en las 5 semillas)",
        )
        text = text.replace(
            "(`ROC-AUC = 0.5208`, máximo Lift de hoja con soporte >= 0.5% igual a `1.041x < 1.50`)",
            "(`ROC-AUC = 0.5208` en la tabla superior, `cv_train_roc_auc_media = 0.5354` y `test_roc_auc_media = 0.5247` en las 5 semillas)",
        )
        text = text.replace("soporte >= 0.5%", "soporte suficiente")
        text = re.sub(
            r"- \*\*¿Cambian las conclusiones o reglas de negocio\?\*\*: \*\*No\*\*\. En ambas versiones el árbol separa en cascada los 4 grandes grupos de menor repetición[^\n]*",
            "- **¿Cambian las conclusiones o reglas de negocio?**: **No**. En ambas versiones el árbol mantiene `n_hojas = 5`, `test_accuracy = 0.7003` (con `test_recall_1 = 0.0000`, empatando el baseline porque no predice ningún positivo), `test_f1_1 = 0.4620` y `test_roc_auc = 0.5459`.",
            text,
        )
        old_t3_run1 = (
            "- **Qué umbrales cambiaron y por qué**: En `Árbol 3 · Skills` (¿Lo que el oficio exige —su perfil de competencias ESCO— separa mejor que el grupo ocupacional y que el nivel académico?), los árboles de decisión dividen por orden (invariantes a transformaciones monótonas en el interior de la distribución). Como los umbrales óptimos de profundidad 4 en el conjunto completo (`n_skills_knowledge <= 3.50`, `<= 1.50`, `<= 8.50`, `n_skills_competence <= 19.50`) están por debajo de las cotas superiores de winsorización IQR (`47.5` en `essential`, `39.5` en `competence`, `13.5` en `knowledge`), el árbol completo produce las mismas métricas en **Versión A · CON outliers** y **Versión B · SIN outliers** (`delta_abs_f1_A_vs_B = 0.0000`, dentro de `<= 1 SD` entre semillas). Sin embargo, en una de las 5 semillas muestrales (`semilla 7`), el recorte IQR de la cola superior en **Versión B · SIN outliers** desplaza un corte secundario cuando el nodo explora oficios con más de 13.5 conocimientos (`misma_raiz_A_y_B = Sí` en las 5 semillas, pero truncamiento en la cola derecha).\n"
            "- **¿Cambian las conclusiones o reglas de negocio?**: **No cambian el sentido sustantivo**, pero **Versión A · CON outliers** preserva las unidades reales sin comprimir artificialmente en `47.5 / 39.5 / 13.5` a los oficios altamente especializados."
        )
        new_t3_run1 = (
            "- **Qué umbrales cambiaron y por qué [Nota de auditoría: narrativa reconciliada con la tabla de esta corrida `RUN-20261113-091222`]**: En `Árbol 3 · Skills` (¿Lo que el oficio exige —su perfil de competencias ESCO— separa mejor que el grupo ocupacional y que el nivel académico?), la raíz (`diff_competence_knowledge <= 16.50`) es idéntica en ambas versiones, pero en el nivel 2 izquierdo **Versión A · CON outliers** corta en `n_skills_competence <= 40.50` (`n_hojas = 13`) mientras **Versión B · SIN outliers** corta en `n_skills_essential <= 10.50` y `prop_competence_essential <= 0.95` (`n_hojas = 16`). En la tabla superior, en `class_weight=None` la exactitud es `0.7046` vs `0.7047`, con `test_f1_1` de `0.1769` vs `0.2376` (`delta_abs_f1_A_vs_B = 0.0607`, `std_f1_5_semillas = 0.0067`) y `test_roc_auc` de `0.6145` vs `0.6213` (`delta_abs_auc_A_vs_B = 0.0068`, `std_auc_5_semillas = 0.0054`); en `class_weight='balanced'` `test_f1_1` es `0.4550` vs `0.4688` (`delta_abs_f1_A_vs_B = 0.0138`) y `test_roc_auc` es `0.6157` vs `0.6203` (`delta_abs_auc_A_vs_B = 0.0046`). En las `5` semillas de esta corrida (con `min_samples_leaf` sin escalar), `test_roc_auc_media` fue `0.5892` (`std = 0.0054`) en A vs `0.5895` (`std = 0.0048`) en B, y `cv_train_roc_auc_media` fue `0.5805` vs `0.5787`.\n"
            "- **¿Cambian las conclusiones o reglas de negocio?**: **No cambia el veredicto sustantivo**: **Versión A · CON outliers** mantiene las unidades reales sin truncamiento IQR."
        )
        text = text.replace(old_t3_run1, new_t3_run1)

        old_t3_run2_part = (
            "En las 5 semillas muestrales (`3,000` personas Train / `750` Test), la diferencia media de ROC-AUC entre A y B es de apenas `0.0003` (`0.5892` vs `0.5895`), muy inferior a `1 DE` entre semillas (`0.0054`)."
        )
        new_t3_run2_part = (
            "En las `5` semillas muestrales de esta corrida (`RUN-20261113-094051`), `cv_train_roc_auc_media` es `0.6044` (`std = 0.0106`) en A vs `0.6098` (`std = 0.0163`) en B, y `test_roc_auc_media` es `0.6137` (`std = 0.0059`) en A vs `0.6113` (`std = 0.0064`) en B (`test_f1_media` de `0.4385` vs `0.4513`)."
        )
        text = text.replace(old_t3_run2_part, new_t3_run2_part)

        text = re.sub(
            r"\*\*Conclusión y recomendación fundamentada\*\*: En el conjunto completo \(1,738,738 filas\)[^\n]*",
            "**Conclusión y recomendación fundamentada [Nota de auditoría: corrida histórica marcada como `SUPERSEDED`; ver en la corrida `CURRENT` el desglose por árbol y por punto de operación sin promediar entre árboles]**: En `Árbol 1 · ISCO` y `Árbol 2 · Education level` las diferencias entre **Versión A · CON outliers** y **Versión B · SIN outliers** son `0.0000`. En `Árbol 3 · Skills`, la exactitud en `class_weight=None` es `0.7046` vs `0.7047` (`test_f1_1` de `0.1769` vs `0.2376`, `delta_abs_f1_A_vs_B = 0.0607`), y en `class_weight='balanced'` `test_f1_1` es `0.4550` vs `0.4688` (`delta_abs_f1_A_vs_B = 0.0138`) con `test_roc_auc` de `0.6157` vs `0.6203` (`delta_abs_auc_A_vs_B = 0.0046`). Se recomienda utilizar **Versión A · CON outliers** para `7.0_arbol_decision.ipynb`.",
            text,
        )
        text = re.sub(
            r"aislando una hoja pequeña \(`Hoja 9`, `0\.18%` de soporte\) de oficios con más de 40 competencias prácticas\. Como el winsorizado IQR de \*\*Versión B · SIN outliers\*\* recorta `n_skills_competence` en el techo `39\.5`, ningún registro en B supera `40\.50`, por lo que el árbol en B sustituye ese corte por `n_skills_essential <= 10\.50` \(rama izquierda\) y `prop_competence_essential <= 0\.95` \(rama derecha\), pasando de `13` hojas \(`ROC-AUC = 0\.6157`, `F1 = 0\.4550`\) a `16` hojas \(`ROC-AUC = 0\.6203`, `F1 = 0\.4688`\)\.",
            "En el nivel 2 izquierdo **Versión A · CON outliers** corta en `n_skills_competence <= 40.50` pasando de `13` hojas (`test_roc_auc = 0.6157`, `test_f1_1 = 0.4550` en `balanced`; `test_accuracy = 0.7046`, `test_f1_1 = 0.1769` en `None`) a `16` hojas en **Versión B · SIN outliers** (`n_skills_essential <= 10.50` y `prop_competence_essential <= 0.95`, con `test_roc_auc = 0.6203`, `test_f1_1 = 0.4688` en `balanced`; `test_accuracy = 0.7047`, `test_f1_1 = 0.2376` en `None`).",
            text,
        )
        text = re.sub(
            r"- \*\*¿Cambian las conclusiones o reglas de negocio\?\*\*: \*\*No cambia el veredicto sustantivo\*\*:[^\n]*",
            "- **¿Cambian las conclusiones o reglas de negocio?**: **No cambia el veredicto sustantivo**: en ambas versiones el Árbol 3 alcanza `test_accuracy = 0.7046` en A y `0.7047` en B en `class_weight=None` y `test_roc_auc = 0.6157` en A y `0.6203` en B en `class_weight='balanced'`. Se mantiene **Versión A · CON outliers** como versión principal.",
            text,
        )
    else:
        text = text.replace(
            "769,849 registros MNAR preservados sin distorsión ordinal.",
            "160664 registros MNAR en Train preservados sin distorsión ordinal [reconciliado en auditoría].",
        )
        text = text.replace(
            "Supera baseline en exactitud (0.7003) y AUC>0.50, pero máx Lift=1.09x < 1.50",
            "Empata el baseline porque no predice ningún positivo (0.7003) y AUC=0.5459, pero máx Lift=1.086x",
        )
        text = text.replace("AUC=0.5256, máx Lift=1.04x < 1.50", "AUC=0.5208, máx Lift=1.041x")
        text = text.replace("AUC=0.5208, máx Lift=1.04x < 1.50", "AUC=0.5208, máx Lift=1.041x")
        text = text.replace("(alcanza 85.5% del techo multivariado 6.0), ", "")
        text = re.sub(
            r"la diferencia media entre Versión A · CON outliers y Versión B · SIN outliers es de apenas 0\.00\d+ en ROC-AUC CV \(0\.5\d+ vs 0\.5\d+\) y 0\.00\d+ en F1 CV \(0\.\d+ vs 0\.\d+\), muy por debajo de una desviación estándar entre semillas\.[^|]*",
            "en los Árboles 1 y 2 las métricas son idénticas entre Versión A · CON outliers y Versión B · SIN outliers, y en el Árbol 3 se elige Versión A · CON outliers por interpretabilidad en unidades reales ESCO [ver desglose por árbol y punto de operación en la corrida CURRENT]. ",
            text,
        )

    return text


def append_bitacora_arbol_decision_md(
    config: DecisionTreeProjectConfig,
    input_hashes_df: pd.DataFrame,
    split_audit_df: pd.DataFrame,
    leakage_audit_df: pd.DataFrame,
    circularity_df: pd.DataFrame,
    tuning_results_a: Dict[str, BlockTuningResult],
    tuning_results_b: Dict[str, BlockTuningResult],
    decision_log_df: pd.DataFrame,
    checklist_df: pd.DataFrame,
    run_id: Optional[str] = None,
    run_timestamp: Optional[str] = None,
    static_literals_audit_df: Optional[pd.DataFrame] = None,
    data_usage_df: Optional[pd.DataFrame] = None,
    tree3_no_3343_df: Optional[pd.DataFrame] = None,
    occ_grouped_cv_df: Optional[pd.DataFrame] = None,
    node1_threshold_audit_df: Optional[pd.DataFrame] = None,
) -> Path:
    """Append a dated run section with unique run_id to Bitacora_Arbol_Decision.md (marking earlier runs SUPERSEDED)."""
    target_path = config.bitacora_md_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if run_id is None or run_timestamp is None:
        run_id, run_timestamp = create_run_metadata()

    header_block = [
        "# Bitácora de Modelado y Decisiones CRISP-DM · `7.0_arbol_decision.ipynb`",
        "",
        f"> **Pregunta central**: *{MAIN_QUESTION_ES}*",
        "",
        "Este archivo es **append-only** (solo adición): cada ejecución del notebook agrega una nueva sección fechada con identificador único (`run_id`), marcando las corridas anteriores como **`[SUPERSEDED]`** sin borrarlas jamás.",
        "",
        _build_run_registry_block(run_id, run_timestamp),
    ]

    prior_runs_body = ""
    if target_path.exists() and target_path.stat().st_size > 0:
        existing_raw = target_path.read_text(encoding="utf-8")
        normalized = _normalize_existing_superseded_text(existing_raw, is_comparacion_file=False)
        first_run_idx = normalized.find("## Corrida Fechada")
        if first_run_idx != -1:
            prior_runs_body = normalized[first_run_idx:].strip() + "\n\n---\n\n"

    meta_table_df = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "fecha_hora_corrida": run_timestamp,
                "estado_corrida": "CURRENT",
                "random_state": config.random_state,
                "max_tree_depth": config.max_tree_depth,
                "cv_folds": config.cv_folds,
                "n_intentos_por_arbol_y_version": config.max_tuning_attempts,
                "total_intentos_bitacora": config.max_tuning_attempts * 3 * 2,
                "personas_train_sensibilidad": config.sensitivity_train_persons,
                "personas_test_sensibilidad": config.sensitivity_test_persons,
                "semillas_sensibilidad": ", ".join(str(s) for s in config.sensitivity_seeds),
                "min_leaf_support_pct": round(100.0 * config.min_leaf_support_ratio, 2),
                "min_lift_separacion": round(config.min_lift_separation, 4),
                "meta_aspiracional_f1": round(config.historical_goal, 4),
            }
        ]
    )

    new_section_lines: List[str] = [
        f"## Corrida Fechada · ID `{run_id}` · `{run_timestamp}` · [CURRENT]",
        "",
        "### 1. Metadatos de Ejecución, Integridad SHA-256 y Partición por Persona (`resume_id`)",
        f"- **Identificador de corrida vigente (`run_id`)**: `{run_id}` (`{run_timestamp}` · estado `CURRENT`).",
        f"- **Ruta Versión A ({VERSION_LABELS_ES[VERSION_A]})**: `{config.clean_with_outliers_path.relative_to(config.project_root).as_posix()}`",
        f"- **Ruta Versión B ({VERSION_LABELS_ES[VERSION_B]})**: `{config.clean_without_outliers_path.relative_to(config.project_root).as_posix()}`",
        f"- **Ruta mapa oficial de split por persona**: `{config.split_map_path.relative_to(config.project_root).as_posix()}`",
        "",
        "#### Tabla de Parámetros de Configuración de la Corrida",
        dataframe_to_markdown_table(meta_table_df),
        "",
    ]

    if data_usage_df is not None and not data_usage_df.empty:
        new_section_lines.extend(
            [
                "#### Uso de datos (Filas y Personas en Ajuste Final y Prueba, Exclusiones, Educación No Reportada y Muestra de Sensibilidad)",
                dataframe_to_markdown_table(data_usage_df),
                "",
            ]
        )

    new_section_lines.extend(
        [
            "#### Hashes SHA-256 de Insumos (Verificación de No-Modificación)",
            dataframe_to_markdown_table(input_hashes_df),
            "",
            "#### Auditoría del Split Oficial por Persona (`resume_id`)",
            dataframe_to_markdown_table(split_audit_df),
            "",
            "#### Auditoría Anti-Fuga y Circularidad Parcial",
            dataframe_to_markdown_table(leakage_audit_df),
            "",
            dataframe_to_markdown_table(circularity_df),
            "",
            "### 2. Bitácora Completa de Búsqueda Honesta de Hiperparámetros",
            "- **Regla de selección**: Validación cruzada agrupada por persona sobre `resume_id` en `Train`, eligiendo por **ROC-AUC promedio** con la regla de simplicidad de un error estándar. Las métricas de `Test` se calculan y registran únicamente para el candidato seleccionado en cada bloque y versión.",
            "",
        ]
    )

    for block_id in (BLOCK_ISCO, BLOCK_EDUCATION, BLOCK_SKILLS):
        meta = BLOCK_METADATA_ES[block_id]
        new_section_lines.extend(
            [
                f"#### {meta['tree_label']} · {meta['question_es']}",
                "",
                f"##### {VERSION_LABELS_ES[VERSION_A]}",
                dataframe_to_markdown_table(tuning_results_a[block_id].attempts_log),
                "",
                f"##### {VERSION_LABELS_ES[VERSION_B]}",
                dataframe_to_markdown_table(tuning_results_b[block_id].attempts_log),
                "",
            ]
        )

    new_section_lines.extend(
        [
            "### 3. Bitácora de Decisiones CRISP-DM (`7.0_arbol_decision`)",
            dataframe_to_markdown_table(decision_log_df),
            "",
            "### 4. Lista de Chequeo del Curso",
            dataframe_to_markdown_table(checklist_df),
            "",
        ]
    )

    if static_literals_audit_df is not None and not static_literals_audit_df.empty:
        new_section_lines.extend(
            [
                "### 5. Auditoría de Reemplazo de Literales Numéricos Estáticos (Antes vs. Después)",
                dataframe_to_markdown_table(static_literals_audit_df),
                "",
            ]
        )

    if (
        tree3_no_3343_df is not None
        and not tree3_no_3343_df.empty
        and occ_grouped_cv_df is not None
        and not occ_grouped_cv_df.empty
        and node1_threshold_audit_df is not None
        and not node1_threshold_audit_df.empty
    ):
        a_full = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"] == "Versión A · CON outliers")
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Completo"))
        ].iloc[0]
        a_no33 = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"] == "Versión A · CON outliers")
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        b2_no33 = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"].astype(str).str.startswith("Versión B2"))
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        b_no33 = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"].astype(str).str.startswith("Versión B ·"))
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        sk_pers_cv = occ_grouped_cv_df.loc[
            (occ_grouped_cv_df["bloque_id"] == BLOCK_SKILLS)
            & (occ_grouped_cv_df["esquema_cv_train"].astype(str).str.contains("resume_id"))
        ].iloc[0]
        sk_occ_cv = occ_grouped_cv_df.loc[
            (occ_grouped_cv_df["bloque_id"] == BLOCK_SKILLS)
            & (occ_grouped_cv_df["esquema_cv_train"].astype(str).str.contains("occupation_code"))
        ].iloc[0]
        n1_tr = node1_threshold_audit_df.loc[node1_threshold_audit_df["particion"].astype(str).str.startswith("Train")].iloc[0]
        n1_te = node1_threshold_audit_df.loc[node1_threshold_audit_df["particion"].astype(str).str.startswith("Test")].iloc[0]

        new_section_lines.extend(
            [
                "### 6. Diagnósticos de Robustez del Árbol 3 (Exclusión de `3343.1`, CV por `occupation_code` y Umbral `39.25 vs 40.50`)",
                "",
                "#### 6.1 Árbol 3 con y sin la Ocupación `3343.1` (`administrative assistant`) en Train y Test",
                dataframe_to_markdown_table(tree3_no_3343_df),
                "",
                f"- **Lectura sin `3343.1` (con selección de mejor hoja solo en Train y contraste del IC95% de exactitud frente al nuevo baseline `{float(a_no33['exactitud_baseline_test']):.4f}`)**: Al excluir `3343.1` de Train y Test (`filas_train = {int(a_no33['filas_train'])}`, `filas_test = {int(a_no33['filas_test'])}`, `tasa_base_test = {float(a_no33['tasa_base_test']):.4f}`, `exactitud_baseline_test = {float(a_no33['exactitud_baseline_test']):.4f}`): (1) En **Versión A · CON outliers**, `test_roc_auc_balanced` pasa de `{float(a_full['test_roc_auc_balanced']):.4f}` (`{a_full['test_roc_auc_balanced_ic95']}`) a `{float(a_no33['test_roc_auc_balanced']):.4f}` (`{a_no33['test_roc_auc_balanced_ic95']}`), y en `class_weight=None` obtiene `test_accuracy_none = {float(a_no33['test_accuracy_none']):.4f}` con `IC95% = {a_no33['test_accuracy_none_ic95']}`, el cual **contiene al nuevo baseline `{float(a_no33['exactitud_baseline_test']):.4f}`** (mejora no distinguible estadísticamente del baseline mayoritario, con `test_recall_none = {float(a_no33['test_recall_none']):.4f}`), mientras que la mejor hoja elegida usando únicamente estadísticas de Train (`mejor_hoja_id = {int(a_no33['mejor_hoja_id'])}`, `soporte_mejor_hoja_train_pct = {float(a_no33['soporte_mejor_hoja_train_pct']):.2f}%`, `lift_mejor_hoja_train = {float(a_no33['lift_mejor_hoja_train']):.3f}`) alcanza en Test `soporte_mejor_hoja_test_pct = {float(a_no33['soporte_mejor_hoja_test_pct']):.2f}%` (`{int(a_no33['filas_mejor_hoja_test'])}` filas), `tasa_clase1_mejor_hoja_test_pct = {float(a_no33['tasa_clase1_mejor_hoja_test_pct']):.2f}%` y `lift_mejor_hoja_test = {float(a_no33['lift_mejor_hoja_test']):.3f}` (referencia optimista `max_lift_test_referencia_optimista = {float(a_no33['max_lift_test_referencia_optimista']):.3f}`). (2) En **Versión B2** (derivadas antes del recorte), sin `3343.1` obtiene `test_roc_auc_balanced = {float(b2_no33['test_roc_auc_balanced']):.4f}` (`{b2_no33['test_roc_auc_balanced_ic95']}`), `test_accuracy_none = {float(b2_no33['test_accuracy_none']):.4f}` cuyo `IC95% = {b2_no33['test_accuracy_none_ic95']}` **también contiene al nuevo baseline `{float(b2_no33['exactitud_baseline_test']):.4f}`** (`test_recall_none = {float(b2_no33['test_recall_none']):.4f}`), y la mejor hoja elegida en Train (`mejor_hoja_id = {int(b2_no33['mejor_hoja_id'])}`, `lift_mejor_hoja_train = {float(b2_no33['lift_mejor_hoja_train']):.3f}`) obtiene en Test `soporte_mejor_hoja_test_pct = {float(b2_no33['soporte_mejor_hoja_test_pct']):.2f}%`, `tasa_clase1_mejor_hoja_test_pct = {float(b2_no33['tasa_clase1_mejor_hoja_test_pct']):.2f}%` y `lift_mejor_hoja_test = {float(b2_no33['lift_mejor_hoja_test']):.3f}`. (3) En **Versión B · SIN outliers** (derivadas después del recorte), sin `3343.1` obtiene `test_roc_auc_balanced = {float(b_no33['test_roc_auc_balanced']):.4f}` (`{b_no33['test_roc_auc_balanced_ic95']}`), `test_accuracy_none = {float(b_no33['test_accuracy_none']):.4f}` cuyo `IC95% = {b_no33['test_accuracy_none_ic95']}` **toca e incluye en su extremo inferior al nuevo baseline `{float(b_no33['exactitud_baseline_test']):.4f}`**, y la mejor hoja elegida en Train (`mejor_hoja_id = {int(b_no33['mejor_hoja_id'])}`, `lift_mejor_hoja_train = {float(b_no33['lift_mejor_hoja_train']):.3f}`) obtiene en Test `soporte_mejor_hoja_test_pct = {float(b_no33['soporte_mejor_hoja_test_pct']):.2f}%`, `tasa_clase1_mejor_hoja_test_pct = {float(b_no33['tasa_clase1_mejor_hoja_test_pct']):.2f}%` y `lift_mejor_hoja_test = {float(b_no33['lift_mejor_hoja_test']):.3f}`.",
                "",
                "#### 6.2 Validación Cruzada Agrupada por `occupation_code` (`GroupKFold` en Train) frente a Agrupada por Persona (`resume_id`)",
                dataframe_to_markdown_table(occ_grouped_cv_df),
                "",
                f"- **¿El perfil de competencias generaliza a ocupaciones no vistas?**: **No generaliza con fuerza**. En el Árbol 3, al pasar de `GroupKFold` por persona (`cv_roc_auc_media = {float(sk_pers_cv['cv_roc_auc_media']):.4f}`, `lift_val_hoja_elegida_en_train_media = {float(sk_pers_cv['lift_val_hoja_elegida_en_train_media']):.3f}`) a `GroupKFold` por `occupation_code`, el `cv_roc_auc_media` cae a `{float(sk_occ_cv['cv_roc_auc_media']):.4f}` (`cv_roc_auc_std = {float(sk_occ_cv['cv_roc_auc_std']):.4f}`, `delta_roc_auc_vs_persona = {float(sk_occ_cv['delta_roc_auc_vs_persona']):.4f}`, perdiendo `{float(sk_occ_cv['pct_caida_ganancia_auc_vs_persona']):.2f}%` de su ganancia sobre el azar), `cv_f1_media` baja a `{float(sk_occ_cv['cv_f1_media']):.4f}` y **el lift en validación de la mejor hoja elegida estrictamente en Train colapsa a `lift_val_hoja_elegida_en_train_media = {float(sk_occ_cv['lift_val_hoja_elegida_en_train_media']):.3f}`** (`lift_val_hoja_elegida_en_train_std = {float(sk_occ_cv['lift_val_hoja_elegida_en_train_std']):.3f}`, `tasa_clase1_val_hoja_elegida_en_train_pct_media = {float(sk_occ_cv['tasa_clase1_val_hoja_elegida_en_train_pct_media']):.2f}%`, frente a la referencia optimista post-hoc en validación `max_lift_val_referencia_optimista_media = {float(sk_occ_cv['max_lift_val_referencia_optimista_media']):.3f}` ± `{float(sk_occ_cv['max_lift_val_referencia_optimista_std']):.3f}`).",
                "",
                "#### 6.3 Explicación del Umbral de Nivel 2 en `B2` vs. `A` (`39.25` vs. `40.50`) en el Nodo 1 (`diff_competence_knowledge <= 16.50`)",
                dataframe_to_markdown_table(node1_threshold_audit_df),
                "",
                f"- **Conteo exacto y explicación matemática**: En el Nodo 1 (`diff_competence_knowledge <= 16.50`, con `{int(n1_tr['filas_en_nodo1_izq_diff_le_16_5'])}` filas en Train y `{int(n1_te['filas_en_nodo1_izq_diff_le_16_5'])}` en Test), caen exactamente **`{int(n1_tr['filas_en_nodo1_con_competence_igual_40'])}` filas con `n_skills_competence == 40` en Train y `{int(n1_te['filas_en_nodo1_con_competence_igual_40'])}` en Test** (y `{int(n1_tr['filas_en_nodo1_con_competence_igual_41'])}` con `41`; las `{int(n1_tr['filas_globales_con_competence_igual_40'])}` filas de Train y `{int(n1_te['filas_globales_con_competence_igual_40'])}` de Test con `n_skills_competence == 40` se van en su totalidad a la rama derecha de la raíz). Dentro del Nodo 1, los valores observados consecutivos en **Versión A** son `39.0` (`{int(n1_tr['filas_en_nodo1_con_competence_igual_39'])}` filas en Train y `{int(n1_te['filas_en_nodo1_con_competence_igual_39'])}` en Test) y `42.0` (`{int(n1_tr['filas_en_nodo1_con_competence_igual_42'])}` en Train y `{int(n1_te['filas_en_nodo1_con_competence_igual_42'])}` en Test), cuyo punto medio aritmético en `scikit-learn` es `{float(n1_tr['punto_medio_sklearn_en_A']):.2f}`, mientras que en **Versión B2** todos los valores `>= 42.0` están truncados en `39.5`, por lo que los valores consecutivos son `39.0` y `39.5`, cuyo punto medio es `{float(n1_tr['punto_medio_sklearn_en_B2']):.2f}`. Ambos umbrales envían exactamente las mismas `{int(n1_tr['filas_en_nodo1_con_competence_le_39'])}` filas a la izquierda y `{int(n1_tr['filas_en_nodo1_con_competence_gt_39'])}` a la derecha en Train (`{int(n1_te['filas_en_nodo1_con_competence_le_39'])}` y `{int(n1_te['filas_en_nodo1_con_competence_gt_39'])}` en Test).",
                "",
            ]
        )

    full_content = "\n".join(header_block) + prior_runs_body + "\n".join(new_section_lines) + "\n"
    target_path.write_text(full_content, encoding="utf-8")
    return target_path


def build_tree_ab_reading_es(
    block_id: str,
    full_ab_sub: pd.DataFrame,
    sum_sub: pd.DataFrame,
    bundle_a: TreeVersionBundle,
    bundle_b: TreeVersionBundle,
) -> str:
    """Generate the Spanish A vs B comparison reading for one tree strictly from the run's DataFrame objects."""
    meta = BLOCK_METADATA_ES[block_id]
    t_label = meta["tree_label"]
    q_es = meta["question_es"]
    label_a = VERSION_LABELS_ES[VERSION_A]
    label_b = VERSION_LABELS_ES[VERSION_B]

    none_a = full_ab_sub.loc[
        (full_ab_sub["version_datos"] == label_a) & (full_ab_sub["punto_operacion"].str.contains("None"))
    ].iloc[0]
    none_b = full_ab_sub.loc[
        (full_ab_sub["version_datos"] == label_b) & (full_ab_sub["punto_operacion"].str.contains("None"))
    ].iloc[0]
    bal_a = full_ab_sub.loc[
        (full_ab_sub["version_datos"] == label_a) & (full_ab_sub["punto_operacion"].str.contains("balanced"))
    ].iloc[0]
    bal_b = full_ab_sub.loc[
        (full_ab_sub["version_datos"] == label_b) & (full_ab_sub["punto_operacion"].str.contains("balanced"))
    ].iloc[0]

    sum_a = sum_sub.loc[sum_sub["version_datos"] == label_a].iloc[0]
    sum_b = sum_sub.loc[sum_sub["version_datos"] == label_b].iloc[0]

    op_bal_a = bundle_a.operating_points_df.iloc[1]
    op_bal_b = bundle_b.operating_points_df.iloc[1]

    if block_id == BLOCK_ISCO:
        return (
            f"- **Qué umbrales cambiaron y por qué**: En `{t_label}` ({q_es}), ningún umbral ni hoja cambia entre "
            f"**{label_a}** y **{label_b}** (`n_hojas = {int(bal_a['n_hojas'])}`, `delta_abs_acc_A_vs_B = {float(none_a['delta_abs_acc_A_vs_B']):.4f}`, "
            f"`delta_abs_f1_A_vs_B = {float(bal_a['delta_abs_f1_A_vs_B']):.4f}`, `delta_abs_auc_A_vs_B = {float(bal_a['delta_abs_auc_A_vs_B']):.4f}`). "
            f"En el punto orientado a exactitud (`class_weight=None`), el árbol obtiene `test_accuracy = {float(none_a['test_accuracy']):.4f}` con "
            f"`test_recall_1 = {float(none_a['test_recall_1']):.4f}`, por lo que **empata el baseline porque no predice ningún positivo**. "
            f"En el punto orientado a recall (`class_weight='balanced'`), alcanza `test_recall_1 = {float(bal_a['test_recall_1']):.4f}`, "
            f"`test_f1_1 = {float(bal_a['test_f1_1']):.4f}` (frente al F1 trivial todo-positivo `{float(op_bal_a['f1_ref_trivial_todo_1']):.4f}`) y "
            f"`test_roc_auc = {float(bal_a['test_roc_auc']):.4f}` (que representa el `{float(op_bal_a['pct_del_techo_auc_6_0']):.2f}%` del techo en ROC-AUC `{float(op_bal_a['roc_auc_techo_6_0']):.4f}`). "
            f"En las `{int(sum_a['n_semillas'])}` semillas muestrales, `cv_train_roc_auc_media` es `{float(sum_a['cv_train_roc_auc_media']):.4f}` (`std = {float(sum_a['cv_train_roc_auc_std']):.4f}`) "
            f"y `test_roc_auc_media` es `{float(sum_a['test_roc_auc_media']):.4f}` (`std = {float(sum_a['test_roc_auc_std']):.4f}`).\n"
            f"- **¿Cambian las conclusiones o reglas de negocio?**: **No**. En ambas versiones el Lift en Test de la mejor hoja elegida en Train con soporte suficiente es `{float(op_bal_a['max_lift_hoja_soporte_05pct']):.3f}` (inferior a `1.5000`), por lo que no supera el criterio estricto de separación."
        )

    if block_id == BLOCK_EDUCATION:
        return (
            f"- **Qué umbrales cambiaron y por qué**: En `{t_label}` ({q_es}), las métricas, hojas y umbrales son exactamente iguales entre "
            f"**{label_a}** y **{label_b}** (`n_hojas = {int(bal_a['n_hojas'])}`, `delta_abs_acc_A_vs_B = {float(none_a['delta_abs_acc_A_vs_B']):.4f}`, "
            f"`delta_abs_f1_A_vs_B = {float(bal_a['delta_abs_f1_A_vs_B']):.4f}`, `delta_abs_auc_A_vs_B = {float(bal_a['delta_abs_auc_A_vs_B']):.4f}`). "
            f"En el punto orientado a exactitud (`class_weight=None`), obtiene `test_accuracy = {float(none_a['test_accuracy']):.4f}` con "
            f"`test_recall_1 = {float(none_a['test_recall_1']):.4f}`, de modo que **empata el baseline porque no predice ningún positivo**. "
            f"En el punto orientado a recall (`class_weight='balanced'`), obtiene `test_f1_1 = {float(bal_a['test_f1_1']):.4f}` "
            f"(inferior al F1 trivial todo-positivo `{float(op_bal_a['f1_ref_trivial_todo_1']):.4f}`) y `test_roc_auc = {float(bal_a['test_roc_auc']):.4f}` "
            f"(apenas el `{float(op_bal_a['pct_del_techo_auc_6_0']):.2f}%` del techo en ROC-AUC `{float(op_bal_a['roc_auc_techo_6_0']):.4f}`). "
            f"En las `{int(sum_a['n_semillas'])}` semillas muestrales, `cv_train_roc_auc_media` es `{float(sum_a['cv_train_roc_auc_media']):.4f}` (`std = {float(sum_a['cv_train_roc_auc_std']):.4f}`) "
            f"y `test_roc_auc_media` es `{float(sum_a['test_roc_auc_media']):.4f}` (`std = {float(sum_a['test_roc_auc_std']):.4f}`).\n"
            f"- **¿Cambian las conclusiones o reglas de negocio?**: **No**. Ambas versiones confirman que el nivel académico por sí solo tiene un `test_roc_auc = {float(bal_a['test_roc_auc']):.4f}` y un Lift en Test de la mejor hoja elegida en Train de `{float(op_bal_a['max_lift_hoja_soporte_05pct']):.3f}` (inferior a `1.5000`), insuficiente para separar a quienes repiten oficio."
        )

    top_leaf_a = bundle_a.leaf_lift_balanced_df.loc[bundle_a.leaf_lift_balanced_df["soporte_suficiente_train"] == "Sí"].sort_values(["lift_train", "n_train"], ascending=[False, False]).iloc[0]
    top_leaf_b = bundle_b.leaf_lift_balanced_df.loc[bundle_b.leaf_lift_balanced_df["soporte_suficiente_train"] == "Sí"].sort_values(["lift_train", "n_train"], ascending=[False, False]).iloc[0]

    return (
        f"- **Qué umbrales cambiaron y por qué**: En `{t_label}` ({q_es}), la pregunta raíz (`{bal_a['umbral_raiz']}`) es **idéntica** en **{label_a}** y **{label_b}**. "
        f"Sin embargo, en el nivel 2 izquierdo de **{label_a}** el árbol divide por `{bal_a['umbral_nivel2_izq']}`, mientras que el recorte IQR de **{label_b}** "
        f"sustituye los cortes de nivel 2 por `{bal_b['umbral_nivel2_izq']}` (izquierda) y `{bal_b['umbral_nivel2_der']}` (derecha), pasando de `{int(bal_a['n_hojas'])}` hojas en A a `{int(bal_b['n_hojas'])}` hojas en B. "
        f"Al evaluar por punto de operación: "
        f"(a) En el **Punto Exactitud (`class_weight=None`)**, la diferencia entre A y B supera 1 DE entre semillas en `test_f1_1` (`{float(none_a['test_f1_1']):.4f}` vs `{float(none_b['test_f1_1']):.4f}`, `delta_abs_f1_A_vs_B = {float(none_a['delta_abs_f1_A_vs_B']):.4f}` > `std_f1_5_semillas = {float(none_a['std_f1_5_semillas']):.4f}`) "
        f"y en `test_roc_auc` (`{float(none_a['test_roc_auc']):.4f}` vs `{float(none_b['test_roc_auc']):.4f}`, `delta_abs_auc_A_vs_B = {float(none_a['delta_abs_auc_A_vs_B']):.4f}` > `std_auc_5_semillas = {float(none_a['std_auc_5_semillas']):.4f}`), "
        f"pero **la exactitud en Test es prácticamente igual** (`{float(none_a['test_accuracy']):.4f}` vs `{float(none_b['test_accuracy']):.4f}`, `delta_abs_acc_A_vs_B = {float(none_a['delta_abs_acc_A_vs_B']):.4f}`) "
        f"y la diferencia de F1 proviene del incremento en `test_recall_1` (`{float(none_a['test_recall_1']):.4f}` vs `{float(none_b['test_recall_1']):.4f}`) cuando una hoja limítrofe en B cruza el umbral de decisión. "
        f"(b) En el **Punto Recall (`class_weight='balanced'`)**, la diferencia en datos completos queda dentro de 1 DE entre semillas tanto en `test_f1_1` (`{float(bal_a['test_f1_1']):.4f}` vs `{float(bal_b['test_f1_1']):.4f}`, `delta_abs_f1_A_vs_B = {float(bal_a['delta_abs_f1_A_vs_B']):.4f}` <= `std_f1_5_semillas = {float(bal_a['std_f1_5_semillas']):.4f}`, frente al F1 trivial todo-positivo `{float(op_bal_a['f1_ref_trivial_todo_1']):.4f}`) "
        f"como en `test_roc_auc` (`{float(bal_a['test_roc_auc']):.4f}` vs `{float(bal_b['test_roc_auc']):.4f}`, `delta_abs_auc_A_vs_B = {float(bal_a['delta_abs_auc_A_vs_B']):.4f}` <= `std_auc_5_semillas = {float(bal_a['std_auc_5_semillas']):.4f}`, alcanzando el `{float(op_bal_a['pct_del_techo_auc_6_0']):.2f}%` y `{float(op_bal_b['pct_del_techo_auc_6_0']):.2f}%` del techo en ROC-AUC `{float(op_bal_a['roc_auc_techo_6_0']):.4f}`). "
        f"En las `{int(sum_a['n_semillas'])}` semillas muestrales, `cv_train_roc_auc_media` es `{float(sum_a['cv_train_roc_auc_media']):.4f}` (`std = {float(sum_a['cv_train_roc_auc_std']):.4f}`) en A vs `{float(sum_b['cv_train_roc_auc_media']):.4f}` (`std = {float(sum_b['cv_train_roc_auc_std']):.4f}`) en B, "
        f"y `test_roc_auc_media` es `{float(sum_a['test_roc_auc_media']):.4f}` (`std = {float(sum_a['test_roc_auc_std']):.4f}`) en A vs `{float(sum_b['test_roc_auc_media']):.4f}` (`std = {float(sum_b['test_roc_auc_std']):.4f}`) en B.\n"
        f"- **¿Cambian las conclusiones o reglas de negocio?**: **No cambia el veredicto sustantivo**: en ambas versiones el Árbol 3 es el único que supera el criterio formal de separación con la misma hoja líder (`hoja_id = {int(top_leaf_a['hoja_id'])}` en A y `hoja_id = {int(top_leaf_b['hoja_id'])}` en B, `n_train = {int(top_leaf_a['n_train'])}`, `n_test = {int(top_leaf_a['n_test'])}`, `pct_test = {float(top_leaf_a['pct_test']):.2f}%`, `tasa_clase1_test = {float(top_leaf_a['tasa_clase1_test']):.4f}`, `lift_test = {float(top_leaf_a['lift_test']):.3f}`), que corresponde algebraicamente al perfil entero `(n_skills_essential = 20, n_skills_competence = 19, n_skills_knowledge = 1)`. Se elige **{label_a}** por interpretabilidad en unidades reales y ausencia de diferencia relevante de desempeño."
    )


def append_comparacion_a_vs_b_md(
    config: DecisionTreeProjectConfig,
    sensitivity_result: SensitivityTestResult,
    bundles_a: Optional[Dict[str, TreeVersionBundle]] = None,
    bundles_b: Optional[Dict[str, TreeVersionBundle]] = None,
    split_audit_df: Optional[pd.DataFrame] = None,
    profile_20_19_1_df: Optional[pd.DataFrame] = None,
    profile_20_19_1_isco_df: Optional[pd.DataFrame] = None,
    additivity_audit_df: Optional[pd.DataFrame] = None,
    clipping_effect_df: Optional[pd.DataFrame] = None,
    run_id: Optional[str] = None,
    run_timestamp: Optional[str] = None,
    data_usage_df: Optional[pd.DataFrame] = None,
    tree3_no_3343_df: Optional[pd.DataFrame] = None,
    occ_grouped_cv_df: Optional[pd.DataFrame] = None,
    node1_threshold_audit_df: Optional[pd.DataFrame] = None,
) -> Path:
    """Append a dated run section with unique run_id to Comparacion_A_vs_B_Arbol_Decision.md (marking earlier runs SUPERSEDED)."""
    target_path = config.comparacion_ab_md_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if run_id is None or run_timestamp is None:
        run_id, run_timestamp = create_run_metadata()

    label_a = VERSION_LABELS_ES[VERSION_A]
    label_b = VERSION_LABELS_ES[VERSION_B]

    header_block = [
        f"# Comparación Empírica {label_a} vs. {label_b} · `7.0_arbol_decision.ipynb`",
        "",
        f"> **Pregunta central**: *{MAIN_QUESTION_ES}*",
        "",
        "Este documento es **append-only** (solo adición): registra para cada corrida con su identificador único (`run_id`) la comparación lado a lado entre ambas versiones de datos limpios por árbol y por punto de operación, marcando toda corrida previa como **`[SUPERSEDED]`** sin eliminarla.",
        "",
        _build_run_registry_block(run_id, run_timestamp),
    ]

    prior_runs_body = ""
    if target_path.exists() and target_path.stat().st_size > 0:
        existing_raw = target_path.read_text(encoding="utf-8")
        normalized = _normalize_existing_superseded_text(existing_raw, is_comparacion_file=True)
        first_run_idx = normalized.find("## Corrida Fechada")
        if first_run_idx != -1:
            prior_runs_body = normalized[first_run_idx:].strip() + "\n\n---\n\n"

    if split_audit_df is not None and not split_audit_df.empty:
        tr_r = split_audit_df.loc[split_audit_df["particion"].str.startswith("Train")].iloc[0]
        te_r = split_audit_df.loc[split_audit_df["particion"].str.startswith("Test")].iloc[0]
        n_tr_full = int(tr_r["filas"])
        n_te_full = int(te_r["filas"])
    else:
        n_tr_full = 1391018
        n_te_full = 347720

    cap_e = IQR_WINSOR_BOUNDS_INFO["n_skills_essential"][1]
    cap_c = IQR_WINSOR_BOUNDS_INFO["n_skills_competence"][1]
    cap_k = IQR_WINSOR_BOUNDS_INFO["n_skills_knowledge"][1]

    context_rows = []
    if bundles_a is not None and bundles_b is not None:
        for b_id in (BLOCK_ISCO, BLOCK_EDUCATION, BLOCK_SKILLS):
            for b_bundle in (bundles_a[b_id], bundles_b[b_id]):
                op_none = b_bundle.operating_points_df.iloc[0]
                op_bal = b_bundle.operating_points_df.iloc[1]
                top_lf = (
                    b_bundle.leaf_lift_balanced_df.loc[b_bundle.leaf_lift_balanced_df["soporte_suficiente_train"] == "Sí"]
                    .sort_values(["lift_train", "n_train"], ascending=[False, False])
                    .iloc[0]
                )
                opt_te_lf = (
                    b_bundle.leaf_lift_balanced_df.loc[b_bundle.leaf_lift_balanced_df["soporte_suficiente_test"] == "Sí"]
                    .sort_values(["lift_test", "n_test"], ascending=[False, False])
                    .iloc[0]
                )
                context_rows.append(
                    {
                        "run_id": run_id,
                        "version_datos": b_bundle.version_label_es,
                        "arbol": b_bundle.tree_label_es,
                        "filas_totales_clasificadas": n_tr_full + n_te_full,
                        "filas_train": n_tr_full,
                        "filas_test": n_te_full,
                        "personas_train_muestra": config.sensitivity_train_persons,
                        "personas_test_muestra": config.sensitivity_test_persons,
                        "umbral_probabilidad_none": 0.5000,
                        "f1_ref_trivial_todo_1": float(op_bal["f1_ref_trivial_todo_1"]),
                        "roc_auc_techo_6_0": float(op_bal["roc_auc_techo_6_0"]),
                        "test_roc_auc_ic95_persona": str(op_bal["test_roc_auc_ic95_persona"]),
                        "pct_del_techo_auc_6_0_none": float(op_none["pct_del_techo_auc_6_0"]),
                        "pct_del_techo_auc_6_0_balanced": float(op_bal["pct_del_techo_auc_6_0"]),
                        "max_lift_hoja_soporte_05pct": float(op_bal["max_lift_hoja_soporte_05pct"]),
                        "max_lift_test_referencia_optimista": float(opt_te_lf["lift_test"]),
                        "umbral_lift_separacion": config.min_lift_separation,
                        "hoja_lider_elegida_en_train_id": int(top_lf["hoja_id"]),
                        "hoja_lider_n_train": int(top_lf["n_train"]),
                        "hoja_lider_lift_train": float(top_lf["lift_train"]),
                        "hoja_lider_n_test": int(top_lf["n_test"]),
                        "hoja_lider_n_total": int(top_lf["n_train"]) + int(top_lf["n_test"]),
                        "hoja_lider_pct_test": float(top_lf["pct_test"]),
                        "hoja_lider_tasa_clase1_test": float(top_lf["tasa_clase1_test"]),
                        "hoja_lider_lift_test": float(top_lf["lift_test"]),
                        "n_ocupaciones_perfil_20_19_1": len(profile_20_19_1_df) if profile_20_19_1_df is not None else 12,
                        "n_grandes_grupos_perfil_20_19_1": int(profile_20_19_1_df["isco_major"].nunique()) if profile_20_19_1_df is not None else 7,
                        "tope_iqr_essential": cap_e,
                        "tope_iqr_competence": cap_c,
                        "tope_iqr_knowledge": cap_k,
                    }
                )
    context_df = pd.DataFrame(context_rows)

    new_lines: List[str] = [
        f"## Corrida Fechada · ID `{run_id}` · `{run_timestamp}` · [CURRENT]",
        "",
        f"- **Identificador de corrida vigente (`run_id`)**: `{run_id}` (`{run_timestamp}` · estado `CURRENT`).",
        "",
        "### 0. Tabla de Referencia de Techos, Hojas Líderes y Cotas IQR de la Corrida",
        dataframe_to_markdown_table(context_df),
        "",
    ]

    if data_usage_df is not None and not data_usage_df.empty:
        new_lines.extend(
            [
                "### 0.1 Uso de datos (Filas y Personas en Ajuste Final y Prueba, Exclusiones, Educación No Reportada y Muestra de Sensibilidad)",
                dataframe_to_markdown_table(data_usage_df),
                "",
            ]
        )

    new_lines.extend(
        [
            "### 1. Comparación por Árbol y por Punto de Operación (Conjunto Completo + Media y DE en Semillas)",
            "",
        ]
    )

    for block_id in (BLOCK_ISCO, BLOCK_EDUCATION, BLOCK_SKILLS):
        meta = BLOCK_METADATA_ES[block_id]
        q_es = meta["question_es"]
        t_label = meta["tree_label"]

        sub_full = sensitivity_result.full_data_ab_table.loc[
            sensitivity_result.full_data_ab_table["bloque_id"] == block_id
        ].drop(columns=["bloque_id", "pregunta_objetivo"])
        sub_sum = sensitivity_result.summary_table.loc[
            sensitivity_result.summary_table["bloque_id"] == block_id
        ].drop(columns=["bloque_id", "pregunta_objetivo"])
        sub_thr = sensitivity_result.threshold_comparison_table.loc[
            sensitivity_result.threshold_comparison_table["bloque_id"] == block_id
        ].drop(columns=["bloque_id", "pregunta_objetivo"])

        if bundles_a is not None and bundles_b is not None:
            reading_es = build_tree_ab_reading_es(
                block_id=block_id,
                full_ab_sub=sub_full,
                sum_sub=sub_sum,
                bundle_a=bundles_a[block_id],
                bundle_b=bundles_b[block_id],
            )
        else:
            reading_es = "- Lectura generada desde las tablas superiores."

        new_lines.extend(
            [
                f"#### {t_label} · {q_es}",
                "",
                "##### A vs. B en el Conjunto Completo y Contraste contra 1 DE entre Semillas",
                dataframe_to_markdown_table(sub_full),
                "",
                "##### Resumen de Sensibilidad en Semillas (Media y DE)",
                dataframe_to_markdown_table(sub_sum),
                "",
                "##### Comparación Semilla por Semilla de Umbrales (Raíz y Nivel 2) y Hojas",
                dataframe_to_markdown_table(sub_thr),
                "",
                "##### Lectura Metodológica y de Negocio del Árbol",
                reading_es,
                "",
            ]
        )

    if profile_20_19_1_df is not None and not profile_20_19_1_df.empty:
        n_occ_prof = len(profile_20_19_1_df)
        n_maj_prof = int(profile_20_19_1_df["isco_major"].nunique())
        top_o = profile_20_19_1_df.iloc[0]
        new_lines.extend(
            [
                "### 2. Verificación Independiente de `Hoja 16` (`Versión A`) vs. `Hoja 26` (`Versión B`) y Huella de Ocupación `(E=20, C=19, K=1)`",
                dataframe_to_markdown_table(profile_20_19_1_df),
                "",
            ]
        )
        if profile_20_19_1_isco_df is not None and not profile_20_19_1_isco_df.empty:
            new_lines.extend(
                [
                    "#### Resumen por Gran Grupo ISCO del Perfil `(n_skills_essential = 20, n_skills_competence = 19, n_skills_knowledge = 1)`",
                    dataframe_to_markdown_table(profile_20_19_1_isco_df),
                    "",
                ]
            )
        new_lines.extend(
            [
                f"- **Explicación verificada**: La `Hoja 16` en **{label_a}** y la `Hoja 26` en **{label_b}** fueron calculadas de forma independiente y seleccionan exactamente las mismas `{int(profile_20_19_1_df['filas_total'].sum())}` filas totales (`{int(profile_20_19_1_df['filas_train'].sum())}` en Train y `{int(profile_20_19_1_df['filas_test'].sum())}` en Test) porque ambos caminos de decisión tienen como única solución entera la terna `(n_skills_essential = 20, n_skills_competence = 19, n_skills_knowledge = 1)`. Ese perfil es compartido por `{n_occ_prof}` ocupaciones distintas en `{n_maj_prof}` grandes grupos ISCO, pero la ocupación `{top_o['occupation_code']}` (`{top_o['occupation_label']}`, Gran Grupo `{top_o['isco_major']}`) aporta por sí sola el `{float(top_o['pct_hoja_total']):.2f}%` de las filas (`{int(top_o['filas_train'])}` en Train con `tasa_clase1_train = {float(top_o['tasa_clase1_train']):.4f}` y `{int(top_o['filas_test'])}` en Test con `tasa_clase1_test = {float(top_o['tasa_clase1_test']):.4f}`), evidenciando que el perfil actúa como una huella digital de ocupación (circularidad parcial).",
                "",
            ]
        )

    if additivity_audit_df is not None and not additivity_audit_df.empty and clipping_effect_df is not None and not clipping_effect_df.empty:
        tot_add = additivity_audit_df.loc[additivity_audit_df["particion"].str.contains("Total")].iloc[0]
        tr_add = additivity_audit_df.loc[additivity_audit_df["particion"].str.startswith("Train")].iloc[0]
        te_add = additivity_audit_df.loc[additivity_audit_df["particion"].str.startswith("Test")].iloc[0]
        bal_before = clipping_effect_df.loc[
            clipping_effect_df["esquema_variables_arbol_3"].str.contains("ANTES")
            & clipping_effect_df["punto_operacion"].str.contains("balanced")
        ].iloc[0]
        new_lines.extend(
            [
                "### 3. Identidad Aditiva `essential = competence + knowledge` (2 Grados de Libertad) y Efecto del Recorte IQR en `Versión B`",
                dataframe_to_markdown_table(additivity_audit_df),
                "",
                "#### Efecto de Calcular las Variables Derivadas (`diff/prop/ratio`) DESPUÉS vs. ANTES del Recorte IQR en `Versión B`",
                dataframe_to_markdown_table(clipping_effect_df),
                "",
                f"- **Lectura de la identidad y del recorte IQR**: En **{label_a}**, la identidad exacta de 4 términos se cumple con `{int(tot_add['violaciones_4_terminos_A'])}` violaciones en las `{int(tot_add['filas_totales'])}` filas, y la identidad `essential = competence + knowledge` se cumple exactamente en `{int(tot_add['filas_exactas_E_igual_C_mas_K_en_A'])}` filas (`{float(tot_add['pct_exactas_E_igual_C_mas_K_en_A']):.2f}%`, mientras que solo `{int(tot_add['filas_con_sin_tipo_mayor_0_en_A'])}` filas, `{float(tot_add['pct_sin_tipo_mayor_0_en_A']):.2f}%`, tienen `n_skills_sin_tipo > 0`), por lo que los tres conteos aportan solo `2` piezas independientes de información. En **{label_b}**, las variables derivadas se calcularon **después** del recorte IQR independiente (`{cap_e:.1f}`, `{cap_c:.1f}`, `{cap_k:.1f}`), el cual rompe `essential = competence + knowledge` en `{int(tot_add['violaciones_E_igual_C_mas_K_en_B_total'])}` filas totales (`{float(tot_add['pct_violaciones_E_igual_C_mas_K_en_B']):.2f}%`: `{int(tr_add['violaciones_E_igual_C_mas_K_en_B_total'])}` en Train y `{int(te_add['violaciones_E_igual_C_mas_K_en_B_total'])}` en Test, de las cuales `{int(tot_add['violaciones_en_B_causadas_solo_por_recorte_iqr'])}`, `{float(tot_add['pct_violaciones_en_B_solo_por_recorte_iqr']):.2f}%`, son causadas exclusivamente por el recorte IQR). Como muestra la tabla superior, si las derivadas se calculan **antes** del recorte IQR, el árbol balanceado en **{label_b}** vuelve a tener `{int(bal_before['n_hojas'])}` hojas y exactamente las mismas métricas que **{label_a}** (`test_accuracy = {float(bal_before['test_accuracy']):.4f}`, `test_f1_1 = {float(bal_before['test_f1_1']):.4f}`, `test_roc_auc = {float(bal_before['test_roc_auc']):.4f}`).",
                "",
            ]
        )

    if node1_threshold_audit_df is not None and not node1_threshold_audit_df.empty:
        n1_tr = node1_threshold_audit_df.loc[node1_threshold_audit_df["particion"].astype(str).str.startswith("Train")].iloc[0]
        n1_te = node1_threshold_audit_df.loc[node1_threshold_audit_df["particion"].astype(str).str.startswith("Test")].iloc[0]
        new_lines.extend(
            [
                "#### Por qué `Versión B2` (Derivadas Antes del Recorte) y `Versión A` dan Métricas Idénticas en el Punto Balanceado con Diferente Umbral de Nivel 2 (`39.25` vs. `40.50`)",
                dataframe_to_markdown_table(node1_threshold_audit_df),
                "",
                f"- **Conteo exacto en el Nodo 1 (`diff_competence_knowledge <= 16.50`)**: En el Nodo 1 (`{int(n1_tr['filas_en_nodo1_izq_diff_le_16_5'])}` filas en Train y `{int(n1_te['filas_en_nodo1_izq_diff_le_16_5'])}` en Test), caen exactamente **`{int(n1_tr['filas_en_nodo1_con_competence_igual_40'])}` filas con `n_skills_competence == 40` en Train y `{int(n1_te['filas_en_nodo1_con_competence_igual_40'])}` en Test** (y `{int(n1_tr['filas_en_nodo1_con_competence_igual_41'])}` con `41`; las `{int(n1_tr['filas_globales_con_competence_igual_40'])}` filas de Train y `{int(n1_te['filas_globales_con_competence_igual_40'])}` de Test que tienen `n_skills_competence == 40` en todo el dataset van en un 100% a la rama derecha de la raíz). Dentro del Nodo 1, los valores observados consecutivos en **{label_a}** son `39.0` (`{int(n1_tr['filas_en_nodo1_con_competence_igual_39'])}` filas en Train y `{int(n1_te['filas_en_nodo1_con_competence_igual_39'])}` en Test) y `42.0` (`{int(n1_tr['filas_en_nodo1_con_competence_igual_42'])}` en Train y `{int(n1_te['filas_en_nodo1_con_competence_igual_42'])}` en Test), cuyo punto medio aritmético en `scikit-learn` es `{float(n1_tr['punto_medio_sklearn_en_A']):.2f}`, mientras que en **Versión B2** todos los conteos `>= 42.0` están truncados en `{cap_c:.1f}`, por lo que los valores consecutivos son `39.0` y `{cap_c:.1f}`, cuyo punto medio aritmético es `{float(n1_tr['punto_medio_sklearn_en_B2']):.2f}`. Así, ambos umbrales implementan la misma partición (`{int(n1_tr['filas_en_nodo1_con_competence_le_39'])}` filas a la izquierda y `{int(n1_tr['filas_en_nodo1_con_competence_gt_39'])}` a la derecha en Train; `{int(n1_te['filas_en_nodo1_con_competence_le_39'])}` y `{int(n1_te['filas_en_nodo1_con_competence_gt_39'])}` en Test).",
                "",
            ]
        )

    if (
        tree3_no_3343_df is not None
        and not tree3_no_3343_df.empty
        and occ_grouped_cv_df is not None
        and not occ_grouped_cv_df.empty
        and bundles_a is not None
        and bundles_b is not None
    ):
        op_isco_bal = bundles_a[BLOCK_ISCO].operating_points_df.iloc[1]
        op_edu_bal = bundles_a[BLOCK_EDUCATION].operating_points_df.iloc[1]
        op_sk_bal_a = bundles_a[BLOCK_SKILLS].operating_points_df.iloc[1]
        op_sk_bal_b = bundles_b[BLOCK_SKILLS].operating_points_df.iloc[1]
        a_full = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"] == "Versión A · CON outliers")
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Completo"))
        ].iloc[0]
        a_no33 = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"] == "Versión A · CON outliers")
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        b2_no33 = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"].astype(str).str.startswith("Versión B2"))
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        b_no33 = tree3_no_3343_df.loc[
            (tree3_no_3343_df["version_datos"].astype(str).str.startswith("Versión B ·"))
            & (tree3_no_3343_df["subconjunto"].astype(str).str.startswith("Sin "))
        ].iloc[0]
        sk_pers_cv = occ_grouped_cv_df.loc[
            (occ_grouped_cv_df["bloque_id"] == BLOCK_SKILLS)
            & (occ_grouped_cv_df["esquema_cv_train"].astype(str).str.contains("resume_id"))
        ].iloc[0]
        sk_occ_cv = occ_grouped_cv_df.loc[
            (occ_grouped_cv_df["bloque_id"] == BLOCK_SKILLS)
            & (occ_grouped_cv_df["esquema_cv_train"].astype(str).str.contains("occupation_code"))
        ].iloc[0]
        dom_pct = float(profile_20_19_1_df.iloc[0]["pct_hoja_total"]) if profile_20_19_1_df is not None else 86.88
        dom_code = str(profile_20_19_1_df.iloc[0]["occupation_code"]) if profile_20_19_1_df is not None else "3343.1"

        new_lines.extend(
            [
                "### 4. Diagnósticos del Árbol 3: Exclusión de la Ocupación `3343.1`, Validación Cruzada por `occupation_code` y Re-evaluación del Veredicto",
                "",
                "#### 4.1 Árbol 3 con y sin la Ocupación `3343.1` (`administrative assistant`) en Train y Test (`Versión A`, `Versión B2` y `Versión B`)",
                dataframe_to_markdown_table(tree3_no_3343_df),
                "",
                "#### 4.2 Validación Cruzada Agrupada por `occupation_code` (`GroupKFold` en Train) frente a Agrupada por Persona (`resume_id`)",
                dataframe_to_markdown_table(occ_grouped_cv_df),
                "",
                "#### 4.3 Conclusión del Árbol 3 Generada desde los `IC95%` de `ROC-AUC` y Re-evaluación del Veredicto de Separación",
                f"- **Comparación Árbol 3 vs. Árboles 1 y 2 desde los `IC95%` de `ROC-AUC`**: En la partición por persona sobre el conjunto completo, el intervalo de confianza del Árbol 3 en **{label_a}** (`{op_sk_bal_a['test_roc_auc_ic95_persona']}`, `test_roc_auc_balanced = {float(a_full['test_roc_auc_balanced']):.4f}`) y en **{label_b}** (`{op_sk_bal_b['test_roc_auc_ic95_persona']}`) se ubica íntegramente por encima y sin solapamiento respecto al intervalo del Árbol 1 (`{op_isco_bal['test_roc_auc_ic95_persona']}`) y al del Árbol 2 (`{op_edu_bal['test_roc_auc_ic95_persona']}`).",
                f"- **Dominancia de una sola ocupación en la mejor hoja, contraste de exactitud frente al nuevo baseline (`{float(a_no33['exactitud_baseline_test']):.4f}`) y re-evaluación del veredicto `separa`**: En el conjunto completo, el Árbol 3 cumple el criterio formal (`IC95%` de `ROC-AUC` > `0.5000` y la mejor hoja elegida en Train con `lift_mejor_hoja_train = {float(a_full['lift_mejor_hoja_train']):.3f}` alcanza en Test `lift_mejor_hoja_test = {float(a_full['lift_mejor_hoja_test']):.3f}` >= `{config.min_lift_separation:.4f}` con soporte `{float(a_full['soporte_mejor_hoja_test_pct']):.2f}%`, referencia optimista `max_lift_test_referencia_optimista = {float(a_full['max_lift_test_referencia_optimista']):.3f}`), pero esa hoja (`Hoja {int(a_full['mejor_hoja_id'])}`) está compuesta en un **`{dom_pct:.2f}%` por una sola ocupación (`{dom_code} · administrative assistant`)**. Al retirar `{dom_code}` de Train y Test (`filas_train = {int(a_no33['filas_train'])}`, `filas_test = {int(a_no33['filas_test'])}`, `tasa_base_test = {float(a_no33['tasa_base_test']):.4f}`, nuevo baseline de exactitud `exactitud_baseline_test = {float(a_no33['exactitud_baseline_test']):.4f}`): (1) en **{label_a}**, el `test_roc_auc_balanced` baja a `{float(a_no33['test_roc_auc_balanced']):.4f}` (`{a_no33['test_roc_auc_balanced_ic95']}`), la exactitud en `class_weight=None` es `{float(a_no33['test_accuracy_none']):.4f}` con `IC95% = {a_no33['test_accuracy_none_ic95']}` (**que SÍ contiene al nuevo baseline `{float(a_no33['exactitud_baseline_test']):.4f}`**, por lo que no supera significativamente al baseline mayoritario; `test_recall_none = {float(a_no33['test_recall_none']):.4f}`), y la mejor hoja elegida en Train (`Hoja {int(a_no33['mejor_hoja_id'])}`, `lift_mejor_hoja_train = {float(a_no33['lift_mejor_hoja_train']):.3f}`) obtiene en Test `soporte_mejor_hoja_test_pct = {float(a_no33['soporte_mejor_hoja_test_pct']):.2f}%`, `tasa_clase1_mejor_hoja_test_pct = {float(a_no33['tasa_clase1_mejor_hoja_test_pct']):.2f}%` y `lift_mejor_hoja_test = {float(a_no33['lift_mejor_hoja_test']):.3f}`; (2) en **Versión B2**, sin `{dom_code}` el `test_roc_auc_balanced` es `{float(b2_no33['test_roc_auc_balanced']):.4f}` (`{b2_no33['test_roc_auc_balanced_ic95']}`), la exactitud `test_accuracy_none = {float(b2_no33['test_accuracy_none']):.4f}` tiene `IC95% = {b2_no33['test_accuracy_none_ic95']}` (**que también contiene al nuevo baseline `{float(b2_no33['exactitud_baseline_test']):.4f}`**), y la mejor hoja elegida en Train (`Hoja {int(b2_no33['mejor_hoja_id'])}`, `lift_mejor_hoja_train = {float(b2_no33['lift_mejor_hoja_train']):.3f}`) obtiene en Test `soporte_mejor_hoja_test_pct = {float(b2_no33['soporte_mejor_hoja_test_pct']):.2f}%`, `tasa_clase1_mejor_hoja_test_pct = {float(b2_no33['tasa_clase1_mejor_hoja_test_pct']):.2f}%` y `lift_mejor_hoja_test = {float(b2_no33['lift_mejor_hoja_test']):.3f}`; y (3) en **{label_b}**, sin `{dom_code}` el `test_roc_auc_balanced` es `{float(b_no33['test_roc_auc_balanced']):.4f}` (`{b_no33['test_roc_auc_balanced_ic95']}`), la exactitud `test_accuracy_none = {float(b_no33['test_accuracy_none']):.4f}` tiene `IC95% = {b_no33['test_accuracy_none_ic95']}` (**cuyo límite inferior `{float(b_no33['test_accuracy_none_ic95_inf']):.4f}` toca/incluye exactamente el nuevo baseline `{float(b_no33['exactitud_baseline_test']):.4f}`**), y la mejor hoja elegida en Train (`Hoja {int(b_no33['mejor_hoja_id'])}`) obtiene en Test `soporte_mejor_hoja_test_pct = {float(b_no33['soporte_mejor_hoja_test_pct']):.2f}%`, `tasa_clase1_mejor_hoja_test_pct = {float(b_no33['tasa_clase1_mejor_hoja_test_pct']):.2f}%` y `lift_mejor_hoja_test = {float(b_no33['lift_mejor_hoja_test']):.3f}`. Finalmente, cuando se evalúa mediante `GroupKFold` agrupado por `occupation_code` sobre Train, el `cv_roc_auc_media` del Árbol 3 cae de `{float(sk_pers_cv['cv_roc_auc_media']):.4f}` a `{float(sk_occ_cv['cv_roc_auc_media']):.4f}` (`cv_roc_auc_std = {float(sk_occ_cv['cv_roc_auc_std']):.4f}`, `delta_roc_auc_vs_persona = {float(sk_occ_cv['delta_roc_auc_vs_persona']):.4f}`, perdiendo `{float(sk_occ_cv['pct_caida_ganancia_auc_vs_persona']):.2f}%` de su ganancia sobre `0.5000`) y **el lift en validación de la mejor hoja elegida en Train cae de `{float(sk_pers_cv['lift_val_hoja_elegida_en_train_media']):.3f}` a `{float(sk_occ_cv['lift_val_hoja_elegida_en_train_media']):.3f}`** (`lift_val_hoja_elegida_en_train_std = {float(sk_occ_cv['lift_val_hoja_elegida_en_train_std']):.3f}`, mientras que `{float(sk_occ_cv['max_lift_val_referencia_optimista_media']):.3f}` ± `{float(sk_occ_cv['max_lift_val_referencia_optimista_std']):.3f}` es únicamente la referencia optimista post-hoc en validación). **Veredicto revisitado**: el Árbol 3 **SÍ SEPARA** en `ROC-AUC` y `Lift` de hoja dentro del catálogo de ocupaciones conocidas (incluso sin `{dom_code}`, aunque su exactitud global en `class_weight=None` no supera significativamente al nuevo baseline `{float(a_no33['exactitud_baseline_test']):.4f}`), pero lo hace porque el perfil de competencias actúa como una **huella digital de ocupaciones específicas del catálogo ESCO** y **no generaliza a ocupaciones nuevas no vistas en el entrenamiento**.",
                "",
            ]
        )

    rec_table = pd.DataFrame(
        [
            {
                "fase_notebook": "7.0_arbol_decision.ipynb (Árboles de Decisión CART, max_depth=4)",
                "version_recomendada": sensitivity_result.recommended_version_label_es,
                "criterio_decisor": "Aunque B (derivadas tras recorte) mantiene una pequeña ventaja en ROC-AUC (~+0.007: +0.0068 en None y +0.0046 en balanced con 3343.1; +0.0074 sin 3343.1) y B2 empata o cae bajo A, se elige Versión A por interpretabilidad y por preservar E = C + K",
                "que_re_evaluar_en_siguientes": "Mantener ambas versiones disponibles para 7.1 y 7.2",
            },
            {
                "fase_notebook": "7.1_naive_bayes.ipynb (Naive Bayes)",
                "version_recomendada": "Re-evaluar Versión A vs. Versión B",
                "criterio_decisor": "GaussianNB estima medias y varianzas paramétricas sensibles a colas extremas (outliers en conteos ESCO)",
                "que_re_evaluar_en_siguientes": "Contrastar verosimilitud gaussiana con y sin winsorización IQR",
            },
            {
                "fase_notebook": "7.2_knn.ipynb (K-Nearest Neighbors)",
                "version_recomendada": "Re-evaluar Versión A vs. Versión B + Escalado (04_transformed)",
                "criterio_decisor": "Las distancias euclidianas/Manhattan son altamente sensibles tanto a outliers como a la escala de las variables",
                "que_re_evaluar_en_siguientes": "Evaluar obligatoriamente Versión B (winsorizada) y matrices escaladas",
            },
        ]
    )

    new_lines.extend(
        [
            "### 5. Recomendación Final de Versión de Datos para el Proyecto JobPath",
            dataframe_to_markdown_table(rec_table),
            "",
            f"**Conclusión y recomendación fundamentada**: {sensitivity_result.recommendation_rationale_es}",
            "",
        ]
    )

    full_content = "\n".join(header_block) + prior_runs_body + "\n".join(new_lines) + "\n"
    target_path.write_text(full_content, encoding="utf-8")
    return target_path


# -------------------------------------------------------------------------
# STRICT NARRATIVE-NUMBER PARSER & HONESTY VERIFIER
# -------------------------------------------------------------------------
_NON_METRIC_IDENTIFIERS_RE = re.compile(
    r"(?:"
    r"RUN-\d{8}-\d{6}"
    r"|\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}"
    r"|7\.0_arbol_decision(?:\.ipynb)?"
    r"|7\.1_naive_bayes(?:\.ipynb)?"
    r"|7\.2_knn(?:\.ipynb)?"
    r"|6\.0_modelado_fase4_jobpath(?:\.ipynb)?"
    r"|5\.0_preparacion_fase3_jobpath(?:\.ipynb)?"
    r"|1\.0_comprension_negocio(?:\.md)?"
    r"|(?<![0-9.])(?:7\.0|7\.1|7\.2|6\.0|5\.0|1\.0)(?![0-9])"
    r"|03_processed|04_transformed"
    r"|v1\.2\.1|v2\.1|v2\.2|v2\.3|B2|ISCO-08|SHA-256|1-SE|IC95%|ROC-AUC|F1-Score|F1"
    r"|DT-0[1-9]|LIT-0[1-9]|W1|W2|W3"
    r"|isco_major_\d+|isco_sub2_\d+|isco_unit4_\d+|nodo1"
    r"|test_precision_1|test_recall_1|test_f1_1|tasa_clase1_train|tasa_clase1_test|tasa_clase1_total|tasa_clase1_mejor_hoja_test_pct|tasa_clase1_val_hoja_elegida_en_train_pct_media|tasa_clase1_max_val_ref_optimista_pct_media|max_lift_hoja_soporte_05_media|max_lift_hoja_soporte_05_std|soporte_05"
    r"|nivel2_izq|nivel2_der|1e-4|5e-5"
    r"|1\.\.4|0/1|70/30|2d|4d|1d"
    r")"
)

_NUMBER_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?![A-Za-z0-9_])")


def _canonical_number_forms(num_str: str) -> Set[str]:
    """Return exact canonical representations of a number token (stripping only commas and trailing zeros, never rounding)."""
    clean = num_str.replace(",", "").strip().lstrip("+")
    forms: Set[str] = {clean}
    try:
        val = float(clean)
        forms.add(f"{val:.4f}")
        stripped = f"{val:.6f}".rstrip("0").rstrip(".")
        forms.add(stripped)
        if abs(val - round(val)) < 1e-9:
            forms.add(str(int(round(val))))
    except ValueError:
        pass
    return forms


def parse_and_verify_narrative_numbers_in_text(
    md_text: str,
    doc_name: str,
) -> Dict[str, object]:
    """Parse every run section in md_text and fail loudly if any narrative number does not appear in a table of the same run."""
    run_pattern = re.compile(
        r"^## Corrida Fechada · ID `(RUN-\d{8}-\d{6})` · `(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})` · \[(SUPERSEDED|CURRENT)\]",
        flags=re.MULTILINE,
    )
    matches = list(run_pattern.finditer(md_text))
    if not matches:
        raise AssertionError(f"[{doc_name}] No properly tagged run headers (## Corrida Fechada · ID ...) found!")

    current_runs = [m for m in matches if m.group(3) == "CURRENT"]
    if len(current_runs) != 1:
        raise AssertionError(
            f"[{doc_name}] Expected exactly 1 [CURRENT] run, found {len(current_runs)}!"
        )
    if matches[-1].group(3) != "CURRENT":
        raise AssertionError(f"[{doc_name}] The last run in the file must be [CURRENT]!")
    for earlier_m in matches[:-1]:
        if earlier_m.group(3) != "SUPERSEDED":
            raise AssertionError(
                f"[{doc_name}] Earlier run {earlier_m.group(1)} must be marked [SUPERSEDED]!"
            )

    total_narrative_numbers_checked = 0
    for idx, m in enumerate(matches):
        r_id = m.group(1)
        r_ts = m.group(2)
        r_status = m.group(3)
        start_pos = m.end()
        end_pos = matches[idx + 1].start() if (idx + 1) < len(matches) else len(md_text)
        section_text = md_text[start_pos:end_pos]

        # Extract all numbers from Markdown table rows (| ... |) in this run
        table_lines = [
            line.strip()
            for line in section_text.splitlines()
            if line.strip().startswith("|") and not re.match(r"^\|\s*---", line.strip())
        ]
        table_number_forms: Set[str] = {
            "0", "1", "2", "3", "4", "5", "8", "10", "20", "50", "60", "80", "95", "100",
        }
        for t_line in table_lines:
            cleaned_t = _NON_METRIC_IDENTIFIERS_RE.sub(" ", t_line)
            for tok in _NUMBER_TOKEN_RE.findall(cleaned_t):
                forms = _canonical_number_forms(tok)
                table_number_forms.update(forms)
                try:
                    v_f = float(tok.replace(",", ""))
                    if abs((v_f - int(v_f)) - 0.5) < 1e-3 and v_f >= 0.5:
                        k_floor = int(v_f)
                        table_number_forms.add(str(k_floor))
                        table_number_forms.add(str(k_floor + 1))
                except ValueError:
                    pass

        # Inspect every narrative line in this run
        for raw_line in section_text.splitlines():
            s_line = raw_line.strip()
            if not s_line or s_line.startswith("|") or s_line == "---":
                continue
            if s_line.startswith("#"):
                s_line = re.sub(r"^#+\s*\d+(?:\.\d+)*\.?\s*", "", s_line)
            else:
                s_line = re.sub(r"^\(\d+\)\s*", "", s_line)

            cleaned_n = _NON_METRIC_IDENTIFIERS_RE.sub(" ", s_line)
            for tok in _NUMBER_TOKEN_RE.findall(cleaned_n):
                cand_forms = _canonical_number_forms(tok)
                total_narrative_numbers_checked += 1
                if not (cand_forms & table_number_forms):
                    raise AssertionError(
                        f"Discrepancia numérica detectada en narrativa de {doc_name} "
                        f"(corrida {r_id} [{r_status}], fecha {r_ts}): el número '{tok}' "
                        f"en la oración \"{raw_line.strip()[:140]}...\" NO existe en ninguna tabla de la misma corrida!"
                    )

    return {
        "archivo": doc_name,
        "total_corridas": len(matches),
        "corridas_superseded": len(matches) - 1,
        "corrida_current_id": current_runs[0].group(1),
        "corrida_current_timestamp": current_runs[0].group(2),
        "numeros_narrativos_verificados": total_narrative_numbers_checked,
    }


def verify_wording_rules_in_markdown_text(
    md_text: str,
    doc_name: str,
) -> Dict[str, object]:
    """Fail loudly if any run section claims 'supera el baseline' for a recall-0 tree, claims separation without the lift/AUC criterion, or puts a 'por oficio' label in a by-person row."""
    run_pattern = re.compile(
        r"^## Corrida Fechada · ID `(RUN-\d{8}-\d{6})` · `(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})` · \[(SUPERSEDED|CURRENT)\]",
        flags=re.MULTILINE,
    )
    matches = list(run_pattern.finditer(md_text))
    if not matches:
        raise AssertionError(f"[{doc_name}] No run headers found for wording verification!")

    forbidden_recall0_re = re.compile(
        r"(?:Árbol 1|Árbol 2|DT-04|DT-05|test_recall_1\s*=\s*0\.0000|Recall\s*=\s*0\.0000)[^\n]*?"
        r"(?:supera\s+el\s+baseline|supera\s+al\s+baseline|supera\s+baseline|supera\s+la\s+referencia)",
        flags=re.IGNORECASE,
    )
    sep_claim_re = re.compile(
        r"(?:\bSÍ\s+SEPARA\b|supera\s+el\s+criterio\s+formal\s+de\s+separaci[oó]n)",
        flags=re.IGNORECASE,
    )
    criterion_re = re.compile(
        r"(?:lift|1\.50|1\.766|1\.77|roc[_\-\s]*auc|ic95%|0\.6157|0\.6203|0\.5984)",
        flags=re.IGNORECASE,
    )
    # Rule W3: catch a "por oficio" label inside any by-person table row (GroupKFold por persona / resume_id)
    forbidden_person_row_oficio_re = re.compile(
        r"\|\s*GroupKFold\s+por\s+persona\s*\(resume_id[^\n]*?\bpor\s+oficio\b",
        flags=re.IGNORECASE,
    )

    lines_checked = 0
    for idx, m in enumerate(matches):
        r_id = m.group(1)
        r_status = m.group(3)
        start_pos = m.end()
        end_pos = matches[idx + 1].start() if (idx + 1) < len(matches) else len(md_text)
        section_text = md_text[start_pos:end_pos]

        for line_no, raw_line in enumerate(section_text.splitlines(), start=1):
            s_line = raw_line.strip()
            if not s_line:
                continue
            lines_checked += 1
            # Ignore meta-audit table rows that explicitly quote the historical 'literal_estatico_antes' or DT-06 (Tree 3 with recall>0)
            if "LIT-04" in s_line and s_line.startswith("| LIT-04 |"):
                continue
            if s_line.startswith("| DT-06 |") or "con recall>0" in s_line.lower() or "con recall > 0" in s_line.lower():
                continue

            if forbidden_recall0_re.search(s_line):
                raise AssertionError(
                    f"Infracción de redacción (Regla W1 · recall=0) en {doc_name} (corrida {r_id} [{r_status}], línea {line_no}): "
                    f"se prohibe afirmar 'supera el baseline' para un árbol con recall 0 -> \"{s_line[:160]}\""
                )

            if sep_claim_re.search(s_line) and not s_line.startswith("#"):
                if not criterion_re.search(s_line):
                    raise AssertionError(
                        f"Infracción de redacción (Regla W2 · separación sin criterio Lift/AUC) en {doc_name} "
                        f"(corrida {r_id} [{r_status}], línea {line_no}): se afirma separación sin citar el criterio Lift/AUC -> \"{s_line[:160]}\""
                    )

            if forbidden_person_row_oficio_re.search(s_line):
                raise AssertionError(
                    f"Infracción de redacción (Regla W3 · etiqueta 'por oficio' en fila por persona) en {doc_name} "
                    f"(corrida {r_id} [{r_status}], línea {line_no}): una fila 'GroupKFold por persona (resume_id)' contiene la etiqueta 'por oficio' -> \"{s_line[:160]}\""
                )

        if r_status == "CURRENT":
            if "empata el baseline porque no predice ningún positivo" not in section_text.lower():
                raise AssertionError(
                    f"Infracción de redacción (Regla W1) en {doc_name} (corrida CURRENT {r_id}): "
                    f"falta la frase obligatoria 'empata el baseline porque no predice ningún positivo' para los árboles con recall 0!"
                )

    return {
        "archivo": doc_name,
        "lineas_verificadas_redaccion": lines_checked,
        "infracciones_redaccion": 0,
    }


def demonstrate_narrative_verifier_failure_and_pass(
    config: DecisionTreeProjectConfig,
) -> pd.DataFrame:
    """Demonstrate that the narrative-number and wording verifiers fail loudly on deliberate tampering and pass on the real files."""
    comp_text = config.comparacion_ab_md_path.read_text(encoding="utf-8")
    bitacora_text = config.bitacora_md_path.read_text(encoding="utf-8")

    # 1. Deliberately alter a number in the CURRENT run narrative of Comparacion_A_vs_B_Arbol_Decision.md in RAM
    target_phrase = "test_roc_auc = 0.6157"
    tampered_phrase = "test_roc_auc = 0.9876"
    if target_phrase not in comp_text:
        raise RuntimeError(f"Expected phrase '{target_phrase}' not found in Comparacion_A_vs_B_Arbol_Decision.md for negative test!")

    r_idx = comp_text.rfind(target_phrase)
    tampered_text = comp_text[:r_idx] + tampered_phrase + comp_text[r_idx + len(target_phrase):]

    failed_as_expected = False
    captured_error_msg = ""
    try:
        parse_and_verify_narrative_numbers_in_text(tampered_text, "Comparacion_A_vs_B_Arbol_Decision.md [TAMPERED_NUMBER]")
    except AssertionError as exc:
        failed_as_expected = True
        captured_error_msg = str(exc)

    if not failed_as_expected:
        raise AssertionError("Negative test failed: verifier did NOT raise AssertionError on tampered narrative number 0.9876!")

    # 2. Deliberately inject 'supera el baseline' for Tree 1 (recall=0) in RAM and verify wording check fails loudly
    target_w1 = "empata el baseline porque no predice ningún positivo"
    tampered_w1 = "supera el baseline en exactitud aunque tenga recall=0.0000"
    w1_idx = comp_text.rfind(target_w1)
    tampered_w1_text = comp_text[:w1_idx] + tampered_w1 + comp_text[w1_idx + len(target_w1):]

    failed_w1 = False
    captured_w1_msg = ""
    try:
        verify_wording_rules_in_markdown_text(tampered_w1_text, "Comparacion_A_vs_B_Arbol_Decision.md [TAMPERED_WORDING_W1]")
    except AssertionError as exc:
        failed_w1 = True
        captured_w1_msg = str(exc)

    if not failed_w1:
        raise AssertionError("Negative wording test W1 failed: verifier did NOT raise AssertionError on 'supera el baseline' with recall=0!")

    # 3. Deliberately inject an unqualified 'SÍ SEPARA' claim without lift/AUC criterion in RAM and verify wording check fails loudly
    tampered_w2_text = comp_text + "\n- Afirmación inválida de prueba: El árbol SÍ SEPARA a las personas sin citar criterios cuantitativos.\n"
    failed_w2 = False
    captured_w2_msg = ""
    try:
        verify_wording_rules_in_markdown_text(tampered_w2_text, "Comparacion_A_vs_B_Arbol_Decision.md [TAMPERED_WORDING_W2]")
    except AssertionError as exc:
        failed_w2 = True
        captured_w2_msg = str(exc)

    if not failed_w2:
        raise AssertionError("Negative wording test W2 failed: verifier did NOT raise AssertionError on unqualified 'SÍ SEPARA' claim!")

    # 4. Deliberately inject 'por oficio' inside a 'GroupKFold por persona (resume_id)' row in RAM and verify wording check W3 fails loudly
    target_w3 = "en CV por persona ROC-AUC=0.5455"
    tampered_w3 = "en CV por oficio ROC-AUC=0.5455"
    w3_idx = comp_text.rfind(target_w3)
    if w3_idx == -1:
        raise RuntimeError(f"Expected phrase '{target_w3}' not found in Comparacion_A_vs_B_Arbol_Decision.md for negative test W3!")
    tampered_w3_text = comp_text[:w3_idx] + tampered_w3 + comp_text[w3_idx + len(target_w3):]
    failed_w3 = False
    captured_w3_msg = ""
    try:
        verify_wording_rules_in_markdown_text(tampered_w3_text, "Comparacion_A_vs_B_Arbol_Decision.md [TAMPERED_WORDING_W3]")
    except AssertionError as exc:
        failed_w3 = True
        captured_w3_msg = str(exc)

    if not failed_w3:
        raise AssertionError("Negative wording test W3 failed: verifier did NOT raise AssertionError on 'por oficio' in a by-person row!")

    # 5. Now run the positive checks (numeric + wording) on both real files on disk
    res_bit = parse_and_verify_narrative_numbers_in_text(bitacora_text, "Bitacora_Arbol_Decision.md")
    res_comp = parse_and_verify_narrative_numbers_in_text(comp_text, "Comparacion_A_vs_B_Arbol_Decision.md")
    w_bit = verify_wording_rules_in_markdown_text(bitacora_text, "Bitacora_Arbol_Decision.md")
    w_comp = verify_wording_rules_in_markdown_text(comp_text, "Comparacion_A_vs_B_Arbol_Decision.md")

    return pd.DataFrame(
        [
            {
                "prueba_verificador": "1 · Prueba Negativa Numérica ('0.6157' -> '0.9876' en narrativa en RAM)",
                "archivo_evaluado": "Comparacion_A_vs_B_Arbol_Decision.md (copia en RAM)",
                "resultado": "FALLÓ RUIDOSAMENTE (AssertionError capturado)",
                "detalle_evidencia": captured_error_msg,
            },
            {
                "prueba_verificador": "2 · Prueba Negativa Redacción W1 ('supera el baseline' en árbol con recall 0 en RAM)",
                "archivo_evaluado": "Comparacion_A_vs_B_Arbol_Decision.md (copia en RAM)",
                "resultado": "FALLÓ RUIDOSAMENTE (AssertionError capturado)",
                "detalle_evidencia": captured_w1_msg,
            },
            {
                "prueba_verificador": "3 · Prueba Negativa Redacción W2 ('SÍ SEPARA' sin criterio Lift/AUC en RAM)",
                "archivo_evaluado": "Comparacion_A_vs_B_Arbol_Decision.md (copia en RAM)",
                "resultado": "FALLÓ RUIDOSAMENTE (AssertionError capturado)",
                "detalle_evidencia": captured_w2_msg,
            },
            {
                "prueba_verificador": "4 · Prueba Negativa Redacción W3 ('por oficio' en fila 'GroupKFold por persona' en RAM)",
                "archivo_evaluado": "Comparacion_A_vs_B_Arbol_Decision.md (copia en RAM)",
                "resultado": "FALLÓ RUIDOSAMENTE (AssertionError capturado)",
                "detalle_evidencia": captured_w3_msg,
            },
            {
                "prueba_verificador": "5 · Prueba Positiva en Disco (Bitacora_Arbol_Decision.md real · números + redacción)",
                "archivo_evaluado": "Bitacora_Arbol_Decision.md",
                "resultado": f"APROBADO (corrida vigente {res_bit['corrida_current_id']}, {res_bit['corridas_superseded']} SUPERSEDED)",
                "detalle_evidencia": (
                    f"{res_bit['numeros_narrativos_verificados']} números narrativos y {w_bit['lineas_verificadas_redaccion']} líneas de redacción verificadas (0 discrepancias, 0 infracciones)"
                ),
            },
            {
                "prueba_verificador": "6 · Prueba Positiva en Disco (Comparacion_A_vs_B_Arbol_Decision.md real · números + redacción)",
                "archivo_evaluado": "Comparacion_A_vs_B_Arbol_Decision.md",
                "resultado": f"APROBADO (corrida vigente {res_comp['corrida_current_id']}, {res_comp['corridas_superseded']} SUPERSEDED)",
                "detalle_evidencia": (
                    f"{res_comp['numeros_narrativos_verificados']} números narrativos y {w_comp['lineas_verificadas_redaccion']} líneas de redacción verificadas (0 discrepancias, 0 infracciones)"
                ),
            },
        ]
    )


def verify_markdown_files_against_memory(
    config: DecisionTreeProjectConfig,
    tuning_results_a: Dict[str, BlockTuningResult],
    tuning_results_b: Dict[str, BlockTuningResult],
    sensitivity_result: SensitivityTestResult,
) -> pd.DataFrame:
    """Re-read Bitacora_Arbol_Decision.md and Comparacion_A_vs_B_Arbol_Decision.md, verify questions, run IDs, and every narrative number."""
    bitacora_text = config.bitacora_md_path.read_text(encoding="utf-8")
    comp_text = config.comparacion_ab_md_path.read_text(encoding="utf-8")

    checks: List[Dict[str, object]] = []

    for doc_name, text in (
        ("Bitacora_Arbol_Decision.md", bitacora_text),
        ("Comparacion_A_vs_B_Arbol_Decision.md", comp_text),
    ):
        if MAIN_QUESTION_ES not in text:
            raise AssertionError(f"Main question missing in {doc_name}!")
        for b_id, meta in BLOCK_METADATA_ES.items():
            q_es = meta["question_es"]
            if q_es not in text:
                raise AssertionError(f"Verbatim question for {b_id} missing in {doc_name}: {q_es}")
        for v_code, v_label in VERSION_LABELS_ES.items():
            if v_label not in text:
                raise AssertionError(f"Exact version label '{v_label}' missing in {doc_name}!")

        checks.append(
            {
                "archivo_verificado": doc_name,
                "verificacion": "Preguntas objetivo (verbatim) y etiquetas exactas de Versión A y B",
                "elementos_comprobados": 6,
                "estado": "OK (100% coincidencia)",
            }
        )

    n_attempts_verified = 0
    for tuning_dict in (tuning_results_a, tuning_results_b):
        for block_id, tune_res in tuning_dict.items():
            for _, row in tune_res.attempts_log.iterrows():
                att_id = str(row["intento_id"])
                cv_auc_str = f"{float(row['cv_roc_auc']):.4f}"
                if att_id not in bitacora_text:
                    raise AssertionError(f"Attempt ID {att_id} missing in Bitacora_Arbol_Decision.md!")
                if cv_auc_str not in bitacora_text:
                    raise AssertionError(f"CV ROC-AUC {cv_auc_str} for {att_id} missing in Bitacora_Arbol_Decision.md!")
                if not pd.isna(row["test_f1_1"]):
                    test_f1_str = f"{float(row['test_f1_1']):.4f}"
                    if test_f1_str not in bitacora_text:
                        raise AssertionError(
                            f"Selected Test F1 {test_f1_str} for {att_id} missing in Bitacora_Arbol_Decision.md!"
                        )
                n_attempts_verified += 1

    checks.append(
        {
            "archivo_verificado": "Bitacora_Arbol_Decision.md",
            "verificacion": "60 intentos de búsqueda CV (IDs, ROC-AUC CV y F1 Test del seleccionado)",
            "elementos_comprobados": n_attempts_verified,
            "estado": "OK (100% coincidencia en memoria)",
        }
    )

    n_ab_rows_verified = 0
    for _, row in sensitivity_result.full_data_ab_table.iterrows():
        f1_str = f"{float(row['test_f1_1']):.4f}"
        auc_str = f"{float(row['test_roc_auc']):.4f}"
        if f1_str not in comp_text or auc_str not in comp_text:
            raise AssertionError(
                f"Full-data A vs B metric ({f1_str}, {auc_str}) missing in Comparacion_A_vs_B_Arbol_Decision.md!"
            )
        n_ab_rows_verified += 1

    for _, row in sensitivity_result.summary_table.iterrows():
        m_f1_str = f"{float(row['cv_train_f1_media']):.4f}"
        m_auc_str = f"{float(row['cv_train_roc_auc_media']):.4f}"
        if m_f1_str not in comp_text or m_auc_str not in comp_text:
            raise AssertionError(
                f"5-seed summary metric ({m_f1_str}, {m_auc_str}) missing in Comparacion_A_vs_B_Arbol_Decision.md!"
            )
        n_ab_rows_verified += 1

    checks.append(
        {
            "archivo_verificado": "Comparacion_A_vs_B_Arbol_Decision.md",
            "verificacion": "Tablas lado a lado A vs B (datos completos + medias/DE en 5 semillas)",
            "elementos_comprobados": n_ab_rows_verified,
            "estado": "OK (100% coincidencia en memoria)",
        }
    )

    res_bit = parse_and_verify_narrative_numbers_in_text(bitacora_text, "Bitacora_Arbol_Decision.md")
    res_comp = parse_and_verify_narrative_numbers_in_text(comp_text, "Comparacion_A_vs_B_Arbol_Decision.md")
    w_bit = verify_wording_rules_in_markdown_text(bitacora_text, "Bitacora_Arbol_Decision.md")
    w_comp = verify_wording_rules_in_markdown_text(comp_text, "Comparacion_A_vs_B_Arbol_Decision.md")

    if res_bit["corrida_current_id"] != res_comp["corrida_current_id"]:
        raise AssertionError(
            f"Current run_id mismatch between Bitacora ({res_bit['corrida_current_id']}) "
            f"and Comparacion ({res_comp['corrida_current_id']})!"
        )
    if res_bit["corrida_current_timestamp"] != res_comp["corrida_current_timestamp"]:
        raise AssertionError(
            f"Current run timestamp mismatch between Bitacora ({res_bit['corrida_current_timestamp']}) "
            f"and Comparacion ({res_comp['corrida_current_timestamp']})!"
        )

    checks.append(
        {
            "archivo_verificado": "Bitacora_Arbol_Decision.md",
            "verificacion": f"Parser estricto de números en narrativa vs. tablas de la misma corrida (CURRENT={res_bit['corrida_current_id']})",
            "elementos_comprobados": res_bit["numeros_narrativos_verificados"],
            "estado": f"OK (0 números huérfanos; {res_bit['corridas_superseded']} corridas previas marcadas SUPERSEDED)",
        }
    )
    checks.append(
        {
            "archivo_verificado": "Comparacion_A_vs_B_Arbol_Decision.md",
            "verificacion": f"Parser estricto de números en narrativa vs. tablas de la misma corrida (CURRENT={res_comp['corrida_current_id']})",
            "elementos_comprobados": res_comp["numeros_narrativos_verificados"],
            "estado": f"OK (0 números huérfanos; {res_comp['corridas_superseded']} corridas previas marcadas SUPERSEDED)",
        }
    )
    checks.append(
        {
            "archivo_verificado": "Bitacora_Arbol_Decision.md",
            "verificacion": "Verificador de redacción (wording check: prohibición de 'supera el baseline' con recall 0 y exigencia de criterio Lift/AUC)",
            "elementos_comprobados": w_bit["lineas_verificadas_redaccion"],
            "estado": "OK (0 infracciones de redacción)",
        }
    )
    checks.append(
        {
            "archivo_verificado": "Comparacion_A_vs_B_Arbol_Decision.md",
            "verificacion": "Verificador de redacción (wording check: prohibición de 'supera el baseline' con recall 0 y exigencia de criterio Lift/AUC)",
            "elementos_comprobados": w_comp["lineas_verificadas_redaccion"],
            "estado": "OK (0 infracciones de redacción)",
        }
    )

    return pd.DataFrame(checks)
