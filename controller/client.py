"""Thin HTTP wrapper around the simulator. The ONLY way the controller learns about the world.

Resilience: transport errors and 5xx are retried with exponential backoff (GETs and idempotent PUT/POST keyed by
proposal_id).  /sim/advance is NOT idempotent, so after an ambiguous failure we re-read the sim clock and only
treat the advance as done if the clock moved; ingestion catches up on chunks from the cursor anyway.
"""
import time

import httpx

RETRIES = 6


class Sim:
    def __init__(self, url: str):
        self.c = httpx.Client(base_url=url, timeout=120)
        self.errors = 0  # surfaced by metrics

    def _req(self, method, path, retry_post=True, **kw):
        delay = 0.5
        for attempt in range(RETRIES):
            try:
                r = self.c.request(method, path, **kw)
                if r.status_code >= 500 and attempt < RETRIES - 1 and (method == "GET" or retry_post):
                    raise httpx.TransportError(f"{r.status_code}")
                return r
            except httpx.TransportError:
                self.errors += 1
                if attempt == RETRIES - 1:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 15)

    def get(self, path, **params):
        r = self._req("GET", path, params=params or None)
        r.raise_for_status()
        return r.json()

    def post(self, path, body=None, retry_post=True):
        """Returns (status_code, json). Does not raise: 409/402/403 are meaningful outcomes."""
        r = self._req("POST", path, retry_post=retry_post, json=body)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"raw": r.text}

    def put(self, path, body):
        r = self._req("PUT", path, json=body)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"raw": r.text}

    def state(self):
        return self.get("/sim/state")

    def workflows(self):
        return self.get("/workflows")

    def workflow(self, wid):
        return self.get(f"/workflows/{wid}")

    def config(self, wid):
        return self.get(f"/workflows/{wid}/config")

    def advance(self, minutes=60):
        before = self.state()["sim_minute"]
        try:
            return self.post("/sim/advance", {"minutes": minutes}, retry_post=False)
        except httpx.TransportError:
            # ambiguous: did the sim move?  re-read the clock instead of blindly advancing again
            now = self.state()
            if now["sim_minute"] > before or now.get("finished"):
                return 200, {"new_chunks": [], "recovered": True, **now}
            raise

    def chunks(self, kind="events", after=-1):
        return self.get("/events/chunks", kind=kind, after=after)

    def chunk_lines(self, n):
        r = self._req("GET", f"/events/chunks/{n}")
        r.raise_for_status()
        return r.text.splitlines()
