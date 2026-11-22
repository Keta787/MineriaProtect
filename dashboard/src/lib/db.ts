import "server-only";
import { neon } from "@neondatabase/serverless";

/**
 * Conexión exclusivamente en servidor hacia Neon PostgreSQL 18 (steep-poetry-63912763)
 * autenticada con el rol de mínimo privilegio `jobpath_readonly` (SELECT-only).
 * El guard `import "server-only"` garantiza en tiempo de compilación que ningún
 * componente cliente pueda importar este módulo ni exponer credenciales.
 */
function getReadOnlySql() {
  const url = process.env.DATABASE_URL_READONLY;
  if (!url) {
    throw new Error(
      "Falta la variable de entorno DATABASE_URL_READONLY (rol jobpath_readonly)."
    );
  }
  return neon(url);
}

// ============================================================================
// 1. Interfaces de Datos (Tipado exacto de las 21 tablas de Neon)
// ============================================================================

export interface FunnelRow {
  stage_order: number;
  stage_code: string;
  stage_label_es: string;
  status_in_neon: string;
  experiences_count: number;
  persons_count: number;
  pct_clean_experiences: number;
  pct_clean_persons: number;
  reason_es: string;
}

export interface CleaningAuditRow {
  timestamp: string;
  etapa: string;
  principio: string;
  columna: string;
  filas_antes: number;
  filas_afectadas: number;
  filas_eliminadas: number;
  filas_despues: number;
  accion: string;
  justificacion: string;
}

export interface EdaSegmentRow {
  trajectory_segment_5_0: string;
  persons_count: number;
  mean_n_jobs: number;
  mean_n_occ: number;
  mean_n_returns: number;
  mean_span_q: number;
  any_repeated_rate_pct: number;
  pct_persons: number;
}

export interface TopTransitionRow {
  from_occupation_code: string;
  to_occupation_code: string;
  transition_count: number;
  rank_order: number;
  from_occupation_label: string;
  to_occupation_label: string;
  is_self_loop: boolean;
  pct_of_all_transitions: number;
}

export interface PcaVarianceRow {
  notebook: string;
  version: string;
  pc: string;
  var_exp_pct: number;
  cum_var_pct: number;
  k_for_80pct: number;
  k_for_90pct: number;
}

export interface SupervisedBenchmarkRow {
  familia: string;
  modelo: string;
  n_variables_x: number;
  ponderacion_clases: string;
  test_pr_auc: number | null;
  test_roc_auc: number;
  test_f1_clase_1: number;
  test_recall_clase_1: number;
  test_precision_clase_1: number;
  test_accuracy: number;
  test_brier_sin_ponderar: number | null;
}

export interface DecisionTreeComparisonRow {
  version_datos: string;
  modelo_corto: string;
  pregunta_objetivo_o_referencia: string;
  punto_operacion: string;
  n_variables_x: number;
  profundidad_max: number | null;
  n_hojas: number | null;
  train_accuracy: number | null;
  test_accuracy: number;
  test_accuracy_ic95_persona: string;
  test_precision_clase_1: number;
  test_recall_clase_1: number;
  test_f1_clase_1: number;
  test_f1_ic95_persona: string;
  test_roc_auc: number;
  test_roc_auc_ic95_persona: string;
  pct_del_techo_auc_6_0: number;
  max_lift_hoja_soporte_05pct: number | null;
  criterio_separa_clases: string;
}

export interface NaiveBayesIscoRow {
  isco_major: number;
  gran_grupo_isco: string;
  soporte_filas_train: number;
  personas_train: number;
  positivos_train: number;
  tasa_observada_train_pct: number;
  ic95_wilson_train_pct: string;
  prob_media_oof_nb_h_train_pct: number;
  soporte_filas_test: number;
  tasa_confirmada_test_pct: number;
  ic95_wilson_test_pct: string;
  prob_media_nb_h_test_pct: number;
}

export interface KnnPurityRow {
  modelo_id: string;
  variante: string;
  dimension_total: number;
  peso_bloque_w: number;
  dist_media_global: number;
  pureza_misma_ocupacion_esco_pct: number;
  pureza_mismo_grupo_isco_pct: number;
  pureza_misma_clase_reincide_pct: number;
}

export interface ClusteringExecutiveRow {
  cluster: string;
  perfil_comportamental: string;
  kmeans_8_0_tamano_y_reincide: string;
  ward_8_1_n3000_tamano_y_reincide: string;
  ward_8_1_n25000_tamano_y_reincide: string;
  isco_dominante_km_vs_ward25k: string;
  patron_reaccion_y_explicacion_es: string;
}

export interface KMeansProfileRow {
  vista: string;
  cluster: number;
  nombre_segmento_es: string;
  n_train: number;
  pct_train: number;
  n_test: number;
  pct_test: number;
  n_total: number;
  pct_total: number;
  n_jobs_media_train: number | null;
  n_jobs_media_test: number | null;
  span_q_media_train: number | null;
  span_q_media_test: number | null;
  dur_mean_media_train: number | null;
  dur_mean_media_test: number | null;
  overlap_ratio_media_train: number | null;
  overlap_ratio_media_test: number | null;
  mean_skills_competence_media_train: number | null;
  mean_skills_competence_media_test: number | null;
  mean_skills_knowledge_media_train: number | null;
  mean_skills_knowledge_media_test: number | null;
  mean_skills_essential_media_train: number | null;
  mean_skills_essential_media_test: number | null;
  tasa_reincide_train_posthoc_pct: number;
  lift_reincide_train_posthoc: number;
  tasa_reincide_test_posthoc_pct: number;
  lift_reincide_test_posthoc: number;
  gran_grupo_isco_dominante_posthoc: string;
  accion_observatorio_recomendada_es: string;
  dur_q_media_train: number | null;
  dur_q_media_test: number | null;
}

export interface Ward25kProfileRow {
  cluster: number;
  nombre_segmento_es: string;
  n_muestra_descubrimiento: number;
  pct_muestra_descubrimiento: number;
  n_total_proyectado: number;
  pct_total_proyectado: number;
  n_test_proyectado: number;
  pct_test_proyectado: number;
  n_jobs_media_muestra: number;
  span_q_media_muestra: number;
  dur_mean_media_muestra: number;
  overlap_ratio_media_muestra: number;
  mean_skills_competence_media_muestra: number;
  mean_skills_knowledge_media_muestra: number;
  mean_skills_essential_media_muestra: number;
  tasa_reincide_muestra_posthoc_pct: number;
  lift_reincide_muestra_posthoc: number;
  tasa_reincide_test_posthoc_pct: number;
  lift_reincide_test_posthoc: number;
  gran_grupo_isco_dominante_posthoc: string;
  accion_observatorio_recomendada_es: string;
}

export interface NmRl04AnnualRow {
  start_year: number;
  n_starts: number;
  n_closed_starts: number;
  mean_skills: number;
  mean_knowledge: number;
  mean_dur_q: number;
  mean_dur_q_incl_active: number;
  mean_green: number;
  reincide_rate: number;
  year_centered: number;
}

export interface NmRl04OlsRegimeRow {
  name: string;
  n: number;
  x_min: number;
  x_max: number;
  a0: number;
  a1: number;
  r2: number;
  r: number;
  s_yx: number;
  quality_verdict: string;
  polyfit_max_abs_diff: number;
  regime: string;
  x_var: string;
  y_var: string;
}

export interface NmRl04ExtrapolationRow {
  y_var: string;
  year: number;
  is_extrapolation: boolean;
  y_pred_from_2000_2019: number;
  y_observed: number | null;
  observed_n_starts: number;
  physically_invalid: boolean;
}

export interface NmLg01SurvivalRow {
  quarter_q: number;
  years: number;
  survival_prob_s_q: number;
  n_closed_jobs: number;
}

export interface NmLg01P3MilestoneRow {
  quarter_q: number;
  years: number;
  is_extrapolation: boolean;
  l0_q4: number;
  l1_q8: number;
  l2_q20: number;
  l3_q40: number;
  sum_li: number;
  p3_pred: number;
  true_s_q: number;
  abs_err: number;
}

export interface NmLg01RungeRow {
  degree: number;
  n_nodes: number;
  node_strategy: string;
  max_abs_err: number;
  rmse: number;
  mae: number;
  min_pred: number;
  max_pred: number;
  n_prob_bound_violations: number;
}

export interface PersonTrajectoryRow {
  resume_id: number;
  split: string;
  sampling_weight: number;
  in_ward_25k_sample: boolean;
  cluster_ward_25k_direct: number | null;
  cluster_ward_25k_projected: number;
  cluster_ward_3k_projected: number;
  cluster_kmeans_8_0: number;
  university_level: string;
  nivel_academico_ord_imputado: number;
  educacion_no_reportada: number;
  isco_major_modal_posthoc: string;
  isco_major_1d_zfill: string;
  n_jobs: number;
  n_jobs_bin: string;
  span_q: number;
  dur_total: number;
  dur_mean: number;
  overlap_ratio: number;
  mean_skills_essential: number;
  mean_skills_competence: number;
  mean_skills_knowledge: number;
  mean_prop_competence: number;
  n_occ_posthoc: number;
  n_returns_posthoc: number;
  any_repeated_posthoc: number;
  tasa_reincide_persona_posthoc: number;
  trajectory_segment_5_0: string;
}

export interface PersonExperienceJoinedRow {
  resume_id: number;
  job_order: number;
  split: string;
  start_year: number;
  start_quarter: number;
  end_year: number;
  end_quarter: number;
  dur_q: number;
  es_vigente: boolean;
  occupation_code: string;
  occupation_label: string;
  isco_group_code: string;
  isco_group_label: string;
  isco_major_1d_zfill: string;
  n_skills_essential_a: number;
  n_skills_competence_a: number;
  n_skills_knowledge_a: number;
  n_skills_essential_b: number;
  n_skills_competence_b: number;
  n_skills_knowledge_b: number;
  reincide: number;
  cluster_exp_kmeans_8_0: number;
}

export interface StratumComparisonRow {
  stratum_key: string;
  census_total: number;
  census_pct: number;
  ward_25k_count: number;
  ward_25k_pct: number;
  diff_pp: number;
}

// ============================================================================
// 2. Funciones de Consulta por Vista (Lectura desde Neon en modo solo lectura)
// ============================================================================

export async function getOverviewData() {
  const sql = getReadOnlySql();
  const [funnel, cleaning, segments, topTransitions, pca] = await Promise.all([
    sql`SELECT * FROM agg_inclusion_exclusion_funnel ORDER BY stage_order ASC`,
    sql`SELECT * FROM agg_cleaning_and_iqr_audit ORDER BY etapa ASC`,
    sql`SELECT * FROM agg_eda_distributions_and_segments ORDER BY persons_count DESC`,
    sql`SELECT * FROM agg_top_occupation_transitions ORDER BY rank_order ASC LIMIT 15`,
    sql`SELECT * FROM agg_pca_variance_and_loadings ORDER BY notebook, version, pc`,
  ]);

  return {
    funnel: funnel as unknown as FunnelRow[],
    cleaning: cleaning as unknown as CleaningAuditRow[],
    segments: segments as unknown as EdaSegmentRow[],
    topTransitions: topTransitions as unknown as TopTransitionRow[],
    pca: pca as unknown as PcaVarianceRow[],
  };
}

export async function getTransparencyData() {
  const sql = getReadOnlySql();
  const [funnel, iscoStrata, eduStrata, kmStrata] = await Promise.all([
    sql`SELECT * FROM agg_inclusion_exclusion_funnel ORDER BY stage_order ASC`,
    sql`
      SELECT
        isco_major_1d_zfill AS stratum_key,
        COUNT(*)::int AS census_total,
        ROUND((COUNT(*) * 100.0 / 352093.0)::numeric, 4)::float AS census_pct,
        SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END)::int AS ward_25k_count,
        ROUND((SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END) * 100.0 / 25000.0)::numeric, 4)::float AS ward_25k_pct,
        ROUND(((SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END) * 100.0 / 25000.0) - (COUNT(*) * 100.0 / 352093.0))::numeric, 4)::float AS diff_pp
      FROM person_trajectories
      GROUP BY isco_major_1d_zfill
      ORDER BY isco_major_1d_zfill ASC
    `,
    sql`
      SELECT
        university_level AS stratum_key,
        COUNT(*)::int AS census_total,
        ROUND((COUNT(*) * 100.0 / 352093.0)::numeric, 4)::float AS census_pct,
        SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END)::int AS ward_25k_count,
        ROUND((SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END) * 100.0 / 25000.0)::numeric, 4)::float AS ward_25k_pct,
        ROUND(((SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END) * 100.0 / 25000.0) - (COUNT(*) * 100.0 / 352093.0))::numeric, 4)::float AS diff_pp
      FROM person_trajectories
      GROUP BY university_level
      ORDER BY census_total DESC
    `,
    sql`
      SELECT
        ('Clúster K-Means ' || cluster_kmeans_8_0::text) AS stratum_key,
        COUNT(*)::int AS census_total,
        ROUND((COUNT(*) * 100.0 / 352093.0)::numeric, 4)::float AS census_pct,
        SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END)::int AS ward_25k_count,
        ROUND((SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END) * 100.0 / 25000.0)::numeric, 4)::float AS ward_25k_pct,
        ROUND(((SUM(CASE WHEN in_ward_25k_sample THEN 1 ELSE 0 END) * 100.0 / 25000.0) - (COUNT(*) * 100.0 / 352093.0))::numeric, 4)::float AS diff_pp
      FROM person_trajectories
      GROUP BY cluster_kmeans_8_0
      ORDER BY cluster_kmeans_8_0 ASC
    `,
  ]);

  return {
    funnel: funnel as unknown as FunnelRow[],
    iscoStrata: iscoStrata as unknown as StratumComparisonRow[],
    eduStrata: eduStrata as unknown as StratumComparisonRow[],
    kmStrata: kmStrata as unknown as StratumComparisonRow[],
  };
}

export interface ExplorerSearchFilters {
  resumeId?: number | null;
  split?: string;
  clusterKmeans?: number | null;
  iscoMajor?: string;
  universityLevel?: string;
  onlyWard25k?: boolean;
  clusterWardDirect?: number | null;
}

/**
 * Busca hasta un máximo estricto de 25 personas que cumplan los filtros
 * utilizando los índices B-tree `person_trajectories_pkey`, `idx_pt_split_km_isco_edu` e `idx_pt_ward25k`.
 * Gobernanza: Prohibidos los endpoints sin límite o de descarga masiva.
 */
export async function searchTrajectoriesBounded(filters: ExplorerSearchFilters) {
  const sql = getReadOnlySql();

  // Caso 1: Búsqueda directa por llave primaria resume_id
  if (
    filters.resumeId !== undefined &&
    filters.resumeId !== null &&
    Number.isInteger(filters.resumeId) &&
    filters.resumeId > 0
  ) {
    const rows = await sql`
      SELECT *
      FROM person_trajectories
      WHERE resume_id = ${filters.resumeId}
      LIMIT 1
    `;
    return rows as unknown as PersonTrajectoryRow[];
  }

  // Caso 2: Filtro sobre la submuestra directa Ward 25k (usa idx_pt_ward25k)
  if (filters.onlyWard25k) {
    const splitVal = filters.split && filters.split !== "all" ? filters.split : "train";
    const hasWardCluster =
      filters.clusterWardDirect !== undefined &&
      filters.clusterWardDirect !== null &&
      filters.clusterWardDirect >= 0;

    if (hasWardCluster) {
      const rows = await sql`
        SELECT *
        FROM person_trajectories
        WHERE in_ward_25k_sample = TRUE
          AND cluster_ward_25k_direct = ${filters.clusterWardDirect}
          AND split = ${splitVal}
        ORDER BY resume_id ASC
        LIMIT 25
      `;
      return rows as unknown as PersonTrajectoryRow[];
    }

    const rows = await sql`
      SELECT *
      FROM person_trajectories
      WHERE in_ward_25k_sample = TRUE
        AND split = ${splitVal}
      ORDER BY resume_id ASC
      LIMIT 25
    `;
    return rows as unknown as PersonTrajectoryRow[];
  }

  // Caso 3: Filtro combinado sobre el censo (usa idx_pt_split_km_isco_edu)
  const splitFilter = filters.split && filters.split !== "all" ? filters.split : "test";
  const kmFilter =
    filters.clusterKmeans !== undefined &&
    filters.clusterKmeans !== null &&
    filters.clusterKmeans >= 0
      ? filters.clusterKmeans
      : 0;
  const iscoFilter =
    filters.iscoMajor && filters.iscoMajor !== "all" ? filters.iscoMajor : null;
  const eduFilter =
    filters.universityLevel && filters.universityLevel !== "all"
      ? filters.universityLevel
      : null;

  if (iscoFilter && eduFilter) {
    const rows = await sql`
      SELECT *
      FROM person_trajectories
      WHERE split = ${splitFilter}
        AND cluster_kmeans_8_0 = ${kmFilter}
        AND isco_major_1d_zfill = ${iscoFilter}
        AND university_level = ${eduFilter}
      ORDER BY resume_id ASC
      LIMIT 25
    `;
    return rows as unknown as PersonTrajectoryRow[];
  }

  if (iscoFilter) {
    const rows = await sql`
      SELECT *
      FROM person_trajectories
      WHERE split = ${splitFilter}
        AND cluster_kmeans_8_0 = ${kmFilter}
        AND isco_major_1d_zfill = ${iscoFilter}
      ORDER BY resume_id ASC
      LIMIT 25
    `;
    return rows as unknown as PersonTrajectoryRow[];
  }

  if (eduFilter) {
    const rows = await sql`
      SELECT *
      FROM person_trajectories
      WHERE split = ${splitFilter}
        AND cluster_kmeans_8_0 = ${kmFilter}
        AND university_level = ${eduFilter}
      ORDER BY resume_id ASC
      LIMIT 25
    `;
    return rows as unknown as PersonTrajectoryRow[];
  }

  const rows = await sql`
    SELECT *
    FROM person_trajectories
    WHERE split = ${splitFilter}
      AND cluster_kmeans_8_0 = ${kmFilter}
    ORDER BY resume_id ASC
    LIMIT 25
  `;
  return rows as unknown as PersonTrajectoryRow[];
}

/**
 * Obtiene el perfil completo de 1 persona y su línea de tiempo cronológica
 * haciendo JOIN indexado con `esco_occupations_catalog` (< 0.15 ms en servidor).
 */
export async function getPersonTimelineById(resumeId: number) {
  const sql = getReadOnlySql();
  const [personRows, experienceRows] = await Promise.all([
    sql`
      SELECT *
      FROM person_trajectories
      WHERE resume_id = ${resumeId}
      LIMIT 1
    `,
    sql`
      SELECT
        pe.resume_id,
        pe.job_order,
        pe.split,
        pe.start_year,
        pe.start_quarter,
        pe.end_year,
        pe.end_quarter,
        pe.dur_q,
        pe.es_vigente,
        pe.occupation_code,
        cat.occupation_label,
        cat.isco_group_code,
        cat.isco_group_label,
        pe.isco_major_1d_zfill,
        pe.n_skills_essential_a,
        pe.n_skills_competence_a,
        pe.n_skills_knowledge_a,
        pe.n_skills_essential_b,
        pe.n_skills_competence_b,
        pe.n_skills_knowledge_b,
        pe.reincide,
        pe.cluster_exp_kmeans_8_0
      FROM person_experiences pe
      INNER JOIN esco_occupations_catalog cat
        ON pe.occupation_code = cat.occupation_code
      WHERE pe.resume_id = ${resumeId}
      ORDER BY pe.job_order ASC
      LIMIT 25
    `,
  ]);

  const person = (personRows[0] as unknown as PersonTrajectoryRow) ?? null;
  const experiences = experienceRows as unknown as PersonExperienceJoinedRow[];

  return { person, experiences };
}

export async function getModelsAndClusteringData() {
  const sql = getReadOnlySql();
  const [
    supervisedBenchmark,
    decisionTrees,
    naiveBayesIsco,
    knnPurity,
    clusteringExec,
    kmeansProfiles,
    ward25kProfiles,
  ] = await Promise.all([
    sql`SELECT * FROM agg_supervised_models_benchmark`,
    sql`SELECT * FROM agg_decision_trees_comparison`,
    sql`SELECT * FROM agg_naive_bayes_isco_rates ORDER BY tasa_confirmada_test_pct DESC`,
    sql`SELECT * FROM agg_knn_neighbor_purity ORDER BY modelo_id ASC, peso_bloque_w ASC`,
    sql`SELECT * FROM agg_clustering_executive_comparison ORDER BY cluster ASC`,
    sql`SELECT * FROM agg_kmeans_full_profiles ORDER BY vista DESC, cluster ASC`,
    sql`SELECT * FROM agg_ward_25k_profiles ORDER BY cluster ASC`,
  ]);

  return {
    supervisedBenchmark: supervisedBenchmark as unknown as SupervisedBenchmarkRow[],
    decisionTrees: decisionTrees as unknown as DecisionTreeComparisonRow[],
    naiveBayesIsco: naiveBayesIsco as unknown as NaiveBayesIscoRow[],
    knnPurity: knnPurity as unknown as KnnPurityRow[],
    clusteringExec: clusteringExec as unknown as ClusteringExecutiveRow[],
    kmeansProfiles: kmeansProfiles as unknown as KMeansProfileRow[],
    ward25kProfiles: ward25kProfiles as unknown as Ward25kProfileRow[],
  };
}

export async function getNumericalMethodsData() {
  const sql = getReadOnlySql();
  const [
    rl04Annual,
    rl04OlsRegimes,
    rl04Extrapolation,
    lg01Survival,
    lg01P3Milestones,
    lg01Runge,
  ] = await Promise.all([
    sql`SELECT * FROM agg_nm_rl04_annual_macro ORDER BY start_year ASC`,
    sql`SELECT * FROM agg_nm_rl04_ols_regimes`,
    sql`SELECT * FROM agg_nm_rl04_extrapolation_audit ORDER BY y_var ASC, year ASC`,
    sql`SELECT * FROM agg_nm_lg01_survival_curve ORDER BY quarter_q ASC`,
    sql`SELECT * FROM agg_nm_lg01_p3_milestones ORDER BY quarter_q ASC`,
    sql`SELECT * FROM agg_nm_lg01_runge_benchmark ORDER BY degree ASC, node_strategy ASC`,
  ]);

  return {
    rl04Annual: rl04Annual as unknown as NmRl04AnnualRow[],
    rl04OlsRegimes: rl04OlsRegimes as unknown as NmRl04OlsRegimeRow[],
    rl04Extrapolation: rl04Extrapolation as unknown as NmRl04ExtrapolationRow[],
    lg01Survival: lg01Survival as unknown as NmLg01SurvivalRow[],
    lg01P3Milestones: lg01P3Milestones as unknown as NmLg01P3MilestoneRow[],
    lg01Runge: lg01Runge as unknown as NmLg01RungeRow[],
  };
}
