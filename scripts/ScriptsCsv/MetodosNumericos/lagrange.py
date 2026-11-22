"""First-principles Lagrange Polynomial Interpolation engine.

Implements Lagrange basis polynomials L_i(x), polynomial evaluation P_n(x),
monomial expansion, Kronecker delta & partition-of-unity invariant verification,
Chebyshev node placement, piecewise local Lagrange (P1/P2/P3), monotonic inverse
Lagrange interpolation, and SciPy cross-verification taught in
`interpolacion_lagrange.html`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
from scipy.interpolate import BarycentricInterpolator, lagrange as scipy_lagrange

from .config import DISTINCT_NODE_TOL


@dataclass(frozen=True)
class LagrangeDiagnostics:
    """Verification diagnostics for a Lagrange interpolant."""

    name: str
    degree: int
    n_nodes: int
    x_min: float
    x_max: float
    monomial_coeffs_desc: Optional[Tuple[float, ...]]
    kronecker_max_err: float
    unity_sum_max_err: float
    scipy_max_abs_diff: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def validate_distinct_nodes(xs: Sequence[float] | np.ndarray) -> np.ndarray:
    """Enforce MR-04: interpolation nodes x_i must be finite and strictly distinct."""
    x_arr = np.asarray(xs, dtype=np.float64)
    if x_arr.ndim != 1 or x_arr.size < 2:
        raise ValueError("At least 2 1D interpolation nodes are required.")
    if not np.all(np.isfinite(x_arr)):
        raise ValueError("Interpolation nodes x_i must be finite (no NaN/Inf).")
    sorted_x = np.sort(x_arr)
    min_gap = float(np.min(np.diff(sorted_x)))
    if min_gap < DISTINCT_NODE_TOL:
        raise ValueError(
            f"Interpolation nodes x_i must be strictly distinct (min gap = {min_gap:.3e} < {DISTINCT_NODE_TOL:.1e})."
        )
    return x_arr


def lagrange_basis(
    xs: Sequence[float] | np.ndarray,
    i: int,
    x_eval: Sequence[float] | np.ndarray | float,
) -> np.ndarray:
    """Evaluate the i-th Lagrange basis polynomial L_i(x) = prod_{j!=i} (x - x_j)/(x_i - x_j)."""
    x_nodes = validate_distinct_nodes(xs)
    n = x_nodes.size
    if not (0 <= i < n):
        raise IndexError(f"Basis index i={i} out of bounds for {n} nodes.")

    xq = np.atleast_1d(np.asarray(x_eval, dtype=np.float64))
    basis = np.ones_like(xq, dtype=np.float64)
    xi = x_nodes[i]
    for j in range(n):
        if j != i:
            basis *= (xq - x_nodes[j]) / (xi - x_nodes[j])
    return basis


def lagrange_weights_matrix(
    xs: Sequence[float] | np.ndarray,
    x_eval: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return matrix W of shape (len(x_eval), len(xs)) where W[k, i] = L_i(x_eval[k])."""
    x_nodes = validate_distinct_nodes(xs)
    xq = np.atleast_1d(np.asarray(x_eval, dtype=np.float64))
    weights = np.empty((xq.size, x_nodes.size), dtype=np.float64)
    for i in range(x_nodes.size):
        weights[:, i] = lagrange_basis(x_nodes, i, xq)
    return weights


def lagrange_eval(
    xs: Sequence[float] | np.ndarray,
    ys: Sequence[float] | np.ndarray,
    x_eval: Sequence[float] | np.ndarray | float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate P_n(x) = sum_i y_i L_i(x).

    Returns:
        y_hat: interpolated values of shape (len(x_eval),)
        weights: basis weight matrix L_i(x_eval) of shape (len(x_eval), len(xs))
        is_extrapolation: boolean mask flagging evaluations outside [min(xs), max(xs)] (MR-05)
    """
    x_nodes = validate_distinct_nodes(xs)
    y_nodes = np.asarray(ys, dtype=np.float64)
    if y_nodes.ndim != 1 or y_nodes.shape != x_nodes.shape:
        raise ValueError("xs and ys must be 1D sequences of identical length.")
    if not np.all(np.isfinite(y_nodes)):
        raise ValueError("Node values y_i must be finite.")

    xq = np.atleast_1d(np.asarray(x_eval, dtype=np.float64))
    weights = lagrange_weights_matrix(x_nodes, xq)
    y_hat = weights @ y_nodes
    is_extrap = (xq < float(np.min(x_nodes))) | (xq > float(np.max(x_nodes)))
    return y_hat, weights, is_extrap


def expand_monomial_coefficients(
    xs: Sequence[float] | np.ndarray,
    ys: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Expand P_n(x) into descending standard monomial coefficients [c_n, ..., c_1, c_0].

    Built directly by polynomial multiplication of linear factors (x - x_j) / (x_i - x_j)
    from first principles (reliable for low/moderate degrees n <= 8).
    """
    x_nodes = validate_distinct_nodes(xs)
    y_nodes = np.asarray(ys, dtype=np.float64)
    n = x_nodes.size
    total = np.zeros(n, dtype=np.float64)
    for i in range(n):
        poly = np.array([1.0], dtype=np.float64)
        denom = 1.0
        for j in range(n):
            if j != i:
                poly = np.polymul(poly, np.array([1.0, -x_nodes[j]], dtype=np.float64))
                denom *= x_nodes[i] - x_nodes[j]
        total += (y_nodes[i] / denom) * poly
    return total


def diagnose_lagrange(
    xs: Sequence[float] | np.ndarray,
    ys: Sequence[float] | np.ndarray,
    name: str = "",
) -> LagrangeDiagnostics:
    """Verify Kronecker delta, partition of unity, and SciPy numerical equivalence."""
    x_nodes = validate_distinct_nodes(xs)
    y_nodes = np.asarray(ys, dtype=np.float64)
    n_nodes = int(x_nodes.size)
    degree = n_nodes - 1

    # 1. Kronecker delta L_i(x_j) == delta_ij
    w_nodes = lagrange_weights_matrix(x_nodes, x_nodes)
    kronecker_max_err = float(np.max(np.abs(w_nodes - np.eye(n_nodes))))

    # 2. Partition of unity sum_i L_i(x) == 1 across 51 interior test points
    x_min, x_max = float(np.min(x_nodes)), float(np.max(x_nodes))
    grid = np.linspace(x_min, x_max, 51)
    y_ours, w_grid, _ = lagrange_eval(x_nodes, y_nodes, grid)
    unity_sum_max_err = float(np.max(np.abs(np.sum(w_grid, axis=1) - 1.0)))

    # 3. SciPy cross-check: scipy.interpolate.lagrange for deg <= 8; Barycentric for deg > 8
    if degree <= 8:
        monomial = tuple(float(c) for c in expand_monomial_coefficients(x_nodes, y_nodes))
        ref_poly = scipy_lagrange(x_nodes, y_nodes)
        y_ref = np.asarray(ref_poly(grid), dtype=np.float64)
    else:
        monomial = None
        ref_bary = BarycentricInterpolator(x_nodes, y_nodes)
        y_ref = np.asarray(ref_bary(grid), dtype=np.float64)

    scipy_max_abs_diff = float(np.max(np.abs(y_ours - y_ref)))

    return LagrangeDiagnostics(
        name=name,
        degree=degree,
        n_nodes=n_nodes,
        x_min=x_min,
        x_max=x_max,
        monomial_coeffs_desc=monomial,
        kronecker_max_err=kronecker_max_err,
        unity_sum_max_err=unity_sum_max_err,
        scipy_max_abs_diff=scipy_max_abs_diff,
    )


def chebyshev_nodes(
    a: float,
    b: float,
    degree: int,
    snap_int: bool = False,
    kind: str = "first",
) -> np.ndarray:
    """Generate Chebyshev nodes mapped to [a, b], sorted ascending.

    - kind="first" (roots of T_{n+1}): cos((2k + 1) * pi / (2 * (degree + 1))), strictly interior.
    - kind="lobatto" (Chebyshev-Lobatto / 2nd-kind extrema): cos(k * pi / degree), always includes
      endpoints a and b, eliminating boundary extrapolation at low degrees.
    When snap_int=True (for discrete integer grids like quarters 1..40), rounds to
    nearest integer and deduplicates to preserve MR-04 strict distinctness.
    """
    if b <= a:
        raise ValueError("Interval requires b > a.")
    if degree < 1:
        raise ValueError("Polynomial degree must be >= 1.")

    k = np.arange(degree + 1, dtype=np.float64)
    if kind == "lobatto":
        t = np.cos(k * np.pi / float(degree))
    elif kind == "first":
        t = np.cos((2.0 * k + 1.0) * np.pi / (2.0 * (degree + 1)))
    else:
        raise ValueError(f"Unsupported Chebyshev node kind={kind!r}; expected 'first' or 'lobatto'.")
    nodes = 0.5 * (a + b) + 0.5 * (b - a) * t
    nodes = np.sort(nodes)
    if snap_int:
        nodes = np.unique(np.round(nodes).astype(int)).astype(np.float64)
    return nodes


def piecewise_lagrange_eval(
    xs: Sequence[float] | np.ndarray,
    ys: Sequence[float] | np.ndarray,
    x_eval: Sequence[float] | np.ndarray,
    degree: int = 2,
) -> np.ndarray:
    """Evaluate local low-degree piecewise Lagrange interpolation (P1, P2, or P3).

    For each query point q, selects the (degree + 1) nearest sorted nodes around q
    and evaluates the local Lagrange polynomial, preventing Runge boundary oscillation.
    """
    x_nodes = validate_distinct_nodes(xs)
    y_nodes = np.asarray(ys, dtype=np.float64)
    order = np.argsort(x_nodes)
    x_sorted = x_nodes[order]
    y_sorted = y_nodes[order]

    k_pts = degree + 1
    if x_sorted.size < k_pts:
        raise ValueError(f"Piecewise degree {degree} requires at least {k_pts} nodes.")

    xq = np.atleast_1d(np.asarray(x_eval, dtype=np.float64))
    out = np.empty_like(xq, dtype=np.float64)
    n = x_sorted.size

    for idx, q in enumerate(xq):
        pos = int(np.searchsorted(x_sorted, q))
        left = max(0, pos - (k_pts // 2))
        right = left + k_pts
        if right > n:
            right = n
            left = n - k_pts
        y_loc, _, _ = lagrange_eval(x_sorted[left:right], y_sorted[left:right], [q])
        out[idx] = float(y_loc[0])
    return out


def inverse_lagrange_eval(
    xs: Sequence[float] | np.ndarray,
    ys: Sequence[float] | np.ndarray,
    y_targets: Sequence[float] | np.ndarray,
    local_degree: int | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Inverse Lagrange interpolation solving x(y*) on strictly monotonic data.

    Validates that y_i are strictly distinct and monotonic before swapping axes
    so duplicate plateaus (e.g., PCA V(9) = V(10) = 1.0) raise a clean ValueError.
    """
    x_nodes = validate_distinct_nodes(xs)
    y_nodes = np.asarray(ys, dtype=np.float64)
    if y_nodes.shape != x_nodes.shape:
        raise ValueError("xs and ys must have identical shapes.")

    # Check strict monotonicity + distinctness of y_nodes
    validate_distinct_nodes(y_nodes)
    diffs = np.diff(y_nodes)
    if not (np.all(diffs > 0) or np.all(diffs < 0)):
        raise ValueError("Inverse Lagrange requires strictly monotonic y_i values.")

    yq = np.atleast_1d(np.asarray(y_targets, dtype=np.float64))
    is_extrap = (yq < float(np.min(y_nodes))) | (yq > float(np.max(y_nodes)))

    if local_degree is not None:
        x_hat = piecewise_lagrange_eval(y_nodes, x_nodes, yq, degree=local_degree)
    else:
        x_hat, _, _ = lagrange_eval(y_nodes, x_nodes, yq)
    return x_hat, is_extrap
