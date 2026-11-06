"""C11 supervisor view: ONE static page. What is being tested, what is winning, what we want from you, what
changed today.  Pickup and engagement are shown as separate numbers, never blended.  Rewritten once a day and at
the end of the run (reports/supervisor.html); open it in a browser.
"""
import html
import json
from datetime import datetime, timedelta

from .decide import OWN

CSS = ("body{font:14px system-ui;margin:24px;max-width:980px;color:#222}h1{font-size:20px}h2{font-size:16px;"
       "margin-top:28px;border-bottom:1px solid #ccc}table{border-collapse:collapse}td,th{padding:3px 10px;"
       "border-bottom:1px solid #eee;text-align:left;vertical-align:top}.ask{background:#fff4d6;padding:6px 10px}"
       "small{color:#666}")
SHOW = ("actor", "changed_dims", "dims", "reasons", "version")


def _kpi(store, wid, day):
    r = store.db.execute("SELECT SUM(dials),SUM(connected),SUM(engaged) FROM seg_stats WHERE workflow_id=? AND "
                         "seg='all' AND dim='voice' AND day=?", (wid, day)).fetchone()
    d, c, e = (x or 0 for x in r)
    return (c / d if d else None), (e / c if c else None), d


def _pct(x):
    return "n/a" if x is None else f"{x:.1%}"


def render(store, sim, workflows, ts, path):
    yday = (datetime.fromisoformat(ts) - timedelta(days=1)).date().isoformat()
    since = (datetime.fromisoformat(ts) - timedelta(hours=24)).isoformat()
    out = [f"<!doctype html><meta charset=utf-8><title>Supervisor view</title><style>{CSS}</style>",
           f"<h1>Agent status — {html.escape(ts[:16])}</h1>"]
    for wid, wf in workflows.items():
        cfg = sim.config(wid)
        c = cfg["config"]
        prim = wf["objective"]["primary"]
        pk, en, n = _kpi(store, wid, yday)
        out.append(f"<h2>{html.escape(wid)} <small>primary: {prim}, config v{cfg['version']}, prompt "
                   f"{html.escape(str(c.get('prompt_version')))}</small></h2>")
        out.append(f"<p>Yesterday: pickup <b>{_pct(pk)}</b> · engagement <b>{_pct(en)}</b> <small>({n} dials; "
                   f"two separate numbers, never blended)</small></p>")
        pend = store.db.execute("SELECT proposal_id,approval_id,body,status FROM proposals WHERE workflow_id=? AND "
                                "status IN ('pending','approved','submitting') ORDER BY created_ts", (wid,)).fetchall()
        out.append("<b>What we need from you</b>")
        if pend:
            for pid, aid, body, st in pend:
                b = json.loads(body) if body and body != "{}" else {}
                out.append(f"<div class=ask>{html.escape(b.get('change_summary', pid))} <small>({st}, {aid or '-'}; "
                           f"affects ~{b.get('affected_leads', '?')} leads; impact {b.get('impact_score', '?')})"
                           f"</small></div>")
        else:
            out.append("<div>Nothing waiting.</div>")
        out.append("<p><b>Being tested</b> (default traffic split)</p><table>")
        for dim in ("welcome_message", "voice", "caller_id"):
            dist = c.get("allocations", {}).get("default", {}).get(dim)
            if dist:
                out.append(f"<tr><td>{dim}</td><td>{', '.join(f'{k} {v:.0%}' for k, v in dist.items())}</td></tr>")
        out.append("</table>")
        out.append("<p><b>Winning (rolled out to a group)</b></p>")
        wins = [co for co in c.get("cohorts", []) if co["id"].startswith(OWN)]
        if wins:
            out.append("<table>")
            for co in wins:
                al = c["allocations"].get(co["id"], {})
                txt = "; ".join(f"{dim}: " + ", ".join(f"{k} {v:.0%}" for k, v in dist.items())
                                for dim, dist in al.items())
                out.append(f"<tr><td>{html.escape(json.dumps(co['where']))}</td><td>{html.escape(txt)}</td></tr>")
            out.append("</table>")
        else:
            out.append("<div>No variant has won yet.</div>")
        out.append("<p><b>Changed in the last 24 hours</b></p><ul>")
        rows = store.db.execute("SELECT sim_ts,action,detail FROM audit WHERE workflow_id=? AND sim_ts>=? AND action IN "
                                "('config_changed','supervisor_edit_seen','auto_apply_caller_id','rejected','expired',"
                                "'lapsed') ORDER BY id", (wid, since)).fetchall()
        for sim_ts, act, det in rows:
            d = json.loads(det)
            shown = json.dumps({k: v for k, v in d.items() if k in SHOW})
            out.append(f"<li>{sim_ts[11:16]} {act}: {html.escape(shown)}</li>")
        out.append("</ul>" if rows else "<li>nothing</li></ul>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
