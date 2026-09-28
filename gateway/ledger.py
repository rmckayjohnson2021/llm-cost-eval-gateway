import sqlite3
from pathlib import Path


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
                estimated_cost_usd REAL NOT NULL,
                latency_ms INTEGER NOT NULL,
                error_type TEXT
            )
            """
        )
