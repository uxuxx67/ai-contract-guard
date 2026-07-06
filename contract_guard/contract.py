"""Contract loading and representation.

A Contract describes what a *valid* model response looks like for a given
prompt/use case: an optional JSON schema, required fields, forbidden regex
patterns, a max/min length, and an optional budget (max tokens, latency, cost).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import ContractLoadError

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a declared dependency
    yaml = None


@dataclass
class BudgetSpec:
    max_tokens: Optional[int] = None
    max_latency_ms: Optional[float] = None
    max_cost_usd: Optional[float] = None


@dataclass
class Contract:
    """A single named contract loaded from YAML/JSON."""

    name: str
    description: str = ""
    json_schema: Optional[Dict[str, Any]] = None
    required_fields: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    required_patterns: List[str] = field(default_factory=list)
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    budget: BudgetSpec = field(default_factory=BudgetSpec)
    drift_pass_rate_threshold: float = 0.10
    drift_latency_threshold_pct: float = 0.30
    baseline_window: int = 50
    recent_window: int = 20

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contract":
        if "name" not in data:
            raise ContractLoadError("Contract is missing required field 'name'")
        budget_data = data.get("budget", {}) or {}
        budget = BudgetSpec(
            max_tokens=budget_data.get("max_tokens"),
            max_latency_ms=budget_data.get("max_latency_ms"),
            max_cost_usd=budget_data.get("max_cost_usd"),
        )
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            json_schema=data.get("json_schema"),
            required_fields=data.get("required_fields", []) or [],
            forbidden_patterns=data.get("forbidden_patterns", []) or [],
            required_patterns=data.get("required_patterns", []) or [],
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
            budget=budget,
            drift_pass_rate_threshold=data.get("drift_pass_rate_threshold", 0.10),
            drift_latency_threshold_pct=data.get("drift_latency_threshold_pct", 0.30),
            baseline_window=data.get("baseline_window", 50),
            recent_window=data.get("recent_window", 20),
        )


def load_contract(path: str) -> Contract:
    """Load a Contract from a YAML or JSON file."""
    p = Path(path)
    if not p.exists():
        raise ContractLoadError(f"Contract file not found: {path}")
    text = p.read_text(encoding="utf-8")
    try:
        if p.suffix.lower() in (".yaml", ".yml"):
            if yaml is None:
                raise ContractLoadError("PyYAML is required to load .yaml contracts")
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception as exc:  # noqa: BLE001 - surface as ContractLoadError
        raise ContractLoadError(f"Failed to parse contract {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractLoadError(f"Contract {path} must define a top-level object")
    return Contract.from_dict(data)
