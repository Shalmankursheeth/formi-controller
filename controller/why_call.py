"""Compliance question: "why did this customer hear this variant on this day?" (answer < 24h, down to the variant
and the reason it was live).

    python -m controller.why_call --db controller.db --lead nw_renewal:l00012345
    python -m controller.why_call --db controller.db --person nw_renewal:p0004567 [--day 2027-01-06]

For each connected call: the variant, the config version and cohort it was dialled under, and the audit entries
(proposal id, approver decision, rationale/evidence, or supervisor edit) that put that config version live.
"""
import argparse
import json
import sqlite3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="controller.db")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--lead")
    g.add_argument("--person")
    ap.add_argument("--day", default="")
    a = ap.parse_args()
    d = sqlite3.connect(a.db)
    col, val = ("lead_id", a.lead) if a.lead else ("person_id", a.person)
    rows = d.execute(f"SELECT workflow_id,ts,lead_id,config_version,cohort_id,welcome,voice,caller_id,prompt,engaged "
                     f"FROM call_log WHERE {col}=? AND ts>=? ORDER BY ts", (val, a.day)).fetchall()
    if not rows:
        print("no connected calls recorded")
    for wf, ts, lead, ver, cohort, w, v, c, p, e in rows:
        print(f"{ts[:16]} {wf} lead={lead} cfg_v{ver} cohort={cohort}: welcome={w} voice={v} caller_id={c} prompt={p} "
              f"engaged={bool(e)}")
        for sim_ts, act, pid, aid, det in d.execute(
                "SELECT sim_ts,action,proposal_id,approval_id,detail FROM audit WHERE workflow_id=? AND action IN "
                "('config_changed','supervisor_edit_seen') AND detail LIKE ? ORDER BY id", (wf, f'%"version": {ver},%')):
            dd = json.loads(det)
            print(f"    live because: v{ver} by {dd.get('actor','supervisor')} at {sim_ts[:16]} "
                  f"proposal={pid or '-'} approval={aid or '-'}")
            if pid:
                for _, a2, _, _, d2 in d.execute("SELECT sim_ts,action,proposal_id,approval_id,detail FROM audit "
                                                 "WHERE proposal_id=? AND action IN ('propose','auto_apply','auto_apply_caller_id') "
                                                 "ORDER BY id", (pid,)):
                    d2 = json.loads(d2)
                    print(f"      rationale: {d2.get('summary') or d2.get('evidence') or d2.get('rationale')}")


if __name__ == "__main__":
    main()
