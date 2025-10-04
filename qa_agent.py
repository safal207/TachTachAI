import os
import json
import time
import datetime
from logger import log_action
import anthropic

# --- Constants ---
AGENT_MEMORY_FILE = "agent_memory.json"
EXECUTION_REPORT_FILE = "execution_report.json"
INSTRUCTIONS_FILE = "claude_instructions.json"
AGENT_MODE_FLAG_FILE = "agent_mode.flag"
AGENT_CYCLE_INTERVAL_SECONDS = 300  # 5 minutes
CRITICAL_COMMANDS = {"update_baseline", "create_performance_baseline"}

# --- Claude API Integration ---
try:
    # It's best practice to get the API key from an environment variable.
    api_key = os.environ["ANTHROPIC_API_KEY"]
    client = anthropic.Anthropic(api_key=api_key)
    CLAUDE_ENABLED = True
    log_action("Anthropic client initialized successfully.")
except KeyError:
    client = None
    CLAUDE_ENABLED = False
    log_action("ANTHROPIC_API_KEY environment variable not set. Claude integration is DISABLED.", is_error=True)

# --- Agent Core Functions ---

def get_agent_memory():
    """Loads the agent's memory from the JSON file."""
    if not os.path.exists(AGENT_MEMORY_FILE):
        return None
    try:
        with open(AGENT_MEMORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_action(f"Error reading agent memory: {e}", is_error=True)
        return None

def get_current_status():
    """Reads the latest execution report."""
    if not os.path.exists(EXECUTION_REPORT_FILE):
        return {"summary": {"total": 0, "passed": 0, "failed": 0}, "tests": []}
    try:
        with open(EXECUTION_REPORT_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "message": f"Could not read report: {e}"}

def claude_analyze(status, memory):
    """Forms a prompt and gets a decision from the Claude API."""
    if not CLAUDE_ENABLED:
        return {"analysis": "Claude is disabled. Falling back to mock.", "decision": "fallback", "reasoning": "API key missing.", "commands": []}

    system_prompt = """You are an autonomous QA Lead Agent. Your task is to analyze the current test report, consider your goals and past decisions, and decide on the next best action to ensure product quality.

Respond ONLY with a JSON object in the specified format. Do not include any other text or explanations.

Available actions:
1. `run_tests`: To run a specific set of tests.
2. `create_scenario`: To create a new test case for an observed gap.
3. `update_baseline`: To update a visual baseline.
4. `create_performance_baseline`: To update a performance baseline.
5. `investigate_failure`: A placeholder for a future deep-dive analysis.
6. `do_nothing`: If the system is stable and no action is required.

Your response MUST be a JSON object with the following structure:
{
  "analysis": "Your brief analysis of the current situation.",
  "decision": "The single best action to take from the list above.",
  "reasoning": "A short justification for your decision.",
  "commands": [
    {"command": "command_name", "params": {"key": "value"}}
  ]
}
"""

    prompt = f"""
Here is the current situation:

**Latest Test Report:**
```json
{json.dumps(status, indent=2)}
```

**Your Goals and Memory:**
```json
{json.dumps(memory, indent=2)}
```

Based on all this information, what is the next best action? Provide your response in the required JSON format.
"""
    try:
        log_action("Sending request to Claude API...")
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text
        log_action("Received response from Claude API.")
        return json.loads(response_text)
    except Exception as e:
        log_action(f"Error calling Claude API: {e}", is_error=True)
        return {"analysis": "Error communicating with Claude.", "decision": "error", "reasoning": str(e), "commands": []}


def execute_decision(decision):
    """Executes the decision by creating an instruction file, with safety checks."""
    commands = decision.get("commands")
    if not commands:
        return False

    instruction = commands[0]
    command_name = instruction.get("command")

    if command_name in CRITICAL_COMMANDS:
        log_action(f"CRITICAL ACTION BLOCKED: Command '{command_name}' requires human approval.", is_error=True)
        return False

    try:
        with open(INSTRUCTIONS_FILE, 'w') as f:
            json.dump(instruction, f, indent=4)
        return True
    except Exception as e:
        log_action(f"Failed to write instruction file: {e}", is_error=True)
        return False

def update_memory(decision, execution_result):
    """Updates the agent's memory with the outcome of the last decision."""
    log_action("Agent is updating its memory...")
    memory = get_agent_memory()
    if not memory:
        return

    # Basic effectiveness calculation (can be improved)
    effectiveness = "neutral"
    if decision and execution_result:
        # A simple heuristic: if the decision led to a successful run, it was effective.
        if execution_result.get("summary", {}).get("failed", 1) == 0:
            effectiveness = "high"
        # If the decision was to investigate and it failed, it might still be effective.
        elif execution_result.get("summary", {}).get("failed", 0) > 0:
             effectiveness = "low"

    new_history_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "decision": decision.get("decision"),
        "reasoning": decision.get("reasoning"),
        "outcome": f"Ran command '{decision.get('commands', [{}])[0].get('command')}'. Result: {execution_result.get('summary', {'status': 'unknown'})}",
        "effectiveness": effectiveness
    }

    memory["decision_history"].append(new_history_entry)
    # Keep history from getting too long
    memory["decision_history"] = memory["decision_history"][-20:]
    memory["metrics"]["total_decisions"] = memory["metrics"].get("total_decisions", 0) + 1

    try:
        with open(AGENT_MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=4)
        log_action("Memory update complete.")
    except Exception as e:
        log_action(f"Failed to save agent memory: {e}", is_error=True)

def is_autonomous_mode():
    """Checks the flag file to see if the agent should be running."""
    if not os.path.exists(AGENT_MODE_FLAG_FILE):
        return False
    try:
        with open(AGENT_MODE_FLAG_FILE, 'r') as f:
            return f.read().strip().lower() == "autonomous"
    except Exception:
        return False

# --- Main Agent Loop ---
def main():
    log_action(f"QA Agent v5.0 started.")

    while True:
        if is_autonomous_mode():
            log_action("--- Starting new autonomous cycle ---")

            status = get_current_status()
            memory = get_agent_memory()

            if not memory:
                log_action("Agent memory not found, cannot proceed.", is_error=True)
                time.sleep(AGENT_CYCLE_INTERVAL_SECONDS)
                continue

            decision = claude_analyze(status, memory)
            was_executed = execute_decision(decision)

            if was_executed:
                log_action("Waiting for command to be processed...")
                wait_timeout = 60
                start_time = time.time()
                while os.path.exists(INSTRUCTIONS_FILE):
                    time.sleep(2)
                    if time.time() - start_time > wait_timeout:
                        log_action("Timeout waiting for instruction file.", is_error=True)
                        break

                new_status = get_current_status()
                update_memory(decision, new_status)
            else:
                log_action("No command was executed in this cycle.")

        else:
            log_action("Agent is in manual mode. Sleeping...")

        time.sleep(AGENT_CYCLE_INTERVAL_SECONDS)

if __name__ == "__main__":
    # Note: The agent is designed to be run as a persistent background process.
    # The user should be informed to set the ANTHROPIC_API_KEY environment variable.
    main()