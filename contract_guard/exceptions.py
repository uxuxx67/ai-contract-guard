"""Exception hierarchy for AI Contract Guard."""


class ContractGuardError(Exception):
    """Base class for all contract_guard errors."""


class ContractLoadError(ContractGuardError):
    """Raised when a contract file cannot be parsed or fails structural checks."""


class ValidationError(ContractGuardError):
    """Raised for programmer errors while validating a response (not for rule failures,
    which are reported as a ValidationResult instead of raised)."""


class StorageError(ContractGuardError):
    """Raised when the SQLite-backed history store cannot be read or written."""


class BudgetExceededError(ContractGuardError):
    """Optionally raised by strict budget checks; normally budgets report instead of raise."""
