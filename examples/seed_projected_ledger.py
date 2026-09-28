import argparse
import random
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gateway.ledger import fetch_usage, init_ledger
from gateway.pricing import PRICING_VERSION, estimate_cost_usd
from gateway.reporting import render_usage_summary_report
from gateway.schemas import UsageRecord
from gateway.settings import ledger_path

REPORT_PATH = Path("reports/projected_ledger_summary.md")

INCIDENT_TYPES = {
    "schema_change": {
        "weight": 0.28,
        "base_input": 9800,
        "base_output": 1850,
        "strong_rate": 0.42,
        "review_rate": 0.08,
    },
    "failed_import": {
        "weight": 0.25,
        "base_input": 8200,
        "base_output": 1550,
        "strong_rate": 0.28,
        "review_rate": 0.06,
    },
    "stale_dashboard": {
        "weight": 0.19,
        "base_input": 6200,
        "base_output": 1250,
        "strong_rate": 0.14,
        "review_rate": 0.03,
    },
    "duplicate_records": {
        "weight": 0.17,
        "base_input": 7600,
        "base_output": 1450,
        "strong_rate": 0.20,
        "review_rate": 0.05,
    },
    "ambiguous_outage": {
        "weight": 0.11,
        "base_input": 12500,
        "base_output": 2350,
        "strong_rate": 0.52,
        "review_rate": 0.22,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the gateway usage ledger with deterministic projected incident rows.",
    )
    parser.add_argument("--ledger-path", default=ledger_path(), help="SQLite ledger path to write.")
    parser.add_argument("--rows", type=int, default=12000, help="Number of projected rows to generate.")
    parser.add_argument("--days", type=int, default=30, help="Spread projected rows across this many days.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable demo data.")
    parser.add_argument("--append", action="store_true", help="Append rows instead of replacing the ledger.")
    return parser.parse_args()


def weighted_incident_type(rng: random.Random) -> str:
    incident_types = list(INCIDENT_TYPES)
    weights = [INCIDENT_TYPES[item]["weight"] for item in incident_types]
    return rng.choices(incident_types, weights=weights, k=1)[0]


def jittered_tokens(rng: random.Random, base: int) -> int:
    return max(40, int(base * rng.uniform(0.72, 1.42)))


def choose_route(rng: random.Random, incident_type: str) -> tuple[str, str | None, str]:
    profile = INCIDENT_TYPES[incident_type]
    roll = rng.random()
    if roll < profile["review_rate"]:
        return "human_review", None, "human_review"
    if roll < profile["review_rate"] + profile["strong_rate"]:
        return "strong_model", "mock-strong", "success"
    if rng.random() < 0.03:
        return "fast_model", "mock-fast", "failed"
    return "fast_model", "mock-fast", "success"


def projected_record(index: int, rng: random.Random, now: datetime, days: int, append: bool) -> UsageRecord:
    incident_type = weighted_incident_type(rng)
    profile = INCIDENT_TYPES[incident_type]
    route, model, status = choose_route(rng, incident_type)
    input_tokens = None if model is None else jittered_tokens(rng, int(profile["base_input"]))
    output_tokens = None if model is None else jittered_tokens(rng, int(profile["base_output"]))
    reserved_cost = (
        0.0
        if model is None or input_tokens is None or output_tokens is None
        else estimate_cost_usd(model, int(profile["base_input"] * 1.45), int(profile["base_output"] * 1.45))
    )
    actual_cost = (
        0.0
        if model is None or input_tokens is None or output_tokens is None or status == "failed"
        else estimate_cost_usd(model, input_tokens, output_tokens)
    )
    created_at = now - timedelta(
        days=rng.randrange(max(days, 1)),
        hours=rng.randrange(24),
        minutes=rng.randrange(60),
    )

    return UsageRecord(
        run_id=f"projected-{uuid4()}" if append else f"projected-{index:04d}",
        created_at=created_at.isoformat(),
        incident_type=incident_type,
        app_name="runbookops-ai",
        workflow_version="projected-v1",
        simulated_team_id="ops-team",
        provider="mock",
        model=model,
        route=route,
        status=status,
        attempts=0 if model is None else rng.choice([1, 1, 1, 2]),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reserved_cost_usd=round(reserved_cost, 10),
        estimated_cost_usd=round(actual_cost, 10),
        pricing_version=PRICING_VERSION,
        latency_ms=0 if model is None else rng.randrange(220, 2400),
        error_type="provider_timeout" if status == "failed" else None,
    )


def usage_record_values(record: UsageRecord) -> tuple:
    return (
        record.run_id,
        record.created_at,
        record.incident_type,
        record.app_name,
        record.workflow_version,
        record.provider,
        record.model,
        record.route,
        record.status,
        record.attempts,
        record.input_tokens,
        record.output_tokens,
        record.reserved_cost_usd,
        record.estimated_cost_usd,
        record.pricing_version,
        record.latency_ms,
        record.error_type,
    )


def bulk_record_usage(records: list[UsageRecord], path: str) -> None:
    init_ledger(path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            """
            INSERT INTO usage_ledger (
                run_id,
                created_at,
                incident_type,
                app_name,
                workflow_version,
                provider,
                model,
                route,
                status,
                attempts,
                input_tokens,
                output_tokens,
                reserved_cost_usd,
                estimated_cost_usd,
                pricing_version,
                latency_ms,
                error_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [usage_record_values(record) for record in records],
        )


def main() -> None:
    args = parse_args()
    target = Path(args.ledger_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not args.append:
        target.unlink()

    rng = random.Random(args.seed)
    now = datetime.now(UTC)
    records = [
        projected_record(index, rng, now, args.days, args.append)
        for index in range(1, args.rows + 1)
    ]
    bulk_record_usage(records, str(target))

    rows = fetch_usage(str(target))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_usage_summary_report(rows), encoding="utf-8")

    print(f"Wrote {args.rows} projected rows to {target}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
