# Outcome-First Agent Loop — Submission

**Name:** Mohamed Shalman Kursheeth · **Date:** 2026-11-06 · **Hours actually spent (be honest):** [fill in] · **Language / storage:** Python 3.12, SQLite (WAL), no other stateful infra

---

## 0. TL;DR
- A single-process controller: ingest events into one shared segment table → detect/experiment once a day → one batched proposal per workflow → governance client applies only what was approved. Fast path every tick for caller-ID degradation and hallucination spikes.
- public_02: spam-flagged caller ID stepped out by policy-bounded auto-apply within hours; bad supervisor prompt reverted via validated proposal in 270 min (hallucinated calls 77 vs 348 baseline); ks_cancel conclusions +18.9%. public_01: roughly flat. public_03: +4.3% conclusions, pickup flat, 12 workflows, ~60 s wall per simulated day.
- Cut on purpose: per-person call time, LLM fix generation, credit/approver-attention fairness, a UI, call-level audit retention (see §2 and §13).

## 1. Assumptions
1. Config changes are the only lever; cadence, windows and capacity are never touched (README §5.2).
2. Customer-facing = `welcome_message`, `voice`, `cohorts`, `prompt_version`. These **always** go through `/approvals`, even where a workflow's policy would permit auto-apply (Kestrel). Reason: Kestrel's supervisor asked to be told before changes (memo 04) and Northwind compliance requires named approval (memo 02). Auto-apply is used only for `caller_id`.
3. A "segment" is `all` or a single feature value (`age_band=60+`). Interactions (e.g. 60+ and Tamil) are not modelled.
4. Within one config version the simulator samples arms independently per dial, so arms are concurrent and comparable; I never compare across versions.
5. Variant effects are roughly stable over a 5-day window except for decay, which the 2-day recent check catches.
6. The hallucination flag is noisy but unbiased across prompts; I use rate ratios and a z-test, not single flags.
7. The previous prompt (largest traffic share before the spike) is a safe revert target if it passes validation; config history has no bodies, so I infer it from my own stats.
8. The simulated clock only moves when I advance it, so decision latency inside the sim is measured in sim-time; wall-clock numbers are reported separately in §8.
9. Hidden scenarios: option names, policies and incident types may differ. Nothing is hard-coded to public ids.

## 2. Scope decisions
| # | Capability | Built / Partial / Cut | Why | What it would take to finish |
|---|---|---|---|---|
| C1 | Ingestion at scale | Built | Atomic chunk+cursor txn, idempotent; 9.7M events in one run | Shard by workflow, move stats to Postgres (§8) |
| C2 | Shared cohort object | Built | One `seg_stats` table read by detection, experiments, rollback | Multi-feature segments |
| C3 | Bootstrap from history | Partial | History ingested for lead universe/baselines; it is single-arm so it cannot rank variants | Use it for call-time priors (C4) |
| C4 | Call-time optimisation | **Cut** | Largest unknown, needs per-hour × cohort tables and a dry-run model | Hourly pickup tables per segment, `hour_weights` proposals |
| C5 | Caller-ID health | Built (conservative) | Incident in public_02; only retires IDs, never widens onto unseen ones (an early version that widened cost ~9% pickup) | Safe exploration of recovered IDs |
| C6 | Variant experimentation | Built | 25% explore share, Bonferroni, min 300/arm, min 3% lift | Sequential tests / bandit with guardrail |
| C7 | Promotion + decay + rollback | Built | 15% hold-out keeps decay observable; 2-day recent z<−2 drops a winner | Faster (hourly) decay detection |
| C8 | Hallucination response | Partial | Detect → validate previous prompt → propose with evidence | `/llm/suggest-fixes` fallback; explicit post-apply verification record |
| C9 | Governance client | Built | Deterministic ids, intent-before-call, reconcile, stale/expired/lapsed | Cross-tenant attention budgeting |
| C10 | Honest impact/dry run | Partial | Dry run = observed concurrent-arm rates, not a counterfactual replay; impact is a heuristic | Replay against held-out cohort |
| C11 | Supervisor view | **Cut** (CLI only) | `python -m controller.why` answers the audit question; no UI | Read-only page over the same tables |
| C12 | Audit store | Built | Append-only `audit` table, queryable by workflow | Retain per-call variant (§13) |
| C13 | Crash recovery | Built + demonstrated | `tests/crash_recovery.py`, 5 hard kills | Deliberately test the submit-window race |
| C14 | Loop observability | **Cut** | Wall time/credits printed at end only | Prometheus counters for lag, decisions/h, credits |
| C15 | Fairness across tenants | **Cut** | Credit spend is tiny (≤5 per incident), no contention here | Per-tenant credit and approver-slot budgets |

Principle: spend the time on what moves the graded outcome safely — a correct experiment loop, governance hygiene and incident response — and be explicit about the rest rather than sketching all fifteen.

## 3. Stakeholders

### 01 Sales (Nikhil Rao)
- **Accepted:** speed matters; one decision slot a day plus fast paths for incidents; caller-ID changes auto-apply within hours.
- **Declined:** a single blended lift score (violates constraint 3, so I report pickup and engagement separately); pushing "winners to everyone by evening" (needs significance and a hold-out); rolling out the persuasive prompt.
- **Wrong in the memo:** "Kestrel turned on auto-apply for everything" — ks_cancel's policy allows only `schedule, caller_id, welcome_message, voice` with `max_shift` 0.2; prompts and cohort changes are not permitted. "Northwind fine with auto-apply on KYC" — `nw_kyc` has auto-apply **disabled**. The "persuasive" prompt (P4) hallucinates ~4× more than P1 (0.025 vs 0.006 in the dev scenario) and is not available in every workflow.
- **Reply:** "Nikhil — I can give you a per-client lift for the summit, but as two numbers: pickup and engagement. Blending them hides exactly the trade-offs clients' compliance teams care about. On auto-apply: Kestrel's policy only allows timing, caller ID, opening line and voice within a 20% traffic shift, and Northwind KYC has it switched off, so those changes go through approval. The persuasive prompt hallucinates about 4× more than today's script and would need to pass validation; I won't propose it. What I can promise: caller-ID fixes within hours and a daily batch of at most two requests."

### 02 Compliance (Meera Iyer, Northwind)
- **Accepted:** every customer-facing change goes through a named approval, never auto-apply; prompt changes carry a validation run; proposals are sent inside approver hours; every decision is in the audit store.
- **Gap:** "answer within 24h why a given customer heard a given variant" — I store per-variant aggregates plus a decision audit, **not** call-level variants. A per-call log table would close this (§13). "No harm even briefly": experimentation necessarily shows ~25% of traffic non-incumbent variants; I state the exposure in each rationale.
- **Wrong in the memo:** "call timing and caller-ID rotation are covered by the policy" is true for `nw_renewal` (schedule, caller_id, shift ≤0.5) but **not** for `nw_kyc`, which has no auto-apply.
- **Reply:** "Meera — customer-facing changes (opening line, voice, script, cohorts) will only be applied after a named approval, inside your approver hours, with validation evidence on any script change. Caller-ID rotation on renewal can auto-apply under your signed policy; KYC cannot, and we will not. Today we retain per-variant aggregates and a full decision trail; call-level 'which customer heard what' is not yet retained and we will add it before go-live."

### 03 Platform/SRE (Kabir Menon)
- **Accepted:** kill/restart evidence (`reports/crash_recovery.md`); idempotent proposals; no new infrastructure (one SQLite file; Postgres is the migration path).
- **Not done:** alerting and a metrics endpoint.
- **Numbers:** public_03: 9.74M events in 302 s wall for 5 simulated days with the simulator on the same machine (≈60 s per simulated day). Peak memory **not measured**.
- **Reply:** "Kabir — kill -9 test passes: five hard kills mid-run on public_02, every approval applied exactly once, same outcomes as the uninterrupted run (reports/crash_recovery.md). State is one SQLite file; I'd move it to your Postgres when we shard by workflow. One simulated day of public_03 takes about a minute end to end, well inside your 10 minutes. Paging alerts and loop metrics are not built yet; they are first on the production list."

### 04 Client ops supervisor (Anita Desai, Kestrel)
- **Accepted:** her edits are never undone — a supervisor `config_changed` freezes that dimension for 3 days; ≤2 proposals a day per workflow, decision slot at 12:00 (never before 11:00); everything bundled into one proposal.
- **Pushed back:** "tell me before anything changes on a running campaign" — ks_cancel allows mid-flight changes, so an approved change reaches running campaigns; the approval request is the notice. The "one screen" is not built.
- **Nuance:** she asks for 2/day; the policy allows 4 — I pace below the policy. Incident fixes (caller ID, prompt revert) are exempt from the daily cap because delay costs more than the interruption; customer-facing ones still need approval.
- **Her script story:** P5 (near-verbatim script) has engage_mult 0.86 in the dev scenario; winners are chosen on measured engagement, so it would not be promoted.
- **Reply:** "Anita — I won't override changes you make; if you edit a setting I leave that dimension alone for three days and record it. You'll get at most two requests a day, never before 11:00, with everything bundled into one. A one-screen view isn't built yet; until then your Formi contact can pull 'what changed and why' for any day."

### 05 Product (Tara Kulkarni)
- **Accepted:** pickup and engagement separate everywhere; one cohort object (`seg_stats`) used by detection, experiments and rollback; expired or rejected proposals are re-proposed with fresh data and a new id; only calls that actually occurred feed learning; a winner updates this workflow only.
- **Open question decided:** min 300 observations per arm, 5-day window, Bonferroni across all (segment × dimension × option) tests, min 3% relative lift. Cost: slow to find small wins (about a week at dev-scale traffic) in exchange for few false winners; with ~100 tests the critical z is ≈3.3.
- **Pushed back:** per-person call time and the supervisor view (her P0s) are cut; caller-ID health is built.
- **Impact score** is `min(1, mean lift × 5)` — a ranking heuristic, not a probability.
- **Reply:** "Tara — pickup and engagement are separate everywhere, cohorts are one shared object, and winners require a statistical test with a stated cost: at least 300 observations per arm and roughly a week of data, in exchange for few false winners. Of your P0s I built caller-ID health; per-person call time and the supervisor view are cut and I'd like to agree the ordering with you."

### 06 CTO (Aryamann)
- **Accepted:** explainability over lift; compute only where it changes a decision (no LLM calls; 5 credits per real incident); choosing and saying no.
- **Reply:** "I cut four of fifteen capabilities and partly built three. The loop is built safety-first: customer-facing changes need approval, winners need a significance test and keep a hold-out, and the audit trail is queryable. What breaks first at 10× is single-writer SQLite and single-process JSON parsing (§8); the plan is to shard by workflow."

## 4. Architecture
```
sim HTTP --chunks--> Ingestor --(one txn: stats + cursor)--> SQLite (WAL)
                                                              seg_stats, hourly, leads, proposals, audit, meta
every 60-min tick:
   reconcile()        approvals API: apply approved, record rejected/expired/lapsed/stale
   fast_checks()      caller-ID health, hallucination spike
   decide() @12:00    find_winners -> build_config -> propose (or auto-apply caller_id only)
```
- State lives only in the SQLite file; the simulator holds the world. On restart: read cursors, catch up on unprocessed chunks, reconcile open proposals (including one whose POST succeeded but whose id was never written), then continue.
- Modules: `ingest.py` (C1/C2), `stats.py`, `decide.py` (experiments/promotion/rollback), `incidents.py` (C5/C8), `governance.py` (C9), `store.py`, `why.py` (audit query), `main.py`.

## 5. The learning loop
- **Cohorts:** a segment is a single feature value; promoted segments become cohorts `ep_<feature>_<value>`. Min 300 observations per arm; only significant winners create cohorts, which limits fragmentation (the sim allows 20).
- **Experiment design:** the default allocation keeps 75% on the incumbent and 25% spread over the other options; settled dims keep a 90/10 spread; promoted winners keep a 15% reference hold-out. Welcome, voice and caller ID are tested independently; interactions are **not** modelled.
- **Winner test:** two-proportion z-test on concurrent arms pooled over versions containing both arms; one-sided Bonferroni at α=0.05 over all candidate tests; min lift 3%; deterministic, no LLM. Family-wise false-winner rate ≤5% by construction (not measured empirically).
- **Decay/rollback:** each day every promoted option is re-tested on the last 2 days against its hold-out (z<−2, ≥150 per arm); a failing one is dropped. Latency is one daily slot plus approval (1–2 days) — slower than the W3 decay window in the dev scenario.
- **Call time:** cut. **Caller ID:** retire-only; step-downs bounded by the policy's `max_shift` per auto-apply.
- **Guardrail:** a winner on the primary KPI must not reduce the other KPI by more than half the guardrail threshold.

## 6. Governance
- Lifecycle: `submitting → pending → approved → applied`, with `rejected | expired | lapsed | failed | stale` terminal. A non-applied proposal is re-derived from fresh data in the next slot with a new id (`<wf>-v<version>-<day>-<hash>`).
- Intent is stored before the POST; `submitting` rows are reconciled against `GET /approvals` after a crash.
- Pacing: 12:00 slot, ≤2/day/workflow (below policy cap), one open proposal at a time; incident proposals only inside approver hours minus an hour.
- Auto-apply: only `caller_id`, only when policy permits and total-variation shift ≤ `max_shift`; welcome/voice are never auto-applied.
- Supervisor edits are detected via `config_changed(actor=supervisor)`, recorded, and freeze that dimension for 3 days; `base_version` is always read fresh so nothing is silently overwritten.

## 7. Incidents (public_02 timeline)
- D2 10:00 caller ID D2 flagged → within hours three auto step-downs on ks_cancel (v3–v5, each within policy shift) → flagged share 0.16 on D2, 0.0 from D3.
- D3 11:30 supervisor ships P2 (hallucination ≈5%) → detection ~13:30 → validation of P1 (500 conversations, pass_rate 0.986, 5 credits) at 14:00 → proposal → applied 16:00 (MTTR 270 min).
- Thresholds: hallucination rate >2.5× baseline, >1.5%, z>3, ≥150 connected calls in 6h; caller ID z<−3.5 vs peers and <80% of peer pickup. False-positive rate not measured beyond public_01, where neither fired.
- Post-apply verification: the detector keeps running on the new prompt; a dedicated verification record is not written (gap).

## 8. Scale
Measured on public_03_load (12 workflows, 5 days, 9,737,591 events, simulator on the same machine):
- End to end 302 s wall → ≈60 s per simulated day (budget: 10 minutes). Roughly 32k events/s including the simulator's own advance time.
- Decision lag: ingest lag ≤ one tick (60 simulated minutes); decisions at 12:00; approval latency dominates.
- Peak memory: **not measured**.
- First to break at 10×: single-process JSON decoding, single-writer SQLite, the in-memory `leads` dict and `affected_leads()`, which scans leads per workflow. Plan: shard by workflow across workers, Postgres partitioned by workflow, and pre-aggregate upstream instead of parsing NDJSON.

## 9. Reliability
`python tests/crash_recovery.py public_02_incidents 5`: five hard kills at random simulated times (D2 01:00 … D8 16:00). `reports/crash_recovery.md`: scenario finished, 8/8 approvals applied exactly once, nothing pending, outcomes and credits identical to an uninterrupted run. Idempotency keys: chunk cursors and proposal ids. Not tested: a kill exactly between POST /approvals and our DB write (the recovery path exists but was not exercised). The controller has no retry/backoff for simulator 5xx; it crashes and relies on restart.

## 10. Audit & observability
```
python -m controller.why --db controller_public_02.db ks_cancel --since 2027-01-07
2027-01-07T11:30  supervisor_edit_seen   {"dims": ["prompt_version"], "version": 6, "freeze_until": "2027-01-10"}
2027-01-07T14:00  validation_run         P1 pass_rate 0.986 (val_00001)
2027-01-07T14:00  propose  apr_00005     "Revert prompt P2 -> P1: hallucination flags 4.8% vs 1.4% before"
2027-01-07T16:00  apply / config_changed version 7, actor controller_approved
```
Would page on: no ingest progress, a proposal near its apply deadline, credits below reserve, controller restart loops. Would not page on: single rejections or individual decayed winners. None of these alerts is implemented.

## 11. Results
Tables: `reports/public_01.md`, `reports/public_02.md`, `reports/public_03.md`.
- public_01: conclusion Δ −0.8%…+0.3% by workflow; 6 changes (3 beneficial, 2 neutral, 1 harmful — nw_kyc welcome/voice, engagement −2.2 pts). Exploration cost offsets gains over an 8-day horizon.
- public_02: ks_cancel +18.9% conclusions (caller-ID and prompt incidents); nw_kyc −1.3% and nw_renewal −2.0% from exploration cost and one harmful voice change.
- public_03: +4.3% conclusions, pickup −0.0%, engagement +3.7%; 43 changes: 21 beneficial, 19 neutral, 3 harmful (all KYC workflows).
- Harmful changes share a cause: promoting from a 5-day window right after exploration noise. Next: higher min n for customer-facing promotions and a post-apply check that rolls back quickly.

## 12. Trade-offs & rejected alternatives
| Option | Why considered | Why rejected / what instead |
|---|---|---|
| Thompson-sampling bandit | Faster learning | Harder to explain to compliance; the Bonferroni z-test is deterministic and auditable |
| LLM `suggest-fixes` | Generates new prompts | Costs credits and is unvalidated; reverting to the previous validated prompt is cheaper and safer |
| Auto-apply welcome/voice at Kestrel | Policy permits it | Supervisor asked to be told first; keep approval |
| Postgres/Redis | Already in your stack | No new infra for a single process; migration path in §8 |
| Per-person call time | Summit headline | Cut for time; needs hourly tables and a dry-run model |

## 13. Known weaknesses
- No call-level retention, so "which customer heard what" (compliance #3) cannot be answered beyond variant aggregates.
- Single-feature segments: the first matching cohort wins, so a lead in two winning segments gets only the first one's dimensions.
- Exploration at 25% is too costly for small workflows; gains are small within 8 days.
- Daily decay checks only; no post-apply verification record.
- No retry/backoff for simulator errors; no memory measurement; no metrics or alerts.
- Impact score and dry run are heuristics, not counterfactual replays.

## 14. If this went to production at Formi next month
1. Persist call-level (lead, variant, config_version) for the 24h audit. 2. Retry/backoff, metrics and alerts. 3. Postgres plus per-workflow sharding. 4. Post-apply verification and faster decay. 5. Read-only supervisor page. 6. Per-person call time with safe exploration. 7. Fair credit and approver budgets across tenants.
