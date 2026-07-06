"""SQLite-backed history of validation runs, used for drift detection and test generation."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional

from .exceptions import StorageError
from .models import RunSummary
from .validator import ValidationResult


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_name TEXT NOT NULL,
    passed INTEGER NOT NULL,
    content_json TEXT,
    rules_json TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    latency_ms REAL,
    cost_usd REAL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_contract_created ON runs (contract_name, created_at);
"""


class Storage:
    """Thin wrapper around a SQLite database storing validation run history."""

    def __init__(self, db_path: str = "contract_guard.db"):
        self.db_path = db_path
        try:
            with self._connect() as conn:
                conn.executescript(SCHEMA)
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to initialize storage at {db_path}: {exc}") from exc

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def record(
        self,
        result: ValidationResult,
        content: Any = None,
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[float] = None,
        cost_usd: Optional[float] = None,
    ) -> int:
        rules_json = json.dumps([{"rule": r.rule, "passed": r.passed, "message": r.message} for r in result.rules])
        content_json = json.dumps(content) if content is not None else None
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO runs
                   (contract_name, passed, content_json, rules_json, model, tokens_used, latency_ms, cost_usd, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result.contract_name,
                    1 if result.passed else 0,
                    content_json,
                    rules_json,
                    model,
                    tokens_used,
                    latency_ms,
                    cost_usd,
                    datetime.utcnow().isoformat(),
                ),
            )
            return cur.lastrowid

    def recent_failures(self, contract_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM runs WHERE contract_name = ? AND passed = 0
                   ORDER BY created_at DESC LIMIT ?""",
                (contract_name, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def window_summary(self, contract_name: str, limit: int, offset: int = 0) -> RunSummary:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM runs WHERE contract_name = ?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (contract_name, limit, offset),
            ).fetchall()
        total = len(rows)
        passed = sum(1 for r in rows if r["passed"])
        latencies = [r["latency_ms"] for r in rows if r["latency_ms"] is not None]
        costs = [r["cost_usd"] for r in rows if r["cost_usd"] is not None]
        now = datetime.utcnow()
        return RunSummary(
            contract_name=contract_name,
            total=total,
            passed=passed,
            avg_latency_ms=(sum(latencies) / len(latencies)) if latencies else None,
            avg_cost_usd=(sum(costs) / len(costs)) if costs else None,
            window_start=now - timedelta(days=1),
            window_end=now,
        )

    def baseline_and_recent(self, contract_name: str, baseline_window: int, recent_window: int):
        recent = self.window_summary(contract_name, limit=recent_window, offset=0)
        baseline = self.window_summary(contract_name, limit=baseline_window, offset=recent_window)
        return baseline, recent
