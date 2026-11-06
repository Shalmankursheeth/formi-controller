"""Detect -> experiment -> propose, once per workflow per day, batched into ONE proposal.

Design (see SUBMISSION.md for reasoning):
  * Explore: default allocation keeps ~25% of traffic spread over non-incumbent options (per dim).
  * Winner per (segment, dim): concurrent-arm z-test, Bonferroni over all tests in the family, min n per arm,
    min relative lift, guardrail KPI must not drop.  Winners become cohorts "ep_<feature>_<value>" (shared object).
  * Winners keep a 15% hold-out of the reference arm, so decay is observable; recent-window check drops decayed ones.
  * Customer-facing dims (welcome_message, voice) ALWAYS go through /approvals. Auto-apply only for caller_id,
    and only when the workflow policy permits it and TV shift <= max_shift.
  * Own pacing: <=2 proposals/day/workflow, never before 11:00, inside approver hours, one open proposal at a time.
"""
import copy
import os
import json
from datetime import datetime, timedelta

from . import call_time, governance
from .ingest import DIMS, FEATURES
from .stats import arms, compare, totals, z_crit

OWN = "ep_"
MIN_DEN = int(os.environ.get('EP_MIN_DEN', 300))          # min observations (denominator) per arm
MIN_LIFT = float(os.environ.get('EP_MIN_LIFT', 0.03))        # min relative lift worth a customer-facing change
ALPHA = 0.05
WINDOW_DAYS = 5
RECENT_DAYS = 2
EXPLORE_SHARE = float(os.environ.get('EP_EXPLORE_SHARE', 0.40))
HOLDOUT = float(os.environ.get('EP_HOLDOUT', 0.15))
SUP_FREEZE_DAYS = 3


def _day(ts, back):
    return (datetime.fromisoformat(ts) - timedelta(days=back)).date().isoformat()


def _kpis(wf):
    obj = wf["objective"]
    primary = obj["primary"]
    other = "engagement_rate" if primary == "pickup_rate" else "pickup_rate"
    g = next(iter(obj.get("guardrail", {}).values()), 0.02)
    return primary, other, g


def _segments(store, wid):
    return [r[0] for r in store.db.execute(
        "SELECT DISTINCT seg FROM seg_stats WHERE workflow_id=?", (wid,))]


def find_winners(store, wf, ts, since):
    """-> (winners, tests). winners: {(seg,dim): dict(opt, ref, lift, z, ...)}"""
    wid = wf["workflow_id"]
    primary, other, gmax = _kpis(wf)
    segs = _segments(store, wid)
    cand = []
    for seg in segs:
        for dim in DIMS:
            by = arms(store, wid, seg, dim, primary, since)
            opts = {o for v in by.values() for o in v}
            if len(opts) < 2:
                continue
            ref = max(opts, key=lambda o: totals(by, o)[1])
            for o in opts - {ref}:
                c = compare(by, o, ref)
                if c and min(c["d1"], c["d0"]) >= MIN_DEN:
                    cand.append((seg, dim, o, ref, c, by))
    m = max(len(cand), 1)
    zc = z_crit(ALPHA, m)
    winners = {}
    for seg, dim, o, ref, c, by in cand:
        if c["z"] < zc or c["lift"] < MIN_LIFT:
            continue
        og = compare(arms(store, wid, seg, dim, other, since), o, ref)
        if og and og["diff"] < -gmax * 0.5:   # guardrail: do not trade the other KPI away
            continue
        key = (seg, dim)
        if key not in winners or c["lift"] > winners[key]["lift"]:
            winners[key] = {"opt": o, "ref": ref, "lift": c["lift"], "z": c["z"], "n": c["d1"], "p1": c["p1"],
                            "p0": c["p0"], "segment": seg, "dim": dim}
    return winners, len(cand), zc


def decayed(store, wf, ts, seg, dim, opt, ref):
    primary, _, _ = _kpis(wf)
    by = arms(store, wf["workflow_id"], seg, dim, primary, _day(ts, RECENT_DAYS))
    c = compare(by, opt, ref)
    return bool(c and min(c["d1"], c["d0"]) >= MIN_DEN // 2 and c["z"] < -2.0)


def tv(a, b):
    ks = set(a) | set(b)
    sa, sb = sum(a.values()) or 1, sum(b.values()) or 1
    return 0.5 * sum(abs(a.get(k, 0) / sa - b.get(k, 0) / sb) for k in ks)


def build_config(store, wf, cur_cfg, winners, ts, frozen):
    wid = wf["workflow_id"]
    cfg = copy.deepcopy(cur_cfg)
    cfg["cohorts"] = [c for c in cfg.get("cohorts", []) if not c["id"].startswith(OWN)]
    allocs = {k: v for k, v in cfg.get("allocations", {}).items() if not k.startswith(OWN)}
    default = allocs.setdefault("default", {})
    options = wf["options"]
    # incumbent per dim = reference arm with most traffic in "all" within the window
    primary, _, _ = _kpis(wf)
    since = _day(ts, WINDOW_DAYS)
    notes = []
    for dim in DIMS:
        if dim in frozen:
            continue
        opts = options[dim]
        if dim == "caller_id":
            # C5 (conservative): never widen onto unseen IDs (they may be spam-flagged); only retire IDs whose
            # recent pickup is significantly worse than a peer already in rotation.
            dist = dict(default.get("caller_id") or {})
            if len(dist) > 1:
                by = arms(store, wid, "all", dim, "pickup_rate", _day(ts, RECENT_DAYS))
                best = max(dist, key=lambda o: (totals(by, o)[0] / totals(by, o)[1]) if totals(by, o)[1] else 0)
                for o in list(dist):
                    c = compare(by, o, best) if o != best else None
                    if c and min(c["d1"], c["d0"]) >= MIN_DEN and c["z"] < -3.0 and len(dist) > 1:
                        dist.pop(o)
                        notes.append(f"retire caller_id {o}")
                s = sum(dist.values())
                default["caller_id"] = {k: round(v / s, 4) for k, v in dist.items()}
            continue
        by = arms(store, wid, "all", dim, primary, since)
        tot = {o: totals(by, o)[1] for o in opts}
        if not any(tot.values()):
            continue
        inc = max(opts, key=lambda o: tot[o])
        w = winners.get(("all", dim))
        base = w["opt"] if w else inc
        others = [o for o in opts if o != base]
        if not others:
            continue
        # keep exploring unexplored/undersampled options; otherwise settle with a small hold-out
        under = [o for o in others if tot[o] < MIN_DEN * 2]
        if w:
            dist = {base: 1 - HOLDOUT, w["ref"]: HOLDOUT}
        elif under:
            dist = {base: 1 - EXPLORE_SHARE}
            for o in others:
                dist[o] = EXPLORE_SHARE / len(others)
        else:
            dist = {base: 0.9}
            for o in others:
                dist[o] = 0.1 / len(others)
        default[dim] = {k: round(v, 4) for k, v in dist.items()}
    ordered = sorted([(k, v) for k, v in winners.items() if k[0] != "all"], key=lambda kv: -kv[1]["lift"] * kv[1]["n"])
    for (seg, dim), w in ordered:
        if dim in frozen or len(cfg["cohorts"]) >= 20:
            continue
        feat, val = seg.split("=", 1)
        cid = f"{OWN}{feat}_{val}"
        if not any(c["id"] == cid for c in cfg["cohorts"]):
            cfg["cohorts"].append({"id": cid, "where": {feat: [val]}})
        allocs.setdefault(cid, {})[dim] = {w["opt"]: 1 - HOLDOUT, w["ref"]: HOLDOUT}
    cfg["allocations"] = allocs
    return cfg


def _dims_changed(a, b):
    ch = set()
    for d in DIMS:
        if json.dumps([a["allocations"].get(k, {}).get(d) for k in sorted(a["allocations"])], sort_keys=True) != \
           json.dumps([b["allocations"].get(k, {}).get(d) for k in sorted(b["allocations"])], sort_keys=True):
            ch.add(d)
    if a.get("cohorts") != b.get("cohorts"):
        ch.add("cohorts")
    return ch


def affected_leads(store, wid, segs, ts):
    since = _day(ts, 3)
    if not segs or "all" in segs:
        return store.db.execute("SELECT COUNT(*) FROM leads WHERE workflow_id=? AND day>=?", (wid, since)).fetchone()[0]
    n = 0
    for seg in segs:
        feat, val = seg.split("=", 1)
        n += sum(1 for (f,) in store.db.execute("SELECT features FROM leads WHERE workflow_id=? AND day>=?", (wid, since))
                 if json.loads(f).get(feat) == val)
        break  # TODO: union across segments; upper-bounded by first for now
    return n


def decide(store, sim, ts, workflows):
    dt = datetime.fromisoformat(ts)
    if dt.minute != 0 or dt.hour != 12:  # one decision slot per day, after standups and inside approver hours
        return
    for wid, wf in workflows.items():
        _decide_wf(store, sim, ts, wid, wf)
        # per-person call time (C4): its own dimension, only when nothing else is in flight for the workflow
        # (an auto-apply would otherwise make an already-pending approval stale)
        if store.db.execute("SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND status IN "
                            "('submitting','pending','approved')", (wid,)).fetchone()[0]:
            continue
        today = ts[:10]
        frozen = {d for d, until in (store.get_meta(f"sup_{wid}", {}) or {}).items() if until > today}
        sent = store.db.execute("SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND created_ts>=? AND "
                                "status!='failed'", (wid, _day(ts, 0))).fetchone()[0]
        call_time.step(store, sim, ts, wid, wf, sim.config(wid), frozen, sent < 2)


def _decide_wf(store, sim, ts, wid, wf):
    gov = wf["governance"]
    open_ = store.db.execute(
        "SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND status IN ('submitting','pending','approved')",
        (wid,)).fetchone()[0]
    if open_:
        return
    today = ts[:10]
    sent = store.db.execute("SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND created_ts>=? AND status!='failed'",
                            (wid, _day(ts, 0))).fetchone()[0]
    sent24 = store.db.execute("SELECT COUNT(*) FROM proposals WHERE workflow_id=? AND created_ts>=? AND status!='failed'",
                              (wid, (datetime.fromisoformat(ts) - timedelta(hours=24)).isoformat())).fetchone()[0]
    if sent >= 2 or sent24 >= gov["max_requests_per_24h"]:
        return
    cur = sim.config(wid)
    version, cur_cfg = cur["version"], cur["config"]
    since = _day(ts, WINDOW_DAYS)
    winners, m, zc = find_winners(store, wf, ts, since)
    # decay / rollback: drop any winner whose recent window turned against it
    dropped = []
    for k, w in list(winners.items()):
        if decayed(store, wf, ts, k[0], k[1], w["opt"], w["ref"]):
            dropped.append(k); winners.pop(k)
    for c in cur_cfg.get("cohorts", []):
        if not c["id"].startswith(OWN):
            continue
        feat, val = next(iter(c["where"].items()))
        seg = f"{feat}={val[0]}"
        for dim, dist in cur_cfg["allocations"].get(c["id"], {}).items():
            live = max(dist, key=dist.get)
            ref = min(dist, key=dist.get)
            if (seg, dim) not in winners and decayed(store, wf, ts, seg, dim, live, ref):
                dropped.append((seg, dim))
    # supervisor edits: freeze the dim for a few days (we never undo them silently)
    frozen = set()
    for dim, until in (store.get_meta(f"sup_{wid}", {}) or {}).items():
        if until > today:
            frozen.add(dim)
    new_cfg = build_config(store, wf, cur_cfg, winners, ts, frozen)
    changed = _dims_changed(cur_cfg, new_cfg)
    if not changed or new_cfg == cur_cfg:
        return
    # cohort-level dims must be considered customer-facing too
    cust = changed & {"welcome_message", "voice", "cohorts"}
    auto_ok = (gov["auto_apply"]["enabled"] and not cust
               and changed <= set(gov["auto_apply"]["allowed_dims"]) and bool(changed))
    if auto_ok:
        a, b = cur_cfg["allocations"], new_cfg["allocations"]
        shift = max(tv(a.get(k, {}).get("caller_id", {}), b.get(k, {}).get("caller_id", {})) for k in set(a) | set(b))
        auto_ok = shift <= gov["auto_apply"]["max_shift"]
    segs = [k[0] for k in winners]
    n_aff = affected_leads(store, wid, segs, ts)
    primary, other, _ = _kpis(wf)
    gains = [w["lift"] for w in winners.values()]
    impact = round(min(1.0, (sum(gains) / max(len(gains), 1)) * 5), 3) if gains else 0.1
    diff = {"changed_dims": sorted(changed), "winners": {f"{k[0]}|{k[1]}": {kk: (round(vv, 4) if isinstance(vv, float) else vv)
            for kk, vv in w.items()} for k, w in winners.items()}, "rolled_back": [list(k) for k in dropped],
            "frozen_dims": sorted(frozen)}
    dry = {"method": "historical concurrent-arm replay", "window_days": WINDOW_DAYS, "tests_in_family": m,
           "z_critical": round(zc, 3), "primary_kpi": primary,
           "per_winner": {f"{k[0]}|{k[1]}": {"observed_rate_option": round(w["p1"], 4),
                                             "observed_rate_reference": round(w["p0"], 4), "n_option": w["n"]}
                          for k, w in winners.items()}}
    summary = (f"{wid}: " + ("; ".join(f"{k[1]} {w['opt']} for {k[0]} (+{w['lift']*100:.0f}% {primary})"
               for k, w in winners.items()) or f"re-balance traffic across variants ({', '.join(sorted(changed))})") +
               (f"; roll back {len(dropped)} decayed" if dropped else ""))
    rationale = (f"Concurrent randomised arms, window {WINDOW_DAYS}d, Bonferroni z>{zc:.2f} over {m} tests, min {MIN_DEN} per arm, "
                 f"min lift {MIN_LIFT:.0%}; guardrail {other} not degraded.")
    if auto_ok:
        pid = governance.proposal_id(wid, version, new_cfg, ts[:10])
        code, resp = sim.put(f"/workflows/{wid}/config", {"proposal_id": pid, "base_version": version,
                             "proposed_config": new_cfg, "rationale": rationale})
        store.db.execute("INSERT OR IGNORE INTO proposals VALUES(?,?,?,?,?,?,?,?,?)",
                         (pid, wid, None, version, "applied" if code == 200 else "rejected", "auto", "{}", ts, ts))
        store.audit(ts, wid, "auto_apply", {"http": code, "resp": resp, "diff": diff, "dry_run": dry}, pid)
        return
    governance.propose(store, sim, ts, wid, version, new_cfg, summary, diff, n_aff, dry, impact, rationale)
