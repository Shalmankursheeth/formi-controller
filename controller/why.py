"""C12: "why did workflow X change, who approved it, what happened next?"

    python -m controller.why --db controller.db nw_renewal [--since 2027-01-05]
Prints the audit trail for the workflow in order: detection evidence, proposal, approver decision, apply, and the
config changes the simulator reported (including supervisor edits).
"""
import argparse
import json
import sqlite3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow")
    ap.add_argument("--db", default="controller.db")
    ap.add_argument("--since", default="")
    a = ap.parse_args()
    d = sqlite3.connect(a.db)
    for ts, act, pid, aid, det in d.execute(
            "SELECT sim_ts,action,proposal_id,approval_id,detail FROM audit WHERE workflow_id=? AND sim_ts>=? ORDER BY id",
            (a.workflow, a.since)):
        det = json.loads(det)
        short = det.get("summary") or det.get("reasons") or det.get("evidence") or det.get("resp") or det
        print(f"{ts[:16]}  {act:<22} prop={pid or '-'} appr={aid or '-'}\n    {json.dumps(short)[:300]}")


if __name__ == "__main__":
    main()
