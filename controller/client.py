"""Thin HTTP wrapper around the simulator. The ONLY way the controller learns about the world."""
import httpx


class Sim:
    def __init__(self, url: str):
        self.c = httpx.Client(base_url=url, timeout=120)

    def get(self, path, **params):
        r = self.c.get(path, params=params or None)
        r.raise_for_status()
        return r.json()

    def post(self, path, body=None):
        """Returns (status_code, json). Does not raise: 409/402/403 are meaningful outcomes."""
        r = self.c.post(path, json=body)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"raw": r.text}

    def put(self, path, body):
        r = self.c.put(path, json=body)
        return r.status_code, r.json()

    def state(self):
        return self.get("/sim/state")

    def workflows(self):
        return self.get("/workflows")

    def workflow(self, wid):
        return self.get(f"/workflows/{wid}")

    def config(self, wid):
        return self.get(f"/workflows/{wid}/config")

    def advance(self, minutes=60):
        return self.post("/sim/advance", {"minutes": minutes})

    def chunks(self, kind="events", after=-1):
        return self.get("/events/chunks", kind=kind, after=after)

    def chunk_lines(self, n):
        r = self.c.get(f"/events/chunks/{n}")
        r.raise_for_status()
        return r.text.splitlines()
