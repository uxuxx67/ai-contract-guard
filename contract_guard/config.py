"""Configuration loading: environment variables with sane defaults.

Keeps configuration explicit and centralized rather than scattering
os.environ.get() calls across modules.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    db_path: str = "contract_guard.db"
    default_report_format: str = "text"
    check_drift: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            db_path=os.environ.get("CONTRACT_GUARD_DB", "contract_guard.db"),
            default_report_format=os.environ.get("CONTRACT_GUARD_REPORT_FORMAT", "text"),
            check_drift=os.environ.get("CONTRACT_GUARD_CHECK_DRIFT", "1") not in ("0", "false", "False"),
        )
