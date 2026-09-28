import sqlite3
from pathlib import Path

from gateway.schemas import UsageRecord


def init_ledger(path: str = "data/ledger.db") -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_ledger (
                run_id TEXT PRIMARY KEY,
                app_name TEXT NOT NULL,
                workflow_version TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT,
                route TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                reserved_cost_usd REAL NOT NULL,
                estimated_cost_usd REAL NOT NULL,
                pricing_version TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                error_type TEXT
            )
            """
        )


def record_usage(record: UsageRecord, path: str = "data/ledger.db") -> None:
    init_ledger(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO usage_ledger (
                run_id,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
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
            ),
        )


def fetch_usage(path: str = "data/ledger.db") -> list[dict]:
    init_ledger(path)
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                run_id,
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
            FROM usage_ledger
            ORDER BY rowid
            """
        ).fetchall()
    return [dict(row) for row in rows]
