"""Cost, token, and latency budget tracking for a single response."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .contract import BudgetSpec


@dataclass
class BudgetResult:
    within_budget: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self):
        return {"within_budget": self.within_budget, "violations": self.violations}


class BudgetTracker:
    """Checks a single response's tokens/latency/cost against a contract's BudgetSpec."""

    def __init__(self, spec: BudgetSpec):
        self.spec = spec

    def check(
        self,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[float] = None,
        cost_usd: Optional[float] = None,
    ) -> BudgetResult:
        violations: List[str] = []
        if self.spec.max_tokens is not None and tokens_used is not None and tokens_used > self.spec.max_tokens:
            violations.append(f"tokens_used {tokens_used} exceeds max_tokens {self.spec.max_tokens}")
        if (
            self.spec.max_latency_ms is not None
            and latency_ms is not None
            and latency_ms > self.spec.max_latency_ms
        ):
            violations.append(f"latency_ms {latency_ms} exceeds max_latency_ms {self.spec.max_latency_ms}")
        if self.spec.max_cost_usd is not None and cost_usd is not None and cost_usd > self.spec.max_cost_usd:
            violations.append(f"cost_usd {cost_usd} exceeds max_cost_usd {self.spec.max_cost_usd}")
        return BudgetResult(within_budget=not violations, violations=violations)
