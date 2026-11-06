"""C1/C2/C3: backlog-safe, idempotent ingestion into the shared segment table.

Shared cohort object: a *segment* is "all" or "<feature>=<value>" (e.g. "age_band=60+"). Detection, experiments
and the supervisor view all read the same `seg_stats` rows, so "seniors" means one thing everywhere.

Idempotency: the chunk cursor is saved in the SAME transaction as the aggregate increments, so a crash either
applies a chunk fully or not at all.  Chunk numbers are global and increasing; history and events have separate
cursors.
"""
import json
from collections import defaultdict

DIMS = ("welcome_message", "voice", "caller_id")
FEATURES = ("lang", "city_tier", "age_band", "value_band")


def bucket(person_id):
    """Stable 0-9 bucket for holdout/pilot assignment (md5-free: python hash() is salted per process)."""
    return sum(ord(c) * (i + 1) for i, c in enumerate(person_id)) % 10


def segments_of(features):
    yield "all"
    for f in FEATURES:
        v = features.get(f)
        if v is not None:
            yield f"{f}={v}"


class Ingestor:
    def __init__(self, store, sim):
        self.store, self.sim = store, sim
        self.leads = {}  # lead_id -> features (also persisted)
        # eligible persons (have a computed preferred hour): wf -> {person_id: hour}; rebuilt after restart
        store.elig = {}
        for wf, pid, hr in store.db.execute('SELECT workflow_id, person_id, hour FROM person_pref'):
            store.elig.setdefault(wf, {})[pid] = hr
        for lid, feats in store.db.execute("SELECT lead_id, features FROM leads"):
            self.leads[lid] = json.loads(feats)

    def chunk(self, chunk_no, cursor_key, side_events):
        agg = defaultdict(lambda: [0, 0, 0, 0])
        hag = defaultdict(lambda: [0, 0, 0])
        new_leads = []
        calls = []
        ph = defaultdict(lambda: [0, 0])
        se = defaultdict(lambda: [0, 0])
        self.last_events = 0
        for line in self.sim.chunk_lines(chunk_no):
            ev = json.loads(line)
            t = ev["type"]
            self.last_events += 1
            if t == "call":
                feats = self.leads.get(ev["lead_id"])
                if feats is None:
                    continue
                day = ev["ts"][:10]
                conn, eng = int(ev["connected"]), int(ev["engaged"])
                hal = int(bool((ev.get("qa") or {}).get("hallucination_flag")))
                hr = ev["ts"][:13]
                x = ph[(ev["workflow_id"], ev["person_id"], int(ev["ts"][11:13]))]
                x[0] += 1; x[1] += conn
                if ev["person_id"] in self.store.elig.get(ev["workflow_id"], ()):
                    y = se[(ev["workflow_id"], bucket(ev["person_id"]), day)]
                    y[0] += 1; y[1] += conn
                if conn and cursor_key != "hist_chunk":  # C12: what each customer who picked up actually heard
                    v = ev["variant"]
                    calls.append((ev["workflow_id"], ev["ts"], ev["person_id"], ev["lead_id"], ev["config_version"],
                                  ev["cohort_id"], v["welcome_message"], v["voice"], v["caller_id"],
                                  v["prompt_version"], eng))
                for kind, key in (("did", ev["variant"]["caller_id"]), ("prompt", ev["variant"]["prompt_version"])):
                    h = hag[(ev["workflow_id"], hr, kind, key)]
                    h[0] += 1; h[1] += conn; h[2] += hal
                for seg in segments_of(feats):
                    for d in DIMS:
                        a = agg[(ev["workflow_id"], seg, d, ev["variant"][d], ev["config_version"], day)]
                        a[0] += 1
                        a[1] += conn
                        a[2] += eng
                        a[3] += hal
            elif t == "lead":
                self.leads[ev["lead_id"]] = ev["features"]
                new_leads.append((ev["lead_id"], ev["workflow_id"], ev["person_id"], ev["ts"][:10],
                                  json.dumps(ev["features"])))
            elif t in ("config_changed", "approval_decided", "campaign_created"):
                side_events.append(ev)
        db = self.store.db
        db.execute("BEGIN")
        try:
            db.executemany("INSERT OR IGNORE INTO leads VALUES(?,?,?,?,?)", new_leads)
            db.executemany(
                """INSERT INTO seg_stats VALUES(?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(workflow_id,seg,dim,option,version,day) DO UPDATE SET
                   dials=dials+excluded.dials, connected=connected+excluded.connected,
                   engaged=engaged+excluded.engaged, halluc=halluc+excluded.halluc""",
                [(*k, *v) for k, v in agg.items()])
            db.executemany(
                """INSERT INTO hourly VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(workflow_id,hour,kind,key) DO UPDATE SET
                   dials=dials+excluded.dials, connected=connected+excluded.connected, halluc=halluc+excluded.halluc""",
                [(*k, *v) for k, v in hag.items()])
            db.executemany(
                """INSERT INTO person_hour VALUES(?,?,?,?,?) ON CONFLICT(workflow_id,person_id,hour) DO UPDATE SET
                   dials=dials+excluded.dials, connected=connected+excluded.connected""",
                [(*k, *v) for k, v in ph.items()])
            db.executemany(
                """INSERT INTO sched_eval VALUES(?,?,?,?,?) ON CONFLICT(workflow_id,bucket,day) DO UPDATE SET
                   dials=dials+excluded.dials, connected=connected+excluded.connected""",
                [(*k, *v) for k, v in se.items()])
            db.executemany("INSERT INTO call_log VALUES(?,?,?,?,?,?,?,?,?,?,?)", calls)
            self.store.set_meta(cursor_key, chunk_no)
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise
