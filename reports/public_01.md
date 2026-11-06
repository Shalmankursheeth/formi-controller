# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.360 | +5.4% | 0.242 | -1.2% | 0.520 | +5.8% | 24% | 68 (57) |
| nw_kyc | 0.376 | +2.5% | 0.241 | -0.2% | 0.608 | +1.9% | 17% | 25 (21) |
| nw_renewal | 0.414 | -0.6% | 0.262 | -0.7% | 0.543 | +0.3% | 6% | 52 (54) |
| ALL | 0.381 | +2.5% | 0.249 | -0.8% | 0.545 | +3.0% | 16% | 145 (132) |

## Changes applied by the controller

15 applied — neutral: 6, beneficial: 6, harmful: 3

- ks_cancel v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- nw_renewal v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.041 didΔ=+0.000 → **beneficial**
- nw_renewal v3 (controller_auto) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- ks_cancel v3 (controller_auto) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_kyc v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.060 didΔ=+0.000 → **beneficial**
- nw_renewal v4 (controller_approved) dims=['welcome_message'] engageΔ=+0.083 didΔ=+0.000 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- ks_cancel v4 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.073 didΔ=+0.000 → **beneficial**
- nw_renewal v5 (controller_approved) dims=['cohorts', 'welcome_message'] engageΔ=-0.051 didΔ=+0.000 → **harmful**
- nw_renewal v6 (controller_approved) dims=['cohorts', 'welcome_message'] engageΔ=+0.012 didΔ=+0.000 → **beneficial**
- nw_kyc v4 (controller_approved) dims=['voice'] engageΔ=+0.030 didΔ=+0.000 → **beneficial**
- ks_cancel v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_renewal v7 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_kyc v5 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.070 didΔ=+0.000 → **harmful**
- ks_cancel v6 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=-0.030 didΔ=+0.000 → **harmful**

## Governance

```
{
  "approval_requests": 17,
  "decisions": {
    "approved": 13,
    "rejected": 4,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 4
  },
  "applied_via_approval": 13,
  "auto_applied": 2,
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
    "3": 0.412,
    "4": 0.67,
    "5": 0.848,
    "6": 0.854,
    "7": 0.851
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0