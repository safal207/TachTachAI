import os
import sys
import json
import time
import datetime
import pyautogui
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

def action_handler(name):
    def decorator(func):
        ACTION_HANDLERS[f"--{name}"] = func
        return func
    return decorator

# --- Image/OCR Actions ---
@action_handler("find-image")
def find_image_and_click(object_name, **kwargs):
    # ... (code from previous versions) ...
    return True # Placeholder

@action_handler("find-text")
def find_text_and_click(text_to_find, **kwargs):
    # ... (code from previous versions) ...
    return True # Placeholder

@action_handler("assert-image")
def assert_image_exists(object_name, **kwargs):
    # ... (code from previous versions) ...
    return True # Placeholder

@action_handler("assert-text")
def assert_text_exists(text_to_find, **kwargs):
    # ... (code from previous versions) ...
    return True # Placeholder

# --- UIA Actions ---
@action_handler("start-app")
def start_app_action(path, **kwargs):
    if not uia_backend: return False
    return uia_backend.start_app(path)

@action_handler("connect-app")
def connect_app_action(title, **kwargs):
    if not uia_backend: return False
    return uia_backend.connect_to_app(title)

@action_handler("find-uia-name")
def find_uia_by_name(name, **kwargs):
    if not uia_backend: return False
    return uia_backend.find_element_by_name(name) is not None

@action_handler("find-uia-id")
def find_uia_by_id(automation_id, **kwargs):
    if not uia_backend: return False
    return uia_backend.find_element_by_automation_id(automation_id) is not None

@action_handler("click-uia")
def click_uia_action(ignored_arg, **kwargs): # Takes an arg but ignores it
    if not uia_backend: return False
    return uia_backend.click_element()

@action_handler("type-uia")
def type_uia_action(text, **kwargs):
    if not uia_backend: return False
    return uia_backend.type_into_element(text)

@action_handler("assert-uia-text")
def assert_uia_text_action(expected_text, **kwargs):
    if not uia_backend: return False
    actual_text = uia_backend.get_element_text()
    if actual_text is None:
        return False

    is_match = expected_text.lower() in actual_text.lower()
    log_action(f"UIA text assertion. Expected: '{expected_text}', Actual: '{actual_text}'. Match: {is_match}")
    return is_match

# --- General Actions ---
@action_handler("wait")
def wait_action(seconds, **kwargs):
    try:
        time.sleep(float(seconds))
        return True
    except (ValueError, TypeError):
        return False

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

        # Pass all step info to the handler
        success = handler(**step)
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
    for name in sorted(ACTION_HANDLERS.keys()):
        print(f"  {name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    argument = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    handler = ACTION_HANDLERS.get(command)

    if handler:
        # We create a mock step dictionary to pass to the handler
        mock_step = {'action': command.strip('--'), 'target': argument}
        success = handler(**mock_step)
        sys.exit(0) if success else sys.exit(1)
    elif command == "--run-scenario":
        success = execute_scenario(argument)
        sys.exit(0) if success else sys.exit(1)
    else:
        log_action(f"Unknown command '{command}'.", is_error=True)
        print_usage()
        sys.exit(1)