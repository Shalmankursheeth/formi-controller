# Grade report — public_03_load

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| arav_cancel_2 | 0.359 | +6.7% | 0.245 | +0.6% | 0.522 | +5.2% | 33% | 394 (409) |
| arav_kyc_1 | 0.364 | +1.6% | 0.215 | +0.1% | 0.604 | +0.6% | 7% | 351 (352) |
| arav_renewal_0 | 0.436 | +7.7% | 0.265 | +0.4% | 0.585 | +6.9% | 38% | 382 (408) |
| kest_cancel_2 | 0.337 | -0.0% | 0.244 | +0.7% | 0.494 | -1.0% | -1% | 419 (418) |
| kest_kyc_1 | 0.360 | +1.3% | 0.215 | +0.1% | 0.602 | +0.8% | 8% | 355 (370) |
| kest_renewal_0 | 0.434 | +7.9% | 0.263 | -0.5% | 0.584 | +7.3% | 38% | 441 (403) |
| nort_cancel_2 | 0.353 | +4.0% | 0.242 | -0.7% | 0.516 | +3.6% | 29% | 377 (368) |
| nort_kyc_1 | 0.367 | +3.3% | 0.215 | +0.2% | 0.610 | +2.5% | 14% | 327 (318) |
| nort_renewal_0 | 0.435 | +7.2% | 0.264 | +0.0% | 0.584 | +6.6% | 39% | 446 (419) |
| tide_cancel_2 | 0.357 | +4.1% | 0.244 | -0.3% | 0.520 | +3.8% | 28% | 394 (401) |
| tide_kyc_1 | 0.368 | +3.2% | 0.214 | -0.2% | 0.612 | +2.4% | 12% | 373 (376) |
| tide_renewal_0 | 0.432 | +6.9% | 0.263 | -0.5% | 0.586 | +7.4% | 38% | 444 (425) |
| ALL | 0.384 | +4.6% | 0.241 | -0.0% | 0.567 | +4.0% | 25% | 4703 (4667) |

## Changes applied by the controller

48 applied — neutral: 28, beneficial: 17, harmful: 3

- arav_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- nort_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.041 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- kest_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- tide_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.041 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.003 didΔ=+0.000 → **neutral**
- nort_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.060 didΔ=+0.000 → **beneficial**
- kest_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.041 didΔ=+0.000 → **beneficial**
- arav_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.041 didΔ=+0.000 → **beneficial**
- kest_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.060 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.045 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.002 didΔ=+0.000 → **neutral**
- arav_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.073 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.045 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.082 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.082 didΔ=+0.000 → **beneficial**
- kest_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.082 didΔ=+0.000 → **beneficial**
- arav_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.082 didΔ=+0.000 → **beneficial**
- tide_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.060 didΔ=+0.000 → **beneficial**
- arav_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.060 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v4 (controller_auto) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_cancel_2 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.027 didΔ=+0.000 → **beneficial**
- kest_renewal_0 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_kyc_1 v3 (controller_approved) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_renewal_0 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- kest_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.042 didΔ=+0.000 → **harmful**
- arav_renewal_0 v4 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_cancel_2 v4 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_renewal_0 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_cancel_2 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.027 didΔ=+0.000 → **beneficial**
- nort_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.043 didΔ=+0.000 → **harmful**
- tide_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.043 didΔ=+0.000 → **harmful**
- nort_cancel_2 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_renewal_0 v5 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_cancel_2 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- kest_renewal_0 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_cancel_2 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_renewal_0 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_renewal_0 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_kyc_1 v4 (controller_approved) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_kyc_1 v4 (controller_approved) dims=['schedule'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_cancel_2 v6 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_cancel_2 v6 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_renewal_0 v6 (controller_approved) dims=['cohorts', 'welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- kest_renewal_0 v6 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_renewal_0 v6 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_cancel_2 v6 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.004 didΔ=+0.000 → **neutral**
- tide_renewal_0 v6 (controller_approved) dims=['cohorts'] engageΔ=+0.001 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 53,
  "decisions": {
    "approved": 47,
    "rejected": 5,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 5
  },
  "applied_via_approval": 47,
  "auto_applied": 1,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nort_renewal_0": 1,
    "nort_kyc_1": 1,
    "nort_cancel_2": 1,
    "kest_renewal_0": 1,
    "kest_kyc_1": 1,
    "kest_cancel_2": 1,
    "arav_renewal_0": 1,
    "arav_kyc_1": 1,
    "arav_cancel_2": 1,
    "tide_renewal_0": 1,
    "tide_kyc_1": 1,
    "tide_cancel_2": 1
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
  "nort_renewal_0:welcome_message=W3": {
    "3": 0.85,
    "4": 0.852
  },
  "kest_renewal_0:welcome_message=W3": {
    "3": 0.852,
    "4": 0.851
  },
  "arav_renewal_0:welcome_message=W3": {
    "3": 0.848,
    "4": 0.851
  },
  "tide_renewal_0:welcome_message=W3": {
    "3": 0.852,
    "4": 0.85
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0