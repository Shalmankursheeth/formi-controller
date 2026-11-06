"""C9: proposal lifecycle. The ONLY module allowed to change a workflow config.

Rules enforced here (see README section 5):
  * deterministic proposal_id  -> a crash/retry can never double-propose (sim returns 409 duplicate)
  * base_version checked       -> supervisor edits trigger re-proposal, never overwrite
  * apply only what was approved, within apply_by
"""
import hashlib
import json


def proposal_id(workflow_id, base_version, proposed_config, sim_day=""):
    """Deterministic per (workflow, base version, content, sim day): a retry after a crash reuses the id (sim
    answers 409 duplicate), but a re-proposal the next day after a rejection/expiry gets a fresh id."""
    h = hashlib.sha256(json.dumps(proposed_config, sort_keys=True).encode()).hexdigest()[:12]
    return f"{workflow_id}-v{base_version}-{sim_day}-{h}"


def propose(store, sim, sim_ts, workflow_id, base_version, proposed_config, summary, diff,
            affected_leads, dry_run, impact_score, rationale, evidence=None, kind="allocation", bucket=10):
    # bucket=10 -> one id per sim day; incidents pass 13 (per hour) so a rejected fix can be retried within the day
    pid = proposal_id(workflow_id, base_version, proposed_config, sim_ts[:bucket])
    body = {"proposal_id": pid, "workflow_id": workflow_id, "base_version": base_version,
            "proposed_config": proposed_config, "change_summary": summary, "diff": diff,
            "affected_leads": affected_leads, "dry_run": dry_run, "impact_score": impact_score,
            "rationale": rationale}
    if evidence:
        body["evidence"] = evidence
    # record intent BEFORE the call so a crash between the two is reconcilable
    store.db.execute("INSERT OR IGNORE INTO proposals VALUES(?,?,?,?,?,?,?,?,?)",
                     (pid, workflow_id, None, base_version, "submitting", kind, json.dumps(body), sim_ts, sim_ts))
    code, resp = sim.post("/approvals", body)
    if code == 200:
        store.db.execute("UPDATE proposals SET approval_id=?, status='pending', updated_ts=? WHERE proposal_id=?",
                         (resp["approval_id"], sim_ts, pid))
    elif code == 409 and resp.get("error") == "duplicate_proposal_id":
        pass  # crash-retry: reconcile() recovers the approval id
    else:
        store.db.execute("UPDATE proposals SET status='failed', updated_ts=? WHERE proposal_id=?", (sim_ts, pid))
    store.audit(sim_ts, workflow_id, "propose", {"http": code, "resp": resp, "summary": summary,
                                                  "rationale": rationale, "impact": impact_score,
                                                  "affected_leads": affected_leads}, proposal_id=pid,
                approval_id=resp.get("approval_id"))
    return code, resp


def reconcile(store, sim, sim_ts):
    """Poll open proposals; apply approved ones. Safe to call every tick and after a restart."""
    rows = store.db.execute(
        "SELECT proposal_id, workflow_id, approval_id FROM proposals WHERE status IN ('pending','approved')"
    ).fetchall()
    for pid, wid, aid in rows:
        if not aid:
            # crash between POST /approvals and our DB write: find it on the sim by proposal_id (idempotency key)
            found = next((x for x in sim.get("/approvals", workflow_id=wid) if x.get("proposal_id") == pid), None)
            if found:
                store.db.execute("UPDATE proposals SET approval_id=?, status='pending', updated_ts=? WHERE proposal_id=?",
                                 (found["approval_id"], sim_ts, pid))
                store.audit(sim_ts, wid, "recovered_submitting", {"approval_id": found["approval_id"]}, pid,
                            found["approval_id"])
            else:  # never reached the sim: safe to forget; the next decision re-proposes with fresh data
                store.db.execute("UPDATE proposals SET status='failed', updated_ts=? WHERE proposal_id=?", (sim_ts, pid))
            continue
        a = sim.get(f"/approvals/{aid}")
        st = a["status"]
        if st == "approved":
            code, resp = sim.post(f"/workflows/{wid}/apply", {"approval_id": aid})
            new = "applied" if code == 200 else ("lapsed" if code == 410 else "stale" if code == 409 else "approved")
            store.db.execute("UPDATE proposals SET status=?, updated_ts=? WHERE proposal_id=?", (new, sim_ts, pid))
            store.audit(sim_ts, wid, "apply", {"http": code, "resp": resp}, pid, aid)
        elif st in ("rejected", "expired", "lapsed"):
            store.db.execute("UPDATE proposals SET status=?, updated_ts=? WHERE proposal_id=?", (st, sim_ts, pid))
            store.audit(sim_ts, wid, st, {"reasons": a.get("reasons")}, pid, aid)
