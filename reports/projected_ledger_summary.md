# Usage Ledger Summary

- Total rows: `12004`
- Total estimated cost: `$671.730555`
- Strong-only baseline cost: `$1593.620830`
- Estimated routing savings: `$921.890275`
- Savings rate: `57.8%`

## By Route

| Route | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fast_model | 7367 | $85.917615 | 1316 ms | 214 | 0 | 0 |
| human_review | 913 | $0.000000 | 0 ms | 0 | 0 | 913 |
| strong_model | 3724 | $585.812940 | 1314 ms | 0 | 0 | 0 |

## By Model

| Model | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| - | 913 | $0.000000 | 0 ms | 0 | 0 | 913 |
| mock-fast | 7367 | $85.917615 | 1316 ms | 214 | 0 | 0 |
| mock-strong | 3724 | $585.812940 | 1314 ms | 0 | 0 | 0 |

## By Incident Type

| Incident_Type | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| - | 3 | $0.000272 | 1 ms | 0 | 0 | 1 |
| ambiguous_outage | 1313 | $151.417039 | 1056 ms | 13 | 0 | 277 |
| duplicate_records | 2059 | $70.919006 | 1254 ms | 40 | 0 | 111 |
| failed_import | 2960 | $135.805901 | 1255.5 ms | 53 | 0 | 189 |
| schema_change | 3436 | $261.618300 | 1190 ms | 48 | 0 | 280 |
| stale_dashboard | 2233 | $51.970037 | 1286 ms | 60 | 0 | 55 |

## By Status

| Status | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| failed | 214 | $0.000000 | 1414 ms | 214 | 0 | 0 |
| human_review | 913 | $0.000000 | 0 ms | 0 | 0 | 913 |
| success | 10877 | $671.730555 | 1314 ms | 0 | 0 | 0 |
