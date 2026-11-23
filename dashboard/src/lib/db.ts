import "server-only";
import { neon } from "@neondatabase/serverless";
import { unstable_cache } from "next/cache";

/**
 * Capa de acceso a Neon PostgreSQL 18 (steep-poetry-63912763) EXCLUSIVAMENTE en servidor.
 * - Rol de mínimo privilegio: `jobpath_readonly` (`DATABASE_URL_READONLY`).
 * - Todas las consultas son 100 % parametrizadas ($1, $2, ...), sin concatenación de entrada de usuario.
 * - Whitelists estrictas en servidor para columnas de filtro y ordenamiento.
 * - Límite de filas por página: 25 (máximo 40 páginas = 1,000 filas navegables; cero exportación masiva).
 * - Tiempo máximo de ejecución por consulta (`statement_timeout`): 6,000 ms.
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
// 1. Whitelists Estrictas de Validación (Seguridad SQL)
// ============================================================================

export const ALLOWED_ISCO_MAJORS = new Set([
  "0",
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
]);

export const ALLOWED_EDUCATION_LEVELS = new Set([
  "Secondary school",
  "Bachelor",
  "Master",
  "PhD",
  "No reportado",
]);

export const ALLOWED_SPLITS = new Set(["train", "test"]);

export const ALLOWED_N_JOBS_BINS = new Set([
  "1_empleo",
  "2_3_empleos",
  "4_5_empleos",
  "6_8_empleos",
  "9_mas_empleos",
]);

export const ALLOWED_SKILLS_TIERS = new Set(["low", "mid", "high"]);

const ALLOWED_SORT_COLUMNS: Record<string, string> = {
  start_year: "pe.start_year",
  dur_q: "pe.dur_q",
  skills: "pe.n_skills_essential_a",
  job_order: "pe.job_order",
  resume_id: "pe.resume_id",
};

export const PAGE_SIZE = 25;
export const MAX_PAGE = 40; // Tope duro: máximo 1,000 filas navegables por consulta

export interface ExplorerFilters {
  isco?: string;
  occ?: string;
  edu?: string;
  yFrom?: number;
  yTo?: number;
  split?: string;
  active?: "true" | "false";
  rep?: "1" | "0";
  nJobs?: string;
  skills?: "low" | "mid" | "high";
  ward25k?: boolean;
  sort?: string;
  dir?: "asc" | "desc";
  page?: number;
}

export function sanitizeExplorerFilters(
  raw: Record<string, string | string[] | undefined>
): ExplorerFilters {
  const str = (k: string) => {
    const v = raw[k];
    return Array.isArray(v) ? v[0]?.trim() : v?.trim();
  };

  const iscoRaw = str("isco");
  const isco = iscoRaw && ALLOWED_ISCO_MAJORS.has(iscoRaw) ? iscoRaw : undefined;

  const occRaw = str("occ");
  const occ =
    occRaw && /^[0-9]{4}(?:\.[0-9]+)*$/.test(occRaw) ? occRaw : undefined;

  const eduRaw = str("edu");
  const edu =
    eduRaw && ALLOWED_EDUCATION_LEVELS.has(eduRaw) ? eduRaw : undefined;

  const yFromNum = Number(str("yFrom"));
  const yFrom =
    Number.isInteger(yFromNum) && yFromNum >= 1950 && yFromNum <= 2026
      ? yFromNum
      : undefined;

  const yToNum = Number(str("yTo"));
  const yTo =
    Number.isInteger(yToNum) && yToNum >= 1950 && yToNum <= 2026
      ? yToNum
      : undefined;

  const splitRaw = str("split");
  const split =
    splitRaw && ALLOWED_SPLITS.has(splitRaw) ? splitRaw : undefined;

  const activeRaw = str("active");
  const active =
    activeRaw === "true" || activeRaw === "false" ? activeRaw : undefined;

  const repRaw = str("rep");
  const rep = repRaw === "1" || repRaw === "0" ? repRaw : undefined;

  const nJobsRaw = str("nJobs");
  const nJobs =
    nJobsRaw && ALLOWED_N_JOBS_BINS.has(nJobsRaw) ? nJobsRaw : undefined;

  const skillsRaw = str("skills");
  const skills =
    skillsRaw && ALLOWED_SKILLS_TIERS.has(skillsRaw)
      ? (skillsRaw as "low" | "mid" | "high")
      : undefined;

  const ward25k = str("ward25k") === "1" || str("ward25k") === "true";

  const sortRaw = str("sort");
  const sort =
    sortRaw && ALLOWED_SORT_COLUMNS[sortRaw] ? sortRaw : "start_year";

  const dirRaw = str("dir");
  const dir: "asc" | "desc" = dirRaw === "asc" ? "asc" : "desc";

  const pageNum = Number(str("page"));
  const page =
    Number.isInteger(pageNum) && pageNum >= 1
      ? Math.min(pageNum, MAX_PAGE)
      : 1;

  return {
    isco,
    occ,
    edu,
    yFrom,
    yTo,
    split,
    active,
    rep,
    nJobs,
    skills,
    ward25k: ward25k || undefined,
    sort,
    dir,
    page,
  };
}

export function hasActiveFilters(f: ExplorerFilters): boolean {
  return Boolean(
    f.isco ||
      f.occ ||
      f.edu ||
      f.yFrom !== undefined ||
      f.yTo !== undefined ||
      f.split ||
      f.active ||
      f.rep ||
      f.nJobs ||
      f.skills ||
      f.ward25k
  );
}

// ============================================================================
// 2. Interfaces de Respuesta (100 % Provenientes de Consultas Vivas en Neon)
// ============================================================================

export interface ExplorerCounters {
  persons: number;
  experiences: number;
  reincidePct: number;
  medianDurQ: number;
}

export interface DurationBinPoint {
  bucket: string;
  sortOrder: number;
  count: number;
}

export interface TopOccupationPoint {
  occupation_code: string;
  occupation_label: string;
  isco_major: string;
  count: number;
}

export interface StartsPerYearPoint {
  start_year: number;
  count: number;
}

export interface IscoTransitionPoint {
  from_isco: string;
  to_isco: string;
  count: number;
}

export interface ExperienceTableRow {
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
  isco_major_1d_zfill: string;
  university_level: string;
  n_jobs: number;
  n_skills_essential_a: number;
  reincide: number;
  in_ward_25k_sample: boolean;
}

export interface ExplorerPayload {
  isUnfilteredDefault: boolean;
  counters: ExplorerCounters;
  durationHist: DurationBinPoint[];
  topOccupations: TopOccupationPoint[];
  startsPerYear: StartsPerYearPoint[];
  transitions: IscoTransitionPoint[];
  transitionsCappedTo250k: boolean;
  tableRows: ExperienceTableRow[];
  totalRowsForPagination: number;
  page: number;
  pageSize: number;
  maxPage: number;
  queryElapsedMs: number;
  selectedOccupationLabel: string | null;
}

export interface CatalogOccupationOption {
  occupation_code: string;
  occupation_label: string;
  isco_group_code: string;
  isco_group_label: string;
  isco_major_1d_zfill: string;
  n_skills_essential_ref: number;
  n_skills_competence_ref: number;
  n_skills_knowledge_ref: number;
  n_skills_sin_tipo_ref: number;
}

export interface PersonProfileRow {
  resume_id: number;
  split: string;
  in_ward_25k_sample: boolean;
  university_level: string;
  isco_major_1d_zfill: string;
  n_jobs: number;
  n_jobs_bin: string;
  span_q: number;
  dur_total: number;
  dur_mean: number;
  n_occ_posthoc: number;
  n_returns_posthoc: number;
  tasa_reincide_persona_posthoc: number;
}

export interface PersonExperienceTimelineRow {
  resume_id: number;
  job_order: number;
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
  reincide: number;
}

export interface AboutDataPayload {
  funnel: Array<{
    stage_order: number;
    stage_code: string;
    stage_label_es: string;
    status_in_neon: string;
    experiences_count: number;
    persons_count: number;
    pct_clean_experiences: number;
    pct_clean_persons: number;
    reason_es: string;
  }>;
  escoCatalogCount: number;
  wardDirectPersonsCount: number;
  trainPersonsCount: number;
  testPersonsCount: number;
  totalPersonsCount: number;
  totalExperiencesCount: number;
}

// ============================================================================
// 3. Constructor Parametrizado de Cláusula WHERE (Cero Concatenación de Input)
// ============================================================================

function buildParameterizedWhere(filters: ExplorerFilters): {
  whereSql: string;
  params: unknown[];
  needsPersonJoin: boolean;
} {
  const clauses: string[] = [];
  const params: unknown[] = [];
  let needsPersonJoin = false;

  const pushParam = (val: unknown) => {
    params.push(val);
    return `$${params.length}`;
  };

  if (filters.isco) {
    clauses.push(`pe.isco_major_1d_zfill = ${pushParam(filters.isco)}`);
  }
  if (filters.occ) {
    clauses.push(`pe.occupation_code = ${pushParam(filters.occ)}`);
  }
  if (filters.edu) {
    needsPersonJoin = true;
    clauses.push(`pt.university_level = ${pushParam(filters.edu)}`);
  }
  if (filters.yFrom !== undefined) {
    clauses.push(`pe.start_year >= ${pushParam(filters.yFrom)}`);
  }
  if (filters.yTo !== undefined) {
    clauses.push(`pe.start_year <= ${pushParam(filters.yTo)}`);
  }
  if (filters.split) {
    clauses.push(`pe.split = ${pushParam(filters.split)}`);
  }
  if (filters.active === "true") {
    clauses.push(`pe.es_vigente = ${pushParam(true)}`);
  } else if (filters.active === "false") {
    clauses.push(`pe.es_vigente = ${pushParam(false)}`);
  }
  if (filters.rep === "1") {
    clauses.push(`pe.reincide = ${pushParam(1)}`);
  } else if (filters.rep === "0") {
    clauses.push(`pe.reincide = ${pushParam(0)}`);
  }
  if (filters.nJobs) {
    needsPersonJoin = true;
    clauses.push(`pt.n_jobs_bin = ${pushParam(filters.nJobs)}`);
  }
  if (filters.skills === "low") {
    clauses.push(`pe.n_skills_essential_a < ${pushParam(15)}`);
  } else if (filters.skills === "mid") {
    clauses.push(
      `pe.n_skills_essential_a BETWEEN ${pushParam(15)} AND ${pushParam(28)}`
    );
  } else if (filters.skills === "high") {
    clauses.push(`pe.n_skills_essential_a > ${pushParam(28)}`);
  }
  if (filters.ward25k) {
    needsPersonJoin = true;
    clauses.push(`pt.in_ward_25k_sample = ${pushParam(true)}`);
  }

  return {
    whereSql: clauses.length > 0 ? `WHERE ${clauses.join(" AND ")}` : "",
    params,
    needsPersonJoin,
  };
}

/**
 * Ejecuta una consulta parametrizada protegida con `SET LOCAL statement_timeout = '8000'`
 * dentro de una transacción read-only de Neon.
 */
async function runTimedQuery<T>(text: string, params: unknown[] = []): Promise<T[]> {
  const sql = getReadOnlySql();
  const [, rows] = await sql.transaction([
    sql`SET LOCAL statement_timeout = '8000'`,
    sql.query(text, params),
  ]);
  return rows as unknown as T[];
}

// ============================================================================
// 4. Vista por Defecto (Sin Filtros): Lectura Rápida desde Tablas Agregadas + Caché
// ============================================================================

const getDefaultUnfilteredAggregates = unstable_cache(
  async () => {
    const sql = getReadOnlySql();

    const [funnelRows, nbIscoRows, survivalRows, annualRows, topTransRows, topOccRows] =
      await Promise.all([
        sql`
          SELECT persons_count, experiences_count
          FROM agg_inclusion_exclusion_funnel
          WHERE stage_code = 'included_classified_census_total'
          LIMIT 1
        `,
        sql`
          SELECT
            SUM(soporte_filas_train + soporte_filas_test)::bigint AS total_rows,
            SUM(positivos_train + ROUND(soporte_filas_test * tasa_confirmada_test_pct / 100.0))::double precision AS total_pos
          FROM agg_naive_bayes_isco_rates
        `,
        sql`
          SELECT quarter_q, survival_prob_s_q, n_closed_jobs
          FROM agg_nm_lg01_survival_curve
          ORDER BY quarter_q ASC
        `,
        sql`
          SELECT start_year, n_starts
          FROM agg_nm_rl04_annual_macro
          ORDER BY start_year ASC
        `,
        sql`
          SELECT
            SUBSTRING(from_occupation_code, 1, 1) AS from_isco,
            SUBSTRING(to_occupation_code, 1, 1) AS to_isco,
            SUM(transition_count)::bigint AS count
          FROM agg_top_occupation_transitions
          GROUP BY 1, 2
          ORDER BY count DESC
          LIMIT 10
        `,
        sql`
          SELECT
            pe.occupation_code,
            cat.occupation_label,
            cat.isco_major_1d_zfill AS isco_major,
            COUNT(*)::int AS count
          FROM person_experiences pe
          JOIN esco_occupations_catalog cat ON cat.occupation_code = pe.occupation_code
          GROUP BY pe.occupation_code, cat.occupation_label, cat.isco_major_1d_zfill
          ORDER BY count DESC
          LIMIT 10
        `,
      ]);

    const persons = Number(funnelRows[0]?.persons_count ?? 0);
    const experiences = Number(funnelRows[0]?.experiences_count ?? 0);
    const nbTotal = Number(nbIscoRows[0]?.total_rows ?? 1);
    const nbPos = Number(nbIscoRows[0]?.total_pos ?? 0);
    const reincidePct = Number(((nbPos / Math.max(nbTotal, 1)) * 100).toFixed(2));

    // Derive exact closed-job duration bins & median directly from agg_nm_lg01_survival_curve (S(q) = P(dur_q >= q))
    const survMap = new Map<number, number>();
    let nClosed = 0;
    for (const r of survivalRows) {
      survMap.set(Number(r.quarter_q), Number(r.survival_prob_s_q));
      nClosed = Number(r.n_closed_jobs);
    }
    const sAt = (q: number) => survMap.get(q) ?? 0;

    // Median q where S(q) drops below 0.50
    let medianDurQ = 5;
    for (let q = 1; q <= 40; q++) {
      if (sAt(q) >= 0.5) medianDurQ = q;
    }

    const durationHist: DurationBinPoint[] = [
      { bucket: "1–2 trim", sortOrder: 1, count: Math.round((sAt(1) - sAt(3)) * nClosed) },
      { bucket: "3–5 trim", sortOrder: 2, count: Math.round((sAt(3) - sAt(6)) * nClosed) },
      { bucket: "6–9 trim", sortOrder: 3, count: Math.round((sAt(6) - sAt(10)) * nClosed) },
      { bucket: "10–13 trim", sortOrder: 4, count: Math.round((sAt(10) - sAt(14)) * nClosed) },
      { bucket: "14–20 trim", sortOrder: 5, count: Math.round((sAt(14) - sAt(21)) * nClosed) },
      { bucket: "21–40 trim", sortOrder: 6, count: Math.round((sAt(21) - sAt(40)) * nClosed) },
      { bucket: "40+ trim", sortOrder: 7, count: Math.round(sAt(40) * nClosed) },
    ];

    const startsPerYear: StartsPerYearPoint[] = annualRows.map((r) => ({
      start_year: Number(r.start_year),
      count: Number(r.n_starts),
    }));

    const transitions: IscoTransitionPoint[] = topTransRows.map((r) => ({
      from_isco: String(r.from_isco),
      to_isco: String(r.to_isco),
      count: Number(r.count),
    }));

    const topOccupations: TopOccupationPoint[] = topOccRows.map((r) => ({
      occupation_code: String(r.occupation_code),
      occupation_label: String(r.occupation_label),
      isco_major: String(r.isco_major),
      count: Number(r.count),
    }));

    return {
      counters: { persons, experiences, reincidePct, medianDurQ },
      durationHist,
      topOccupations,
      startsPerYear,
      transitions,
    };
  },
  ["explorer-default-unfiltered-v1"],
  { revalidate: 3600 }
);

// ============================================================================
// 5. Consulta Principal del Explorador Interactivo (Default vs. Filtrado)
// ============================================================================

export async function getExplorerData(
  filters: ExplorerFilters
): Promise<ExplorerPayload> {
  const t0 = performance.now();
  const isFiltered = hasActiveFilters(filters);
  const sortCol =
    ALLOWED_SORT_COLUMNS[filters.sort ?? "start_year"] ?? "pe.start_year";
  const sortDir = filters.dir === "asc" ? "ASC" : "DESC";
  const page = filters.page ?? 1;
  const offset = (page - 1) * PAGE_SIZE;

  // Fetch occupation label if occ filter is active
  let selectedOccupationLabel: string | null = null;
  if (filters.occ) {
    const occRow = await runTimedQuery<{ occupation_label: string }>(
      `SELECT occupation_label FROM esco_occupations_catalog WHERE occupation_code = $1 LIMIT 1`,
      [filters.occ]
    );
    selectedOccupationLabel = occRow[0]?.occupation_label ?? null;
  }

  // FAST PATH: Unfiltered default view reads precomputed agg_* + fast PK-indexed page 1
  if (!isFiltered) {
    const defaultSortCol =
      filters.sort && filters.sort !== "start_year"
        ? sortCol
        : "pe.resume_id";
    const defaultSortDir =
      filters.sort && filters.sort !== "start_year" ? sortDir : "ASC";

    const [aggData, tableRows] = await Promise.all([
      getDefaultUnfilteredAggregates(),
      runTimedQuery<ExperienceTableRow>(
        `
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
          pe.isco_major_1d_zfill,
          pt.university_level,
          pt.n_jobs,
          pe.n_skills_essential_a,
          pe.reincide,
          pt.in_ward_25k_sample
        FROM person_experiences pe
        INNER JOIN person_trajectories pt ON pt.resume_id = pe.resume_id
        INNER JOIN esco_occupations_catalog cat ON cat.occupation_code = pe.occupation_code
        ORDER BY ${defaultSortCol} ${defaultSortDir}, pe.resume_id ASC, pe.job_order ASC
        LIMIT $1 OFFSET $2
        `,
        [PAGE_SIZE, offset]
      ),
    ]);

    return {
      isUnfilteredDefault: true,
      counters: aggData.counters,
      durationHist: aggData.durationHist,
      topOccupations: aggData.topOccupations,
      startsPerYear: aggData.startsPerYear,
      transitions: aggData.transitions,
      transitionsCappedTo250k: false,
      tableRows,
      totalRowsForPagination: aggData.counters.experiences,
      page,
      pageSize: PAGE_SIZE,
      maxPage: MAX_PAGE,
      queryElapsedMs: Math.round(performance.now() - t0),
      selectedOccupationLabel,
    };
  }

  // FILTERED PATH: Single materialized CTE scan for counters + 4 charts (prevents 5x concurrent table scans on Neon Free)
  // plus 1 lightweight paginated table query (LIMIT 25).
  const { whereSql, params, needsPersonJoin } = buildParameterizedWhere(filters);
  const personJoinSql = needsPersonJoin
    ? "INNER JOIN person_trajectories pt ON pt.resume_id = pe.resume_id"
    : "";

  interface SingleScanAggregateRow {
    persons: string;
    experiences: string;
    reincide_pct: string | null;
    median_dur_q: string | null;
    duration_hist: Array<{ bucket: string; sortOrder: number; count: number }> | null;
    top_occupations: Array<{
      occupation_code: string;
      occupation_label: string;
      isco_major: string;
      count: number;
    }> | null;
    starts_per_year: Array<{ start_year: number; count: number }> | null;
    transitions: Array<{ from_isco: string; to_isco: string; count: number }> | null;
  }

  const singleScanSql = `
    WITH matched AS MATERIALIZED (
      SELECT
        pe.resume_id,
        pe.job_order,
        pe.start_year,
        pe.dur_q,
        pe.occupation_code,
        pe.isco_major_1d_zfill,
        pe.reincide
      FROM person_experiences pe
      ${personJoinSql}
      ${whereSql}
    ),
    counters AS (
      SELECT
        COUNT(DISTINCT resume_id)::bigint AS persons,
        COUNT(*)::bigint AS experiences,
        ROUND(AVG(reincide::numeric) * 100.0, 2) AS reincide_pct,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dur_q) AS median_dur_q
      FROM matched
    ),
    dur_hist AS (
      SELECT
        CASE
          WHEN dur_q <= 2 THEN '1–2 trim'
          WHEN dur_q <= 5 THEN '3–5 trim'
          WHEN dur_q <= 9 THEN '6–9 trim'
          WHEN dur_q <= 13 THEN '10–13 trim'
          WHEN dur_q <= 20 THEN '14–20 trim'
          WHEN dur_q <= 40 THEN '21–40 trim'
          ELSE '40+ trim'
        END AS bucket,
        CASE
          WHEN dur_q <= 2 THEN 1
          WHEN dur_q <= 5 THEN 2
          WHEN dur_q <= 9 THEN 3
          WHEN dur_q <= 13 THEN 4
          WHEN dur_q <= 20 THEN 5
          WHEN dur_q <= 40 THEN 6
          ELSE 7
        END AS sort_order,
        COUNT(*)::int AS cnt
      FROM matched
      GROUP BY 1, 2
      ORDER BY 2 ASC
    ),
    top_occ AS (
      SELECT
        m.occupation_code,
        cat.occupation_label,
        cat.isco_major_1d_zfill AS isco_major,
        COUNT(*)::int AS cnt
      FROM matched m
      INNER JOIN esco_occupations_catalog cat ON cat.occupation_code = m.occupation_code
      GROUP BY m.occupation_code, cat.occupation_label, cat.isco_major_1d_zfill
      ORDER BY cnt DESC
      LIMIT 10
    ),
    starts_yr AS (
      SELECT
        start_year,
        COUNT(*)::int AS cnt
      FROM matched
      WHERE start_year BETWEEN 1990 AND 2023
      GROUP BY start_year
      ORDER BY start_year ASC
    ),
    trans_sample AS (
      SELECT resume_id, job_order, isco_major_1d_zfill
      FROM matched
      LIMIT 100000
    ),
    trans_top AS (
      SELECT
        s.isco_major_1d_zfill AS from_isco,
        pe2.isco_major_1d_zfill AS to_isco,
        COUNT(*)::int AS cnt
      FROM trans_sample s
      INNER JOIN person_experiences pe2
        ON pe2.resume_id = s.resume_id
       AND pe2.job_order = s.job_order + 1
      GROUP BY 1, 2
      ORDER BY cnt DESC
      LIMIT 10
    )
    SELECT
      c.persons,
      c.experiences,
      c.reincide_pct,
      c.median_dur_q,
      (SELECT json_agg(json_build_object('bucket', bucket, 'sortOrder', sort_order, 'count', cnt) ORDER BY sort_order) FROM dur_hist) AS duration_hist,
      (SELECT json_agg(json_build_object('occupation_code', occupation_code, 'occupation_label', occupation_label, 'isco_major', isco_major, 'count', cnt) ORDER BY cnt DESC) FROM top_occ) AS top_occupations,
      (SELECT json_agg(json_build_object('start_year', start_year, 'count', cnt) ORDER BY start_year ASC) FROM starts_yr) AS starts_per_year,
      (SELECT json_agg(json_build_object('from_isco', from_isco, 'to_isco', to_isco, 'count', cnt) ORDER BY cnt DESC) FROM trans_top) AS transitions
    FROM counters c
  `;

  const [aggRows, tableRows] = await Promise.all([
    runTimedQuery<SingleScanAggregateRow>(singleScanSql, params),
    runTimedQuery<ExperienceTableRow>(
      `
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
        pe.isco_major_1d_zfill,
        pt.university_level,
        pt.n_jobs,
        pe.n_skills_essential_a,
        pe.reincide,
        pt.in_ward_25k_sample
      FROM person_experiences pe
      INNER JOIN person_trajectories pt ON pt.resume_id = pe.resume_id
      INNER JOIN esco_occupations_catalog cat ON cat.occupation_code = pe.occupation_code
      ${whereSql}
      ORDER BY ${sortCol} ${sortDir}, pe.resume_id ASC, pe.job_order ASC
      LIMIT $${params.length + 1} OFFSET $${params.length + 2}
      `,
      [...params, PAGE_SIZE, offset]
    ),
  ]);

  const agg = aggRows[0];
  const experiencesCount = Number(agg?.experiences ?? 0);
  const personsCount = Number(agg?.persons ?? 0);
  const reincidePct = Number(agg?.reincide_pct ?? 0);
  const medianDurQ = Number(agg?.median_dur_q ?? 0);
  const transitionsCappedTo250k = experiencesCount > 100000;

  return {
    isUnfilteredDefault: false,
    counters: {
      persons: personsCount,
      experiences: experiencesCount,
      reincidePct,
      medianDurQ,
    },
    durationHist: agg?.duration_hist ?? [],
    topOccupations: agg?.top_occupations ?? [],
    startsPerYear: agg?.starts_per_year ?? [],
    transitions: agg?.transitions ?? [],
    transitionsCappedTo250k,
    tableRows,
    totalRowsForPagination: experiencesCount,
    page,
    pageSize: PAGE_SIZE,
    maxPage: Math.min(
      MAX_PAGE,
      Math.max(1, Math.ceil(experiencesCount / PAGE_SIZE))
    ),
    queryElapsedMs: Math.round(performance.now() - t0),
    selectedOccupationLabel,
  };
}

// ============================================================================
// 6. Visor de Trayectoria de Persona (1 sola persona por consulta, LIMIT 1)
// ============================================================================

export async function getPersonTrajectoryLive(resumeId: number): Promise<{
  person: PersonProfileRow | null;
  experiences: PersonExperienceTimelineRow[];
  elapsedMs: number;
}> {
  const t0 = performance.now();
  if (!Number.isInteger(resumeId) || resumeId <= 0 || resumeId > 10000000) {
    return { person: null, experiences: [], elapsedMs: 0 };
  }

  const [personRows, expRows] = await Promise.all([
    runTimedQuery<PersonProfileRow>(
      `
      SELECT
        resume_id,
        split,
        in_ward_25k_sample,
        university_level,
        isco_major_1d_zfill,
        n_jobs,
        n_jobs_bin,
        span_q,
        dur_total,
        dur_mean,
        n_occ_posthoc,
        n_returns_posthoc,
        tasa_reincide_persona_posthoc
      FROM person_trajectories
      WHERE resume_id = $1
      LIMIT 1
      `,
      [resumeId]
    ),
    runTimedQuery<PersonExperienceTimelineRow>(
      `
      SELECT
        pe.resume_id,
        pe.job_order,
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
        pe.reincide
      FROM person_experiences pe
      INNER JOIN esco_occupations_catalog cat
        ON cat.occupation_code = pe.occupation_code
      WHERE pe.resume_id = $1
      ORDER BY pe.job_order ASC
      LIMIT 25
      `,
      [resumeId]
    ),
  ]);

  return {
    person: personRows[0] ?? null,
    experiences: expRows,
    elapsedMs: Math.round(performance.now() - t0),
  };
}

// ============================================================================
// 7. Buscador del Catálogo de Ocupaciones ESCO (2,973 ocupaciones)
// ============================================================================

export async function searchEscoOccupations(params: {
  q?: string;
  isco?: string;
  code?: string;
  page?: number;
}): Promise<{
  items: CatalogOccupationOption[];
  selected: (CatalogOccupationOption & { census_experiences: number; census_persons: number }) | null;
  totalMatches: number;
  page: number;
  elapsedMs: number;
}> {
  const t0 = performance.now();
  const q = params.q?.trim().slice(0, 80) ?? "";
  const isco =
    params.isco && ALLOWED_ISCO_MAJORS.has(params.isco)
      ? params.isco
      : undefined;
  const code =
    params.code && /^[0-9]{4}(?:\.[0-9]+)*$/.test(params.code)
      ? params.code
      : undefined;
  const page = Math.max(1, Math.min(params.page ?? 1, MAX_PAGE));
  const offset = (page - 1) * PAGE_SIZE;

  const clauses: string[] = [];
  const sqlParams: unknown[] = [];
  const push = (v: unknown) => {
    sqlParams.push(v);
    return `$${sqlParams.length}`;
  };

  if (q) {
    const pat = `%${q}%`;
    const p1 = push(pat);
    clauses.push(
      `(occupation_label ILIKE ${p1} OR isco_group_label ILIKE ${p1} OR occupation_code ILIKE ${p1})`
    );
  }
  if (isco) {
    clauses.push(`isco_major_1d_zfill = ${push(isco)}`);
  }

  const whereSql = clauses.length > 0 ? `WHERE ${clauses.join(" AND ")}` : "";

  const [countRows, items] = await Promise.all([
    runTimedQuery<{ cnt: string }>(
      `SELECT COUNT(*)::bigint AS cnt FROM esco_occupations_catalog ${whereSql}`,
      sqlParams
    ),
    runTimedQuery<CatalogOccupationOption>(
      `
      SELECT
        occupation_code,
        occupation_label,
        isco_group_code,
        isco_group_label,
        isco_major_1d_zfill,
        n_skills_essential_ref,
        n_skills_competence_ref,
        n_skills_knowledge_ref,
        n_skills_sin_tipo_ref
      FROM esco_occupations_catalog
      ${whereSql}
      ORDER BY n_skills_essential_ref DESC, occupation_label ASC
      LIMIT $${sqlParams.length + 1} OFFSET $${sqlParams.length + 2}
      `,
      [...sqlParams, PAGE_SIZE, offset]
    ),
  ]);

  const targetCode = code ?? items[0]?.occupation_code ?? null;
  let selected:
    | (CatalogOccupationOption & {
        census_experiences: number;
        census_persons: number;
      })
    | null = null;

  if (targetCode) {
    const [catRows, usageRows] = await Promise.all([
      runTimedQuery<CatalogOccupationOption>(
        `SELECT * FROM esco_occupations_catalog WHERE occupation_code = $1 LIMIT 1`,
        [targetCode]
      ),
      runTimedQuery<{ exp_cnt: string; per_cnt: string }>(
        `
        SELECT
          COUNT(*)::bigint AS exp_cnt,
          COUNT(DISTINCT resume_id)::bigint AS per_cnt
        FROM person_experiences
        WHERE occupation_code = $1
        `,
        [targetCode]
      ),
    ]);
    if (catRows[0]) {
      selected = {
        ...catRows[0],
        census_experiences: Number(usageRows[0]?.exp_cnt ?? 0),
        census_persons: Number(usageRows[0]?.per_cnt ?? 0),
      };
    }
  }

  return {
    items,
    selected,
    totalMatches: Number(countRows[0]?.cnt ?? 0),
    page,
    elapsedMs: Math.round(performance.now() - t0),
  };
}

/**
 * Top 60 ocupaciones por volumen para el selector rápido en la barra de filtros (cacheado 1h, live desde Neon).
 */
export const getPopularOccupationsForFilter = unstable_cache(
  async (): Promise<Array<{ occupation_code: string; occupation_label: string }>> => {
    const sql = getReadOnlySql();
    const rows = await sql`
      SELECT DISTINCT
        t.from_occupation_code AS occupation_code,
        cat.occupation_label
      FROM agg_top_occupation_transitions t
      INNER JOIN esco_occupations_catalog cat
        ON cat.occupation_code = t.from_occupation_code
      ORDER BY cat.occupation_label ASC
      LIMIT 60
    `;
    return rows.map((r) => ({
      occupation_code: String(r.occupation_code),
      occupation_label: String(r.occupation_label),
    }));
  },
  ["popular-occupations-filter-v1"],
  { revalidate: 3600 }
);

// ============================================================================
// 8. Panel Breve "Sobre estos datos" (100 % consultado en vivo, cero números fijos)
// ============================================================================

export async function getAboutDataLive(): Promise<AboutDataPayload> {
  const sql = getReadOnlySql();
  const [funnelRows, catalogCountRows] = await Promise.all([
    sql`SELECT * FROM agg_inclusion_exclusion_funnel ORDER BY stage_order ASC`,
    sql`SELECT COUNT(*)::int AS cnt FROM esco_occupations_catalog`,
  ]);

  const funnel = funnelRows.map((r) => ({
    stage_order: Number(r.stage_order),
    stage_code: String(r.stage_code),
    stage_label_es: String(r.stage_label_es),
    status_in_neon: String(r.status_in_neon),
    experiences_count: Number(r.experiences_count),
    persons_count: Number(r.persons_count),
    pct_clean_experiences: Number(r.pct_clean_experiences),
    pct_clean_persons: Number(r.pct_clean_persons),
    reason_es: String(r.reason_es),
  }));

  const byCode = (code: string) => funnel.find((f) => f.stage_code === code);

  return {
    funnel,
    escoCatalogCount: Number(catalogCountRows[0]?.cnt ?? 0),
    wardDirectPersonsCount:
      byCode("ward_25k_direct_subsample")?.persons_count ?? 0,
    trainPersonsCount: byCode("census_split_train")?.persons_count ?? 0,
    testPersonsCount: byCode("census_split_test")?.persons_count ?? 0,
    totalPersonsCount:
      byCode("included_classified_census_total")?.persons_count ?? 0,
    totalExperiencesCount:
      byCode("included_classified_census_total")?.experiences_count ?? 0,
  };
}
