import os
import sys
import json
import time
import datetime
from logger import log_action

# --- Backend Imports ---
# Image/OCR based actions
try:
    import pytesseract
    from PIL import Image, ImageChops
except ImportError:
    pytesseract = None
    log_action("Pillow/pytesseract not found. OCR/Visual Assertions disabled.", is_error=True)

# UI Automation based actions
try:
    import uia_backend
except ImportError:
    uia_backend = None
    log_action("uia_backend.py not found. UIA functionality disabled.", is_error=True)


# --- Constants ---
KB_FILE = os.path.join("knowledge_base", "kb.json")
SCENARIO_FILE = os.path.join("knowledge_base", "scenarios.json")
ENGINE_MODE = os.getenv("SMART_CURSOR_ENGINE", "uia").strip().lower()
SUPPORTED_ENGINES = {"uia", "ocr"}

if ENGINE_MODE not in SUPPORTED_ENGINES:
    log_action(
        f"Unknown SMART_CURSOR_ENGINE='{ENGINE_MODE}'. Falling back to 'uia'.",
        is_error=True,
    )
    ENGINE_MODE = "uia"

# --- Data Loading ---
def get_knowledge_base():
    if not os.path.exists(KB_FILE) or os.path.getsize(KB_FILE) == 0: return {}
    with open(KB_FILE, 'r') as f: return json.load(f)

def get_scenarios():
    if not os.path.exists(SCENARIO_FILE) or os.path.getsize(SCENARIO_FILE) == 0: return {}
    with open(SCENARIO_FILE, 'r') as f: return json.load(f)

# --- Action Implementations ---

# A dictionary to hold all action functions.
# This makes the main execution block cleaner.
ACTION_HANDLERS = {}
ACTION_GROUPS = {
    "general": set(),
    "uia": set(),
    "ocr": set(),
}

def action_handler(name, group="general"):
    def decorator(func):
        command_name = f"--{name}"
        ACTION_HANDLERS[command_name] = func
        ACTION_GROUPS.setdefault(group, set()).add(command_name)
        return func
    return decorator


def _is_command_allowed(command_name):
    if command_name in ACTION_GROUPS["general"]:
        return True
    if ENGINE_MODE == "uia" and command_name in ACTION_GROUPS["uia"]:
        return True
    if ENGINE_MODE == "ocr" and command_name in ACTION_GROUPS["ocr"]:
        return True
    return False


def _available_actions():
    return sorted([name for name in ACTION_HANDLERS.keys() if _is_command_allowed(name)])

# --- Image/OCR Actions ---
@action_handler("find-image", group="ocr")
def find_image_and_click(target, **kwargs):
    object_name = target
    # ... (code from previous versions) ...
    return True # Placeholder

@action_handler("find-text", group="ocr")
def find_text_and_click(target, **kwargs):
    text_to_find = target
    # ... (code from previous versions) ...
    return True # Placeholder

@action_handler("assert-image", group="ocr")
def assert_image_exists(target, **kwargs):
    object_name = target
    # ... (code from previous versions) ...
    return True # Placeholder

@action_handler("assert-text", group="ocr")
def assert_text_exists(target, **kwargs):
    text_to_find = target
    # ... (code from previous versions) ...
    return True # Placeholder

# --- UIA Actions ---
@action_handler("start-app", group="uia")
def start_app_action(target, **kwargs):
    path = target
    if not uia_backend: return False
    return uia_backend.start_app(path)

@action_handler("connect-app", group="uia")
def connect_app_action(target, **kwargs):
    title = target
    if not uia_backend: return False
    return uia_backend.connect_to_app(title)

@action_handler("find-uia-name", group="uia")
def find_uia_by_name(target, **kwargs):
    name = target
    if not uia_backend: return False
    return uia_backend.find_element_by_name(name) is not None

@action_handler("find-uia-id", group="uia")
def find_uia_by_id(target, **kwargs):
    automation_id = target
    if not uia_backend: return False
    return uia_backend.find_element_by_automation_id(automation_id) is not None

@action_handler("click-uia", group="uia")
def click_uia_action(target=None, **kwargs): # Takes an arg but ignores it
    if not uia_backend: return False
    return uia_backend.click_element()

@action_handler("type-uia", group="uia")
def type_uia_action(target, **kwargs):
    text = target
    if not uia_backend: return False
    return uia_backend.type_into_element(text)

@action_handler("assert-uia-text", group="uia")
def assert_uia_text_action(target, **kwargs):
    expected_text = target
    if not uia_backend: return False
    actual_text = uia_backend.get_element_text()
    if actual_text is None:
        return False

    is_match = expected_text.lower() in actual_text.lower()
    log_action(f"UIA text assertion. Expected: '{expected_text}', Actual: '{actual_text}'. Match: {is_match}")
    return is_match

# --- General Actions ---
@action_handler("wait")
def wait_action(target, **kwargs):
    seconds = target
    try:
        time.sleep(float(seconds))
        return True
    except (ValueError, TypeError):
        return False


@action_handler("status")
def status_action(target="", **kwargs):
    """
    Prints runtime status as JSON for external callers (e.g., command_interface).
    """
    status_payload = {
        "timestamp": datetime.datetime.now().isoformat(),
        "engine_mode": ENGINE_MODE,
        "uia_enabled": bool(uia_backend and getattr(uia_backend, "UIA_ENABLED", False)),
        "ocr_enabled": bool(pytesseract),
        "available_actions": _available_actions(),
    }
    print(json.dumps(status_payload))
    return True

# --- Scenario Execution ---
def execute_scenario(scenario_name):
    scenarios = get_scenarios()
    if scenario_name not in scenarios:
        log_action(f"Scenario '{scenario_name}' not found.", is_error=True)
        return False

    steps = scenarios[scenario_name]
    for i, step in enumerate(steps, 1):
        action_name = step.get('action')
        command_name = f"--{action_name}"
        target = step.get('target', '') # Default to empty string

        log_action(f"Executing step {i}/{len(steps)}: {action_name} -> '{target}'")

        handler = ACTION_HANDLERS.get(command_name)
        if not handler:
            log_action(f"Unknown action '{action_name}' in scenario.", is_error=True)
            return False
        if not _is_command_allowed(command_name):
            log_action(
                f"Action '{action_name}' is disabled in engine mode '{ENGINE_MODE}'.",
                is_error=True,
            )
            return False

        handler_kwargs = {k: v for k, v in step.items() if k not in {"action", "target"}}
        try:
            success = handler(target=target, **handler_kwargs)
        except TypeError as exc:
            log_action(
                f"Handler '{action_name}' rejected provided parameters {handler_kwargs}: {exc}",
                is_error=True,
            )
            return False
        except Exception as exc:
            log_action(
                f"Handler '{action_name}' raised an unexpected error: {exc}",
                is_error=True,
            )
            return False

        if not success:
            log_action(f"Scenario '{scenario_name}' failed at step {i}.", is_error=True)
            return False

    log_action(f"--- Successfully completed SCENARIO: '{scenario_name}' ---")
    return True

# --- Main Execution Block ---
def print_usage():
    print("--- Smart Cursor: The Universal Automator ---")
    print("\nUsage: python smart_cursor.py --action_name \"argument\"")
    print("\nAvailable Actions:")
    for name in _available_actions():
        print(f"  {name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    argument = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    handler = ACTION_HANDLERS.get(command)

    if handler:
        if not _is_command_allowed(command):
            log_action(
                f"Command '{command}' is disabled in engine mode '{ENGINE_MODE}'.",
                is_error=True,
            )
            sys.exit(1)
        try:
            success = handler(target=argument)
        except TypeError as exc:
            log_action(
                f"Command '{command}' rejected provided argument '{argument}': {exc}",
                is_error=True,
            )
            sys.exit(1)
        except Exception as exc:
            log_action(
                f"Command '{command}' raised an unexpected error: {exc}",
                is_error=True,
            )
            sys.exit(1)

        sys.exit(0) if success else sys.exit(1)
    elif command == "--run-scenario":
        success = execute_scenario(argument)
        sys.exit(0) if success else sys.exit(1)
    else:
        log_action(f"Unknown command '{command}'.", is_error=True)
        print_usage()
        sys.exit(1)
