"""
Automated test script for tradernet.com using TachTachAI framework.
This script creates a test scenario for checking tradernet.com website.
"""
import json
import os
import time
import pyautogui

# Paths
SCENARIO_FILE = os.path.join("knowledge_base", "scenarios.json")

def create_tradernet_scenario():
    """Creates a test scenario for tradernet.com"""

    # Load existing scenarios
    scenarios = {}
    if os.path.exists(SCENARIO_FILE):
        with open(SCENARIO_FILE, 'r') as f:
            content = f.read()
            if content:
                scenarios = json.loads(content)

    # Define tradernet.com test scenario
    # Note: This scenario takes a screenshot to verify the page loaded
    tradernet_scenario = [
        {"action": "wait", "target": "5"},  # Wait for page to load completely
        {"action": "assert-visuals", "target": "tradernet_homepage"},  # Visual verification
    ]

    scenarios["tradernet_basic_check"] = tradernet_scenario

    # Save scenarios
    with open(SCENARIO_FILE, 'w') as f:
        json.dump(scenarios, f, indent=4)

    print("[+] Created scenario: tradernet_basic_check")
    print(f"[+] Scenario saved to: {SCENARIO_FILE}")

    return scenarios

def take_screenshot_for_learning(element_name):
    """Helper to take a screenshot of a specific area for learning"""
    print(f"\n[*] Preparing to capture element: {element_name}")
    print("[*] Move your mouse to the element you want to capture...")
    time.sleep(3)

    # Get mouse position
    x, y = pyautogui.position()
    print(f"[*] Mouse position: ({x}, {y})")

    # Take a small screenshot around the cursor
    region = (x-50, y-50, 100, 100)
    screenshot = pyautogui.screenshot(region=region)

    # Save to knowledge base
    kb_dir = "knowledge_base"
    os.makedirs(kb_dir, exist_ok=True)

    img_path = os.path.join(kb_dir, f"{element_name}.png")
    screenshot.save(img_path)

    print(f"[+] Saved screenshot to: {img_path}")

    # Update knowledge base
    kb_file = os.path.join(kb_dir, "kb.json")
    kb = {}
    if os.path.exists(kb_file):
        with open(kb_file, 'r') as f:
            content = f.read()
            if content:
                kb = json.loads(content)

    kb[element_name] = img_path

    with open(kb_file, 'w') as f:
        json.dump(kb, f, indent=4)

    print(f"[+] Updated knowledge base with '{element_name}'")

def run_tradernet_test():
    """Runs the tradernet test scenario"""
    import subprocess

    print("\n[*] Running tradernet test scenario...")
    result = subprocess.run(
        ["python", "smart_cursor.py", "--run-scenario", "tradernet_basic_check"],
        capture_output=True,
        text=True
    )

    print("\n--- Test Output ---")
    print(result.stdout)
    if result.stderr:
        print("--- Errors ---")
        print(result.stderr)

    if result.returncode == 0:
        print("\n[+] Test PASSED!")
    else:
        print("\n[-] Test FAILED!")

    return result.returncode == 0

if __name__ == "__main__":
    print("=== TachTachAI - Tradernet.com Test ===\n")

    choice = input("What do you want to do?\n1. Create test scenario\n2. Run test scenario\n3. Learn new element (manual)\nChoice: ").strip()

    if choice == "1":
        create_tradernet_scenario()
        print("\n[+] Scenario created successfully!")
        print("[*] You can now run the test with option 2")

    elif choice == "2":
        if run_tradernet_test():
            print("\n[OK] All tests passed!")
        else:
            print("\n[ERROR] Some tests failed. Check the logs.")

    elif choice == "3":
        element_name = input("Enter element name: ").strip()
        take_screenshot_for_learning(element_name)
        print("\n[+] Element learned! You can now use it in scenarios.")

    else:
        print("Invalid choice!")
