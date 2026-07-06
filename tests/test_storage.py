import os
import tempfile

import pytest

from contract_guard.contract import Contract
from contract_guard.storage import Storage
from contract_guard.validator import validate


@pytest.fixture
def storage():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = Storage(path)
    yield store
    os.remove(path)


def _contract():
    return Contract(name="orders", required_fields=["order_id"])


def test_record_and_recent_failures(storage):
    contract = _contract()
    passing = validate({"order_id": "1"}, contract)
    failing = validate({"other": "x"}, contract)
    storage.record(passing, content={"order_id": "1"})
    storage.record(failing, content={"other": "x"})

    failures = storage.recent_failures("orders", limit=10)
    assert len(failures) == 1
    assert failures[0]["passed"] == 0


def test_window_summary_counts_pass_rate(storage):
    contract = _contract()
    for i in range(3):
        storage.record(validate({"order_id": str(i)}, contract))
    storage.record(validate({}, contract))

    summary = storage.window_summary("orders", limit=10)
    assert summary.total == 4
    assert summary.passed == 3
    assert summary.pass_rate == 0.75


def test_baseline_and_recent_split_by_offset(storage):
    contract = _contract()
    for i in range(10):
        storage.record(validate({"order_id": str(i)}, contract))

    baseline, recent = storage.baseline_and_recent("orders", baseline_window=5, recent_window=5)
    assert recent.total == 5
    assert baseline.total == 5
