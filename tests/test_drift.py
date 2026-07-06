from datetime import datetime

from contract_guard.drift import DriftDetector
from contract_guard.models import RunSummary


def _summary(total, passed, avg_latency_ms=100.0):
    now = datetime.utcnow()
    return RunSummary(
        contract_name="test",
        total=total,
        passed=passed,
        avg_latency_ms=avg_latency_ms,
        avg_cost_usd=0.01,
        window_start=now,
        window_end=now,
    )


def test_no_drift_when_stable():
    baseline = _summary(50, 48)
    recent = _summary(20, 19)
    report = DriftDetector().compare(baseline, recent)
    assert not report.drifted


def test_drift_detected_on_pass_rate_drop():
    baseline = _summary(50, 48)  # 96%
    recent = _summary(20, 10)  # 50%
    report = DriftDetector(pass_rate_threshold=0.10).compare(baseline, recent)
    assert report.drifted
    assert any("pass rate dropped" in r for r in report.reasons)


def test_drift_detected_on_latency_increase():
    baseline = _summary(50, 50, avg_latency_ms=100.0)
    recent = _summary(20, 20, avg_latency_ms=200.0)
    report = DriftDetector(latency_threshold_pct=0.30).compare(baseline, recent)
    assert report.drifted
    assert any("latency increased" in r for r in report.reasons)


def test_latency_increase_within_threshold_is_not_drift():
    baseline = _summary(50, 50, avg_latency_ms=100.0)
    recent = _summary(20, 20, avg_latency_ms=110.0)
    report = DriftDetector(latency_threshold_pct=0.30).compare(baseline, recent)
    assert not report.drifted
