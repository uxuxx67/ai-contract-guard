# Changelog

*[Русская версия](CHANGELOG.ru.md)*

## [0.1.0] - 2026-07-06
### Added
- Initial release: contract model, validator, SQLite-backed history storage
- Drift detection comparing recent window against historical baseline
- Cost/token/latency budget tracking
- Auto-generation of pytest regression tests from stored failures
- CI gate command with configurable exit codes
- Text, JSON, and JUnit XML reporters
- CLI tying together validate / ci-gate / gen-tests / report commands
- Unit test suite for validator, drift, and storage
