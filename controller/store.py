"""Durable state: SQLite (WAL). One file, survives kill -9.

Tables
  meta        key/value (event cursor, last advance ts)
  cohort_stats  aggregated counts per (workflow, config_version, cohort, variant dims, hour bucket)
  proposals   our own proposal lifecycle (idempotency key = proposal_id, derived deterministically)
  audit       append-only "why did X change" log
Ingestion is idempotent: the chunk cursor and the stats update commit in ONE transaction.
"""
import json
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS seg_stats(
  workflow_id TEXT, seg TEXT, dim TEXT, option TEXT, version INTEGER, day TEXT,
  dials INTEGER DEFAULT 0, connected INTEGER DEFAULT 0, engaged INTEGER DEFAULT 0,
  halluc INTEGER DEFAULT 0,
  PRIMARY KEY(workflow_id, seg, dim, option, version, day));
CREATE TABLE IF NOT EXISTS hourly(
  workflow_id TEXT, hour TEXT, kind TEXT, key TEXT,
  dials INTEGER DEFAULT 0, connected INTEGER DEFAULT 0, halluc INTEGER DEFAULT 0,
  PRIMARY KEY(workflow_id, hour, kind, key));
CREATE TABLE IF NOT EXISTS leads(
  lead_id TEXT PRIMARY KEY, workflow_id TEXT, person_id TEXT, day TEXT, features TEXT);
CREATE TABLE IF NOT EXISTS proposals(
  proposal_id TEXT PRIMARY KEY, workflow_id TEXT, approval_id TEXT, base_version INTEGER,
  status TEXT, kind TEXT, body TEXT, created_ts TEXT, updated_ts TEXT);
CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY AUTOINCREMENT, sim_ts TEXT, wall REAL, workflow_id TEXT,
  action TEXT, proposal_id TEXT, approval_id TEXT, detail TEXT);
CREATE INDEX IF NOT EXISTS audit_wf ON audit(workflow_id, id);
"""


class Store:
    def __init__(self, path="controller.db"):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript(SCHEMA)

    def get_meta(self, k, default=None):
        row = self.db.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, k, v):
        self.db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, json.dumps(v)))

    def audit(self, sim_ts, workflow_id, action, detail, proposal_id=None, approval_id=None):
        self.db.execute(
            "INSERT INTO audit(sim_ts,wall,workflow_id,action,proposal_id,approval_id,detail) VALUES(?,?,?,?,?,?,?)",
            (sim_ts, time.time(), workflow_id, action, proposal_id, approval_id, json.dumps(detail)))

    def why(self, workflow_id):
        """C12: everything that happened to a workflow, in order."""
        cur = self.db.execute(
            "SELECT sim_ts,action,proposal_id,approval_id,detail FROM audit WHERE workflow_id=? ORDER BY id",
            (workflow_id,))
        return [dict(zip(("sim_ts", "action", "proposal_id", "approval_id", "detail"), r)) for r in cur]
