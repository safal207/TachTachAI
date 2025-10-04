import os
from playwright.sync_api import sync_playwright, expect

def verify_js_execution():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        dashboard_path = "file://" + os.path.abspath("qa_dashboard.html")

        # 1. Go to the local dashboard file
        page.goto(dashboard_path)

        # 2. The Ultimate Test:
        # Check if the simple, hardcoded JS command executed on page load.
        prompt_textarea = page.locator("#prompt-output")

        # We expect the debug message to be present.
        expect(prompt_textarea).to_have_value("DEBUG: DOMContentLoaded fired. JS is running.", timeout=5000)

        # 3. Take a screenshot for final proof.
        screenshot_path = "jules-scratch/verification/verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Final diagnostic screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    verify_js_execution()