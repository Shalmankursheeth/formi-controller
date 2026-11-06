"""C4: per-person call time, learned from history and validated with a controlled pilot.

What the controller may change is only WHO gets called in which hour (schedule.lead_preferred_hour), never how
many calls or when the business allows calling (README constraint 2).

Method
  1. person_hour holds dials/pickups per (person, hour) from history and live events.
  2. A person's preferred hour = the hour with the best shrunk pickup rate (prior = workflow pickup rate,
     weight 2 dials), needing >=1 pickup there and a shrunk rate >= 1.5x the workflow rate.
  3. Persons hash into 10 buckets.  Pilot: buckets 1-5 get their preferred hour published, the rest (the
     controls) do not, though both groups are tracked from the same eligibility rule.  After enough dials
     we compare pickup of treated vs control with a z-test.
        z > 2.5 and lift >= 3%   -> roll out to buckets 1-9 (bucket 0 stays a permanent hold-out)
        z < -2.5                 -> withdraw everything (disabled for 5 days)
        no verdict after 6 days  -> withdraw (no evidence of benefit, so no change)
     In rollout the same test (buckets 1-9 vs bucket 0) keeps running and withdraws on harm.
  4. The change is one config update: auto-apply if the workflow's policy permits `schedule`, otherwise an
     approval request carrying the pilot evidence.
"""
import copy
import json
import math
from datetime import datetime, timedelta

from . import governance
from .ingest import bucket

PRIOR_W = 2
MIN_RATIO = 1.5
MIN_GROUP_DIALS = 1500
MAX_ENTRIES = 150000
MAX_PILOT_DAYS = 6
Z_GO = 2.5


def _prefs(store, wid, p0):
    out = {}
    rows = store.db.execute("SELECT person_id, hour, dials, connected FROM person_hour WHERE workflow_id=?", (wid,))
    best = {}
    for pid, hr, d, c in rows:
        r = (c + PRIOR_W * p0) / (d + PRIOR_W)
        if c >= 1 and r >= MIN_RATIO * p0 and (pid not in best or r > best[pid][0]):
            best[pid] = (r, hr)
    ranked = sorted(best.items(), key=lambda kv: -kv[1][0])[:MAX_ENTRIES]
    for pid, (_, hr) in ranked:
        out[pid] = hr
    return out


def _grp(store, wid, buckets, since):
    d, c = store.db.execute(
        f"SELECT SUM(dials), SUM(connected) FROM sched_eval WHERE workflow_id=? AND day>=? AND bucket IN "
        f"({','.join(map(str, buckets))})", (wid, since)).fetchone()
    return (d or 0), (c or 0)


def _z(t, c):
    (d1, n1), (d0, n0) = t, c
    if d1 < MIN_GROUP_DIALS or d0 < MIN_GROUP_DIALS:
        return None
    p1, p0 = n1 / d1, n0 / d0
    p = (n1 + n0) / (d1 + d0)
    se = math.sqrt(max(p * (1 - p) * (1 / d1 + 1 / d0), 1e-12))
    return {"z": (p1 - p0) / se, "p_treated": p1, "p_control": p0, "lift": (p1 / p0 - 1) if p0 else 0.0,
            "d_treated": d1, "d_control": d0}


def step(store, sim, ts, wid, wf, cfg_resp, frozen, may_propose):
    """Called once a day per workflow. Returns True if it changed or proposed something."""
    st = store.get_meta(f"sched_{wid}", {"phase": "idle"}) or {"phase": "idle"}
    today = ts[:10]
    cfg = cfg_resp["config"]
    cur = (cfg.get("schedule") or {}).get("lead_preferred_hour") or {}

    def publish(prefs, why, evidence):
        new = copy.deepcopy(cfg)
        new.setdefault("schedule", {})["lead_preferred_hour"] = prefs
        if new == cfg:
            return False
        pol = wf["governance"]["auto_apply"]
        diff = {"schedule.lead_preferred_hour": {"entries": len(prefs), "was": len(cur)}}
        if pol["enabled"] and "schedule" in pol["allowed_dims"]:
            pid = governance.proposal_id(wid, cfg_resp["version"], {"n": len(prefs), "why": why}, today)
            code, resp = sim.put(f"/workflows/{wid}/config", {
                "proposal_id": pid, "base_version": cfg_resp["version"], "proposed_config": new,
                "rationale": why, "evidence": evidence})
            store.db.execute("INSERT OR IGNORE INTO proposals VALUES(?,?,?,?,?,?,?,?,?)",
                             (pid, wid, None, cfg_resp["version"], "applied" if code == 200 else "failed", "auto_sched",
                              "{}", ts, ts))
            store.audit(ts, wid, "auto_apply_schedule", {"http": code, "resp": resp, "summary": why,
                                                         "evidence": evidence, "diff": diff}, pid)
            return code == 200
        if not may_propose:
            return False
        code, _ = governance.propose(
            store, sim, ts, wid, cfg_resp["version"], new, why, diff, len(prefs), evidence,
            min(1.0, round(abs(evidence.get("lift", 0.05)) * 5, 3)), why, kind="schedule")
        return code == 200

    def withdraw(reason, evidence):
        ok = publish({}, reason, evidence)
        if ok or not cur:
            st.update(phase="off", until=(datetime.fromisoformat(ts) + timedelta(days=5)).date().isoformat())
            store.db.execute("DELETE FROM person_pref WHERE workflow_id=?", (wid,))
            store.elig[wid] = {}
            store.set_meta(f"sched_{wid}", st)
        return ok

    if "schedule" in frozen:
        return False
    ph = st["phase"]
    if ph == "off" and today < st.get("until", ""):
        return False
    if ph in ("idle", "off"):
        p0 = store.db.execute("SELECT SUM(connected)*1.0/NULLIF(SUM(dials),0) FROM seg_stats WHERE workflow_id=? AND "
                              "seg='all' AND dim='voice'", (wid,)).fetchone()[0] or 0.25
        prefs = _prefs(store, wid, p0)
        if len(prefs) < 2 * MIN_GROUP_DIALS / 3:  # not enough persons for a measurable pilot
            return False
        store.db.execute("DELETE FROM person_pref WHERE workflow_id=?", (wid,))
        store.db.executemany("INSERT INTO person_pref VALUES(?,?,?)", [(wid, p, h) for p, h in prefs.items()])
        store.elig[wid] = prefs
        treated = {p: h for p, h in prefs.items() if 1 <= bucket(p) <= 5}
        ev = {"phase": "pilot", "eligible": len(prefs), "treated": len(treated), "method": "bucket 1-5 vs controls"}
        if publish(treated, f"Pilot: call {len(treated)} people in the hour they historically answer (half of the "
                            f"{len(prefs)} eligible; the rest are controls)", ev):
            st.update(phase="pilot", start=today)
            store.set_meta(f"sched_{wid}", st)
            return True
        return False
    since = (datetime.fromisoformat(st["start"]) + timedelta(days=1)).date().isoformat() if "start" in st else today
    if ph == "pilot":
        res = _z(_grp(store, wid, [1, 2, 3, 4, 5], since), _grp(store, wid, [0, 6, 7, 8, 9], since))
        age = (datetime.fromisoformat(today) - datetime.fromisoformat(st["start"])).days
        store.audit(ts, wid, "schedule_pilot_check", {"result": res, "age_days": age})
        if res and res["z"] < -Z_GO:
            return withdraw("Withdraw per-person call times: pilot pickup is lower than controls", res)
        if res and res["z"] > Z_GO and res["lift"] >= 0.03:
            prefs = store.elig.get(wid, {})
            roll = {p: h for p, h in prefs.items() if bucket(p) >= 1}
            if publish(roll, f"Roll out per-person call times: pilot pickup {res['p_treated']:.1%} vs "
                             f"{res['p_control']:.1%} controls (+{res['lift']:.0%}, z={res['z']:.1f})", res):
                st.update(phase="rollout", start=today)
                store.set_meta(f"sched_{wid}", st)
                return True
        elif age >= MAX_PILOT_DAYS:
            return withdraw("Withdraw per-person call times: no measurable benefit after the pilot", res or {})
        return False
    if ph == "rollout":
        res = _z(_grp(store, wid, list(range(1, 10)), since), _grp(store, wid, [0], since))
        store.audit(ts, wid, "schedule_rollout_check", {"result": res})
        if res and res["z"] < -Z_GO:
            return withdraw("Withdraw per-person call times: rollout pickup fell below the hold-out", res)
    return False
