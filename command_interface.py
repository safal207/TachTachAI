import os
import json
import time
import subprocess
import datetime
from logger import log_action

# Import functions from our refactored modules
from test_runner import run_test_suite
from scenario_manager import create_or_update_scenario, delete_visual_baseline

# --- Constants ---
INSTRUCTIONS_FILE = "claude_instructions.json"
REPORT_FILE = "execution_report.json"
PYTHON_CMD = "python" # or python3
FRAMEWORK_VERSION = "2.0"

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

# --- Command Handlers ---

def handle_run_tests(params):
    """Handler for the 'run_tests' command."""
    log_action(f"Executing 'run_tests' with params: {params}")
    test_names = params.get("scenarios", ["all"])

    test_results = run_test_suite(test_names)

    # Format the report according to the spec
    passed = sum(1 for r in test_results if r['status'] == 'PASSED')
    failed = len(test_results) - passed
    success_rate = (passed / len(test_results) * 100) if test_results else 100

    report = {
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
    return report

def handle_create_scenario(params):
    """Handler for the 'create_scenario' command."""
    log_action(f"Executing 'create_scenario' with params: {params}")
    name = params.get('name')
    steps = params.get('steps')

    if not name or not steps:
        return {"status": "error", "message": "Missing 'name' or 'steps' for create_scenario."}

    success = create_or_update_scenario(name, steps)
    if success:
        return {"status": "completed", "message": f"Scenario '{name}' created/updated successfully."}
    else:
        return {"status": "error", "message": f"Failed to create/update scenario '{name}'."}


def handle_update_baseline(params):
    """Handler for the 'update_baseline' command."""
    log_action(f"Executing 'update_baseline' with params: {params}")
    baseline_name = params.get('visual_test_name')
    if not baseline_name:
        return {"status": "error", "message": "Missing 'visual_test_name' for update_baseline."}

    success = delete_visual_baseline(baseline_name)
    if success:
        return {"status": "completed", "message": f"Visual baseline for '{baseline_name}' deleted. It will be recreated on the next run."}
    else:
        return {"status": "error", "message": f"Failed to delete visual baseline for '{baseline_name}'. It might not exist."}


def handle_get_status(params):
    """Handler for the 'get_status' command."""
    log_action(f"Executing 'get_status' with params: {params}")
    try:
        result = subprocess.run(
            [PYTHON_CMD, "smart_cursor.py", "--status"],
            capture_output=True, text=True, check=True
        )
        # The output of --status is human-readable, so we just wrap it.
        return {"status": "completed", "data": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": "Failed to get status.", "details": e.stderr}
    except FileNotFoundError:
        return {"status": "error", "message": "smart_cursor.py not found or python command is incorrect."}


# --- Main Loop ---

def main():
    """Main loop to check for instructions and execute them."""
    log_action("Command Interface started. Watching for instructions...")
    command_handlers = {
        "run_tests": handle_run_tests,
        "create_scenario": handle_create_scenario,
        "update_baseline": handle_update_baseline,
        "get_status": handle_get_status,
    }

    while True:
        instructions = read_instructions()
        if instructions:
            command = instructions.get("command")
            params = instructions.get("params", {})

            if command in command_handlers:
                execution_report = command_handlers[command](params)
                write_report(execution_report)
            else:
                log_action(f"Unknown command received: {command}", is_error=True)
                error_report = {"status": "error", "command": command, "message": "Unknown command."}
                write_report(error_report)

            cleanup_instructions()

        time.sleep(10)

if __name__ == "__main__":
    main()