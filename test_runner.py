import os
import json
import csv
import subprocess
import datetime
from logger import log_action
from diagnostics import run_diagnostics
from performance_tracker import PerformanceTracker

# --- Constants ---
REPORTS_DIR = "reports"
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")
SCENARIO_FILE = os.path.join("knowledge_base", "scenarios.json")
PYTHON_CMD = "python" # or "python3"

# --- Helper Functions ---

def get_scenarios():
    """Loads all test scenarios from the JSON file."""
    if not os.path.exists(SCENARIO_FILE):
        log_action(f"Scenario file not found at {SCENARIO_FILE}", is_error=True)
        return None
    with open(SCENARIO_FILE, 'r') as f:
        return json.load(f)

def _substitute_placeholders(steps, data_row):
    """Substitutes placeholders like {column_name} in steps with data from a row."""
    new_steps = json.loads(json.dumps(steps)) # Deep copy
    for step in new_steps:
        for key, value in step.items():
            if isinstance(value, str):
                try:
                    step[key] = value.format(**data_row)
                except KeyError:
                    pass
    return new_steps

# --- Core Test Execution ---

def run_single_test(scenario_name, steps):
    """Runs a single, fully-defined test case and returns the result dictionary."""
    log_action(f"--- Running Test: {scenario_name} ---")
    perf_tracker = PerformanceTracker(scenario_name)

    for i, step in enumerate(steps):
        action = step.get('action')
        target = step.get('target')
        timeout = step.get('timeout')

        log_action(f"  Executing Step {i+1}/{len(steps)}: {action} -> '{target}'")

        command = [PYTHON_CMD, "smart_cursor.py", f"--{action}", target]
        if timeout:
            command.append(str(timeout))

        perf_tracker.start_step(i)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        perf_tracker.stop_step(i)

        if result.returncode != 0:
            log_action(f"  >> STEP FAILED! Return code: {result.returncode}", is_error=True)
            diagnostics_data = run_diagnostics(scenario_name, i)
            performance_data = perf_tracker.finalize()
            step_description = f"{action} '{target}'" + (f" (timeout: {timeout}s)" if timeout else "")
            main_screenshot = diagnostics_data["screenshots"][0] if diagnostics_data.get("screenshots") else None

            return {
                "name": scenario_name,
                "status": "FAILED",
                "failed_step": i + 1,
                "step_description": step_description,
                "error": result.stdout.strip() or result.stderr.strip(),
                "screenshot": main_screenshot,
                "diagnostics": diagnostics_data,
                "performance": performance_data
            }

    performance_data = perf_tracker.finalize()
    return {
        "name": scenario_name,
        "status": "PASSED",
        "steps_executed": len(steps),
        "performance": performance_data
    }

# --- Test Suite Execution Modes ---

def run_scenario_based_suite(test_names=None):
    """Runs a standard test suite based on scenario names."""
    log_action("Standard test suite run initiated.")
    scenarios = get_scenarios()
    if not scenarios: return []

    tests_to_run = scenarios
    if test_names and "all" not in test_names:
        tests_to_run = {name: steps for name, steps in scenarios.items() if name in test_names}

    results = [run_single_test(name, steps) for name, steps in tests_to_run.items()]
    return results

def run_data_driven_suite(scenario_name, data_file_path):
    """Runs a single scenario multiple times with data from a CSV file."""
    log_action(f"Data-driven test for '{scenario_name}' with '{data_file_path}' initiated.")

    scenarios = get_scenarios()
    if scenario_name not in scenarios:
        return [{"name": scenario_name, "status": "ERROR", "error": "Base scenario not found."}]
    base_steps = scenarios[scenario_name]

    if not os.path.exists(data_file_path):
        return [{"name": scenario_name, "status": "ERROR", "error": f"Data file not found: {data_file_path}"}]

    results = []
    try:
        with open(data_file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                iteration_name = f"{scenario_name}_[row_{i+1}]"
                iteration_steps = _substitute_placeholders(base_steps, row)
                result = run_single_test(iteration_name, iteration_steps)
                results.append(result)
    except Exception as e:
        return [{"name": scenario_name, "status": "ERROR", "error": f"Failed to process CSV: {e}"}]

    return results

# --- Main function for standalone execution ---

def main():
    """Main function for standalone execution, prints summary to console."""
    log_action("QA Test Runner session started (standalone mode).")
    results = run_scenario_based_suite()

    if not results:
        log_action("No tests were run.")
        return

    passed_count = sum(1 for r in results if r['status'] == 'PASSED')
    failed_count = len(results) - passed_count

    print(f"\n--- Test Run Summary (Console) ---")
    for res in results:
        print(f"  - Test '{res['name']}': {res['status']}")
        if res.get('performance', {}).get('has_regression'):
            print(f"    -> PERFORMANCE REGRESSION DETECTED!")
        if res['status'] == 'FAILED':
            print(f"    -> Failed at step {res.get('failed_step')}: {res.get('step_description')}")
            diag = res.get('diagnostics', {})
            print(f"    -> Diagnostics: CPU: {diag.get('cpu_usage')}, RAM: {diag.get('ram_usage')}, Network: {'OK' if diag.get('network_available') else 'FAIL'}")
            print(f"    -> Screenshots: {diag.get('screenshots')}")

    print(f"\nResult: {passed_count} passed, {len(results) - passed_count} failed out of {len(results)} total tests.")
    log_action("QA Test Runner session finished.")

if __name__ == "__main__":
    main()