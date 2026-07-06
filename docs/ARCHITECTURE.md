# Architecture

*[Русская версия](ARCHITECTURE.ru.md)*

## Data flow
```
response (dict/json) --> validator.validate(contract) --> ValidationResult
                                                                |
                                                                v
                                                   storage.record(result, ...)
                                                                |
                            +-----------------------------------+-------------------------------+
                            |                                                                     |
                            v                                                                     v
                storage.baseline_and_recent()                                     test_generator.generate_tests()
                            |                                                                     |
                            v                                                                     v
             drift.DriftDetector.compare() -> DriftReport                          pytest regression file (text)
```

`ci_gate.run_gate()` orchestrates the above for a batch of responses: it validates each one, records it to storage, checks token/latency/cost budgets, and (if storage has enough history) asks the drift detector to compare a recent window of runs to an older baseline window. The resulting `GateResult` exposes a single `.ok` boolean and `.exit_code()` so it drops straight into any CI system as a shell step.

## Modules

| Module | Responsibility |
|---|---|
| `contract.py` | Parse a YAML/JSON contract file into a `Contract` dataclass |
| `validator.py` | Check one response against a `Contract`, rule by rule |
| `budget.py` | Check tokens/latency/cost against a contract's budget |
| `storage.py` | Persist every run to SQLite; compute window summaries |
| `drift.py` | Compare two `RunSummary` windows and flag regressions |
| `test_generator.py` | Turn stored failures into a pytest file |
| `ci_gate.py` | Tie validator + budget + storage + drift together for a batch |
| `reporters.py` | Render a `GateResult` as text / JSON / JUnit XML |
| `config.py` | Centralized environment-variable configuration |
| `cli.py` | `validate` / `ci-gate` / `gen-tests` command-line commands |

## Design principles

1. **Every rule failure is explainable.** No opaque "quality score" — each rule reports its own pass/fail and message.
2. **History lives in one place (SQLite)**, so drift detection and test generation both read from the same source of truth.
3. **No network calls in the core library.** `contract_guard` observes and judges responses you already have; fetching those responses from your LLM provider is your integration's job, not this library's.
4. **CI-first.** The primary interface is a CLI command with a meaningful exit code, so it works with any CI system without extra plumbing.
