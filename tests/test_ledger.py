import pytest

from gateway.ledger import PROJECT_ROOT, resolve_ledger_path


def test_resolve_ledger_path_allows_project_data_directory():
    resolved = resolve_ledger_path("data/test-ledger.db")

    assert resolved == PROJECT_ROOT / "data" / "test-ledger.db"


def test_resolve_ledger_path_allows_pytest_temp_directory(tmp_path):
    resolved = resolve_ledger_path(str(tmp_path / "usage.db"))

    assert resolved == tmp_path / "usage.db"


def test_resolve_ledger_path_rejects_non_db_file(tmp_path):
    with pytest.raises(ValueError, match=r"\.db"):
        resolve_ledger_path(str(tmp_path / "usage.sqlite"))


def test_resolve_ledger_path_rejects_unapproved_directory():
    outside_project = PROJECT_ROOT.parent / "outside-ledger.db"

    with pytest.raises(ValueError, match="approved directory"):
        resolve_ledger_path(str(outside_project))
