"""Fast-path checks run EVERY tick (not just the daily slot): C5 caller-ID health and C8 hallucination response.

Both use *concurrent* comparisons / pre-spike baselines on the hourly table, never single calls.

C5  A caller ID whose pickup in the last 6h is significantly (z<-3.5, n>=150) below the pooled other IDs is
    stepped down. Where the workflow policy permits auto-apply for caller_id we step down by <= max_shift
    (total-variation) per step, so a 50% share retires in a few hourly steps, each one inside the policy.
    Otherwise it goes through /approvals (batched into the normal pacing).
C8  Hallucination flag rate of the live prompt over the last 6h (n>=150 connected) vs. the rate of the
    previous days. If it is >2.5x the baseline AND >1.5% AND z>3: find the last prompt that ran before, validate
    it (costs credits, paid only when an incident is real), and propose reverting with the validation evidence.
    The LLM is NOT consulted: reverting to a known prompt is cheaper and safer than a freshly generated one.
"""
import copy
import json
import math
from datetime import datetime, timedelta

from . import governance

WINDOW_H = 6


def _hour(ts, back):
    return (datetime.fromisoformat(ts) - timedelta(hours=back)).strftime("%Y-%m-%dT%H")


def _rows(store, wid, kind, since, until=None):
    q = "SELECT key, SUM(dials), SUM(connected), SUM(halluc) FROM hourly WHERE workflow_id=? AND kind=? AND hour>=?"
    args = [wid, kind, since]
    if until:
        q += " AND hour<?"; args.append(until)
    q += " GROUP BY key"
    return {k: (d or 0, c or 0, h or 0) for k, d, c, h in store.db.execute(q, args)}


def _open_proposal(store, wid):
    return store.db.execute(
        "SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND status IN ('submitting','pending','approved')",
        (wid,)).fetchone()[0]


def _in_approver_hours(wf, ts):
    lo, hi = wf["governance"]["approver_hours"]
    h = datetime.fromisoformat(ts).hour
    return lo <= h < hi - 1


def check_caller_ids(store, sim, ts, wid, wf, cfg_resp):
    cfg = cfg_resp["config"]
    dist = dict(cfg["allocations"].get("default", {}).get("caller_id") or {})
    if len(dist) < 2:
        return
    rows = _rows(store, wid, "did", _hour(ts, WINDOW_H))
    bad = None
    for k in dist:
        d, c, _ = rows.get(k, (0, 0, 0))
        od = sum(rows.get(o, (0, 0, 0))[0] for o in dist if o != k)
        oc = sum(rows.get(o, (0, 0, 0))[1] for o in dist if o != k)
        if d < 150 or od < 150:
            continue
        p1, p0 = c / d, oc / od
        p = (c + oc) / (d + od)
        se = math.sqrt(max(p * (1 - p) * (1 / d + 1 / od), 1e-12))
        z = (p1 - p0) / se
        if z < -3.5 and p1 < p0 * 0.8 and (bad is None or z < bad[1]):
            bad = (k, z, p1, p0, d)
    if not bad:
        return
    k, z, p1, p0, d = bad
    pol = wf["governance"]["auto_apply"]
    auto = pol["enabled"] and "caller_id" in pol["allowed_dims"]
    step = min(dist[k] / sum(dist.values()), pol["max_shift"] * 0.98) if auto else dist[k]
    tot = sum(dist.values())
    new = {o: w / tot for o, w in dist.items()}
    cut = min(new[k], step)
    new[k] -= cut
    rest = [o for o in new if o != k]
    for o in rest:
        new[o] += cut / len(rest)
    new = {o: round(w, 4) for o, w in new.items() if w > 0.0001}
    new_cfg = copy.deepcopy(cfg)
    new_cfg["allocations"]["default"]["caller_id"] = new
    evidence = {"caller_id": k, "pickup_recent": round(p1, 4), "pickup_peers": round(p0, 4), "z": round(z, 2),
                "dials": d, "window_hours": WINDOW_H}
    if auto:
        pid = governance.proposal_id(wid, cfg_resp["version"], new_cfg, ts[:13])
        code, resp = sim.put(f"/workflows/{wid}/config", {
            "proposal_id": pid, "base_version": cfg_resp["version"], "proposed_config": new_cfg,
            "rationale": f"caller ID {k} degraded: pickup {p1:.1%} vs peers {p0:.1%} (z={z:.1f}); step-down"})
        store.db.execute("INSERT OR IGNORE INTO proposals VALUES(?,?,?,?,?,?,?,?,?)",
                         (pid, wid, None, cfg_resp["version"], "applied" if code == 200 else "failed", "auto_did", "{}", ts, ts))
        store.audit(ts, wid, "auto_apply_caller_id", {"http": code, "resp": resp, "evidence": evidence,
                                                      "new_dist": new}, pid)
    elif not _open_proposal(store, wid) and _in_approver_hours(wf, ts):
        governance.propose(
            store, sim, ts, wid, cfg_resp["version"], new_cfg,
            f"Retire degraded caller ID {k} (pickup {p1:.0%} vs {p0:.0%} on other IDs)",
            {"caller_id": {"from": dist, "to": new}}, d,
            {"method": "concurrent comparison, last %dh" % WINDOW_H, **evidence},
            min(1.0, round((p0 - p1) * 3, 3)), "Spam-flag pattern: pickup collapsed on one ID while peers unchanged.",
            kind="caller_id", bucket=13)


def check_hallucination(store, sim, ts, wid, wf, cfg_resp):
    cfg = cfg_resp["config"]
    cur = cfg["prompt_version"]
    now = _rows(store, wid, "prompt", _hour(ts, WINDOW_H)).get(cur)
    if not now or now[1] < 150:
        return
    base_rows = _rows(store, wid, "prompt", _hour(ts, 24 * 4), _hour(ts, WINDOW_H))
    d, c, h = base_rows.get(cur, (0, 0, 0))
    if c < 400:  # no baseline for this prompt: compare against everything that ran before it
        c = sum(v[1] for v in base_rows.values()); h = sum(v[2] for v in base_rows.values())
    if c < 400:
        return
    p0, p1 = h / c, now[2] / now[1]
    p = (h + now[2]) / (c + now[1])
    z = (p1 - p0) / math.sqrt(max(p * (1 - p) * (1 / c + 1 / now[1]), 1e-12))
    if not (p1 > 2.5 * p0 and p1 > 0.015 and z > 3):
        return
    if _open_proposal(store, wid) or not _in_approver_hours(wf, ts):
        return
    # last good prompt = the other prompt that carried the most traffic before the spike (config history has no bodies)
    others = {k: v[1] for k, v in base_rows.items() if k != cur}
    prev = max(others, key=others.get) if others else None
    if prev is None or prev not in wf["options"]["prompt_version"]:
        return
    minpass = wf["governance"].get("min_validation_pass_rate", 0.97)
    code, val = sim.post("/validation/runs", {"workflow_id": wid, "prompt_version": prev, "n": 500})
    store.audit(ts, wid, "validation_run", {"http": code, "resp": val, "prompt": prev})
    if code != 200 or val["pass_rate"] < minpass:
        return  # TODO: fall back to /llm/suggest-fixes
    new_cfg = copy.deepcopy(cfg)
    new_cfg["prompt_version"] = prev
    ev = {"incident": "hallucination_spike", "current_prompt": cur, "flag_rate_recent": round(p1, 4),
          "flag_rate_baseline": round(p0, 4), "z": round(z, 2), "n_recent": now[1]}
    governance.propose(
        store, sim, ts, wid, cfg_resp["version"], new_cfg,
        f"Revert prompt {cur} -> {prev}: hallucination flags {p1:.1%} vs {p0:.1%} before",
        {"prompt_version": {"from": cur, "to": prev}}, now[0],
        {"validation_run_id": val["validation_run_id"], "pass_rate": val["pass_rate"], **ev},
        min(1.0, round(p1 * 10, 3)),
        "Prompt change raised flagged-hallucination rate well above baseline; reverting to the prompt that "
        "previously ran, which passed validation.",
        evidence={"validation_run_id": val["validation_run_id"]}, kind="prompt_revert", bucket=13)


def fast_checks(store, sim, ts, workflows):
    for wid, wf in workflows.items():
        cfg = sim.config(wid)
        check_hallucination(store, sim, ts, wid, wf, cfg)
        check_caller_ids(store, sim, ts, wid, wf, cfg)
