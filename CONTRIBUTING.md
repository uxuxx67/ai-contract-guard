# Contributing to AI Contract Guard

*[Русская версия](CONTRIBUTING.ru.md)*

Thanks for considering a contribution! This project favors explicit, auditable rules over opaque scoring — every validation failure should be traceable to a specific contract rule.

## Adding a validation rule type

1. Extend `Contract` in `contract.py` with the new rule field.
2. Implement the check in `validator.py`, returning a clear `RuleResult` (rule name, passed, message).
3. Add test cases in `tests/test_validator.py` covering pass and fail paths.

## Drift detection changes

Changes to `drift.py` should include before/after examples in the PR description and should not silently change existing default thresholds without a CHANGELOG entry.

## Code style

Keep `contract_guard/` free of network calls — this project observes and evaluates responses you already have; it does not call model APIs itself. Adapters that fetch responses belong in your own integration code, not in this core library.

## Tests

Run `pytest` before opening a PR. New features should ship with tests.
