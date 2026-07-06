"""Shared dataclasses used across contract_guard modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ResponseRecord:
    """A single model response being evaluated, plus metadata used for budget checks."""

    content: Any
    prompt_id: str = "default"
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseRecord":
        return cls(
            content=data.get("content"),
            prompt_id=data.get("prompt_id", "default"),
            model=data.get("model"),
            tokens_used=data.get("tokens_used"),
            latency_ms=data.get("latency_ms"),
            cost_usd=data.get("cost_usd"),
            raw=data,
        )


@dataclass
class RuleOutcome:
    """Result of a single contract rule check."""

    rule: str
    passed: bool
    message: str = ""


@dataclass
class RunSummary:
    """Aggregate summary of a batch of validation runs, used by drift detection."""

    contract_name: str
    total: int
    passed: int
    avg_latency_ms: Optional[float]
    avg_cost_usd: Optional[float]
    window_start: datetime
    window_end: datetime

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0
