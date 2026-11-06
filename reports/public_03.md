# Grade report — public_03_load

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| arav_cancel_2 | 0.345 | +2.3% | 0.245 | +0.7% | 0.502 | +1.2% | 5% | 388 (409) |
| arav_kyc_1 | 0.363 | +1.1% | 0.214 | -0.4% | 0.607 | +1.1% | 7% | 362 (352) |
| arav_renewal_0 | 0.435 | +7.2% | 0.264 | +0.1% | 0.583 | +6.4% | 37% | 467 (408) |
| kest_cancel_2 | 0.357 | +6.0% | 0.244 | +0.5% | 0.519 | +4.0% | 28% | 391 (418) |
| kest_kyc_1 | 0.371 | +4.5% | 0.215 | +0.3% | 0.617 | +3.2% | 19% | 351 (370) |
| kest_renewal_0 | 0.427 | +6.2% | 0.264 | -0.1% | 0.573 | +5.3% | 27% | 462 (403) |
| nort_cancel_2 | 0.340 | +0.2% | 0.243 | -0.3% | 0.500 | +0.3% | 5% | 393 (368) |
| nort_kyc_1 | 0.365 | +2.5% | 0.215 | -0.1% | 0.607 | +1.9% | 10% | 357 (318) |
| nort_renewal_0 | 0.436 | +7.6% | 0.265 | +0.2% | 0.586 | +6.9% | 36% | 448 (419) |
| tide_cancel_2 | 0.357 | +4.1% | 0.244 | -0.2% | 0.521 | +3.9% | 31% | 396 (401) |
| tide_kyc_1 | 0.360 | +1.0% | 0.214 | -0.4% | 0.604 | +0.9% | 7% | 373 (376) |
| tide_renewal_0 | 0.433 | +6.9% | 0.262 | -0.9% | 0.586 | +7.3% | 39% | 427 (425) |
| ALL | 0.382 | +4.3% | 0.241 | -0.0% | 0.566 | +3.7% | 22% | 4815 (4667) |

## Changes applied by the controller

43 applied — beneficial: 21, neutral: 19, harmful: 3

- nort_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.025 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- tide_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- kest_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.037 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- arav_cancel_2 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- tide_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.025 didΔ=+0.000 → **beneficial**
- kest_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.025 didΔ=+0.000 → **beneficial**
- arav_renewal_0 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.025 didΔ=+0.000 → **beneficial**
- arav_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.037 didΔ=+0.000 → **beneficial**
- nort_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.038 didΔ=+0.000 → **beneficial**
- nort_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.076 didΔ=+0.000 → **beneficial**
- arav_cancel_2 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.001 didΔ=+0.000 → **neutral**
- tide_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.098 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.001 didΔ=+0.000 → **neutral**
- tide_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.061 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.029 didΔ=+0.000 → **beneficial**
- arav_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.098 didΔ=+0.000 → **beneficial**
- arav_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.022 didΔ=+0.000 → **harmful**
- tide_kyc_1 v2 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.038 didΔ=+0.000 → **beneficial**
- kest_kyc_1 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.029 didΔ=+0.000 → **beneficial**
- tide_cancel_2 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.010 didΔ=+0.000 → **beneficial**
- kest_cancel_2 v4 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.010 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v4 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_renewal_0 v4 (controller_approved) dims=['cohorts', 'welcome_message'] engageΔ=+0.020 didΔ=+0.000 → **beneficial**
- kest_renewal_0 v3 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.098 didΔ=+0.000 → **beneficial**
- arav_renewal_0 v4 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.022 didΔ=+0.000 → **harmful**
- tide_kyc_1 v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.021 didΔ=+0.000 → **harmful**
- tide_cancel_2 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_cancel_2 v4 (controller_approved) dims=['welcome_message'] engageΔ=+0.029 didΔ=+0.000 → **beneficial**
- kest_renewal_0 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- kest_cancel_2 v5 (controller_approved) dims=['cohorts', 'welcome_message', 'voice'] engageΔ=+0.061 didΔ=+0.000 → **beneficial**
- tide_renewal_0 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_renewal_0 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- kest_cancel_2 v6 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_renewal_0 v6 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_renewal_0 v5 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_cancel_2 v4 (controller_approved) dims=['cohorts', 'voice'] engageΔ=+0.070 didΔ=+0.000 → **beneficial**
- nort_cancel_2 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- kest_renewal_0 v5 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_renewal_0 v6 (controller_approved) dims=['cohorts', 'welcome_message'] engageΔ=+0.001 didΔ=+0.000 → **neutral**
- tide_cancel_2 v6 (controller_approved) dims=['cohorts'] engageΔ=+0.000 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 50,
  "decisions": {
    "approved": 43,
    "rejected": 6,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 6
  },
  "applied_via_approval": 43,
  "auto_applied": 0,
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
    "3": 0.847,
    "4": 0.852
  },
  "kest_renewal_0:welcome_message=W3": {
    "3": 0.853,
    "4": 0.849
  },
  "arav_renewal_0:welcome_message=W3": {
    "3": 0.853,
    "4": 0.848
  },
  "tide_renewal_0:welcome_message=W3": {
    "3": 0.852,
    "4": 0.857
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0