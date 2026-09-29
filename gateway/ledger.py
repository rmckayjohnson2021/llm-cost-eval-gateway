import re
import sqlite3
import tempfile
from pathlib import Path

from gateway.schemas import UsageRecord

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = Path(tempfile.gettempdir()).resolve()
ALLOWED_LEDGER_ROOTS = (
    (PROJECT_ROOT / "data").resolve(),
    (PROJECT_ROOT / "reports").resolve(),
    TEMP_ROOT,
)
SAFE_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")


def normalized_path_text(path: str) -> str:
    return path.strip().replace("\\", "/").rstrip("/")


def validate_relative_db_path(relative_path: str) -> list[str]:
    parts = relative_path.split("/")
    if not parts or parts[-1] == "":
        raise ValueError("Ledger path must point to a .db file.")
    if not parts[-1].endswith(".db"):
        raise ValueError("Ledger path must point to a .db file.")
    if any(part in {"", ".", ".."} or not SAFE_PATH_SEGMENT.fullmatch(part) for part in parts):
        raise ValueError("Ledger path contains an unsafe path segment.")
    return parts


def resolve_ledger_path(path: str = "data/ledger.db") -> Path:
    path_text = normalized_path_text(path)
    project_root_text = PROJECT_ROOT.as_posix()
    temp_root_text = TEMP_ROOT.as_posix()

    if path_text.startswith(f"{project_root_text}/"):
        relative_path = path_text.removeprefix(f"{project_root_text}/")
        if not relative_path.startswith(("data/", "reports/")):
            allowed = ", ".join(str(root) for root in ALLOWED_LEDGER_ROOTS)
            raise ValueError(f"Ledger path must be under an approved directory: {allowed}")
        return PROJECT_ROOT.joinpath(*validate_relative_db_path(relative_path))

    if path_text.startswith(f"{temp_root_text}/"):
        relative_path = path_text.removeprefix(f"{temp_root_text}/")
        return TEMP_ROOT.joinpath(*validate_relative_db_path(relative_path))

    if path_text.startswith(("data/", "reports/")):
        return PROJECT_ROOT.joinpath(*validate_relative_db_path(path_text))

    allowed = ", ".join(str(root) for root in ALLOWED_LEDGER_ROOTS)
    raise ValueError(f"Ledger path must be under an approved directory: {allowed}")


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
