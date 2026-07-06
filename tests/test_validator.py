from contract_guard.contract import Contract
from contract_guard.validator import validate


def _contract(**overrides):
    base = dict(name="test", required_fields=[], forbidden_patterns=[], required_patterns=[])
    base.update(overrides)
    return Contract(**base)


def test_required_fields_pass():
    contract = _contract(required_fields=["answer"])
    result = validate({"answer": "42"}, contract)
    assert result.passed


def test_required_fields_fail_when_missing():
    contract = _contract(required_fields=["answer"])
    result = validate({"other": "x"}, contract)
    assert not result.passed
    assert any(r.rule == "required_field:answer" for r in result.failed_rules())


def test_forbidden_pattern_fails_on_match():
    contract = _contract(forbidden_patterns=[r"as an ai language model"])
    result = validate("As an AI language model, I cannot help.", contract)
    assert not result.passed


def test_forbidden_pattern_passes_without_match():
    contract = _contract(forbidden_patterns=[r"as an ai language model"])
    result = validate("Here is your answer: 42", contract)
    assert result.passed


def test_required_pattern_must_be_present():
    contract = _contract(required_patterns=[r"\bSKU-\d+\b"])
    assert not validate("no sku here", contract).passed
    assert validate("Your order is SKU-1234", contract).passed


def test_length_bounds():
    contract = _contract(min_length=5, max_length=10)
    assert not validate("hi", contract).passed
    assert validate("hello!", contract).passed
    assert not validate("way too long a string", contract).passed


def test_json_schema_validation():
    schema = {"type": "object", "properties": {"count": {"type": "integer"}}, "required": ["count"]}
    contract = _contract(json_schema=schema)
    assert validate({"count": 3}, contract).passed
    assert not validate({"count": "three"}, contract).passed
