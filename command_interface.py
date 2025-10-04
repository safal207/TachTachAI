import os
import json
import time
import subprocess
import datetime
from logger import log_action

# Import functions from our refactored modules
from test_runner import run_scenario_based_suite, run_data_driven_suite
from scenario_manager import create_or_update_scenario, delete_visual_baseline
from performance_tracker import delete_baseline as delete_performance_baseline
from analysis_packager import create_analysis_package

# --- Constants ---
RECOMMENDATIONS_FILE = "recommendations.json"
INSTRUCTIONS_FILE = "claude_instructions.json" # For manual override
REPORT_FILE = "execution_report.json"
HISTORY_DIR = os.path.join("reports", "history")
PYTHON_CMD = "python"
FRAMEWORK_VERSION = "5.0" # AI-Assisted Mode

# --- File I/O ---

def read_json_file(filepath):
    """Generic function to read a JSON file."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            return json.loads(content) if content else None
    except Exception as e:
        log_action(f"Error reading {filepath}: {e}", is_error=True)
        return None

def archive_file(filepath, subfolder=''):
    """Archives a file by moving it to the history directory with a timestamp."""
    if os.path.exists(filepath):
        try:
            target_dir = os.path.join(HISTORY_DIR, subfolder)
            os.makedirs(target_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = os.path.join(target_dir, f"{os.path.basename(filepath)}_{timestamp}.json")
            os.rename(filepath, archive_path)
            log_action(f"Archived {filepath} to {archive_path}")
        except Exception as e:
            log_action(f"Could not archive {filepath}: {e}", is_error=True)

def write_report(data):
    """Archives the old report and writes the new one."""
    archive_file(REPORT_FILE, subfolder='reports')
    log_action("Writing new execution report.")
    try:
        with open(REPORT_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log_action(f"Failed to write report: {e}", is_error=True)

# --- Command Handlers ---

def _format_test_report(test_results):
    """Helper function to format the final JSON report from test results."""
    # ... (implementation from previous phase)
    passed = sum(1 for r in test_results if r['status'] == 'PASSED')
    failed = len(test_results) - passed
    success_rate = (passed / len(test_results) * 100) if test_results else 100
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "framework_version": FRAMEWORK_VERSION,
        "summary": {"total": len(test_results), "passed": passed, "failed": failed, "success_rate": round(success_rate, 2)},
        "tests": test_results
    }

command_handlers = {
    "run_tests": lambda p: _format_test_report(run_scenario_based_suite(p.get("scenarios", ["all"]))),
    "run_tests_with_data": lambda p: _format_test_report(run_data_driven_suite(p.get("scenario_name"), p.get("data_file"))),
    "create_scenario": lambda p: {"status": "completed" if create_or_update_scenario(p.get('name'), p.get('steps')) else "error"},
    "update_baseline": lambda p: {"status": "completed" if delete_visual_baseline(p.get('visual_test_name')) else "error"},
    "create_performance_baseline": lambda p: {"status": "completed" if delete_performance_baseline(p.get('test_name')) else "error"},
    "get_status": lambda p: {"data": subprocess.run([PYTHON_CMD, "smart_cursor.py", "--status"], capture_output=True, text=True).stdout}
}

def execute_command(command_data):
    """Executes a single command dictionary."""
    command_name = command_data.get("command")
    params = command_data.get("params", {})
    handler = command_handlers.get(command_name)
    if handler:
        log_action(f"Executing command: {command_name} with params: {params}")
        return handler(params)
    else:
        log_action(f"Unknown command '{command_name}'", is_error=True)
        return {"status": "error", "message": f"Unknown command: {command_name}"}

# --- Main Loop ---

def main():
    """Main loop to check for recommendations or manual instructions."""
    log_action(f"AI-Assisted Command Interface v{FRAMEWORK_VERSION} started.")

    while True:
        recommendations = read_json_file(RECOMMENDATIONS_FILE)

        if recommendations:
            log_action("Found AI-generated recommendations.")
            print("\n--- 🤖 AI Recommendations Loaded ---")
            for i, action in enumerate(recommendations.get("priority_actions", [])):
                print(f"  {i+1}. Action: {action.get('action')}")
                print(f"     Reasoning: {action.get('reasoning')}")

            confirm = input("Execute these recommendations? (yes/no): ").lower().strip()

            if confirm == 'yes':
                log_action("User approved execution of recommendations.")
                for action in recommendations.get("priority_actions", []):
                    for command in action.get("commands", []):
                        # We don't generate a full report for each sub-step, just log it.
                        execute_command(command)
                # After executing all, we generate a new analysis package
                create_analysis_package()
            else:
                log_action("User rejected execution of recommendations.")

            archive_file(RECOMMENDATIONS_FILE, subfolder='recommendations')

        else:
            # Fallback to manual instruction mode if no recommendations
            instruction = read_json_file(INSTRUCTIONS_FILE)
            if instruction:
                log_action("Found manual instruction file.")
                report = execute_command(instruction)
                if report:
                    write_report(report)
                os.remove(INSTRUCTIONS_FILE)
                # After manual action, also generate a new analysis package
                create_analysis_package()

        time.sleep(10)

if __name__ == "__main__":
    main()