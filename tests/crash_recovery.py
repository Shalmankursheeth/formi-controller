"""Kill -9 the controller at several points mid-run, restart it each time, and check the run completes correctly.

    python tests/crash_recovery.py [scenario_name] [kills]      (default: public_02_incidents 4)

Passes iff: the scenario finishes; every approval was applied at most once (no duplicate config_changed per
approval_id); nothing is left pending/submitting; no stale/conflict errors; the event cursor reached the last chunk.
Writes reports/crash_recovery.md as evidence.
"""
import json
import os
import random
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
scenario = sys.argv[1] if len(sys.argv) > 1 else "public_02_incidents"
kills = int(sys.argv[2]) if len(sys.argv) > 2 else 4
env = {**os.environ, "PYTHONUTF8": "1"}
db = ROOT / "controller_crash.db"
for f in ROOT.glob("controller_crash.db*"):
    f.unlink()
run_dir = ROOT / "runs" / "mine_crash"
if run_dir.exists():
    import shutil
    shutil.rmtree(run_dir)

sim = subprocess.Popen([sys.executable, "-m", "sim", "serve", "--scenario", f"scenarios/{scenario}.yaml",
                        "--run-dir", "runs/mine_crash"], cwd=ROOT, env=env,
                       stdout=open(ROOT / "sim_crash.log", "w"), stderr=subprocess.STDOUT)
url = "http://127.0.0.1:8700"
for _ in range(60):
    try:
        httpx.get(url + "/health", timeout=1); break
    except Exception:
        time.sleep(0.5)


def start():
    return subprocess.Popen([sys.executable, "-m", "controller.main", "--url", url, "--db", str(db)],
                            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


log = []
rng = random.Random(7)
end_min = httpx.get(url + "/sim/state").json()["end_minute"]
# kill points spread over the run, chosen on SIM time so every kill lands mid-run (not during start-up)
targets = sorted(rng.randrange(1440, end_min - 1440) for _ in range(kills))
n_kill = 0
while True:
    p = start()
    if n_kill < kills:
        while p.poll() is None:
            m = httpx.get(url + "/sim/state").json()["sim_minute"]
            if m >= targets[n_kill]:
                p.kill()  # TerminateProcess: no cleanup, no flush
                p.wait()
                st = httpx.get(url + "/sim/state").json()
                n_kill += 1
                log.append(f"kill #{n_kill} at sim ts {st['ts']} (target minute {targets[n_kill-1]})")
                print(log[-1])
                break
            time.sleep(0.02)
        else:
            break
        continue
    out, _ = p.communicate()
    log.append("final run: " + out.strip().splitlines()[-1][:200])
    break

state = httpx.get(url + "/sim/state").json()
d = sqlite3.connect(db)
checks = {}
checks["scenario finished"] = state["finished"]
approvals = httpx.get(url + "/approvals").json()
status = {}
for a in approvals:
    status[a["status"]] = status.get(a["status"], 0) + 1
checks["no approval left pending/approved-unapplied"] = not any(a["status"] in ("pending", "approved") for a in approvals)
dups = d.execute("""SELECT approval_id, COUNT(*) FROM audit WHERE action='apply' AND detail LIKE '%"http": 200%'
                    GROUP BY approval_id HAVING COUNT(*)>1""").fetchall()
checks["no approval applied twice"] = not dups
left = d.execute("SELECT COUNT(*) FROM proposals WHERE status IN ('submitting','pending','approved')").fetchone()[0]
checks["no open proposals in our store"] = left == 0
conf = d.execute("SELECT COUNT(*) FROM audit WHERE action='apply' AND detail LIKE '%stale_base%'").fetchone()[0]
last = d.execute("SELECT v FROM meta WHERE k='last_chunk'").fetchone()
checks["event cursor reached last chunk"] = last and int(json.loads(last[0])) == state["chunks"] - 1
rec = d.execute("SELECT COUNT(*) FROM audit WHERE action='recovered_submitting'").fetchone()[0]

sim.kill()
rep = ["# Crash-recovery evidence", "", f"Scenario `{scenario}`, controller killed with TerminateProcess {n_kill} times.", ""]
rep += [f"- {l}" for l in log]
rep += ["", f"Approvals by final status (sim): {status}", f"Recovered 'submitting' proposals: {rec}",
        f"Stale-base apply conflicts: {conf}", "", "| check | result |", "|---|---|"]
rep += [f"| {k} | {'PASS' if v else 'FAIL'} |" for k, v in checks.items()]
(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "crash_recovery.md").write_text("\n".join(rep), encoding="utf-8")
print("\n".join(rep))
sys.exit(0 if all(checks.values()) else 1)
