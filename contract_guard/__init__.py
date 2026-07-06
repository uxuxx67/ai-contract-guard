"""AI Contract Guard - contract testing for LLM integrations.

Public API re-exports for convenience:

    from contract_guard import Contract, validate, DriftDetector, Storage
"""
from .contract import Contract, load_contract
from .validator import validate, ValidationResult, RuleResult
from .drift import DriftDetector, DriftReport
from .storage import Storage
from .budget import BudgetTracker, BudgetResult
from .exceptions import ContractGuardError, ContractLoadError, ValidationError

__version__ = "0.1.0"

__all__ = [
    "Contract",
    "load_contract",
    "validate",
    "ValidationResult",
    "RuleResult",
    "DriftDetector",
    "DriftReport",
    "Storage",
    "BudgetTracker",
    "BudgetResult",
    "ContractGuardError",
    "ContractLoadError",
    "ValidationError",
]
