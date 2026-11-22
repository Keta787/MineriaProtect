/**
 * Diccionario de etiquetas en español para los 10 Grandes Grupos ISCO-08 (0..9),
 * niveles educativos, segmentos de trayectoria (5.0), clústeres K-Means (8.0) y Ward (8.1),
 * y glosas en español para las ocupaciones ESCO más frecuentes.
 */

export const ISCO_MAJOR_LABELS_ES: Record<string, { code: string; title: string; short: string; color: string }> = {
  "0": {
    code: "ISCO 0",
    title: "Ocupaciones militares",
    short: "0 · Militares",
    color: "#475569",
  },
  "1": {
    code: "ISCO 1",
    title: "Directores y gerentes",
    short: "1 · Directores y gerentes",
    color: "#1d4ed8",
  },
  "2": {
    code: "ISCO 2",
    title: "Profesionales científicos e intelectuales",
    short: "2 · Profesionales científicos",
    color: "#0284c7",
  },
  "3": {
    code: "ISCO 3",
    title: "Técnicos y profesionales de nivel medio",
    short: "3 · Técnicos nivel medio",
    color: "#0d9488",
  },
  "4": {
    code: "ISCO 4",
    title: "Personal de apoyo administrativo",
    short: "4 · Apoyo administrativo",
    color: "#059669",
  },
  "5": {
    code: "ISCO 5",
    title: "Trabajadores de los servicios y vendedores",
    short: "5 · Servicios y ventas",
    color: "#d97706",
  },
  "6": {
    code: "ISCO 6",
    title: "Agricultores y trabajadores agropecuarios",
    short: "6 · Agropecuarios y forestales",
    color: "#65a30d",
  },
  "7": {
    code: "ISCO 7",
    title: "Oficiales, operarios y artesanos",
    short: "7 · Oficiales y operarios",
    color: "#ea580c",
  },
  "8": {
    code: "ISCO 8",
    title: "Operadores de instalaciones y máquinas",
    short: "8 · Operadores y conductores",
    color: "#7c3aed",
  },
  "9": {
    code: "ISCO 9",
    title: "Ocupaciones elementales",
    short: "9 · Ocupaciones elementales",
    color: "#db2777",
  },
};

export function formatIscoMajor(digit: string | number | null | undefined): string {
  const key = String(digit ?? "").trim();
  const entry = ISCO_MAJOR_LABELS_ES[key];
  if (!entry) return `Grupo ISCO ${key || "N/D"}`;
  return `${entry.title} (${entry.code})`;
}

export const UNIVERSITY_LEVEL_ES: Record<string, string> = {
  "Secondary school": "Educación Secundaria (Secondary school)",
  Bachelor: "Pregrado Universitario (Bachelor)",
  Master: "Maestría / Posgrado (Master)",
  PhD: "Doctorado (PhD)",
  "No reportado": "Educación no reportada (Bandera MNAR = 1)",
};

export function formatEducationEs(level: string | null | undefined): string {
  const key = String(level ?? "No reportado").trim();
  return UNIVERSITY_LEVEL_ES[key] ?? key;
}

export const TRAJECTORY_SEGMENT_ES: Record<
  string,
  { label: string; description: string; badgeClass: string }
> = {
  exploradora: {
    label: "Exploradora pura",
    description: "Cambia de oficio ESCO en cada transición laboral (0 retornos a oficios previos).",
    badgeClass: "bg-sky-100 text-sky-900 border-sky-300",
  },
  mixta: {
    label: "Trayectoria mixta",
    description: "Combina exploración de nuevos oficios con retornos ocasionales.",
    badgeClass: "bg-indigo-100 text-indigo-900 border-indigo-300",
  },
  permanente: {
    label: "Permanencia / Especialización",
    description: "Alta proporción de continuidad o retorno recurrente al mismo oficio ESCO.",
    badgeClass: "bg-emerald-100 text-emerald-900 border-emerald-300",
  },
  sin_transicion: {
    label: "Sin transición (1 empleo)",
    description: "Persona con 1 única experiencia clasificada en su historial.",
    badgeClass: "bg-slate-100 text-slate-800 border-slate-300",
  },
};

export const KMEANS_CLUSTER_PROFILES_ES: Record<
  number,
  { name: string; shareCensus: string; summary: string; badgeClass: string; color: string }
> = {
  0: {
    name: "Clúster 0 · Inserción Temprana y Operativos/Servicios",
    shareCensus: "43.91 % del censo (154,606 personas)",
    summary: "Secundaria/Técnico, oficios operativos y comerciales con competencias prácticas moderadas.",
    badgeClass: "bg-blue-100 text-blue-900 border-blue-300",
    color: "#2563eb",
  },
  1: {
    name: "Clúster 1 · Educación No Reportada (Segmento MNAR)",
    shareCensus: "11.67 % del censo (41,082 personas)",
    summary: "Omisión informativa de nivel educativo (educacion_no_reportada = 1), carreras cortas.",
    badgeClass: "bg-amber-100 text-amber-900 border-amber-300",
    color: "#d97706",
  },
  2: {
    name: "Clúster 2 · Profesionales Intensivos en Conocimiento",
    shareCensus: "27.97 % del censo (98,494 personas)",
    summary: "Pregrado/Maestría (ISCO 2 y 3), alta densidad de conocimientos teóricos ESCO.",
    badgeClass: "bg-emerald-100 text-emerald-900 border-emerald-300",
    color: "#059669",
  },
  3: {
    name: "Clúster 3 · Trayectorias Largas, Estables y Pluriempleo",
    shareCensus: "16.45 % del censo (57,911 personas)",
    summary: "Carreras extensas (media ~49 trimestres de amplitud) y alta retención ocupacional.",
    badgeClass: "bg-purple-100 text-purple-900 border-purple-300",
    color: "#7c3aed",
  },
};

export const WARD_CLUSTER_PROFILES_ES: Record<
  number,
  { name: string; shareSample25k: string; summary: string; badgeClass: string; color: string }
> = {
  0: {
    name: "Ward 0 · Profesionales y Técnicos de Alta Competencia",
    shareSample25k: "27.27 % de la muestra Ward (6,818 / 25,000)",
    summary: "Alta calificación teórica y académica en grupos ISCO 2 y 3.",
    badgeClass: "bg-teal-100 text-teal-900 border-teal-300",
    color: "#0d9488",
  },
  1: {
    name: "Ward 1 · Educación No Reportada (MNAR)",
    shareSample25k: "11.86 % de la muestra Ward (2,966 / 25,000)",
    summary: "Aísla limpiamente la ausencia informativa de educación reportada.",
    badgeClass: "bg-amber-100 text-amber-900 border-amber-300",
    color: "#d97706",
  },
  2: {
    name: "Ward 2 · Base Operativa, Administrativa y Comercial",
    shareSample25k: "47.70 % de la muestra Ward (11,924 / 25,000)",
    summary: "Núcleo mayoritario de servicios, ventas y apoyo administrativo.",
    badgeClass: "bg-indigo-100 text-indigo-900 border-indigo-300",
    color: "#4f46e5",
  },
  3: {
    name: "Ward 3 · Carreras Extensas de Alta Permanencia",
    shareSample25k: "13.17 % de la muestra Ward (3,292 / 25,000)",
    summary: "Mayor amplitud temporal en trimestres y alta estabilidad por puesto.",
    badgeClass: "bg-fuchsia-100 text-fuchsia-900 border-fuchsia-300",
    color: "#c026d3",
  },
};

/**
 * Glosas en español para los oficios ESCO más frecuentes en el top de transiciones.
 */
export const ESCO_LABEL_GLOSS_ES: Record<string, string> = {
  "shop sales assistant": "Asistente de ventas en tienda",
  "administrative assistant": "Asistente administrativo",
  "cleaner": "Personal de limpieza",
  "warehouse worker": "Operario de almacén / logística",
  "waiter/waitress": "Mesero / camarero",
  "kitchen assistant": "Auxiliar de cocina",
  "cashier": "Cajero de comercio",
  "receptionist": "Recepcionista",
  "forklift operator": "Operador de montacargas",
  "call centre agent": "Agente de centro de llamadas",
  "accountant": "Contador",
  "project manager": "Gerente de proyectos",
  "software developer": "Desarrollador de software",
  "nurse": "Enfermero/a profesional",
  "teacher": "Docente / profesor",
  "driver": "Conductor",
  "production worker": "Operario de producción",
  "sales representative": "Representante comercial",
  "human resources assistant": "Asistente de recursos humanos",
  "customer service representative": "Representante de atención al cliente",
};

export function formatEscoOccupationWithCode(
  label: string | null | undefined,
  code: string | null | undefined
): string {
  const cleanLabel = String(label ?? "Ocupación ESCO").trim();
  const cleanCode = String(code ?? "").trim();
  const gloss = ESCO_LABEL_GLOSS_ES[cleanLabel.toLowerCase()];
  if (gloss) {
    return `${gloss} — "${cleanLabel}" (ESCO ${cleanCode})`;
  }
  return `${cleanLabel} (ESCO ${cleanCode})`;
}
