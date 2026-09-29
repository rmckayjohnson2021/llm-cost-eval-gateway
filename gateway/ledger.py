import sqlite3
import tempfile
from pathlib import Path

from gateway.schemas import UsageRecord

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_LEDGER_ROOTS = (
    (PROJECT_ROOT / "data").resolve(),
    (PROJECT_ROOT / "reports").resolve(),
    Path(tempfile.gettempdir()).resolve(),
)


def resolve_ledger_path(path: str = "data/ledger.db") -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    db_path = candidate.resolve(strict=False)

    if db_path.suffix != ".db":
        raise ValueError("Ledger path must point to a .db file.")

    if not any(db_path == root or db_path.is_relative_to(root) for root in ALLOWED_LEDGER_ROOTS):
        allowed = ", ".join(str(root) for root in ALLOWED_LEDGER_ROOTS)
        raise ValueError(f"Ledger path must be under an approved directory: {allowed}")

    return db_path


def init_ledger(path: str = "data/ledger.db") -> Path:
    db_path = resolve_ledger_path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_ledger (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT '',
                incident_type TEXT,
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
        columns = {row[1] for row in conn.execute("PRAGMA table_info(usage_ledger)").fetchall()}
        if "created_at" not in columns:
            conn.execute("ALTER TABLE usage_ledger ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
        if "incident_type" not in columns:
            conn.execute("ALTER TABLE usage_ledger ADD COLUMN incident_type TEXT")
    return db_path


def record_usage(record: UsageRecord, path: str = "data/ledger.db") -> None:
    db_path = init_ledger(path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
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
            (
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
            ),
        )


def fetch_usage(path: str = "data/ledger.db") -> list[dict]:
    db_path = init_ledger(path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
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
            FROM usage_ledger
            ORDER BY rowid
            """
        ).fetchall()
    return [dict(row) for row in rows]
