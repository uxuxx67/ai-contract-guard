"""CI/CD gate: validate a batch of responses against a contract and decide pass/fail.

Designed to be wired into any CI system: run it as a step, and let its exit
code gate the deploy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .budget import BudgetTracker
from .contract import Contract
from .drift import DriftDetector, DriftReport
from .models import ResponseRecord
from .storage import Storage
from .validator import ValidationResult, validate


@dataclass
class GateResult:
    contract_name: str
    total: int
    passed: int
    failed: int
    budget_violations: int
    drift: Optional[DriftReport]
    results: List[ValidationResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        no_drift = self.drift is None or not self.drift.drifted
        return self.failed == 0 and self.budget_violations == 0 and no_drift

    def exit_code(self) -> int:
        return 0 if self.ok else 1


def run_gate(
    contract: Contract,
    responses: Iterable[Dict[str, Any]],
    storage: Optional[Storage] = None,
    check_drift: bool = True,
) -> GateResult:
    """Validate every response in `responses` against `contract`, record to storage
    if provided, and optionally check for drift against stored history.
    """
    budget_tracker = BudgetTracker(contract.budget)
    results: List[ValidationResult] = []
    budget_violations = 0

    for raw in responses:
        record = ResponseRecord.from_dict(raw)
        result = validate(record.content, contract)
        results.append(result)

        budget_result = budget_tracker.check(
            tokens_used=record.tokens_used, latency_ms=record.latency_ms, cost_usd=record.cost_usd
        )
        if not budget_result.within_budget:
            budget_violations += 1

        if storage is not None:
            storage.record(
                result,
                content=record.content,
                model=record.model,
                tokens_used=record.tokens_used,
                latency_ms=record.latency_ms,
                cost_usd=record.cost_usd,
            )

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    drift_report = None
    if check_drift and storage is not None:
        baseline, recent = storage.baseline_and_recent(
            contract.name, contract.baseline_window, contract.recent_window
        )
        if baseline.total > 0 and recent.total > 0:
            detector = DriftDetector(
                pass_rate_threshold=contract.drift_pass_rate_threshold,
                latency_threshold_pct=contract.drift_latency_threshold_pct,
            )
            drift_report = detector.compare(baseline, recent)

    return GateResult(
        contract_name=contract.name,
        total=len(results),
        passed=passed,
        failed=failed,
        budget_violations=budget_violations,
        drift=drift_report,
        results=results,
    )
