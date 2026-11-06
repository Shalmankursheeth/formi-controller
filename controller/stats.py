"""Deterministic statistics. No LLM ever decides what won (constraint 4).

Comparison design: within one (segment, dim, config_version) bucket the simulator samples options independently
and randomly per dial, so arms are concurrent and comparable.  We only compare arms *inside* the same version
bucket and sum the evidence across buckets, which avoids confounding with time or with allocation changes.
"""
import math

KPI = {  # name -> (numerator column, denominator column)
    "pickup_rate": ("connected", "dials"),
    "engagement_rate": ("engaged", "connected"),
}


def arms(store, wf, seg, dim, kpi, since_day):
    """-> {version: {option: (num, den)}} for rows with day >= since_day."""
    ncol, dcol = KPI[kpi]
    out = {}
    q = f"""SELECT version, option, SUM({ncol}), SUM({dcol}) FROM seg_stats
            WHERE workflow_id=? AND seg=? AND dim=? AND day>=? GROUP BY version, option"""
    for ver, opt, n, d in store.db.execute(q, (wf, seg, dim, since_day)):
        out.setdefault(ver, {})[opt] = (n or 0, d or 0)
    return out


def compare(by_version, opt, ref):
    """Pooled concurrent comparison opt vs ref -> dict(n1,d1,n0,d0,p1,p0,lift,z) or None."""
    n1 = d1 = n0 = d0 = 0
    for opts in by_version.values():
        if opt in opts and ref in opts:
            n1 += opts[opt][0]; d1 += opts[opt][1]
            n0 += opts[ref][0]; d0 += opts[ref][1]
    if d1 == 0 or d0 == 0:
        return None
    p1, p0 = n1 / d1, n0 / d0
    p = (n1 + n0) / (d1 + d0)
    se = math.sqrt(max(p * (1 - p) * (1 / d1 + 1 / d0), 1e-12))
    return {"n1": n1, "d1": d1, "n0": n0, "d0": d0, "p1": p1, "p0": p0,
            "lift": (p1 / p0 - 1) if p0 > 0 else 0.0, "diff": p1 - p0, "z": (p1 - p0) / se}


def z_crit(alpha, m):
    """One-sided Bonferroni critical z for m simultaneous tests (conservative, deterministic)."""
    a = alpha / max(m, 1)
    # inverse normal tail via bisection (no scipy dependency)
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if 0.5 * math.erfc(mid / math.sqrt(2)) > a:
            lo = mid
        else:
            hi = mid
    return hi


def totals(by_version, opt):
    d = n = 0
    for opts in by_version.values():
        if opt in opts:
            n += opts[opt][0]; d += opts[opt][1]
    return n, d
