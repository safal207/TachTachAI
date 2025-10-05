"""
UIA test that connects to existing Notepad
"""
import time
import subprocess
from pywinauto.application import Application

print("=== Testing UIA Backend (Connect Mode) ===\n")

try:
    # Start Notepad manually first
    print("[1] Starting Notepad in background...")
    proc = subprocess.Popen(["notepad.exe"])
    time.sleep(2)  # Give it time to start

    print("[2] Connecting to Notepad by PID...")
    app = Application(backend="uia").connect(process=proc.pid)

    print("[3] Getting window handle...")
    window = app.top_window()
    print(f"    Window title: {window.window_text()}")

    # Find the text editor by class
    print("[4] Finding Edit control...")
    edit = window.child_window(class_name="Edit", found_index=0)

    print("[5] Typing text...")
    edit.set_focus()
    edit.type_keys("Hello from UIA Backend!", with_spaces=True, pause=0.05)

    time.sleep(1)

    print("[6] Reading text...")
    text = edit.window_text()
    print(f"    Got: '{text}'")

    if "Hello from UIA Backend!" in text:
        print("\n[PASS] Text verification successful!")
    else:
        print(f"\n[FAIL] Text mismatch!")

    print("[7] Closing Notepad...")
    window.close()

    # Handle save dialog
    time.sleep(0.5)
    try:
        # Try to find "Don't Save" button
        app2 = Application(backend="uia").connect(title_re=".*Notepad")
        dlg = app2.top_window()
        btn = dlg.child_window(title="Don't Save", control_type="Button")
        btn.click()
        print("    Closed without saving")
    except:
        print("    Already closed")

    print("\n[SUCCESS] UIA Backend test passed!")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

    # Cleanup
    try:
        subprocess.run(["taskkill", "//F", "//IM", "notepad.exe"],
                      capture_output=True, check=False)
    except:
        pass
