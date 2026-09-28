# Gateway Demo Report

| Case | Route | Status | Model | Attempts | Reserved | Estimated | Reason |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| case-routine | fast_model | success | mock-fast | 1 | $0.006000 | $0.000026 | Routine request with no high-risk signals. |
| case-sev1 | strong_model | success | mock-strong | 1 | $0.070000 | $0.000380 | High-impact language detected. |
| case-review | human_review | human_review | - | 0 | $0.000000 | $0.000000 | Ambiguous or unclear evidence. |

## Budget State

- Limit: `$0.25`
- Spent: `$0.000406`
- Reserved: `$0.000000`
- Available: `$0.249594`

## Ledger

- Rows written: `3`
- Ledger path: `reports/gateway_demo_ledger.db`
