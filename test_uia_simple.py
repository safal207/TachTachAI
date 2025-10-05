"""
Simple UIA test to verify pywinauto works
"""
import time
from pywinauto.application import Application

print("=== Testing UIA Backend ===\n")

try:
    # Start Notepad
    print("[1] Starting Notepad...")
    app = Application(backend="uia").start("notepad.exe", timeout=10)

    print("[2] Connecting to Notepad window...")
    window = app.window(title_re=".*Notepad")
    window.wait("visible", timeout=10)

    print(f"[3] Window found: {window.window_text()}")

    # Find the text editor control
    print("[4] Finding text editor control...")
    edit = window.child_window(class_name="Edit", found_index=0)
    edit.wait("visible", timeout=5)

    print("[5] Typing text...")
    edit.type_keys("Hello from UIA test!", with_spaces=True)

    time.sleep(1)

    print("[6] Getting text back...")
    text = edit.window_text()
    print(f"    Text in editor: '{text}'")

    print("[7] Closing Notepad without saving...")
    window.close()

    # Handle "Do you want to save?" dialog
    time.sleep(0.5)
    try:
        dialog = app.window(title_re=".*Notepad")
        dont_save_btn = dialog.child_window(title="Don't Save", control_type="Button")
        dont_save_btn.click()
        print("    Clicked 'Don't Save'")
    except:
        print("    No save dialog (OK)")

    print("\n[OK] UIA Backend works correctly!")

except Exception as e:
    print(f"\n[ERROR] Test failed: {e}")
    import traceback
    traceback.print_exc()

    # Try to cleanup
    try:
        import subprocess
        subprocess.run(["taskkill", "/F", "/IM", "notepad.exe"],
                      capture_output=True, check=False)
    except:
        pass
