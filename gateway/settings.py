import os

from dotenv import load_dotenv

load_dotenv()


def ledger_path(default: str = "data/ledger.db") -> str:
    return os.getenv("GATEWAY_LEDGER_PATH", default).strip() or default


def api_key(default: str = "local-dev-key") -> str:
    return os.getenv("GATEWAY_API_KEY", default).strip() or default
