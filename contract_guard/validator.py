"""Validates a single response against a Contract."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contract import Contract
from .models import RuleOutcome

try:
    import jsonschema
except ImportError:  # pragma: no cover - declared dependency
    jsonschema = None


@dataclass
class RuleResult:
    rule: str
    passed: bool
    message: str = ""


@dataclass
class ValidationResult:
    contract_name: str
    passed: bool
    rules: List[RuleResult] = field(default_factory=list)

    def failed_rules(self) -> List[RuleResult]:
        return [r for r in self.rules if not r.passed]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract": self.contract_name,
            "passed": self.passed,
            "rules": [{"rule": r.rule, "passed": r.passed, "message": r.message} for r in self.rules],
        }


def _as_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, (dict, list)):
        import json

        return json.dumps(content)
    return str(content)


def _check_schema(content: Any, schema: Optional[Dict[str, Any]]) -> RuleResult:
    if schema is None:
        return RuleResult("json_schema", True, "no schema configured")
    if jsonschema is None:
        return RuleResult("json_schema", False, "jsonschema package not installed")
    try:
        jsonschema.validate(instance=content, schema=schema)
        return RuleResult("json_schema", True)
    except Exception as exc:  # noqa: BLE001
        return RuleResult("json_schema", False, str(exc))


def _check_required_fields(content: Any, fields: List[str]) -> List[RuleResult]:
    results = []
    if not fields:
        return results
    if not isinstance(content, dict):
        return [RuleResult(f"required_field:{f}", False, "content is not an object") for f in fields]
    for f in fields:
        present = f in content and content[f] not in (None, "")
        results.append(RuleResult(f"required_field:{f}", present, "" if present else "field missing or empty"))
    return results


def _check_forbidden_patterns(text: str, patterns: List[str]) -> List[RuleResult]:
    results = []
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        results.append(RuleResult(f"forbidden_pattern:{pattern}", match is None, f"matched: {match.group(0)}" if match else ""))
    return results


def _check_required_patterns(text: str, patterns: List[str]) -> List[RuleResult]:
    results = []
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        results.append(RuleResult(f"required_pattern:{pattern}", match is not None, "" if match else "pattern not found"))
    return results


def _check_length(text: str, min_length: Optional[int], max_length: Optional[int]) -> List[RuleResult]:
    results = []
    if min_length is not None:
        ok = len(text) >= min_length
        results.append(RuleResult("min_length", ok, "" if ok else f"length {len(text)} < {min_length}"))
    if max_length is not None:
        ok = len(text) <= max_length
        results.append(RuleResult("max_length", ok, "" if ok else f"length {len(text)} > {max_length}"))
    return results


def validate(content: Any, contract: Contract) -> ValidationResult:
    """Validate `content` (a parsed response payload) against `contract`."""
    text = _as_text(content)
    rules: List[RuleResult] = [_check_schema(content, contract.json_schema)]
    rules += _check_required_fields(content, contract.required_fields)
    rules += _check_forbidden_patterns(text, contract.forbidden_patterns)
    rules += _check_required_patterns(text, contract.required_patterns)
    rules += _check_length(text, contract.min_length, contract.max_length)
    passed = all(r.passed for r in rules)
    return ValidationResult(contract_name=contract.name, passed=passed, rules=rules)
