"""Command-line entry point for AI Contract Guard.

Commands:
  validate <contract> <response.json>          - validate one response
  ci-gate  <contract> <responses.jsonl>        - batch validate + drift/budget gate
  gen-tests <contract> --out <file.py>         - generate regression tests from failures
  report   <contract> --format text|json|junit - re-render the last gate result
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Iterable

from .ci_gate import run_gate
from .config import Config
from .contract import load_contract
from .reporters import RENDERERS
from .storage import Storage
from .test_generator import generate_tests
from .validator import validate as validate_one


def _read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def cmd_validate(args: argparse.Namespace) -> int:
    contract = load_contract(args.contract)
    with open(args.response, "r", encoding="utf-8") as f:
        content = json.load(f)
    result = validate_one(content, contract)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.passed else 1


def cmd_ci_gate(args: argparse.Namespace) -> int:
    config = Config.from_env()
    contract = load_contract(args.contract)
    storage = Storage(config.db_path)
    responses = list(_read_jsonl(args.responses))
    result = run_gate(contract, responses, storage=storage, check_drift=config.check_drift)
    renderer = RENDERERS.get(args.format or config.default_report_format, RENDERERS["text"])
    print(renderer(result))
    return result.exit_code()


def cmd_gen_tests(args: argparse.Namespace) -> int:
    config = Config.from_env()
    contract = load_contract(args.contract)
    storage = Storage(config.db_path)
    text = generate_tests(storage, args.contract, contract.name, limit=args.limit)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Wrote regression tests to {args.out}")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="contract_guard", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate one response against a contract")
    p_validate.add_argument("contract")
    p_validate.add_argument("response")
    p_validate.set_defaults(func=cmd_validate)

    p_gate = sub.add_parser("ci-gate", help="batch validate + drift/budget gate for CI")
    p_gate.add_argument("contract")
    p_gate.add_argument("responses", help="JSONL file, one response object per line")
    p_gate.add_argument("--format", choices=list(RENDERERS.keys()), default=None)
    p_gate.set_defaults(func=cmd_ci_gate)

    p_gen = sub.add_parser("gen-tests", help="generate pytest regression tests from stored failures")
    p_gen.add_argument("contract")
    p_gen.add_argument("--out", default=None)
    p_gen.add_argument("--limit", type=int, default=20)
    p_gen.set_defaults(func=cmd_gen_tests)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
