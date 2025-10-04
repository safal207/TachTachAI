import os
import json
import subprocess
import datetime
import pyautogui
from logger import log_action

# --- Constants ---
REPORTS_DIR = "reports"
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
SCENARIO_FILE = os.path.join("knowledge_base", "scenarios.json")
PYTHON_CMD = "python" # or "python3" depending on your system

def get_scenarios():
    """Loads all test scenarios from the JSON file."""
    log_action("Loading test scenarios...")
    if not os.path.exists(SCENARIO_FILE):
        log_action(f"Scenario file not found at {SCENARIO_FILE}", is_error=True)
        return None
    with open(SCENARIO_FILE, 'r') as f:
        return json.load(f)

def take_failure_screenshot(scenario_name, step_index):
    """Takes a screenshot and saves it with a descriptive name."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{scenario_name}_step_{step_index + 1}_failure_{timestamp}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    try:
        pyautogui.screenshot(filepath)
        log_action(f"Failure screenshot saved to: {filepath}")
        return filepath
    except Exception as e:
        log_action(f"Failed to take screenshot: {e}", is_error=True)
        return None

def run_single_test(scenario_name, steps):
    """Runs a single test case (scenario) and returns the result dictionary."""
    log_action(f"--- Running Test: {scenario_name} ---")

    for i, step in enumerate(steps):
        action = step.get('action')
        target = step.get('target')
        timeout = step.get('timeout') # Will be None for most actions

        log_action(f"  Executing Step {i+1}/{len(steps)}: {action} -> '{target}'")

        # Construct the command to call smart_cursor.py
        command = [PYTHON_CMD, "smart_cursor.py", f"--{action}", target]
        # Add timeout if it's a wait-for-* command
        if timeout:
            command.append(str(timeout))

        # Execute the command as a subprocess
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        # Check the return code. 0 is success.
        if result.returncode != 0:
            log_action(f"  >> STEP FAILED! Return code: {result.returncode}", is_error=True)
            screenshot_path = take_failure_screenshot(scenario_name, i)

            step_description = f"{action} '{target}'"
            if timeout:
                step_description += f" (timeout: {timeout}s)"

            return {
                "name": scenario_name,
                "status": "FAILED",
                "failed_step": i + 1,
                "step_description": step_description,
                "error": result.stdout.strip() or result.stderr.strip(),
                "screenshot": screenshot_path
            }

    log_action(f"--- Test Passed: {scenario_name} ---")
    return {
        "name": scenario_name,
        "status": "PASSED",
        "steps_executed": len(steps)
    }

def run_test_suite(test_names=None):
    """
    Runs all test scenarios or a specific subset and returns the results.
    This is the main entry point for external callers.
    :param test_names: A list of test names to run. If None or ["all"], runs all.
    :return: A list of result dictionaries.
    """
    log_action("Test run initiated.")
    scenarios = get_scenarios()

    if not scenarios:
        log_action("No test scenarios found to run.", is_error=True)
        return []

    tests_to_run = scenarios
    if test_names and "all" not in test_names:
        tests_to_run = {name: steps for name, steps in scenarios.items() if name in test_names}
        log_action(f"Running a subset of tests: {list(tests_to_run.keys())}")

    results = [run_single_test(name, steps) for name, steps in tests_to_run.items()]
    return results

def main():
    """The main function for standalone execution, prints summary to console."""
    log_action("QA Test Runner session started (standalone mode).")
    results = run_test_suite()

    if not results:
        log_action("No tests were run.")
        return

    total_tests = len(results)
    passed_count = sum(1 for r in results if r['status'] == 'PASSED')
    failed_count = total_tests - passed_count

    print(f"\n--- Test Run Summary (Console) ---")
    for res in results:
        print(f"  - Test '{res['name']}': {res['status']}")
        if res['status'] == 'FAILED':
            print(f"    -> Failed at step {res.get('failed_step')}: {res.get('step_description')}")
            print(f"    -> Screenshot: {res.get('screenshot')}")

    print(f"\nResult: {passed_count} passed, {failed_count} failed out of {total_tests} total tests.")
    log_action("QA Test Runner session finished.")

if __name__ == "__main__":
    main()