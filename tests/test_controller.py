"""Unit tests for the parts where a bug would hurt a client: statistics, id determinism, idempotent ingest,
frozen supervisor dims.  Run: python -m pytest -q tests/test_controller.py"""
import json
import sqlite3

from controller import governance
from controller.decide import build_config, OWN
from controller.ingest import Ingestor, segments_of
from controller.stats import compare, z_crit
from controller.store import Store


def test_z_crit_grows_with_family_size():
    assert 1.6 < z_crit(0.05, 1) < 1.7
    assert z_crit(0.05, 100) > 3.2


def test_compare_only_uses_concurrent_arms():
    by = {1: {"A": (50, 100)}, 2: {"A": (10, 100), "B": (30, 100)}}  # v1 has no B: must be ignored
    c = compare(by, "B", "A")
    assert (c["d1"], c["d0"]) == (100, 100) and abs(c["lift"] - 2.0) < 1e-9


def test_proposal_id_deterministic_per_day_but_fresh_next_day():
    cfg = {"a": 1}
    assert governance.proposal_id("w", 3, cfg, "2027-01-05") == governance.proposal_id("w", 3, cfg, "2027-01-05")
    assert governance.proposal_id("w", 3, cfg, "2027-01-05") != governance.proposal_id("w", 3, cfg, "2027-01-06")


class FakeSim:
    def __init__(self, lines):
        self.lines = lines

    def chunk_lines(self, n):
        return self.lines


def _call(i):
    return json.dumps({"type": "call", "workflow_id": "w", "lead_id": "l1", "person_id": "p", "cohort_id": "default", "ts": "2027-01-04T10:00:00+05:30",
                       "connected": True, "engaged": i % 2 == 0, "config_version": 1,
                       "variant": {"welcome_message": "W1", "voice": "V1", "caller_id": "D1", "prompt_version": "P1"}})


def test_ingest_is_atomic_and_cursor_advances(tmp_path):
    store = Store(str(tmp_path / "t.db"))
    lead = json.dumps({"type": "lead", "workflow_id": "w", "lead_id": "l1", "person_id": "p", "ts": "2027-01-04T08:00:00+05:30",
                       "features": {"lang": "hi", "age_band": "60+"}})
    ing = Ingestor(store, FakeSim([lead, _call(0), _call(1)]))
    ing.chunk(0, "last_chunk", [])
    assert store.get_meta("last_chunk") == 0
    n, = store.db.execute("SELECT SUM(dials) FROM seg_stats WHERE seg='all' AND dim='voice'").fetchone()
    assert n == 2
    assert {s for s in segments_of({"lang": "hi", "age_band": "60+"})} == {"all", "lang=hi", "age_band=60+"}


def test_frozen_dim_is_not_touched():
    wf = {"workflow_id": "w", "options": {"welcome_message": ["W1", "W2"], "voice": ["V1", "V2"], "caller_id": ["D1"]},
          "objective": {"primary": "engagement_rate", "guardrail": {"pickup_rate_max_drop": 0.02}}}
    store = Store(":memory:")
    cur = {"cohorts": [], "allocations": {"default": {"voice": {"V2": 1}}}, "prompt_version": "P1"}
    store.db.execute("INSERT INTO seg_stats VALUES('w','all','voice','V1',1,'2027-01-04',500,200,100,0)")
    store.db.execute("INSERT INTO seg_stats VALUES('w','all','voice','V2',1,'2027-01-04',50,20,10,0)")
    new = build_config(store, wf, cur, {}, "2027-01-05T12:00:00+05:30", frozen={"voice"})
    assert new["allocations"]["default"]["voice"] == {"V2": 1}  # supervisor's choice preserved
    assert new["prompt_version"] == "P1"
