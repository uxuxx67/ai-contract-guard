"""Render validation/gate results as text, JSON, or JUnit XML."""
from __future__ import annotations

import json
from xml.sax.saxutils import escape

from .ci_gate import GateResult


def render_text(result: GateResult) -> str:
    lines = [
        f"Contract: {result.contract_name}",
        f"Total: {result.total}  Passed: {result.passed}  Failed: {result.failed}",
        f"Budget violations: {result.budget_violations}",
    ]
    if result.drift is not None:
        lines.append(f"Drift detected: {result.drift.drifted}")
        for reason in result.drift.reasons:
            lines.append(f"  - {reason}")
    lines.append("PASS" if result.ok else "FAIL")
    return "\n".join(lines)


def render_json(result: GateResult) -> str:
    payload = {
        "contract": result.contract_name,
        "total": result.total,
        "passed": result.passed,
        "failed": result.failed,
        "budget_violations": result.budget_violations,
        "ok": result.ok,
        "drift": result.drift.to_dict() if result.drift else None,
        "results": [r.to_dict() for r in result.results],
    }
    return json.dumps(payload, indent=2)


def render_junit(result: GateResult) -> str:
    cases = []
    for i, r in enumerate(result.results):
        name = f"{escape(result.contract_name)}.case_{i}"
        if r.passed:
            cases.append(f'  <testcase classname="contract_guard" name="{name}"/>')
        else:
            messages = "; ".join(escape(rule.message) for rule in r.failed_rules())
            cases.append(
                f'  <testcase classname="contract_guard" name="{name}">'
                f'<failure message="{escape(messages)}"/></testcase>'
            )
    body = "\n".join(cases)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="{escape(result.contract_name)}" tests="{result.total}" '
        f'failures="{result.failed}">\n{body}\n</testsuite>\n'
    )


RENDERERS = {"text": render_text, "json": render_json, "junit": render_junit}
