"""Feature construction and data usage summary for K-Means Clustering (reusing the verified loader from ClusteringJerarquico)."""

from __future__ import annotations

import pandas as pd

from scripts.ScriptsCsv.ClusteringJerarquico.sampling_and_features import (
    PreparedClusteringDataset,
    assert_zero_leakage_in_feature_lists,
    draw_stratified_subsample,
    load_and_prepare_clustering_dataset,
)

from .config import KMeansClusteringConfig


def build_kmeans_data_usage_table(
    dataset_b: PreparedClusteringDataset,
    config: KMeansClusteringConfig,
) -> pd.DataFrame:
    """Build the 'Uso de datos' summary table for K-Means (with 'no aplica' on pre-classification rows)."""
    df_p = dataset_b.df_persons
    df_e = dataset_b.df_experiences

    n_p_tr = int((df_p["split"] == "train").sum())
    n_p_te = int((df_p["split"] == "test").sum())
    n_e_tr = int((df_e["split"] == "train").sum())
    n_e_te = int((df_e["split"] == "test").sum())

    def _pct_raw(val: int) -> str:
        return f"{val / dataset_b.raw_total_rows * 100.0:.2f}%"

    def _pct_cls(val: int) -> str:
        return f"{val / dataset_b.classified_total_rows * 100.0:.2f}%"

    rows = [
        {
            "etapa_uso_de_datos": "1. Universo bruto en CSV de entrada (Versión B y Versión A)",
            "filas_experiencias": dataset_b.raw_total_rows,
            "personas_unicas": dataset_b.raw_total_persons,
            "pct_sobre_total_csv": "100.00%",
            "pct_sobre_clasificados": "no aplica",
            "detalle_y_justificacion": "Total de experiencias laborales antes de filtrar ocupaciones sin código ESCO estandarizado.",
        },
        {
            "etapa_uso_de_datos": "2. Filas excluidas en RAM (es_ocupacion_clasificada == 0)",
            "filas_experiencias": dataset_b.excluded_unclassified_rows,
            "personas_unicas": dataset_b.excluded_exclusive_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.excluded_unclassified_rows),
            "pct_sobre_clasificados": "no aplica",
            "detalle_y_justificacion": (
                f"Excluidas en RAM antes de clusterizar (Decisión D07 de Fase 3) por carecer de perfil ESCO "
                f"({dataset_b.excluded_unknown_rows} con emparejado='unknown' y {dataset_b.excluded_rescatado_rows} "
                f"con 'rescatado' sin padre ESCO; {dataset_b.excluded_exclusive_persons} personas exclusivas)."
            ),
        },
        {
            "etapa_uso_de_datos": "3. Universo clasificado modelado (es_ocupacion_clasificada == 1)",
            "filas_experiencias": dataset_b.classified_total_rows,
            "personas_unicas": dataset_b.classified_total_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.classified_total_rows),
            "pct_sobre_clasificados": "100.00%",
            "detalle_y_justificacion": "Universo válido alineado 1 a 1 entre Versión B (sin outliers IQR, primaria) y Versión A (con outliers, sensibilidad).",
        },
        {
            "etapa_uso_de_datos": "4. Ajuste de StandardScaler y KMeans (Train 80% agrupado por resume_id)",
            "filas_experiencias": n_e_tr,
            "personas_unicas": n_p_tr,
            "pct_sobre_total_csv": _pct_raw(n_e_tr),
            "pct_sobre_clasificados": _pct_cls(n_e_tr),
            "detalle_y_justificacion": "Partición de entrenamiento (seed=42, 0 personas compartidas con Test) donde se ajustan StandardScaler y los centroides K-Means (k-means++, n_init=10).",
        },
        {
            "etapa_uso_de_datos": "5. Validación out-of-sample de clústeres y perfiles (Test 20% por resume_id)",
            "filas_experiencias": n_e_te,
            "personas_unicas": n_p_te,
            "pct_sobre_total_csv": _pct_raw(n_e_te),
            "pct_sobre_clasificados": _pct_cls(n_e_te),
            "detalle_y_justificacion": "Partición de prueba retenida (20%, seed=42) asignada mediante km.predict(scaler.transform(X_test)) para verificar estabilidad fuera de muestra.",
        },
        {
            "etapa_uso_de_datos": "6. Educación no reportada (MNAR · educacion_no_reportada == 1) en Train",
            "filas_experiencias": dataset_b.mnar_edu_train_rows,
            "personas_unicas": dataset_b.mnar_edu_train_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.mnar_edu_train_rows),
            "pct_sobre_clasificados": f"{dataset_b.mnar_edu_train_rows / n_e_tr * 100.0:.2f}%",
            "detalle_y_justificacion": "Registros de Train sin grado académico reportado (codificados con bandera binaria 1 + mediana ordinal de Train=2.0, sin rellenar jamás con 0).",
        },
        {
            "etapa_uso_de_datos": "7. Educación no reportada (MNAR · educacion_no_reportada == 1) en Test",
            "filas_experiencias": dataset_b.mnar_edu_test_rows,
            "personas_unicas": dataset_b.mnar_edu_test_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.mnar_edu_test_rows),
            "pct_sobre_clasificados": f"{dataset_b.mnar_edu_test_rows / n_e_te * 100.0:.2f}%",
            "detalle_y_justificacion": "Registros de Test sin grado académico reportado (mantenidos con bandera binaria 1 + mediana ordinal de Train=2.0).",
        },
        {
            "etapa_uso_de_datos": "8. Educación no reportada (MNAR · educacion_no_reportada == 1) en Total Clasificado",
            "filas_experiencias": dataset_b.mnar_edu_total_rows,
            "personas_unicas": dataset_b.mnar_edu_total_persons,
            "pct_sobre_total_csv": _pct_raw(dataset_b.mnar_edu_total_rows),
            "pct_sobre_clasificados": _pct_cls(dataset_b.mnar_edu_total_rows),
            "detalle_y_justificacion": "Total de registros clasificados con educación no reportada (Train + Test = 200,934 filas; 42,884 personas según primera experiencia).",
        },
        {
            "etapa_uso_de_datos": "9. Muestra de evaluación de Silueta (sample_size para O(n^2) tractable)",
            "filas_experiencias": config.silhouette_sample_size,
            "personas_unicas": config.silhouette_sample_size,
            "pct_sobre_total_csv": f"{config.silhouette_sample_size / dataset_b.raw_total_rows * 100.0:.2f}%",
            "pct_sobre_clasificados": f"{config.silhouette_sample_size / dataset_b.classified_total_rows * 100.0:.2f}%",
            "detalle_y_justificacion": "Submuestra aleatoria reproducible (seed=42) usada por silhouette_score mientras Inercia, Davies-Bouldin y Calinski-Harabasz se calculan sobre el 100% de Train.",
        },
        {
            "etapa_uso_de_datos": "10. Sensibilidad Versión B vs. Versión A en 5 Semillas (42, 100, 2026, 7, 999)",
            "filas_experiencias": config.sensitivity_sample_persons,
            "personas_unicas": config.sensitivity_sample_persons,
            "pct_sobre_total_csv": f"{config.sensitivity_sample_persons / dataset_b.raw_total_rows * 100.0:.2f}%",
            "pct_sobre_clasificados": f"{config.sensitivity_sample_persons / dataset_b.classified_total_persons * 100.0:.2f}%",
            "detalle_y_justificacion": "5 muestras estratificadas de 10,000 personas de Train + evaluación en datos completos (281,674 personas Train / 70,419 Test) comparando Versión B vs. Versión A.",
        },
    ]
    return pd.DataFrame(rows)


__all__ = [
    "PreparedClusteringDataset",
    "assert_zero_leakage_in_feature_lists",
    "build_kmeans_data_usage_table",
    "draw_stratified_subsample",
    "load_and_prepare_clustering_dataset",
]
