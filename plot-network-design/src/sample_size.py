"""
sample_size.py

Sample size, precision, and power arithmetic for the TRPA forest health plot
network. Every number in the sample-size literature review is produced by a
function in this module, so the document and the code cannot drift apart.

The estimand for VP9 and VP10 is a proportion of forested area whose structure
falls inside an adopted range. That makes the plot-level response a binary
indicator, and the relevant statistics are those for a proportion.

Functions
---------
ci_halfwidth(n, p, conf)            half-width of a two-sided CI on a proportion
n_for_halfwidth(p, d, conf)         plots needed for a given half-width
n_one_sided(p0, p1, alpha, power)   plots needed to reject p <= p0 when truth is p1
detectable_margin(n, p0, ...)       smallest p1 - p0 a sample of n can detect
model_assisted_n(n, r2)             plots needed after model-assisted variance reduction
kish_deff(weights)                  Kish design effect from a weight vector
split_deff(f, k)                    design effect for a two-part sample with weight ratio k
n_change(p1, p2, rho, ...)          plots needed to detect a change, paired or independent
allocate_by_share(n, shares)        integer split of n across strata by share
planning_tables()                   prints the tables used in the literature review

References
----------
Cochran 1977 (proportions); Särndal, Swensson & Wretman 1992 and Brus 2022
(model-assisted variance ratio 1 - R^2); Kish 1965, 1992 (design effect);
Scott 1998 (change with permanent plots); McRoberts, Liknes & Domke 2014
(empirical relative efficiency for an area proportion, 1.5 to 3.1).
"""

from __future__ import annotations

import math
from typing import Dict, Iterable

try:
    from scipy.stats import norm
    _z = norm.ppf
except ImportError:  # pragma: no cover
    def _z(q: float) -> float:
        """Inverse normal CDF, Acklam's rational approximation, adequate here."""
        a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
             1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
        b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
             6.680131188771972e+01, -1.328068155288572e+01]
        c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
             -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
        d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
             3.754408661907416e+00]
        pl, ph = 0.02425, 1 - 0.02425
        if q < pl:
            t = math.sqrt(-2 * math.log(q))
            return (((((c[0]*t+c[1])*t+c[2])*t+c[3])*t+c[4])*t+c[5]) / ((((d[0]*t+d[1])*t+d[2])*t+d[3])*t+1)
        if q > ph:
            t = math.sqrt(-2 * math.log(1 - q))
            return -(((((c[0]*t+c[1])*t+c[2])*t+c[3])*t+c[4])*t+c[5]) / ((((d[0]*t+d[1])*t+d[2])*t+d[3])*t+1)
        t = q - 0.5
        r = t * t
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*t / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


# ---------------------------------------------------------------------------
# Status precision
# ---------------------------------------------------------------------------

def ci_halfwidth(n: int, p: float = 0.5, conf: float = 0.95) -> float:
    """Half-width, in proportion units, of a two-sided CI on a proportion.

    Finite population correction is omitted: the population is area, not
    plots, and the sampling fraction is effectively zero.
    """
    z = _z(1 - (1 - conf) / 2)
    return z * math.sqrt(p * (1 - p) / n)


def n_for_halfwidth(p: float, d: float, conf: float = 0.95) -> int:
    """Plots needed so that the two-sided CI half-width is d (proportion units)."""
    z = _z(1 - (1 - conf) / 2)
    return math.ceil(z * z * p * (1 - p) / (d * d))


# ---------------------------------------------------------------------------
# One-sided threshold test, which is what a standard written as
# "at least X percent shall ..." actually poses
# ---------------------------------------------------------------------------

def n_one_sided(p0: float, p1: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """Plots needed to reject H0: p <= p0 with the stated power when truth is p1 > p0."""
    if p1 <= p0:
        raise ValueError("p1 must exceed p0 for a one-sided test of attainment")
    za, zb = _z(1 - alpha), _z(power)
    num = (za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) ** 2
    return math.ceil(num / (p1 - p0) ** 2)


def detectable_margin(n: int, p0: float, alpha: float = 0.05, power: float = 0.80,
                      tol: float = 1e-5) -> float:
    """Smallest margin (p1 - p0) that n plots can detect at the stated alpha and power.

    Solved by bisection on n_one_sided.
    """
    lo, hi = 1e-4, 1 - p0 - 1e-4
    for _ in range(200):
        mid = (lo + hi) / 2
        if n_one_sided(p0, p0 + mid, alpha, power) > n:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return hi


# ---------------------------------------------------------------------------
# Model-assisted estimation
# ---------------------------------------------------------------------------

def model_assisted_n(n_srs: int, r2: float) -> int:
    """Plots needed for the same precision as n_srs, with a model-assisted
    estimator whose prediction correlates with the response at R^2 = r2.

    Var(regression estimator) / Var(SRS estimator) = 1 - R^2 asymptotically
    (Särndal, Swensson & Wretman 1992; Brus 2022 ch. 10). Note that for a
    binary in-range indicator the relevant R^2 is the squared correlation of
    the indicator with its predicted probability, which is much lower than the
    R^2 of the underlying continuous structure model.
    """
    if not 0 <= r2 < 1:
        raise ValueError("r2 must be in [0, 1)")
    return math.ceil(n_srs * (1 - r2))


def relative_efficiency(r2: float) -> float:
    """RE = 1 / (1 - R^2); n_eff = n * RE."""
    return 1 / (1 - r2)


# ---------------------------------------------------------------------------
# Design effect from unequal weights
# ---------------------------------------------------------------------------

def kish_deff(weights: Iterable[float]) -> float:
    """Kish (1965, 1992) design effect from unequal weighting, n * sum(w^2) / sum(w)^2.

    A bound that treats the weights as unrelated to the response. When
    oversampling is deliberate and informative, the true loss is smaller.
    """
    w = list(weights)
    n = len(w)
    return n * sum(x * x for x in w) / sum(w) ** 2


def split_deff(f: float, k: float) -> float:
    """Design effect for a sample where fraction f carries weight 1 and the
    remainder carries weight k (k = ratio of weights, e.g. 2 means the second
    part was selected at half the inclusion probability of the first).
    """
    return (f + (1 - f) * k * k) / (f + (1 - f) * k) ** 2


def effective_n(n: int, deff: float) -> float:
    return n / deff


# ---------------------------------------------------------------------------
# Change between two measurement occasions
# ---------------------------------------------------------------------------

def n_change(p1: float, p2: float, rho: float = 0.0, alpha: float = 0.05,
             power: float = 0.80, two_sided: bool = True) -> int:
    """Plots per occasion needed to detect a change from p1 to p2.

    rho is the correlation between occasions on the same plots. rho = 0 is two
    independent samples. With permanent plots, Var(p2 - p1) is reduced by
    approximately (1 - rho) when p1 and p2 are similar (Scott 1998). For a
    proportion the exact paired analysis is McNemar's test and the governing
    quantity is the discordant fraction; this function uses the (1 - rho)
    approximation and the document says so.
    """
    if p1 == p2:
        raise ValueError("p1 and p2 must differ")
    za = _z(1 - alpha / 2) if two_sided else _z(1 - alpha)
    zb = _z(power)
    pbar = (p1 + p2) / 2
    v_null = 2 * pbar * (1 - pbar)
    v_alt = p1 * (1 - p1) + p2 * (1 - p2)
    n_indep = (za * math.sqrt(v_null) + zb * math.sqrt(v_alt)) ** 2 / (p2 - p1) ** 2
    return math.ceil(n_indep * (1 - rho))


# ---------------------------------------------------------------------------
# Allocation helpers
# ---------------------------------------------------------------------------

def allocate_by_share(n: int, shares: Dict[str, float]) -> Dict[str, int]:
    """Largest-remainder integer allocation of n across keys by share."""
    total = sum(shares.values())
    raw = {k: n * v / total for k, v in shares.items()}
    base = {k: int(math.floor(v)) for k, v in raw.items()}
    short = n - sum(base.values())
    for k, _ in sorted(raw.items(), key=lambda kv: kv[1] - math.floor(kv[1]), reverse=True)[:short]:
        base[k] += 1
    return base


# ---------------------------------------------------------------------------
# Planning tables
# ---------------------------------------------------------------------------

def planning_tables(area_shares: Dict[str, float] | None = None) -> str:
    """Return the planning tables as markdown. Used to build the literature review."""
    area_shares = area_shares or {"SMC": 60276, "JP": 28783, "RF": 22365}  # acres, threshold repo
    out = []

    out.append("### Table A. Two-sided 95 percent CI half-width by n\n")
    out.append("| n | p = 0.50 (VP10) | p = 0.75 (VP9) |")
    out.append("|---|---|---|")
    for n in (60, 100, 150, 200, 300, 400, 600):
        out.append(f"| {n} | ±{100*ci_halfwidth(n, 0.5):.1f} pts | ±{100*ci_halfwidth(n, 0.75):.1f} pts |")

    out.append("\n### Table B. One-sided attainment test, plots needed (alpha 0.05, power 0.80)\n")
    out.append("| Standard p0 | True p1 | Margin | n (design-based) | n at RE 1.5 | n at RE 2.0 |")
    out.append("|---|---|---|---|---|---|")
    for p0, p1 in ((0.50, 0.55), (0.50, 0.60), (0.50, 0.65), (0.75, 0.80), (0.75, 0.85), (0.75, 0.90)):
        n = n_one_sided(p0, p1)
        out.append(f"| {p0:.2f} | {p1:.2f} | {100*(p1-p0):.0f} pts | {n} | {math.ceil(n/1.5)} | {math.ceil(n/2.0)} |")

    out.append("\n### Table C. Smallest margin above the standard that n plots can detect (alpha 0.05, power 0.80)\n")
    out.append("| n | VP10 (p0 = 0.50) | VP9 (p0 = 0.75) |")
    out.append("|---|---|---|")
    for n in (100, 150, 200, 250, 300, 400):
        out.append(f"| {n} | +{100*detectable_margin(n, 0.5):.1f} pts | +{100*detectable_margin(n, 0.75):.1f} pts |")

    out.append("\n### Table D. Per forest type at n = 300, area-proportional allocation\n")
    alloc = allocate_by_share(300, area_shares)
    out.append("| Forest type | Area share | Plots | 95 percent half-width at p = 0.5 | Detectable margin, one-sided |")
    out.append("|---|---|---|---|---|")
    tot = sum(area_shares.values())
    for k in ("SMC", "JP", "RF"):
        n = alloc[k]
        out.append(f"| {k} | {100*area_shares[k]/tot:.0f} percent | {n} | ±{100*ci_halfwidth(n, 0.5):.1f} pts | +{100*detectable_margin(n, 0.5):.1f} pts |")

    out.append("\n### Table E. Design effect of the split sample\n")
    out.append("Half the sample at equal probability, half at a weight ratio of k. Kish bound.\n")
    out.append("| Weight ratio k | deff | Effective n from 300 | Half-width at p = 0.5 |")
    out.append("|---|---|---|---|")
    for k in (1.0, 1.5, 2.0, 3.0, 5.0):
        d = split_deff(0.5, k)
        ne = 300 / d
        out.append(f"| {k:.1f} | {d:.3f} | {ne:.0f} | ±{100*ci_halfwidth(int(ne), 0.5):.1f} pts |")

    out.append("\n### Table F. Detecting a 10 point change in VP10 between two cycles (two-sided alpha 0.05, power 0.80)\n")
    out.append("| Plot correlation between occasions | Plots per occasion |")
    out.append("|---|---|")
    for rho in (0.0, 0.5, 0.7, 0.8, 0.9):
        label = "0.0 (independent samples)" if rho == 0 else f"{rho:.1f} (permanent plots)"
        out.append(f"| {label} | {n_change(0.50, 0.60, rho)} |")

    return "\n".join(out)


if __name__ == "__main__":
    print(planning_tables())
