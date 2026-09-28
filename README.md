# LLM Cost and Evaluation Gateway

Repository: https://github.com/rmckayjohnson2021/llm-cost-eval-gateway

## Overview

LLM Cost and Evaluation Gateway is a reusable execution layer for AI applications. It centralizes model calls, records usage, enforces budgets before provider calls, applies routing rules, handles bounded retries, and supports evaluation across model configurations.

This project demonstrates the operational layer needed to run AI workflows with cost control and measurable quality.

## Project Status

This repo is a working version 1 backend gateway with mock-provider execution, optional OpenAI-backed execution, configuration-driven routing policies, budget reservation, retry handling, SQLite usage logging, and a runnable demo report. It is designed to become the companion execution layer for RunbookOps AI.

## Why This Exists

AI applications often start by calling a model directly from the product workflow. That works for prototypes, but teams quickly need shared controls around model choice, cost exposure, retries, evaluation, and auditability. This gateway demonstrates those controls as a reusable layer.

## What It Does

- Provides one central executor for model calls.
- Records usage and execution attempts in SQLite.
- Estimates cost using versioned pricing.
- Reserves budget before provider calls.
- Blocks over-budget requests before inference.
- Applies configurable route policies.
- Handles timeouts and bounded retries.
- Supports mock-provider tests without paid API calls.
- Supports optional OpenAI provider mode when explicitly configured.
- Compares strong-only, fast-only, and routed configurations.

## Two-Minute Demo Path

1. Run the gateway demo.
2. Inspect the generated Markdown report.
3. Compare `fast_only`, `strong_only`, and `routed` behavior.
4. Review the SQLite ledger rows.
5. Run the tests to confirm budget, retry, routing, and ledger behavior.

```powershell
uv run python examples/run_gateway_demo.py
```

Demo output:

- Report: [`reports/gateway_demo_report.md`](reports/gateway_demo_report.md)
- Ledger summary: [`reports/ledger_summary_report.md`](reports/ledger_summary_report.md)
- Ledger: `reports/gateway_demo_ledger.db` local generated file, ignored by Git

## Architecture Decisions

| Decision | Reason |
| --- | --- |
| Central executor | Keeps product workflows from calling providers directly |
| Pre-call budget reservation | Blocks over-budget requests before inference spend |
| Budget commit/release | Prevents failed calls from leaving stale reservations |
| YAML routing policies | Lets teams tune model choice without changing app code |
| SQLite usage ledger | Provides local auditability without cloud services |
| Markdown ledger summaries | Turns stored usage rows into reviewer-friendly cost and routing reports |
| Mock provider | Enables repeatable tests without paid API calls |
| Optional OpenAI provider | Allows real provider execution without changing gateway flow |
| Versioned pricing table | Makes cost estimates explainable and reproducible |

## Routing Policies

Routing policies live in [`examples/routing_policies.yaml`](examples/routing_policies.yaml). Each policy names the fast model, strong model, default route, human-review signals, and strong-model signals.

The included policies are:

| Policy | Behavior |
| --- | --- |
| `fast_only` | Sends every automatable request to the lower-cost model |
| `strong_only` | Sends every automatable request to the stronger model |
| `routed` | Sends routine work to fast model, high-impact work to strong model, and ambiguous work to human review |
| `openai_routed` | Uses OpenAI model aliases from `.env` while keeping the same routed behavior |

Application code selects a policy with the request field:

```python
ModelRequest(..., route_policy="routed")
```

That allows teams to compare cost, quality, and risk tradeoffs without rewriting the product workflow.

## Provider Modes

Mock mode is the default and does not make paid API calls:

```ini
GATEWAY_PROVIDER=mock
```

OpenAI mode is opt-in:

```ini
GATEWAY_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
DEFAULT_FAST_MODEL=gpt-5-mini
DEFAULT_STRONG_MODEL=gpt-5-mini
```

Then use the OpenAI policy alias:

```python
ModelRequest(..., route_policy="openai_routed")
```

The gateway still performs the same routing, budget reservation, retry handling, ledger logging, and reporting. The only change is the provider used for model execution.

Cost estimates are local gateway estimates for budget control and demos. They do not replace provider billing records.

## What It Does Not Do

- It does not include production authentication.
- It does not provide a full admin billing UI.
- It does not claim provider billing records are replaced by local estimates.
- It does not require cloud deployment.

## Tech Stack

- Python
- Pydantic
- SQLite
- OpenAI SDK
- pytest
- Ruff
- YAML configuration

## Project Structure

```text
llm-cost-eval-gateway/
  gateway/
    schemas.py
    providers.py
    executor.py
    budgets.py
    ledger.py
    pricing.py
    routing.py
    retries.py
    evaluation.py
    errors.py
  examples/
    routing_policies.yaml
    run_gateway_demo.py
  reports/
  tests/
```

## Setup

```powershell
uv sync
Copy-Item .env.example .env
```

Edit `.env` and add local values. Do not commit `.env`.

## Run Tests

```powershell
uv run pytest
uv run ruff check .
```

## Run Demo Report

```powershell
uv run python examples/run_gateway_demo.py
```

The demo executes three representative requests under three routing policies:

- `fast_only`
- `strong_only`
- `routed`

It writes a policy comparison report, a ledger summary report, and a local SQLite ledger so the cost, routing, and audit trail are visible.

## Core Flow

Every request should follow this sequence:

1. Validate request.
2. Select route.
3. Check allowed model policy.
4. Estimate bounded cost.
5. Reserve budget atomically.
6. Call provider.
7. Apply timeout and retry rules.
8. Record usage.
9. Reconcile reserved cost.
10. Return structured response.

## Budget Enforcement

Budget controls are pre-call controls. A request that exceeds the configured budget should be blocked before the provider is called.

Budget behavior should be tested with:

- ordinary successful requests
- over-budget requests
- concurrent requests
- retries
- unknown provider usage
- provider failures

## Evaluation

The gateway should support comparisons across:

- strong-only configuration
- fast-only configuration
- routed configuration

Metrics:

- total cases
- acceptable automated results
- human-review rate
- invalid-output rate
- total estimated cost
- median latency
- slowest latency
- cost per acceptable automated result

## Companion Project

This gateway is designed to support `team-ai-incident-triage`, a Streamlit app that triages synthetic data-pipeline incidents using approved runbooks.

## Limitations

This is a portfolio demonstration. Production use would require:

- provider billing reconciliation
- authentication
- authorization
- secure deployment
- monitoring
- incident response procedures
- larger evaluation suites
