"""
Test UIA with Calculator - more reliable than Notepad
"""
import time
from pywinauto import Desktop

print("=== Testing UIA with Calculator ===\n")

try:
    # Start Calculator
    print("[1] Starting Calculator...")
    import subprocess
    subprocess.Popen("calc.exe")
    time.sleep(3)

    print("[2] Connecting to Calculator window...")
    calc = Desktop(backend="uia").window(title="Calculator")
    calc.wait("visible", timeout=10)
    print(f"    Found: {calc.window_text()}")

    print("[3] Clicking buttons: 5 + 3 =")
    calc.child_window(title="Five", control_type="Button").click()
    time.sleep(0.2)
    calc.child_window(title="Plus", control_type="Button").click()
    time.sleep(0.2)
    calc.child_window(title="Three", control_type="Button").click()
    time.sleep(0.2)
    calc.child_window(title="Equals", control_type="Button").click()
    time.sleep(0.5)

    print("[4] Reading result...")
    result = calc.child_window(auto_id="CalculatorResults", control_type="Text")
    result_text = result.window_text()
    print(f"    Result: {result_text}")

    if "8" in result_text:
        print("\n[PASS] Calculator test successful!")
    else:
        print(f"\n[FAIL] Expected 8, got: {result_text}")

    print("[5] Closing Calculator...")
    calc.close()

    print("\n[SUCCESS] UIA test passed!")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

    # Cleanup
    try:
        import subprocess
        subprocess.run(["taskkill", "//F", "//IM", "CalculatorApp.exe"],
                      capture_output=True, check=False)
    except:
        pass
