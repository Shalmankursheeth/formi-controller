# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.287 | +21.8% | 0.200 | +10.3% | 0.507 | +8.4% | 33% | 84 (348) |
| nw_kyc | 0.371 | -0.7% | 0.236 | +0.7% | 0.600 | -1.4% | -3% | 26 (29) |
| nw_renewal | 0.435 | +0.5% | 0.265 | +1.0% | 0.552 | -0.4% | 7% | 55 (54) |
| ALL | 0.354 | +7.1% | 0.229 | +4.5% | 0.543 | +2.0% | 19% | 165 (431) |

## Changes applied by the controller

19 applied — beneficial: 8, harmful: 3, neutral: 8

- ks_cancel v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.013 didΔ=+0.000 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.015 didΔ=+0.000 → **harmful**
- ks_cancel v3 (controller_auto) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_renewal v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.026 didΔ=+0.000 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_auto) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- ks_cancel v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.189 → **beneficial**
- ks_cancel v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.158 → **beneficial**
- ks_cancel v6 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.074 → **beneficial**
- ks_cancel v8 (controller_approved) dims=['welcome_message'] engageΔ=-0.007 didΔ=+0.000 → **neutral**
- ks_cancel v9 (controller_approved) dims=['prompt_version'] engageΔ=+0.102 didΔ=+0.000 → **beneficial**
- nw_kyc v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**
- nw_renewal v4 (controller_approved) dims=['welcome_message'] engageΔ=+0.014 didΔ=+0.000 → **beneficial**
- ks_cancel v10 (controller_approved) dims=['voice'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- nw_kyc v5 (controller_approved) dims=['cohorts', 'voice'] engageΔ=-0.022 didΔ=+0.000 → **harmful**
- ks_cancel v11 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- ks_cancel v12 (controller_auto) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_renewal v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.037 didΔ=+0.000 → **harmful**
- nw_renewal v7 (controller_auto) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 17,
  "decisions": {
    "approved": 12,
    "rejected": 5,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 4,
    "change_summary, diff, dry_run and rationale must all be non-empty": 1
  },
  "applied_via_approval": 12,
  "auto_applied": 7,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 1,
    "nw_kyc": 1,
    "ks_cancel": 2
  }
}
```

## Incidents

```
[
  {
    "type": "did_flagged",
    "workflow": "ks_cancel",
    "at": "D2 10:00",
    "flagged_did_share_by_day": {
      "2": 0.21,
      "3": 0.0,
      "4": 0.0,
      "5": 0.0,
      "6": 0.0,
      "7": 0.0,
      "8": 0.0,
      "9": 0.0
    }
  },
  {
    "type": "supervisor_edit",
    "workflow": "ks_cancel",
    "at": "D3 11:30",
    "mttr_minutes": 270,
    "fixed_by": "controller_approved"
  },
  {
    "type": "supervisor_edit",
    "workflow": "nw_renewal",
    "at": "D5 15:00"
  }
]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{
  "nw_renewal:welcome_message=W3": {
    "3": 0.224,
    "4": 0.2,
    "5": 0.116,
    "6": 0.054,
    "7": 0.044,
    "8": 0.113,
    "9": 0.203
  }
}
```

Credits used: 5 · validation runs: 1 · LLM fix calls: 0