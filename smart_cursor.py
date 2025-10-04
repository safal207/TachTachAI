import pyautogui
import json
import os
import sys
import time
import datetime
from logger import log_action

try:
    import pytesseract
    from PIL import Image, ImageChops
except ImportError:
    log_action("Warning: 'pytesseract' or 'Pillow' not found. OCR and Visual Assertions will not work.", is_error=True)
    pytesseract = None

# --- Constants ---
KB_FILE = os.path.join("knowledge_base", "kb.json")
SCENARIO_FILE = os.path.join("knowledge_base", "scenarios.json")
SCREENSHOTS_DIR = os.path.join("reports", "screenshots")

# --- Data Loading Functions ---
def get_knowledge_base():
    if not os.path.exists(KB_FILE) or os.path.getsize(KB_FILE) == 0: return {}
    with open(KB_FILE, 'r') as f: return json.load(f)

def get_scenarios():
    if not os.path.exists(SCENARIO_FILE) or os.path.getsize(SCENARIO_FILE) == 0: return {}
    with open(SCENARIO_FILE, 'r') as f: return json.load(f)

# --- Core Action Functions ---
def find_image_and_click(object_name, should_log=True):
    if should_log: log_action(f"ACTION: Find and click IMAGE '{object_name}'")
    location = assert_image_exists(object_name, should_log=False)
    if location:
        pyautogui.click(location)
        log_action(f"SUCCESS: Clicked image '{object_name}' at {location}.")
        return True
    else:
        log_action(f"FAILURE: Could not find image '{object_name}' to click.", is_error=True)
        return False

def find_text_and_click(text_to_find, should_log=True):
    if should_log: log_action(f"ACTION: Find and click TEXT '{text_to_find}'")
    location = assert_text_exists(text_to_find, should_log=False)
    if location:
        pyautogui.click(location)
        log_action(f"SUCCESS: Clicked text '{text_to_find}' at {location}.")
        return True
    else:
        log_action(f"FAILURE: Could not find text '{text_to_find}' to click.", is_error=True)
        return False

def assert_image_exists(object_name, should_log=True):
    """
    Checks if a pre-learned image exists on screen, returns its location or None.
    Includes self-healing by trying a lower confidence if the first attempt fails.
    """
    if should_log: log_action(f"ASSERTION: Check for IMAGE '{object_name}'")
    kb = get_knowledge_base()
    if object_name not in kb:
        log_action(f"Object '{object_name}' not in knowledge base.", is_error=True)
        return None
    image_path = kb[object_name]

    try:
        # 1. First attempt with high confidence
        location = pyautogui.locateCenterOnScreen(image_path, confidence=0.9)
        if location:
            log_action(f"SUCCESS: Found image '{object_name}' at {location} (confidence=0.9).")
            return location

        # 2. Self-healing: wait and try again with lower confidence
        if should_log: log_action(f"Self-healing: Retrying with lower confidence for '{object_name}'...")
        time.sleep(1)
        location = pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
        if location:
            log_action(f"SELF-HEALED: Found image '{object_name}' at {location} (confidence=0.8).")
            return location

        if should_log: log_action(f"FAILURE: Did not find image '{object_name}' after self-healing.", is_error=True)
        return None

    except Exception as e:
        log_action(f"Error during image assertion for '{object_name}': {e}", is_error=True)
        return None

def assert_text_exists(text_to_find, should_log=True):
    """
    Checks if text exists on screen, returns its location or None.
    Includes a simple self-healing retry mechanism.
    """
    if should_log: log_action(f"ASSERTION: Check for TEXT '{text_to_find}'")
    if pytesseract is None:
        log_action("OCR libraries missing.", is_error=True)
        return None

    def _find_text_internal():
        try:
            ocr_data = pytesseract.image_to_data(pyautogui.screenshot(), output_type=pytesseract.Output.DICT)
            for i, fragment in enumerate(ocr_data['text']):
                if int(ocr_data['conf'][i]) > 60 and text_to_find.lower() in fragment.lower():
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    return (x + w // 2, y + h // 2)
            return None
        except Exception as e:
            # This internal error should be logged but not double-log the failure message
            log_action(f"Error during internal OCR call: {e}", is_error=True)
            return None

    # First attempt
    location = _find_text_internal()
    if location:
        log_action(f"SUCCESS: Found text '{text_to_find}' near {location}.")
        return location

    # Self-healing attempt
    if should_log: log_action(f"Self-healing: Retrying text search for '{text_to_find}' in 1s...")
    time.sleep(1)
    location = _find_text_internal()

    if location:
        log_action(f"SELF-HEALED: Found text '{text_to_find}' near {location} on second attempt.")
        return location

    if should_log: log_action(f"FAILURE: Did not find text '{text_to_find}' after self-healing.", is_error=True)
    return None

def type_text(text_to_type, should_log=True):
    if should_log: log_action(f"ACTION: Type text '{text_to_type}'")
    try:
        pyautogui.write(text_to_type, interval=0.05)
        log_action(f"SUCCESS: Typed text.")
        return True
    except Exception as e:
        log_action(f"Error while typing: {e}", is_error=True)
        return False

def wait(seconds_to_wait, should_log=True):
    if should_log: log_action(f"ACTION: Wait for {seconds_to_wait} seconds")
    try:
        time.sleep(float(seconds_to_wait))
        log_action(f"SUCCESS: Waited for {seconds_to_wait} seconds.")
        return True
    except ValueError:
        log_action(f"Invalid wait time: '{seconds_to_wait}'. Must be a number.", is_error=True)
        return False
    except Exception as e:
        log_action(f"Error while waiting: {e}", is_error=True)
        return False

def wait_for_element(check_function, target, timeout_seconds):
    """Generic function to wait for an element to appear."""
    start_time = time.time()
    timeout = float(timeout_seconds)
    log_action(f"Waiting for up to {timeout} seconds for '{target}'...")

    while time.time() - start_time < timeout:
        if check_function(target, should_log=False):
            log_action(f"SUCCESS: Element '{target}' appeared after {time.time() - start_time:.2f} seconds.")
            return True
        time.sleep(0.5) # Check every half a second

    log_action(f"FAILURE: Timed out after {timeout} seconds waiting for '{target}'.", is_error=True)
    return False

def wait_for_image(target, timeout):
    return wait_for_element(assert_image_exists, target, timeout)

def wait_for_text(target, timeout):
    return wait_for_element(assert_text_exists, target, timeout)

def assert_visuals(page_name, should_log=True):
    """
    Performs visual regression testing.
    - On first run, it creates a baseline screenshot.
    - On subsequent runs, it compares the current screen with the baseline.
    """
    if should_log: log_action(f"ASSERTION: Visual check for '{page_name}'")

    baseline_dir = os.path.join("knowledge_base", "visual_baselines")
    baseline_path = os.path.join(baseline_dir, f"{page_name}.png")

    # Take a screenshot of the current state
    current_screenshot = pyautogui.screenshot()

    # If baseline does not exist, create it
    if not os.path.exists(baseline_path):
        log_action(f"No baseline found for '{page_name}'. Creating a new one.")
        current_screenshot.save(baseline_path)
        log_action(f"SUCCESS: New baseline created at {baseline_path}.")
        return True

    # If baseline exists, compare
    try:
        baseline_image = Image.open(baseline_path)

        # Check if dimensions are the same
        if baseline_image.size != current_screenshot.size:
            log_action("Visual assertion failed: Screen dimensions have changed.", is_error=True)
            return False

        # Find the difference
        diff_image = ImageChops.difference(baseline_image, current_screenshot)

        # If there is a difference, the diff_image will have non-zero bounding box
        if diff_image.getbbox():
            log_action(f"FAILURE: Visual differences found for '{page_name}'.", is_error=True)

            # Save the failing images for review
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            current_path = os.path.join(SCREENSHOTS_DIR, f"visual_fail_{page_name}_current_{timestamp}.png")
            diff_path = os.path.join(SCREENSHOTS_DIR, f"visual_fail_{page_name}_diff_{timestamp}.png")

            current_screenshot.save(current_path)
            diff_image.save(diff_path)

            log_action(f"  -> Baseline: {baseline_path}")
            log_action(f"  -> Current state saved to: {current_path}")
            log_action(f"  -> Difference map saved to: {diff_path}")
            return False
        else:
            log_action(f"SUCCESS: Visuals for '{page_name}' match the baseline.")
            return True

    except Exception as e:
        log_action(f"Error during visual comparison for '{page_name}': {e}", is_error=True)
        return False

# --- Scenario Execution ---
def execute_scenario(scenario_name):
    log_action(f"--- Starting execution of SCENARIO: '{scenario_name}' ---")
    scenarios = get_scenarios()
    if scenario_name not in scenarios:
        log_action(f"Scenario '{scenario_name}' not found.", is_error=True)
        return

    steps = scenarios[scenario_name]
    for i, step in enumerate(steps, 1):
        log_action(f"Executing step {i}/{len(steps)}: {step['action']} -> '{step['target']}'")
        action = step['action']
        target = step['target']
        success = False

        action = step.get('action')
        target = step.get('target')
        timeout = step.get('timeout') # Will be None if not present
        success = False

        if action == "find-image": success = find_image_and_click(target, should_log=False)
        elif action == "find-text": success = find_text_and_click(target, should_log=False)
        elif action == "type": success = type_text(target, should_log=False)
        elif action == "wait": success = wait(target, should_log=False)
        elif action == "assert-image": success = assert_image_exists(target, should_log=False) is not None
        elif action == "assert-text": success = assert_text_exists(target, should_log=False) is not None
        elif action == "wait-for-image": success = wait_for_image(target, timeout)
        elif action == "wait-for-text": success = wait_for_text(target, timeout)
        elif action == "assert-visuals": success = assert_visuals(target)
        else:
            log_action(f"Unknown action '{action}' in scenario.", is_error=True)

        if not success:
            log_action(f"Scenario '{scenario_name}' failed at step {i}. Aborting.", is_error=True)
            return False

    log_action(f"--- Successfully completed SCENARIO: '{scenario_name}' ---")
    return True

# --- Status Reporting ---
def generate_status_report():
    """Reads knowledge files and logs to generate a status report."""
    log_action("Generating status report.")
    print("\n--- Smart Cursor Status Report ---")

    # 1. Report on Learned Images (Knowledge Base)
    kb = get_knowledge_base()
    print(f"\n[1] Image Memory (Knowledge Base):")
    if not kb:
        print("  - I haven't learned any images yet. Use learn.py to teach me.")
    else:
        print(f"  - I know {len(kb)} image(s):")
        for name, path in kb.items():
            status = "OK" if os.path.exists(path) else "MISSING"
            print(f"    - '{name}' (Status: {status})")

    # 2. Report on Scenarios
    scenarios = get_scenarios()
    print(f"\n[2] Stored Plans (Scenarios):")
    if not scenarios:
        print("  - I don't have any scenarios. Use scenario_manager.py to create some.")
    else:
        print(f"  - I know {len(scenarios)} scenario(s):")
        for name, steps in scenarios.items():
            print(f"    - '{name}' ({len(steps)} steps)")

    # 3. Report on Recent History (Log File)
    print(f"\n[3] Recent Activity (last 10 entries from history.log):")
    if not os.path.exists("history.log"):
        print("  - No history log found.")
    else:
        try:
            with open("history.log", 'r', encoding='utf-8') as f:
                last_lines = f.readlines()[-10:]
                if not last_lines:
                    print("  - History is empty.")
                for line in last_lines:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"  - Error reading history log: {e}")

    print("\n------------------------------------")

def print_usage():
    print("--- Smart Cursor: The Conscious QA Engineer ---")
    print("\nUsage: python smart_cursor.py [command] [arguments...]")
    print("\nCommands:")
    print("  --find-image <name>              Clicks a pre-learned image.")
    print("  --find-text <text>               Clicks the first occurrence of text on screen.")
    print("  --type <text>                    Types text at the current cursor location.")
    print("  --wait <seconds>                 Pauses for a number of seconds.")
    print("  --assert-image <name>            Checks if a pre-learned image is visible.")
    print("  --assert-text <text>             Checks if text is visible on screen.")
    print("  --wait-for-image <name> <sec>    Waits until an image appears or timeout.")
    print("  --wait-for-text <text> <sec>     Waits until text appears or timeout.")
    print("  --run-scenario <name>            Executes a multi-step test case.")
    print("  --status                         Shows what the cursor knows and remembers.")


if __name__ == "__main__":
    log_action("Smart Cursor session started.")

    if len(sys.argv) == 2 and sys.argv[1] == '--status':
        generate_status_report()
        sys.exit(0)

    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # Actions that take a single string argument
    if command in ["--find-image", "--find-text", "--type", "--wait", "--assert-image", "--assert-text", "--run-scenario", "--assert-visuals"]:
        if len(sys.argv) != 3:
            print(f"Error: {command} requires exactly one argument.")
            sys.exit(1)
        argument = sys.argv[2]
        actions = {
            "--find-image": find_image_and_click,
            "--find-text": find_text_and_click,
            "--type": type_text,
            "--wait": wait,
            "--assert-image": lambda arg: assert_image_exists(arg) is not None,
            "--assert-text": lambda arg: assert_text_exists(arg) is not None,
            "--run-scenario": execute_scenario,
            "--assert-visuals": assert_visuals,
        }
        success = actions[command](argument)
        sys.exit(0) if success else sys.exit(1)

    # Actions that take two arguments
    elif command in ["--wait-for-image", "--wait-for-text"]:
        if len(sys.argv) != 4:
            print(f"Error: {command} requires a target and a timeout.")
            sys.exit(1)
        target, timeout = sys.argv[2], sys.argv[3]
        actions = {
            "--wait-for-image": wait_for_image,
            "--wait-for-text": wait_for_text,
        }
        success = actions[command](target, timeout)
        sys.exit(0) if success else sys.exit(1)

    else:
        log_action(f"Unknown command '{command}'.", is_error=True)
        print_usage()
        sys.exit(1)