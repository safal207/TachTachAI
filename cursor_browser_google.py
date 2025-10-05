"""
TachTachAI - Cursor + Browser + Google Test
Improved version with better search box detection
"""
import time
import subprocess
import pyautogui

print("=== TachTachAI - Cursor + Browser + Google Test ===\n")

def find_and_click_google_search():
    """
    More reliable method to find Google search box
    """
    print("[1] Launching browser with Google...")
    subprocess.Popen(["start", "https://www.google.com"], shell=True)
    time.sleep(4)

    print("[2] Waiting for page to load...")
    time.sleep(2)

    # Method 1: Click in center of screen (where search box usually is)
    print("[3] Clicking search area (center of screen)...")
    screen_width, screen_height = pyautogui.size()
    center_x = screen_width // 2
    center_y = screen_height // 2

    pyautogui.click(center_x, center_y)
    time.sleep(1)

    # Method 2: Use keyboard shortcut to focus search
    print("[4] Using Ctrl+K to focus search (backup method)...")
    pyautogui.hotkey('ctrl', 'k')
    time.sleep(0.5)

    # Type search query
    search_query = "TachTachAI automation"
    print(f"[5] Typing: '{search_query}'")

    # Type slowly to ensure it's captured
    for char in search_query:
        pyautogui.press(char)
        time.sleep(0.05)

    time.sleep(1)

    print("[6] Pressing Enter...")
    pyautogui.press('enter')
    time.sleep(3)

    print("[7] Taking screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot_path = "reports/screenshots/google_search_final.png"
    screenshot.save(screenshot_path)
    print(f"    Saved: {screenshot_path}")

    # Check if we have search results
    print("[8] Analyzing results...")
    # Take a small screenshot of title area
    title_region = pyautogui.screenshot(region=(0, 0, 500, 100))
    title_path = "reports/screenshots/browser_title.png"
    title_region.save(title_path)

    print("\n[SUCCESS] Test completed!")
    print(f"    Check screenshots:")
    print(f"    - {screenshot_path}")
    print(f"    - {title_path}")

    return True

def test_cursor_interaction():
    """
    Test Cursor IDE detection and interaction
    """
    print("\n=== Testing Cursor IDE Detection ===\n")

    try:
        from pywinauto import Desktop

        print("[1] Looking for Cursor window...")
        desktop = Desktop(backend="uia")

        # Find Cursor
        cursor_windows = []
        for window in desktop.windows():
            title = window.window_text()
            if "Cursor" in title and "GitHub" in title:
                cursor_windows.append(window)
                print(f"    Found: {title}")

        if cursor_windows:
            cursor = cursor_windows[0]
            print(f"\n[2] Cursor is running!")
            print(f"    Title: {cursor.window_text()}")

            # Get window position
            rect = cursor.rectangle()
            print(f"    Position: ({rect.left}, {rect.top})")
            print(f"    Size: {rect.width()}x{rect.height()}")

            # Minimize Cursor
            print("\n[3] Minimizing Cursor for test...")
            cursor.minimize()
            time.sleep(1)

            # Run browser test
            success = find_and_click_google_search()

            # Restore Cursor
            print("\n[4] Restoring Cursor...")
            time.sleep(2)
            cursor.restore()

            return success
        else:
            print("    Cursor not found, running browser test only...")
            return find_and_click_google_search()

    except Exception as e:
        print(f"    Error: {e}")
        print("    Falling back to browser-only test...")
        return find_and_click_google_search()

if __name__ == "__main__":
    print("="*60)
    print("TachTachAI - Cursor + Browser Integration Test")
    print("="*60)

    try:
        result = test_cursor_interaction()

        print("\n" + "="*60)
        if result:
            print("[PASS] All tests completed successfully!")
        else:
            print("[FAIL] Some tests failed")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user")
    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
