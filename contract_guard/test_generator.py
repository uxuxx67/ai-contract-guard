"""Auto-generates pytest regression tests from stored validation failures.

The idea: every time a real response fails a contract in production, that
exact failure becomes a permanent regression test, so the same bug/drift can
never silently reappear unnoticed.
"""
from __future__ import annotations

import json
from typing import List

from .storage import Storage


_TEST_FILE_HEADER = '''"""Auto-generated regression tests from contract_guard failures.

Do not hand-edit sections between AUTO-GENERATED markers; re-run
`contract_guard gen-tests` to refresh this file.
"""
import json

from contract_guard.contract import load_contract
from contract_guard.validator import validate

'''


def _sanitize_name(raw: str, index: int) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in raw)
    return f"test_regression_{index}_{cleaned}"[:80]


def generate_tests(storage: Storage, contract_path: str, contract_name: str, limit: int = 20) -> str:
    """Return the full text of a pytest module covering recent failures for a contract."""
    failures = storage.recent_failures(contract_name, limit=limit)
    lines: List[str] = [_TEST_FILE_HEADER]
    lines.append(f'CONTRACT_PATH = "{contract_path}"\n')
    if not failures:
        lines.append("# No stored failures yet - nothing to generate.\n")
        return "".join(lines)

    for i, failure in enumerate(failures, start=1):
        content = failure.get("content_json")
        rules = json.loads(failure["rules_json"])
        failed_rules = [r["rule"] for r in rules if not r["passed"]]
        test_name = _sanitize_name(failure.get("model") or "unknown", i)
        lines.append(f"\n\ndef {test_name}():\n")
        lines.append(f'    """Regression test for run #{failure["id"]} (failed rules: {failed_rules})."""\n')
        lines.append(f"    contract = load_contract(CONTRACT_PATH)\n")
        lines.append(f"    content = json.loads({content!r})\n" if content else "    content = None\n")
        lines.append("    result = validate(content, contract)\n")
        lines.append(
            "    # This response failed before; once fixed, this asserts it now passes.\n"
            "    assert result.passed, [r.message for r in result.failed_rules()]\n"
        )
    return "".join(lines)
