# Gateway Demo Report

This report runs the same synthetic requests through three routing policies: `fast_only`, `strong_only`, and `routed`.

## Policy Comparison

| Policy | Cases | Fast | Strong | Human Review | Blocked | Failed | Estimated Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fast_only | 3 | 3 | 0 | 0 | 0 | 0 | $0.000081 |
| strong_only | 3 | 0 | 3 | 0 | 0 | 0 | $0.001110 |
| routed | 3 | 1 | 1 | 1 | 0 | 0 | $0.000406 |

## Request-Level Results

| Policy | Case | Route | Status | Model | Attempts | Reserved | Estimated | Reason |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| fast_only | case-routine | fast_model | success | mock-fast | 1 | $0.006000 | $0.000026 | Policy 'fast_only' defaulted to fast model. |
| fast_only | case-sev1 | fast_model | success | mock-fast | 1 | $0.006000 | $0.000028 | Policy 'fast_only' defaulted to fast model. |
| fast_only | case-review | fast_model | success | mock-fast | 1 | $0.006000 | $0.000027 | Policy 'fast_only' defaulted to fast model. |
| strong_only | case-routine | strong_model | success | mock-strong | 1 | $0.070000 | $0.000360 | Policy 'strong_only' defaulted to strong model. |
| strong_only | case-sev1 | strong_model | success | mock-strong | 1 | $0.070000 | $0.000380 | Policy 'strong_only' defaulted to strong model. |
| strong_only | case-review | strong_model | success | mock-strong | 1 | $0.070000 | $0.000370 | Policy 'strong_only' defaulted to strong model. |
| routed | case-routine | fast_model | success | mock-fast | 1 | $0.006000 | $0.000026 | Policy 'routed' defaulted to fast model. |
| routed | case-sev1 | strong_model | success | mock-strong | 1 | $0.070000 | $0.000380 | Policy 'routed' matched strong-model signal: sev1. |
| routed | case-review | human_review | human_review | - | 0 | $0.000000 | $0.000000 | Policy 'routed' matched human-review signal: ambiguous. |

## Budget State

- Limit: `$0.25`
- Spent: `$0.001597`
- Reserved: `$0.000000`
- Available: `$0.248403`

## Ledger

- Rows written: `9`
- Ledger path: `reports/gateway_demo_ledger.db`
- Summary report: [`reports\ledger_summary_report.md`](reports\ledger_summary_report.md)
