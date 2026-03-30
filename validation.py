"""
Validation helpers for scenarios and command payloads.

Production goal: fail-fast on malformed inputs instead of propagating
runtime errors deep in execution flow.
"""

from typing import Any


VALID_ACTIONS = {
    "wait",
    "find-image",
    "find-text",
    "assert-image",
    "assert-text",
    "start-app",
    "connect-app",
    "find-uia-name",
    "find-uia-id",
    "type-uia",
    "click-uia",
    "assert-uia-text",
}


VALID_COMMANDS = {
    "run_tests",
    "run_tests_with_data",
    "create_scenario",
    "update_baseline",
    "create_performance_baseline",
    "get_status",
}


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_step(step: Any) -> tuple[bool, str | None]:
    if not isinstance(step, dict):
        return False, "Each step must be an object."

    action = step.get("action")
    if action not in VALID_ACTIONS:
        return False, f"Unknown or missing step action: {action}"

    if "target" not in step:
        return False, "Each step must include 'target'."

    if not isinstance(step.get("target"), (str, int, float)):
        return False, "Step 'target' must be string/number."

    if "timeout" in step:
        timeout = step["timeout"]
        if not isinstance(timeout, (int, float, str)):
            return False, "Step 'timeout' must be int/float/string."

    return True, None


def validate_steps(steps: Any) -> tuple[bool, str | None]:
    if not isinstance(steps, list) or not steps:
        return False, "Scenario steps must be a non-empty list."

    for idx, step in enumerate(steps, start=1):
        ok, error = validate_step(step)
        if not ok:
            return False, f"Invalid step #{idx}: {error}"

    return True, None


def validate_scenarios_payload(payload: Any) -> tuple[bool, str | None]:
    if not isinstance(payload, dict):
        return False, "Scenarios file must contain an object (name -> steps)."

    for name, steps in payload.items():
        if not _is_non_empty_string(name):
            return False, "Scenario names must be non-empty strings."
        ok, error = validate_steps(steps)
        if not ok:
            return False, f"Scenario '{name}': {error}"

    return True, None


def validate_command_payload(command_data: Any) -> tuple[bool, str | None]:
    if not isinstance(command_data, dict):
        return False, "Command payload must be a JSON object."

    command_name = command_data.get("command")
    if command_name not in VALID_COMMANDS:
        return False, f"Unknown or missing command: {command_name}"

    params = command_data.get("params", {})
    if not isinstance(params, dict):
        return False, "Command 'params' must be an object."

    return True, None
