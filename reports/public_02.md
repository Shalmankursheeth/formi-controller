# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.280 | +18.9% | 0.199 | +9.9% | 0.493 | +5.5% | 32% | 77 (348) |
| nw_kyc | 0.369 | -1.3% | 0.235 | +0.4% | 0.595 | -2.1% | -7% | 26 (29) |
| nw_renewal | 0.425 | -2.0% | 0.260 | -0.8% | 0.550 | -0.8% | 5% | 63 (54) |
| ALL | 0.347 | +5.0% | 0.227 | +3.5% | 0.536 | +0.7% | 18% | 166 (431) |

## Changes applied by the controller

11 applied — neutral: 5, beneficial: 5, harmful: 1

- ks_cancel v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.008 didΔ=+0.000 → **neutral**
- nw_renewal v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.016 didΔ=+0.000 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.009 didΔ=+0.000 → **neutral**
- ks_cancel v3 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.189 → **beneficial**
- ks_cancel v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.158 → **beneficial**
- ks_cancel v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.074 → **beneficial**
- ks_cancel v7 (controller_approved) dims=['prompt_version'] engageΔ=+0.102 didΔ=+0.000 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- ks_cancel v8 (controller_approved) dims=['welcome_message'] engageΔ=-0.004 didΔ=+0.000 → **neutral**
- ks_cancel v9 (controller_approved) dims=['welcome_message'] engageΔ=+0.004 didΔ=+0.000 → **neutral**
- nw_renewal v4 (controller_approved) dims=['voice'] engageΔ=-0.015 didΔ=+0.000 → **harmful**

## Governance

```
{
  "approval_requests": 8,
  "decisions": {
    "approved": 8,
    "expired": 0
  },
  "rejection_reasons": {},
  "applied_via_approval": 8,
  "auto_applied": 3,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 1,
    "nw_kyc": 1,
    "ks_cancel": 1
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
      "2": 0.16,
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
    "2": 0.124,
    "3": 0.124,
    "4": 0.119,
    "5": 0.125,
    "6": 0.124,
    "7": 0.125,
    "8": 0.125,
    "9": 0.121
  }
}
```

Credits used: 5 · validation runs: 1 · LLM fix calls: 0