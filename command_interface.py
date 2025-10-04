import os
import json
import time
import subprocess
import datetime
from logger import log_action

# Import functions from our refactored modules
from test_runner import run_scenario_based_suite, run_data_driven_suite
from scenario_manager import create_or_update_scenario, delete_visual_baseline

# --- Constants ---
INSTRUCTIONS_FILE = "claude_instructions.json"
REPORT_FILE = "execution_report.json"
PYTHON_CMD = "python" # or python3
FRAMEWORK_VERSION = "3.0" # Updated version

# --- Core Functions ---

def read_instructions():
    """Checks for and reads the instructions file."""
    if os.path.exists(INSTRUCTIONS_FILE):
        log_action("Found instructions file.")
        try:
            with open(INSTRUCTIONS_FILE, 'r') as f:
                content = f.read()
                if not content: return None
                return json.loads(content)
        except Exception as e:
            log_action(f"Error reading {INSTRUCTIONS_FILE}: {e}", is_error=True)
            return None
    return None

def write_report(data):
    """Writes the execution result to the report file."""
    log_action("Writing execution report.")
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        log_action(f"Report successfully written to {REPORT_FILE}.")
    except Exception as e:
        log_action(f"Failed to write report: {e}", is_error=True)

def cleanup_instructions():
    """Deletes the instructions file after processing."""
    if os.path.exists(INSTRUCTIONS_FILE):
        os.remove(INSTRUCTIONS_FILE)
        log_action("Instructions file cleaned up.")

def _format_test_report(test_results):
    """Helper function to format the final JSON report from test results."""
    if not test_results:
        return {"status": "error", "message": "No test results to report."}

    passed = sum(1 for r in test_results if r['status'] == 'PASSED')
    failed = len(test_results) - passed
    success_rate = (passed / len(test_results) * 100) if test_results else 100

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "framework_version": FRAMEWORK_VERSION,
        "summary": {
            "total": len(test_results),
            "passed": passed,
            "failed": failed,
            "success_rate": round(success_rate, 2)
        },
        "tests": test_results
    }

# --- Command Handlers ---

def handle_run_tests(params):
    """Handler for the 'run_tests' command."""
    log_action(f"Executing 'run_tests' with params: {params}")
    test_names = params.get("scenarios", ["all"])
    test_results = run_scenario_based_suite(test_names)
    return _format_test_report(test_results)

def handle_run_data_driven_tests(params):
    """Handler for the 'run_tests_with_data' command."""
    log_action(f"Executing 'run_tests_with_data' with params: {params}")
    scenario_name = params.get("scenario_name")
    data_file = params.get("data_file")

    if not scenario_name or not data_file:
        return {"status": "error", "message": "Missing 'scenario_name' or 'data_file'."}

    test_results = run_data_driven_suite(scenario_name, data_file)
    return _format_test_report(test_results)

def handle_create_scenario(params):
    """Handler for the 'create_scenario' command."""
    name = params.get('name')
    steps = params.get('steps')
    if not name or not steps:
        return {"status": "error", "message": "Missing 'name' or 'steps'."}
    success = create_or_update_scenario(name, steps)
    return {"status": "completed" if success else "error", "message": f"Scenario '{name}' processed."}

def handle_update_baseline(params):
    """Handler for the 'update_baseline' command."""
    baseline_name = params.get('visual_test_name')
    if not baseline_name:
        return {"status": "error", "message": "Missing 'visual_test_name'."}
    success = delete_visual_baseline(baseline_name)
    return {"status": "completed" if success else "error", "message": f"Baseline '{baseline_name}' processed."}

def handle_get_status(params):
    """Handler for the 'get_status' command."""
    try:
        result = subprocess.run([PYTHON_CMD, "smart_cursor.py", "--status"], capture_output=True, text=True, check=True)
        return {"status": "completed", "data": result.stdout}
    except Exception as e:
        return {"status": "error", "message": "Failed to get status.", "details": str(e)}

# --- Main Loop ---
def main():
    """Main loop to check for instructions and execute them."""
    log_action(f"Command Interface v{FRAMEWORK_VERSION} started. Watching for instructions...")
    command_handlers = {
        "run_tests": handle_run_tests,
        "run_tests_with_data": handle_run_data_driven_tests,
        "create_scenario": handle_create_scenario,
        "update_baseline": handle_update_baseline,
        "get_status": handle_get_status,
    }

    while True:
        instructions = read_instructions()
        if instructions:
            command = instructions.get("command")
            params = instructions.get("params", {})

            handler = command_handlers.get(command)
            if handler:
                execution_report = handler(params)
                write_report(execution_report)
            else:
                log_action(f"Unknown command received: {command}", is_error=True)
                write_report({"status": "error", "command": command, "message": "Unknown command."})

            cleanup_instructions()

        time.sleep(10)

if __name__ == "__main__":
    main()