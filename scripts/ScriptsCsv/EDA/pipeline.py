"""Facade that wires every EDA component and runs the analysis.

The notebook only talks to :class:`EDAPipeline`.  Dependencies are injected in
the constructor (dependency inversion): the pipeline does not create loaders,
renderers or analyzers, it receives them.  ``EDAPipeline.default`` is a
convenience factory for the notebook.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from .bivariate import CorrelationAnalyzer
from .config import (
    CORRELATION_NUMERIC,
    EDAConfig,
    EXPERIENCE_NUMERIC,
    PERSON_NUMERIC,
    TARGET_COL,
    TARGET_DISPLAY,
    UNIVERSITY_ORDER,
    VERSION_LABELS,
    VERSIONS,
    VERSION_WITH_OUTLIERS,
    VERSION_WITHOUT_OUTLIERS,
    default_config,
)
from .decision_log import DecisionLog
from .descriptive import ExperienceDescriber
from .leakage import LeakageAuditor
from .loader import JobPathLoader
from .pca_evidence import PCAEvidenceReader
from .person_level import PersonLevelAggregator
from .plots import ChartRenderer
from .profiling import ColumnProfiler, DataQualityAuditor
from .split_map import SplitMapper, SplitMapResult
from .target import SplitGuard, TargetAnalyzer
from .transitions import TransitionAnalyzer
from .validation import FigureManifest, FileHasher, TargetUsageValidator


def cramers_v(table: pd.DataFrame) -> float:
    """Cramér's V for a contingency table (0 = independent, 1 = perfect)."""
    values = table.to_numpy(dtype=float)
    if values.sum() == 0 or min(values.shape) < 2:
        return float("nan")
    chi2 = chi2_contingency(values, correction=False)[0]
    n = values.sum()
    return float(np.sqrt(chi2 / (n * (min(values.shape) - 1))))


def _fmt_int(value: int) -> str:
    """Format an integer with Spanish thousands separator."""
    return f"{int(value):,}".replace(",", ".")


@dataclass
class EDAResults:
    """Container for every table produced by the run."""

    profiles: Dict[str, pd.DataFrame] = field(default_factory=dict)
    quality: Dict[str, pd.DataFrame] = field(default_factory=dict)
    text_stats: Dict[str, pd.DataFrame] = field(default_factory=dict)
    winsorization: pd.DataFrame = field(default_factory=pd.DataFrame)
    numeric_summary: Dict[str, pd.DataFrame] = field(default_factory=dict)
    outliers: Dict[str, pd.DataFrame] = field(default_factory=dict)
    duration_spikes: pd.DataFrame = field(default_factory=pd.DataFrame)
    ab_comparison: pd.DataFrame = field(default_factory=pd.DataFrame)
    whatif: Dict[str, float] = field(default_factory=dict)
    person: pd.DataFrame = field(default_factory=pd.DataFrame)
    person_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    job_distribution: pd.DataFrame = field(default_factory=pd.DataFrame)
    returns_distribution: pd.DataFrame = field(default_factory=pd.DataFrame)
    thresholds: Dict[str, float] = field(default_factory=dict)
    person_segment: pd.DataFrame = field(default_factory=pd.DataFrame)
    segment_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    segment_by_education: pd.DataFrame = field(default_factory=pd.DataFrame)
    segment_by_isco: pd.DataFrame = field(default_factory=pd.DataFrame)
    segment_cramers_v: Dict[str, float] = field(default_factory=dict)
    transitions: pd.DataFrame = field(default_factory=pd.DataFrame)
    transition_summary: Dict[str, float] = field(default_factory=dict)
    top_moves: pd.DataFrame = field(default_factory=pd.DataFrame)
    transition_rates: pd.DataFrame = field(default_factory=pd.DataFrame)
    return_stats: pd.DataFrame = field(default_factory=pd.DataFrame)
    occupation_matrix: pd.DataFrame = field(default_factory=pd.DataFrame)
    isco_matrix: pd.DataFrame = field(default_factory=pd.DataFrame)
    pearson: pd.DataFrame = field(default_factory=pd.DataFrame)
    spearman: pd.DataFrame = field(default_factory=pd.DataFrame)
    high_pairs: pd.DataFrame = field(default_factory=pd.DataFrame)
    scatter_sample: pd.DataFrame = field(default_factory=pd.DataFrame)
    pca_evidence: List[object] = field(default_factory=list)
    pca_stability: pd.DataFrame = field(default_factory=pd.DataFrame)
    pca_variance: pd.DataFrame = field(default_factory=pd.DataFrame)
    pca_components: pd.DataFrame = field(default_factory=pd.DataFrame)
    pca_loadings: pd.DataFrame = field(default_factory=pd.DataFrame)
    target_balance: pd.DataFrame = field(default_factory=pd.DataFrame)
    target_overall: Dict[str, float] = field(default_factory=dict)
    target_by_isco: pd.DataFrame = field(default_factory=pd.DataFrame)
    target_by_duration: pd.DataFrame = field(default_factory=pd.DataFrame)
    target_by_education: pd.DataFrame = field(default_factory=pd.DataFrame)
    duration_edges: List[float] = field(default_factory=list)
    leakage_audit: pd.DataFrame = field(default_factory=pd.DataFrame)
    leakage_contamination: pd.DataFrame = field(default_factory=pd.DataFrame)
    x_leak_columns: List[str] = field(default_factory=list)
    split_verification: Dict[str, object] = field(default_factory=dict)
    split_map_path: str = ""
    figures: Dict[str, object] = field(default_factory=dict)
    input_integrity: pd.DataFrame = field(default_factory=pd.DataFrame)
    figure_manifest: pd.DataFrame = field(default_factory=pd.DataFrame)
    target_usage: pd.DataFrame = field(default_factory=pd.DataFrame)


class EDAPipeline:
    """Orchestrate the EDA from loading to validation."""

    def __init__(
        self,
        config: EDAConfig,
        loader: JobPathLoader,
        profiler: ColumnProfiler,
        quality: DataQualityAuditor,
        describer: ExperienceDescriber,
        person_aggregator: PersonLevelAggregator,
        transitions: TransitionAnalyzer,
        correlations: CorrelationAnalyzer,
        target: TargetAnalyzer,
        leakage: LeakageAuditor,
        split_mapper: SplitMapper,
        pca_reader: PCAEvidenceReader,
        renderer: ChartRenderer,
        hasher: FileHasher,
        manifest: FigureManifest,
        usage_validator: TargetUsageValidator,
        guard: SplitGuard,
        decisions: DecisionLog,
    ) -> None:
        self.config = config
        self.loader = loader
        self.profiler = profiler
        self.quality = quality
        self.describer = describer
        self.person_aggregator = person_aggregator
        self.transitions = transitions
        self.correlations = correlations
        self.target = target
        self.leakage = leakage
        self.split_mapper = split_mapper
        self.pca_reader = pca_reader
        self.renderer = renderer
        self.hasher = hasher
        self.manifest = manifest
        self.usage_validator = usage_validator
        self.guard = guard
        self.decisions = decisions
        self.results = EDAResults()
        self.frames: Dict[str, pd.DataFrame] = {}
        self.y: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.train: Dict[str, pd.DataFrame] = {}
        self.test: Dict[str, pd.DataFrame] = {}
        self._fingerprints = {}
        self._split_result: Optional[SplitMapResult] = None

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------
    @classmethod
    def default(cls, config: Optional[EDAConfig] = None) -> "EDAPipeline":
        """Build the standard pipeline with the production dependencies."""
        cfg = config or default_config()
        guard = SplitGuard()
        return cls(
            config=cfg,
            loader=JobPathLoader(cfg),
            profiler=ColumnProfiler(),
            quality=DataQualityAuditor(),
            describer=ExperienceDescriber(),
            person_aggregator=PersonLevelAggregator(),
            transitions=TransitionAnalyzer(),
            correlations=CorrelationAnalyzer(),
            target=TargetAnalyzer(guard),
            leakage=LeakageAuditor(),
            split_mapper=SplitMapper(),
            pca_reader=PCAEvidenceReader(cfg),
            renderer=ChartRenderer(cfg),
            hasher=FileHasher(),
            manifest=FigureManifest(),
            usage_validator=TargetUsageValidator(),
            guard=guard,
            decisions=DecisionLog(),
        )

    # ------------------------------------------------------------------
    # 1. Loading and integrity snapshot
    # ------------------------------------------------------------------
    def start(self) -> "EDAPipeline":
        """Fingerprint the inputs and load both versions in memory."""
        self._fingerprints = self.hasher.snapshot(self.config.input_paths)
        self.frames = {version: self.loader.load_clean(version) for version in VERSIONS}
        self.y = {
            version: {
                split: self.loader.load_y(version, split) for split in ("train", "test")
            }
            for version in VERSIONS
        }
        self.results.text_stats = {
            version: pd.DataFrame(
                [stat.__dict__ for stat in self.loader.text_column_stats(version)]
            )
            for version in VERSIONS
        }
        return self

    # ------------------------------------------------------------------
    # 2. Profiling and quality
    # ------------------------------------------------------------------
    def profile(self) -> "EDAPipeline":
        """Column profile, inherited quality and winsorization effect."""
        for version in VERSIONS:
            self.results.profiles[version] = self.profiler.profile(self.frames[version])
            text_rows = self.results.text_stats[version]
            if not text_rows.empty:
                extra = self.profiler.profile(
                    self.frames[version].iloc[:, :0],
                    text_stats=list(text_rows.itertuples(index=False)),
                )
                self.results.profiles[version] = pd.concat(
                    [self.results.profiles[version], extra], ignore_index=True
                )
            self.results.quality[version] = self.quality.summary(self.frames[version])
            text_nulls = int(text_rows["nulls"].sum()) if not text_rows.empty else 0
            tabular = self.results.quality[version]
            tabular.loc[tabular["metric"] == "Nulos totales", "metric"] = (
                "Nulos totales (columnas tabulares)"
            )
            extra_quality = pd.DataFrame(
                [
                    {
                        "metric": "Nulos en listas ESCO",
                        "value": text_nulls,
                        "comment": "skills, knowledge y sin_tipo se perfilan por separado.",
                    },
                    {
                        "metric": "Nulos totales (incluye listas ESCO)",
                        "value": int(tabular.loc[tabular["metric"] == "Nulos totales (columnas tabulares)", "value"].iloc[0]) + text_nulls,
                        "comment": "Coincide con el control que falló en la validación de 2.0.",
                    },
                ]
            )
            self.results.quality[version] = pd.concat(
                [tabular, extra_quality], ignore_index=True
            )
            self.results.outliers[version] = self.describer.iqr_outliers(
                self.frames[version], EXPERIENCE_NUMERIC
            )
        self.results.winsorization = self.quality.winsorization_effect(
            self.frames[VERSION_WITH_OUTLIERS],
            self.frames[VERSION_WITHOUT_OUTLIERS],
            columns=("n_skills_essential", "n_skills_competence",
                     "n_skills_knowledge", "veces_ese_oficio"),
        )
        return self

    # ------------------------------------------------------------------
    # 3. Split map and target attachment
    # ------------------------------------------------------------------
    def build_split(self) -> "EDAPipeline":
        """Rebuild, verify and persist the person-level split map."""
        self._split_result = self.split_mapper.build(
            self.frames[VERSION_WITH_OUTLIERS],
            self.y[VERSION_WITH_OUTLIERS]["train"],
            self.y[VERSION_WITH_OUTLIERS]["test"],
            self.config,
        )
        self.results.split_map_path = self.split_mapper.save(self._split_result, self.config)
        self.results.split_verification = self._split_result.verification

        self.train[VERSION_WITH_OUTLIERS] = self._split_result.train
        self.test[VERSION_WITH_OUTLIERS] = self._split_result.test

        # Version B has the same rows in the same order; the split is reused
        # through the stored row position, never recomputed.
        train_positions = self._split_result.train["_row_position"].to_numpy()
        test_positions = self._split_result.test["_row_position"].to_numpy()
        train_b = self.frames[VERSION_WITHOUT_OUTLIERS].iloc[train_positions].reset_index(drop=True)
        test_b = self.frames[VERSION_WITHOUT_OUTLIERS].iloc[test_positions].reset_index(drop=True)
        train_b[TARGET_COL] = self._split_result.train[TARGET_COL].to_numpy()
        test_b[TARGET_COL] = self._split_result.test[TARGET_COL].to_numpy()
        train_b[TARGET_DISPLAY] = train_b[TARGET_COL]
        test_b[TARGET_DISPLAY] = test_b[TARGET_COL]
        self.train[VERSION_WITHOUT_OUTLIERS] = train_b
        self.test[VERSION_WITHOUT_OUTLIERS] = test_b
        return self

    # ------------------------------------------------------------------
    # 4. Experience-level description
    # ------------------------------------------------------------------
    def describe(self) -> "EDAPipeline":
        """Numeric summaries, outliers, duration spikes and A/B comparison."""
        frame_a = self.frames[VERSION_WITH_OUTLIERS]
        frame_b = self.frames[VERSION_WITHOUT_OUTLIERS]
        for version, frame in ((VERSION_WITH_OUTLIERS, frame_a), (VERSION_WITHOUT_OUTLIERS, frame_b)):
            self.results.numeric_summary[version] = self.describer.numeric_summary(
                frame, EXPERIENCE_NUMERIC
            )
            self.results.outliers[version] = self.describer.iqr_outliers(
                frame, EXPERIENCE_NUMERIC
            )
        self.results.duration_spikes = self.describer.duration_spikes(frame_a)
        self.results.ab_comparison = self.describer.compare_versions(
            frame_a, frame_b, EXPERIENCE_NUMERIC
        )
        whatif = self.describer.dur_q_what_if(frame_a)
        self.results.whatif = whatif.__dict__
        return self

    # ------------------------------------------------------------------
    # 5. Person level and derived segment
    # ------------------------------------------------------------------
    def person_level(self) -> "EDAPipeline":
        """Aggregate by person and build the target-free trajectory segment."""
        frame = self.frames[VERSION_WITH_OUTLIERS]
        person = self.person_aggregator.aggregate(frame)
        self.results.person = person
        self.results.person_summary = self.person_aggregator.summary(person)
        self.results.job_distribution = self.person_aggregator.job_distribution(person)
        self.results.returns_distribution = self.person_aggregator.returns_distribution(person)

        eligible = person.loc[person["has_classified_job"]].copy()
        thresholds = self.person_aggregator.segment_thresholds(eligible)
        self.results.thresholds = thresholds.__dict__
        segment = self.person_aggregator.assign_segment(eligible, thresholds)
        self.results.person_segment = segment
        self.results.segment_summary = self.person_aggregator.segment_summary(segment)

        education = pd.crosstab(segment["segmento"], segment["university_level"])
        education_pct = education.div(education.sum(axis=1), axis=0).mul(100).round(2)
        self.results.segment_by_education = education_pct.reset_index()

        isco_top = segment["isco_main"].value_counts().head(10).index
        isco_data = segment.loc[segment["isco_main"].isin(isco_top)]
        isco = pd.crosstab(isco_data["segmento"], isco_data["isco_main"])
        isco_pct = isco.div(isco.sum(axis=1), axis=0).mul(100).round(2)
        self.results.segment_by_isco = isco_pct.reset_index()

        self.results.segment_cramers_v = {
            "segmento_vs_nivel_educativo": round(cramers_v(education), 4),
            "segmento_vs_isco": round(cramers_v(isco), 4),
        }
        return self

    # ------------------------------------------------------------------
    # 6. Transitions
    # ------------------------------------------------------------------
    def transition_analysis(self) -> "EDAPipeline":
        """Consecutive moves, self-loops and the two transition matrices."""
        transitions = self.transitions.build(self.frames[VERSION_WITH_OUTLIERS])
        self.results.transitions = transitions
        summary = self.transitions.summary(transitions)
        self.results.transition_summary = summary.__dict__
        self.results.top_moves = self.transitions.top_moves(transitions, top_n=20)
        self.results.transition_rates = self.transitions.transition_rates(transitions)
        self.results.return_stats = self.transitions.return_stats(transitions)
        self.results.occupation_matrix = self.transitions.occupation_matrix(transitions, top_n=20)
        self.results.isco_matrix = self.transitions.isco_matrix(transitions, top_n=15)
        return self

    # ------------------------------------------------------------------
    # 7. Bivariate
    # ------------------------------------------------------------------
    def bivariate(self) -> "EDAPipeline":
        """Pearson, Spearman, redundant pairs and the hexbin sample."""
        frame = self.frames[VERSION_WITH_OUTLIERS]
        self.results.pearson = self.correlations.matrix(frame, CORRELATION_NUMERIC, "pearson")
        self.results.spearman = self.correlations.matrix(frame, CORRELATION_NUMERIC, "spearman")
        self.results.high_pairs = self.correlations.high_pairs(frame, CORRELATION_NUMERIC, 0.7)
        self.results.scatter_sample = self.correlations.scatter_sample(
            self.results.person,
            x="n_jobs",
            y="n_occ",
            n=self.config.scatter_sample,
            seed=self.config.seed,
        )
        return self

    # ------------------------------------------------------------------
    # 8. PCA evidence
    # ------------------------------------------------------------------
    def pca(self) -> "EDAPipeline":
        """Read the saved PCA outputs; never refit."""
        evidence = self.pca_reader.read_all()
        self.results.pca_evidence = evidence
        self.results.pca_stability = self.pca_reader.stability(evidence)
        self.results.pca_variance = pd.concat([item.variance for item in evidence], ignore_index=True)
        self.results.pca_components = pd.concat(
            [item.components for item in evidence], ignore_index=True
        )
        loadings = pd.concat([item.loadings for item in evidence], ignore_index=True)
        self.results.pca_loadings = loadings
        return self

    # ------------------------------------------------------------------
    # 9. Target, train only
    # ------------------------------------------------------------------
    def target_analysis(self) -> "EDAPipeline":
        """Balance and group rates of the target, always on the train split."""
        parts = {
            version: (self.train[version], self.test[version]) for version in VERSIONS
        }
        self.results.target_balance = self.target.balance(parts, VERSION_LABELS)

        train = self.train[VERSION_WITH_OUTLIERS]
        self.results.target_overall = self.target.overall_rate(train, "tasa global del target")
        self.results.target_by_isco = self.target.rate_by(
            train, "isco_group_label", "tasa por ISCO", min_n=self.config.min_group_n, top_n=15
        )
        edges, labels = self.target.quantile_bins(train, "dur_q", n_bins=4)
        self.results.duration_edges = edges
        self.results.target_by_duration = self.target.rate_by_bins(
            train, "dur_q", edges, labels, "tasa por duración"
        )
        self.results.target_by_education = self.target.rate_by(
            train,
            "university_level",
            "tasa por nivel educativo",
            order=UNIVERSITY_ORDER,
        )
        return self

    # ------------------------------------------------------------------
    # 10. Leakage
    # ------------------------------------------------------------------
    def leakage_analysis(self) -> "EDAPipeline":
        """Direct, person-level and column-name leakage audit."""
        train = self.train[VERSION_WITH_OUTLIERS]
        x_header = self.loader.load_x_header(VERSION_WITH_OUTLIERS, "train")
        self.results.x_leak_columns = self.leakage.x_leak_columns(x_header)
        leak_columns = [
            column
            for column in ("veces_ese_oficio_bin", "veces_ese_oficio_rob")
            if column in x_header
        ]
        x_leak = self.loader.load_x_subset(VERSION_WITH_OUTLIERS, "train", leak_columns)
        audit_experience = self.leakage.audit_experience(train)
        audit_x = self.leakage.audit_x(train, x_leak, train[TARGET_DISPLAY])
        audit_person = self.leakage.audit_person(self.results.person)
        self.results.leakage_audit = self.leakage.verdict_summary(
            audit_experience, audit_x, audit_person
        )
        self.results.leakage_contamination = self.leakage.contamination_table(train)
        return self

    # ------------------------------------------------------------------
    # 11. Figures
    # ------------------------------------------------------------------
    def render_quality(self) -> Dict[str, object]:
        """G08, G09 and G10."""
        figures = {
            "G08": self.renderer.g08_nulls_heatmap(self.results.profiles[VERSION_WITH_OUTLIERS]),
            "G09": self.renderer.g09_outliers_ab(
                self.results.outliers[VERSION_WITH_OUTLIERS],
                self.results.outliers[VERSION_WITHOUT_OUTLIERS],
            ),
            "G10": self.renderer.g10_esco_coverage_by_year(
                self.frames[VERSION_WITH_OUTLIERS]
            ),
        }
        self.results.figures.update(figures)
        return figures

    def render_experience(self) -> Dict[str, object]:
        """G01 to G07, except G02 and G04 which use precomputed tables."""
        frame = self.frames[VERSION_WITH_OUTLIERS]
        education = self.describer.top_categories(frame, "university_level", top_n=10)
        occupations = self.describer.top_categories(frame, "occupation_label", top_n=15)
        figures = {
            "G01": self.renderer.g01_duration_hist(frame),
            "G02": self.renderer.g02_top_occupations(occupations),
            "G03": self.renderer.g03_duration_by_isco(frame),
            "G04": self.renderer.g04_education_levels(education),
            "G05": self.renderer.g05_skills_hist(frame),
            "G06": self.renderer.g06_skills_by_isco(frame),
            "G07": self.renderer.g07_experiences_by_year(frame),
        }
        self.results.figures.update(figures)
        return figures

    def render_person(self) -> Dict[str, object]:
        """G11 to G15, except G13 and G15 which use precomputed tables."""
        sample = self.results.scatter_sample
        if sample.empty:
            sample = self.correlations.scatter_sample(
                self.results.person,
                x="n_jobs",
                y="n_occ",
                n=self.config.scatter_sample,
                seed=self.config.seed,
            )
        figures = {
            "G11": self.renderer.g11_jobs_per_person(self.results.person),
            "G12": self.renderer.g12_career_span(self.results.person),
            "G13": self.renderer.g13_returns_per_person(self.results.returns_distribution),
            "G14": self.renderer.g14_trajectory_shape(
                self.results.person_segment, self.results.thresholds
            ),
            "G15": self.renderer.g15_hexbin_jobs_occupations(sample),
        }
        self.results.figures.update(figures)
        return figures

    def render_transitions(self) -> Dict[str, object]:
        """G16, G20, G21 and G22."""
        figures = {
            "G16": self.renderer.g16_top_moves(self.results.top_moves),
            "G20": self.renderer.g20_occupation_transitions(self.results.occupation_matrix),
            "G21": self.renderer.g21_isco_transitions(self.results.isco_matrix),
            "G22": self.renderer.g22_selfloop_by_occupation(self.results.transition_rates),
        }
        self.results.figures.update(figures)
        return figures

    def render_bivariate(self) -> Dict[str, object]:
        """G17 and G19."""
        figures = {
            "G17": self.renderer.g17_correlation(self.results.pearson),
            "G19": self.renderer.g19_pearson_vs_spearman(
                self.results.pearson, self.results.spearman
            ),
        }
        self.results.figures.update(figures)
        return figures

    def render_pca(self) -> Dict[str, object]:
        """G23."""
        figures = {
            "G23": self.renderer.g23_pca_stability(
                self.results.pca_variance, self.results.pca_components
            )
        }
        self.results.figures.update(figures)
        return figures

    def render_ab(self) -> Dict[str, object]:
        """G25."""
        figures = {
            "G25": self.renderer.g25_ab_comparison(
                self.results.ab_comparison, self.results.whatif
            )
        }
        self.results.figures.update(figures)
        return figures

    def render_target(self) -> Dict[str, object]:
        """G26, G27, G28 and G29."""
        figures = {
            "G26": self.renderer.g26_target_balance(self.results.target_balance),
            "G27": self.renderer.g27_target_by_isco(self.results.target_by_isco),
            "G28": self.renderer.g28_target_by_duration(self.results.target_by_duration),
            "G29": self.renderer.g29_target_by_education(self.results.target_by_education),
        }
        self.results.figures.update(figures)
        return figures

    def render_leakage(self) -> Dict[str, object]:
        """G30."""
        audit = self.results.leakage_audit
        panel = audit.loc[
            audit["check"].str.contains("==")
            & audit["variable"].isin(
                ["veces_ese_oficio", "veces_ese_oficio_bin", "veces_ese_oficio_rob"]
            )
        ].copy()
        figures = {
            "G30": self.renderer.g30_leakage(panel, self.results.leakage_contamination)
        }
        self.results.figures.update(figures)
        return figures

    # ------------------------------------------------------------------
    # 12. Findings and validation
    # ------------------------------------------------------------------
    def record_findings(self) -> pd.DataFrame:
        """Fill the decision log with values produced by this run."""
        if len(self.decisions):
            return self.decisions.to_frame()
        leakage_max = float(self.results.leakage_audit["value"].max())
        self.decisions.add(
            hallazgo="El target está dentro de la matriz de features",
            evidencia=(
                f"veces_ese_oficio_bin reproduce el target en el {leakage_max:.2f}% "
                "de las filas de train; la columna también existe como "
                "veces_ese_oficio_rob y veces_ese_oficio."
            ),
            figura="G30",
            accion=(
                "Excluir veces_ese_oficio, veces_ese_oficio_bin y veces_ese_oficio_rob "
                "de X antes de la fase 4; registrar la fuga como riesgo bloqueante."
            ),
            tarea_crispdm="Data Understanding · verificación de calidad",
        )
        spike = self.results.duration_spikes.iloc[0]
        self.decisions.add(
            hallazgo="La duración se concentra en valores redondos",
            evidencia=(
                f"El valor {int(spike['trimestres'])} trimestres aparece en "
                f"{_fmt_int(int(spike['frecuencia']))} experiencias ({spike['pct']:.2f}%)."
            ),
            figura="G01",
            accion=(
                "Mantener dur_q como medida descriptiva; no derivar de los picos una "
                "regla de negocio sin validar con la fuente."
            ),
            tarea_crispdm="Data Understanding · describir",
        )
        person = self.results.person
        returns_share = float(person["any_repeated"].mean() * 100)
        self.decisions.add(
            hallazgo="La repetición de oficio es frecuente a nivel persona",
            evidencia=(
                f"{returns_share:.2f}% de las personas tiene al menos un retorno a un "
                f"oficio previo; el autolazo representa "
                f"{self.results.transition_summary['self_loop_pct']:.2f}% de las transiciones."
            ),
            figura="G13",
            accion=(
                "Usar n_returns solo como descriptor; no cruzarlo con el target porque "
                "es una reexpresión del mismo fenómeno."
            ),
            tarea_crispdm="Data Understanding · explorar",
        )
        summary = self.results.transition_summary
        rates = self.results.transition_rates
        lateral = rates.nlargest(1, "mismo_isco_pct").iloc[0]
        self.decisions.add(
            hallazgo="El cambio lateral dentro del área pesa más que el autolazo",
            evidencia=(
                f"El autolazo es el {summary['self_loop_pct']:.2f}% de las transiciones y la "
                f"permanencia en el mismo grupo ISCO llega al {summary['same_isco_pct']:.2f}%; "
                f"en {lateral['source_label']} el {lateral['mismo_isco_pct']:.2f}% de las salidas "
                "se queda en el mismo grupo ISCO."
            ),
            figura="G22",
            accion=(
                "En fase 4 tratar occupation_code e isco_group como bloques separados y no "
                "leer un cambio de ISCO como promoción."
            ),
            tarea_crispdm="Data Understanding · explorar relaciones",
        )
        coverage_frame = self.frames[VERSION_WITH_OUTLIERS]
        coverage = (
            pd.crosstab(coverage_frame["start_year"], coverage_frame["emparejado"], normalize="index")
            .get("ok", pd.Series(dtype=float))
            .mul(100)
        )
        coverage = coverage.loc[coverage.index.to_series().between(2000, 2020)]
        coverage_min_year = int(coverage.idxmin())
        coverage_max_year = int(coverage.idxmax())
        self.decisions.add(
            hallazgo="La cobertura del emparejamiento ESCO es estable en el tiempo",
            evidencia=(
                f"Entre 2000 y 2020 la proporción de experiencias emparejadas se mantiene "
                f"entre {coverage.min():.2f}% ({coverage_min_year}) y "
                f"{coverage.max():.2f}% ({coverage_max_year}); el oficio no clasificado no es "
                "un deterioro reciente de la fuente."
            ),
            figura="G10",
            accion=(
                "Tratar el oficio no clasificado como nulo estructural y no imputarlo; en "
                "fase 4 evaluar un indicador explícito de missing de oficio."
            ),
            tarea_crispdm="Data Understanding · verificar calidad",
        )
        overall = self.results.target_overall
        self.decisions.add(
            hallazgo="El target está moderadamente desbalanceado",
            evidencia=(
                f"Prevalencia en train = {overall['tasa_pct']:.2f}% "
                f"(IC 95 %: {overall['ic95_inf_pct']:.2f}–{overall['ic95_sup_pct']:.2f}), "
                f"con {_fmt_int(overall['positivos'])} positivos de "
                f"{_fmt_int(overall['n'])} filas."
            ),
            figura="G26",
            accion=(
                "En fase 4, usar métricas sensibles al desbalance (PR-AUC, recall) y "
                "no solo exactitud."
            ),
            tarea_crispdm="Data Understanding · describir el target",
        )
        duration = self.results.target_by_duration
        self.decisions.add(
            hallazgo="La duración del empleo se asocia con la reincidencia",
            evidencia=(
                f"La tasa va de {duration['tasa_pct'].min():.2f}% a "
                f"{duration['tasa_pct'].max():.2f}% entre tramos de duración; "
                f"la diferencia es de {duration['tasa_pct'].max() - duration['tasa_pct'].min():.2f} puntos."
            ),
            figura="G28",
            accion=(
                "Mantener dur_q y sus derivados en la fase 4, controlando la "
                "colinealidad con dur_total y span_q."
            ),
            tarea_crispdm="Data Understanding · explorar relaciones",
        )
        stability = self.results.pca_stability
        con = stability.loc[stability["version"].str.startswith("A")]
        comp_min = int(con["componentes_80"].min())
        comp_max = int(con["componentes_80"].max())
        comp_text = str(comp_min) if comp_min == comp_max else f"{comp_min}–{comp_max}"
        self.decisions.add(
            hallazgo="El diagnóstico PCA es estable entre muestras",
            evidencia=(
                f"PC1 explica entre {con['pc1_pct'].min():.2f}% y {con['pc1_pct'].max():.2f}% "
                f"y se necesitan {comp_text} componentes para el 80% en la versión con outliers."
            ),
            figura="G23",
            accion=(
                "No repetir el PCA en el EDA; reutilizar el diagnóstico de 4.0/4.1 como "
                "evidencia de estabilidad."
            ),
            tarea_crispdm="Data Understanding · verificar calidad",
        )
        thresholds = self.results.thresholds
        self.decisions.add(
            hallazgo="El segmento de trayectoria requiere umbrales observados",
            evidencia=(
                f"Q75 de autolazo = {thresholds['self_loop_q75']:.4f}, "
                f"Q75 de exploración = {thresholds['exploration_q75']:.4f}, "
                f"Q75 de retorno no adyacente = {thresholds['nonadjacent_q75']:.4f} "
                f"sobre {_fmt_int(thresholds['n_persons'])} personas con al menos dos empleos."
            ),
            figura="Tabla de segmentos",
            accion=(
                "Usar el segmento solo para describir perfiles; no compararlo con el "
                "target porque comparte la definición de retorno."
            ),
            tarea_crispdm="Data Understanding · explorar",
        )
        return self.decisions.to_frame()

    def validate(self) -> "EDAPipeline":
        """Check input hashes, figure manifest and train-only target usage."""
        self.results.input_integrity = self.hasher.verify(self._fingerprints)
        self.results.figure_manifest = self.manifest.check(
            self.config.figures_dir, self.config.figure_files
        )
        self.manifest.assert_complete(self.results.figure_manifest)
        self.results.target_usage = self.usage_validator.check(self.guard)
        self.usage_validator.assert_train_only(self.guard)
        return self
