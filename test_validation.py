import pytest

from validation import (
    validate_step,
    validate_steps,
    validate_scenarios_payload,
    validate_command_payload,
)


def test_validate_step_ok():
    ok, err = validate_step({"action": "wait", "target": "1"})
    assert ok is True
    assert err is None


def test_validate_step_missing_action():
    ok, err = validate_step({"target": "1"})
    assert ok is False
    assert "action" in err


def test_validate_steps_empty():
    ok, err = validate_steps([])
    assert ok is False
    assert "non-empty list" in err


def test_validate_scenarios_payload_ok():
    payload = {"smoke": [{"action": "wait", "target": "1"}]}
    ok, err = validate_scenarios_payload(payload)
    assert ok is True
    assert err is None


def test_validate_command_payload_unknown():
    ok, err = validate_command_payload({"command": "unknown", "params": {}})
    assert ok is False
    assert "Unknown or missing command" in err


def test_validate_command_payload_ok():
    ok, err = validate_command_payload({"command": "get_status", "params": {}})
    assert ok is True
    assert err is None
