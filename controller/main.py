"""Controller loop. Restart-safe: all state is in SQLite; the sim keeps the world.

    python -m controller.main --url http://127.0.0.1:8700 --db controller.db
"""
import argparse
import time
from datetime import datetime, timedelta

from .client import Sim
from .decide import SUP_FREEZE_DAYS, decide
from .governance import reconcile
from .incidents import fast_checks
from .ingest import Ingestor
from .store import Store

TICK_MIN = 60


def note_supervisor_edits(store, side):
    for ev in side:
        if ev["type"] == "config_changed" and ev.get("actor") == "supervisor":
            wid = ev["workflow_id"]
            until = (datetime.fromisoformat(ev["ts"]) + timedelta(days=SUP_FREEZE_DAYS)).date().isoformat()
            m = store.get_meta(f"sup_{wid}", {}) or {}
            for d in ev.get("changed_dims", []):
                m[d] = until
            store.set_meta(f"sup_{wid}", m)
            store.audit(ev["ts"], wid, "supervisor_edit_seen", {"dims": ev.get("changed_dims"), "version": ev["version"],
                                                               "freeze_until": until})
        elif ev["type"] == "config_changed":
            store.audit(ev["ts"], ev["workflow_id"], "config_changed",
                        {k: ev.get(k) for k in ("version", "actor", "changed_dims", "proposal_id", "approval_id")},
                        ev.get("proposal_id"), ev.get("approval_id"))


def catch_up(ing, store, sim, kind, key, side):
    last = store.get_meta(key, -1)
    for ch in sim.chunks(kind=kind, after=last):
        ing.chunk(ch["chunk"], key, side)


def run(url, db):
    sim = Sim(url)
    store = Store(db)
    ing = Ingestor(store, sim)
    wfs = {w["workflow_id"]: sim.workflow(w["workflow_id"]) for w in sim.workflows()}
    t0 = time.time()
    side = []
    catch_up(ing, store, sim, "history", "hist_chunk", side)   # C3: lead universe + baseline rates
    side.clear()
    while True:
        catch_up(ing, store, sim, "events", "last_chunk", side)  # backlog first (post-crash)
        note_supervisor_edits(store, side)
        side.clear()
        st = sim.state()
        reconcile(store, sim, st["ts"])
        if st.get("finished"):
            break
        fast_checks(store, sim, st["ts"], wfs)
        decide(store, sim, st["ts"], wfs)
        code, resp = sim.advance(TICK_MIN)
        if code == 409:
            break
    print(f"done in {time.time()-t0:.1f}s", sim.state())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--db", default="controller.db")
    a = ap.parse_args()
    run(a.url, a.db)
