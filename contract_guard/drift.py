"""Drift detection: compares a recent window of runs against a historical baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .models import RunSummary


@dataclass
class DriftReport:
    contract_name: str
    drifted: bool
    pass_rate_baseline: float
    pass_rate_recent: float
    pass_rate_drop: float
    latency_baseline_ms: Optional[float]
    latency_recent_ms: Optional[float]
    latency_increase_pct: Optional[float]
    reasons: List[str]

    def to_dict(self):
        return {
            "contract": self.contract_name,
            "drifted": self.drifted,
            "pass_rate_baseline": round(self.pass_rate_baseline, 4),
            "pass_rate_recent": round(self.pass_rate_recent, 4),
            "pass_rate_drop": round(self.pass_rate_drop, 4),
            "latency_baseline_ms": self.latency_baseline_ms,
            "latency_recent_ms": self.latency_recent_ms,
            "latency_increase_pct": self.latency_increase_pct,
            "reasons": self.reasons,
        }


class DriftDetector:
    """Compares a baseline RunSummary against a more recent RunSummary and flags drift.

    Drift is flagged when either:
      - pass rate drops by more than `pass_rate_threshold` (absolute), or
      - average latency increases by more than `latency_threshold_pct` (relative)
    relative to the baseline window.
    """

    def __init__(self, pass_rate_threshold: float = 0.10, latency_threshold_pct: float = 0.30):
        self.pass_rate_threshold = pass_rate_threshold
        self.latency_threshold_pct = latency_threshold_pct

    def compare(self, baseline: RunSummary, recent: RunSummary) -> DriftReport:
        reasons: List[str] = []
        pass_rate_drop = baseline.pass_rate - recent.pass_rate
        if pass_rate_drop > self.pass_rate_threshold:
            reasons.append(
                f"pass rate dropped {pass_rate_drop:.1%} "
                f"(baseline {baseline.pass_rate:.1%} -> recent {recent.pass_rate:.1%})"
            )

        latency_increase_pct = None
        if baseline.avg_latency_ms and recent.avg_latency_ms is not None:
            latency_increase_pct = (recent.avg_latency_ms - baseline.avg_latency_ms) / baseline.avg_latency_ms
            if latency_increase_pct > self.latency_threshold_pct:
                reasons.append(
                    f"latency increased {latency_increase_pct:.1%} "
                    f"(baseline {baseline.avg_latency_ms:.0f}ms -> recent {recent.avg_latency_ms:.0f}ms)"
                )

        return DriftReport(
            contract_name=baseline.contract_name,
            drifted=bool(reasons),
            pass_rate_baseline=baseline.pass_rate,
            pass_rate_recent=recent.pass_rate,
            pass_rate_drop=pass_rate_drop,
            latency_baseline_ms=baseline.avg_latency_ms,
            latency_recent_ms=recent.avg_latency_ms,
            latency_increase_pct=latency_increase_pct,
            reasons=reasons,
        )
