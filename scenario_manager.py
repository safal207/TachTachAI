import json
import os
import sys
from logger import log_action

# --- Constants ---
SCENARIO_FILE = os.path.join("knowledge_base", "scenarios.json")
BASELINE_DIR = os.path.join("knowledge_base", "visual_baselines")

# --- Programmatic API for Command Interface ---

def create_or_update_scenario(name, steps):
    """
    Creates a new scenario or updates an existing one programmatically.
    :param name: The name of the scenario.
    :param steps: A list of step dictionaries.
    :return: True on success, False on failure.
    """
    if not name or not steps:
        log_action("Scenario name and steps cannot be empty.", is_error=True)
        return False

    log_action(f"Programmatically creating/updating scenario: '{name}'")
    scenarios = get_scenarios()
    scenarios[name] = steps
    save_scenarios(scenarios)
    return True

def delete_visual_baseline(baseline_name):
    """
    Deletes a visual baseline image, forcing it to be recreated on the next run.
    :param baseline_name: The name of the visual test page.
    :return: True on success, False if file not found.
    """
    log_action(f"Attempting to delete visual baseline for: '{baseline_name}'")
    baseline_path = os.path.join(BASELINE_DIR, f"{baseline_name}.png")

    if os.path.exists(baseline_path):
        try:
            os.remove(baseline_path)
            log_action(f"Successfully deleted baseline: {baseline_path}")
            return True
        except Exception as e:
            log_action(f"Error deleting baseline file {baseline_path}: {e}", is_error=True)
            return False
    else:
        log_action(f"Baseline file not found at {baseline_path}. Nothing to delete.", is_error=True)
        return False

# --- Core Helper Functions ---

def get_scenarios():
    """Loads scenarios from the JSON file."""
    if not os.path.exists(SCENARIO_FILE) or os.path.getsize(SCENARIO_FILE) == 0:
        return {}
    with open(SCENARIO_FILE, 'r') as f:
        return json.load(f)

def save_scenarios(data):
    """Saves scenarios to the JSON file."""
    with open(SCENARIO_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    log_action(f"Scenarios saved to {SCENARIO_FILE}")


# --- Interactive Mode Functions (for standalone use) ---

def record_scenario_interactive():
    """Interactive session to record a new multi-step scenario."""
    log_action("Starting new scenario recording (interactive).")
    scenario_name = input("Enter a name for your new scenario: ").strip()
    if not scenario_name:
        log_action("Scenario name cannot be empty.", is_error=True)
        return

    scenarios = get_scenarios()
    if scenario_name in scenarios:
        overwrite = input(f"Scenario '{scenario_name}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            log_action(f"User chose not to overwrite '{scenario_name}'.", is_error=True)
            return

    print("\n--- Start adding steps to your test case ---")
    print("Actions: find-image, find-text, type, wait, assert-image, assert-text, wait-for-image, wait-for-text, assert-visuals")
    print("Usage: action \"target\" OR wait-for-* \"target\" <seconds>")
    print("Type 'done' when you are finished.")

    steps = []
    while True:
        command_input = input(f"Step {len(steps) + 1}: ").strip()
        if command_input.lower() == 'done': break

        parts = command_input.split()
        action = parts[0]

        step = None
        try:
            if action in ["wait-for-image", "wait-for-text"]:
                target = " ".join(parts[1:-1]).strip('"\'')
                timeout = parts[-1]
                step = {"action": action, "target": target, "timeout": timeout}
            else:
                target = " ".join(parts[1:]).strip('"\'')
                step = {"action": action, "target": target}
        except IndexError:
            print("Invalid command format.")
            continue

        steps.append(step)
        print(f"  -> Step added: {step}")

    if steps:
        create_or_update_scenario(scenario_name, steps)
        print(f"\nScenario '{scenario_name}' saved!")

def list_scenarios_interactive():
    """Lists all saved scenarios and their steps to the console."""
    scenarios = get_scenarios()
    if not scenarios:
        print("No scenarios recorded yet.")
        return
    print("--- Available Scenarios ---")
    for name, steps in scenarios.items():
        print(f"\n[{name}]")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
    print("\n-------------------------")

def main():
    """Main function for standalone script execution."""
    if len(sys.argv) != 2:
        print("Usage: python scenario_manager.py --record | --list")
        sys.exit(1)

    command = sys.argv[1]
    if command == "--record":
        record_scenario_interactive()
    elif command == "--list":
        list_scenarios_interactive()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()