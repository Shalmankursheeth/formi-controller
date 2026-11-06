# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.342 | +0.1% | 0.243 | -0.8% | 0.495 | +0.6% | -0% | 57 (57) |
| nw_kyc | 0.368 | +0.3% | 0.243 | +0.6% | 0.601 | +0.7% | 10% | 14 (21) |
| nw_renewal | 0.413 | -0.8% | 0.263 | -0.3% | 0.539 | -0.6% | 7% | 47 (54) |
| ALL | 0.371 | -0.2% | 0.250 | -0.4% | 0.531 | +0.2% | 5% | 118 (132) |

## Changes applied by the controller

6 applied — beneficial: 3, neutral: 2, harmful: 1

- nw_renewal v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.025 didΔ=+0.000 → **beneficial**
- ks_cancel v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- nw_kyc v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.037 didΔ=+0.000 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.022 didΔ=+0.000 → **harmful**
- ks_cancel v3 (controller_approved) dims=['welcome_message'] engageΔ=+0.005 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_approved) dims=['cohorts', 'welcome_message'] engageΔ=+0.043 didΔ=+0.000 → **beneficial**

## Governance

```
{
  "approval_requests": 6,
  "decisions": {
    "approved": 6,
    "expired": 0
  },
  "rejection_reasons": {},
  "applied_via_approval": 6,
  "auto_applied": 0,
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
[]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{
  "nw_renewal:welcome_message=W3": {
    "3": 0.125,
    "4": 0.122,
    "5": 0.113,
    "6": 0.133,
    "7": 0.084
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0