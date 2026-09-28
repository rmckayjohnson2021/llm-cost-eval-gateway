# LLM Cost and Evaluation Gateway

Repository: https://github.com/rmckayjohnson2021/llm-cost-eval-gateway

## Overview

LLM Cost and Evaluation Gateway is a reusable execution layer for AI applications. It centralizes model calls, records usage, enforces budgets before provider calls, applies routing rules, handles bounded retries, and supports evaluation across model configurations.

This project demonstrates the operational layer needed to run AI workflows with cost control and measurable quality.

## Employer Signal

> I can build the operational layer that makes AI applications measurable, reliable, and cost-controlled.

## What It Does

- Provides one central executor for model calls.
- Records usage and execution attempts in SQLite.
- Estimates cost using versioned pricing.
- Reserves budget before provider calls.
- Blocks over-budget requests before inference.
- Applies route policies.
- Handles timeouts and bounded retries.
- Supports mock-provider tests without paid API calls.
- Compares strong-only, fast-only, and routed configurations.

## What It Does Not Do

- It does not include production authentication.
- It does not provide a full admin billing UI.
- It does not claim provider billing records are replaced by local estimates.
- It does not require cloud deployment.

## Tech Stack

- Python
- Pydantic
- SQLite
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
