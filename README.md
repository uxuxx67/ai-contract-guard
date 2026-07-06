# AI Contract Guard

*[Русская версия](README.ru.md)*

Contract testing for LLM integrations — the missing safety net between your prompts and production. Define a **contract** for what a model response must look like (schema, required fields, forbidden patterns, tone, cost/latency budget), then let AI Contract Guard catch silent drift when a provider quietly changes model behavior, auto-generate regression tests from real failures, and gate CI/CD deploys before a bad prompt or model swap reaches users.

## Why

Unlike a normal API, an LLM's output is not guaranteed stable across model versions, temperature, or provider-side updates. Teams usually notice "the AI got worse" only after users complain. AI Contract Guard borrows the idea of **contract testing** (like Pact for REST APIs) and applies it to AI: your contract is the source of truth, and every response — in dev or in prod — is checked against it, with history stored so drift over time is visible, not anecdotal.

## Core ideas

1. **Contracts** — YAML/JSON documents describing what a *valid* response for a given prompt/use case looks like: JSON schema, required fields, forbidden regex patterns, max tokens, max latency, max cost.
2. **Validator** — checks a single response against a contract, returns a structured `ValidationResult` with pass/fail per rule.
3. **Storage** — every validation run is persisted to SQLite, building a history per contract.
4. **Drift detector** — compares recent pass-rate/latency/cost against a historical baseline window and flags statistically meaningful regressions.
5. **Test generator** — turns real failed validations into ready-to-commit pytest regression tests, so failures never repeat silently.
6. **CI gate** — a single CLI command that runs contracts against a batch of responses (e.g. from your eval suite) and exits non-zero if drift/budget thresholds are breached, so you can wire it into any CI pipeline.

## Quick start

```bash
pip install -r requirements.txt

# Validate one response against a contract
python -m contract_guard.cli validate examples/example_contract.yaml response.json

# Run the CI gate against a batch of responses
python -m contract_guard.cli ci-gate examples/example_contract.yaml responses.jsonl

# Generate a regression test file from stored failures
python -m contract_guard.cli gen-tests examples/example_contract.yaml --out tests/test_regressions.py
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a full breakdown of the module layout and data flow.

## Files

- `contract_guard/contract.py` — contract loading/parsing (YAML/JSON -> `Contract`)
- `contract_guard/validator.py` — validates a response dict against a `Contract`
- `contract_guard/drift.py` — baseline vs. recent-window drift detection
- `contract_guard/storage.py` — SQLite-backed history of validation runs
- `contract_guard/budget.py` — cost/token/latency budget tracking
- `contract_guard/test_generator.py` — auto-generates pytest tests from failures
- `contract_guard/ci_gate.py` — CI/CD gate: run + decide pass/fail + exit code
- `contract_guard/reporters.py` — text/JSON/JUnit XML report rendering
- `contract_guard/config.py` — config loading (env vars + file)
- `contract_guard/cli.py` — command-line entry point tying it all together
- `tests/` — unit tests for validator, drift, storage
- `examples/example_contract.yaml` — a fully worked example contract

## Roadmap

- Native adapters for OpenAI/Anthropic/Gemini response objects
- Web dashboard for drift history
- Slack/webhook alerting on drift detection
- Contract versioning and diffing

## License

MIT — see [LICENSE](LICENSE).
