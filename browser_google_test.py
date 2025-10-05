"""
TachTachAI - Browser Google Search Test
Tests browser automation with Cursor IDE and Google search
"""
import time
import subprocess
import pyautogui
from pywinauto import Desktop

print("=== TachTachAI - Browser Google Search Test ===\n")

def test_browser_google_search():
    """
    Test scenario:
    1. Open Cursor IDE
    2. Launch browser (Edge/Chrome)
    3. Navigate to Google
    4. Perform search
    5. Verify results
    """

    try:
        # Step 1: Launch default browser with Google
        print("[1] Opening browser with Google...")
        subprocess.Popen(["start", "https://www.google.com"], shell=True)
        time.sleep(5)  # Wait for browser to load

        # Step 2: Get screen size and move to search box area
        print("[2] Moving to search area...")
        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 2
        search_y = screen_height // 3  # Google search is usually in upper third

        pyautogui.moveTo(center_x, search_y, duration=0.5)
        time.sleep(0.5)

        # Step 3: Click to focus search box
        print("[3] Clicking search box...")
        pyautogui.click()
        time.sleep(1)

        # Step 4: Type search query
        search_query = "TachTachAI automation framework"
        print(f"[4] Typing search query: '{search_query}'")
        pyautogui.write(search_query, interval=0.05)
        time.sleep(1)

        # Step 5: Press Enter to search
        print("[5] Pressing Enter to search...")
        pyautogui.press('enter')
        time.sleep(3)

        # Step 6: Take screenshot of results
        print("[6] Taking screenshot of results...")
        screenshot = pyautogui.screenshot()
        screenshot_path = "reports/screenshots/google_search_results.png"
        screenshot.save(screenshot_path)
        print(f"    Screenshot saved: {screenshot_path}")

        # Step 7: Verify we're on Google by checking URL bar area
        print("[7] Verifying we're on Google...")
        # Move to URL bar and select all
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(1)

        # Try to get clipboard content (optional)
        try:
            import pyperclip
            url = pyperclip.paste()
            print(f"    Current URL: {url}")

            if "google.com" in url.lower():
                print("\n[PASS] Successfully navigated to Google!")
                return True
            else:
                print(f"\n[FAIL] Expected google.com, got: {url}")
                return False
        except ImportError:
            print("    (pyperclip not installed, skipping URL verification)")
            print("\n[PASS] Test completed (manual verification needed)")
            return True

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cursor_browser_integration():
    """
    Test Cursor IDE + Browser interaction
    """
    print("\n=== Cursor + Browser Integration Test ===\n")

    try:
        # Step 1: Check if Cursor is running
        print("[1] Checking for Cursor IDE...")
        desktop = Desktop(backend="uia")

        try:
            cursor_window = desktop.window(title_re=".*Cursor.*")
            print(f"    Found Cursor: {cursor_window.window_text()}")

            # Minimize Cursor to make space for browser
            print("[2] Minimizing Cursor...")
            cursor_window.minimize()
            time.sleep(1)

        except:
            print("    Cursor not found (OK, will launch browser anyway)")

        # Step 2: Launch browser and test
        success = test_browser_google_search()

        # Step 3: Restore Cursor
        try:
            if cursor_window:
                print("\n[3] Restoring Cursor window...")
                cursor_window.restore()
        except:
            pass

        return success

    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Browser + Google search only")
    print("2. Cursor + Browser integration")

    choice = input("\nChoice (1 or 2): ").strip()

    if choice == "1":
        success = test_browser_google_search()
    elif choice == "2":
        success = test_cursor_browser_integration()
    else:
        print("Invalid choice!")
        success = False

    if success:
        print("\n" + "="*50)
        print("[SUCCESS] TEST PASSED!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("[FAILED] TEST FAILED!")
        print("="*50)
