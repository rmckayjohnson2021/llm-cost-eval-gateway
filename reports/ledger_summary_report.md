# Usage Ledger Summary

- Total rows: `9`
- Total estimated cost: `$0.001597`
- Strong-only baseline cost: `$0.002960`
- Estimated routing savings: `$0.001363`
- Savings rate: `46.0%`

## By Route

| Route | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fast_model | 4 | $0.000107 | 0 ms | 0 | 0 | 0 |
| human_review | 1 | $0.000000 | 0 ms | 0 | 0 | 1 |
| strong_model | 4 | $0.001490 | 0 ms | 0 | 0 | 0 |

## By Model

| Model | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| - | 1 | $0.000000 | 0 ms | 0 | 0 | 1 |
| mock-fast | 4 | $0.000107 | 0 ms | 0 | 0 | 0 |
| mock-strong | 4 | $0.001490 | 0 ms | 0 | 0 | 0 |

## By Incident Type

| Incident_Type | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ambiguous_outage | 3 | $0.000788 | 0 ms | 0 | 0 | 0 |
| failed_import | 3 | $0.000412 | 0 ms | 0 | 0 | 0 |
| schema_change | 3 | $0.000397 | 0 ms | 0 | 0 | 1 |

## By Status

| Status | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| human_review | 1 | $0.000000 | 0 ms | 0 | 0 | 1 |
| success | 8 | $0.001597 | 0 ms | 0 | 0 | 0 |
