"""C14 loop health: per-tick metrics row + alerts.  Every alert says what to look at.

  page   (wakes someone): ingest stalled; approved proposal not applied; credits < 15% of budget
  ticket (can wait until morning): repeated simulator errors; rejection streak
Read it without logs:   python -m controller.health --db controller.db
"""
import sys
import time


def record(store, sim, st, events, chunks, ingest_s, t0):
    open_props = store.db.execute(
        "SELECT COUNT(*) FROM proposals WHERE status IN ('submitting','pending','approved')").fetchone()[0]
    store.db.execute("INSERT OR REPLACE INTO metrics VALUES(?,?,?,?,?,?,?,?)",
                     (st["ts"], time.time() - t0, events, chunks, ingest_s, st.get("credits_remaining"),
                      sim.errors, open_props))


def _alert(store, ts, kind, level, msg):
    key = f"alert_{kind}"
    if store.get_meta(key) == msg:  # dedupe: same condition, same text
        return
    store.set_meta(key, msg)
    store.audit(ts, "-", "ALERT", {"level": level, "kind": kind, "msg": msg})
    print(f"ALERT[{level}] {kind}: {msg}", file=sys.stderr)


def check(store, sim, st, new_chunks, budget):
    ts = st["ts"]
    # stalled = chunks listed by the sim but not ingested after catch-up, or the sim clock not moving between ticks
    lag = len(sim.chunks(kind="events", after=store.get_meta("last_chunk", -1)))
    frozen = store.get_meta("last_minute") == st.get("sim_minute") and not st.get("finished")
    store.set_meta("last_minute", st.get("sim_minute"))
    stalls = (store.get_meta("stall", 0) + 1) if (lag > 0 or frozen) else 0
    store.set_meta("stall", stalls)
    if stalls >= 3:
        _alert(store, ts, "ingest_stalled", "page",
               f"{lag} chunks un-ingested / sim clock frozen={frozen} for {stalls} ticks: check sim health, controller "
               f"errors and the chunk cursor (meta.last_chunk) vs GET /events/chunks")
    cr = st.get("credits_remaining")
    if cr is not None and budget and cr < 0.15 * budget:
        _alert(store, ts, "credits_low", "page",
               f"credits {cr:.0f} < 15% of {budget:.0f}: stop non-incident spend; look at audit action=validation_run")
    stuck = store.db.execute("SELECT proposal_id, approval_id FROM proposals WHERE status='approved'").fetchall()
    if stuck:
        _alert(store, ts, "approved_not_applied", "page",
               f"approved but not applied: {stuck[:3]}; apply window may lapse: check audit action=apply http code")
    if sim.errors >= 5:
        _alert(store, ts, "sim_errors", "ticket", f"{sim.errors} simulator transport/5xx errors so far (retried)")
    last = store.db.execute("SELECT status FROM proposals WHERE status IN ('applied','rejected','expired','lapsed') "
                            "ORDER BY updated_ts DESC LIMIT 4").fetchall()
    if len(last) == 4 and all(r[0] != "applied" for r in last):
        _alert(store, ts, "rejection_streak", "ticket",
               "last 4 proposals not applied: read approver reasons in audit (action=rejected/expired)")


if __name__ == "__main__":
    import argparse

    from .store import Store
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="controller.db")
    d = Store(ap.parse_args().db).db
    for r in d.execute("SELECT sim_ts,wall,events,chunks,ingest_s,credits,sim_errors,open_props FROM metrics "
                       "ORDER BY sim_ts DESC LIMIT 5"):
        print("sim", r[0][:16], f"wall={r[1]:.0f}s events/tick={r[2]} ingest={r[4]:.1f}s credits={r[5]} "
                                f"errors={r[6]} open={r[7]}")
    for r in d.execute("SELECT sim_ts,detail FROM audit WHERE action='ALERT' ORDER BY id DESC LIMIT 10"):
        print("ALERT", r[0][:16], r[1])
