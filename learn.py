import pyautogui
import time
import json
import os
from logger import log_action

KB_FILE = os.path.join("knowledge_base", "kb.json")
IMAGES_DIR = os.path.join("knowledge_base", "images")

def get_knowledge_base():
    """Loads the knowledge base from the JSON file."""
    if not os.path.exists(KB_FILE) or os.path.getsize(KB_FILE) == 0:
        return {}
    with open(KB_FILE, 'r') as f:
        return json.load(f)

def save_knowledge_base(data):
    """Saves the knowledge base to the JSON file."""
    with open(KB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def learn_object():
    """Guides the user to teach the system a new object."""
    try:
        # 1. Get object name from user
        object_name = input("Enter a name for the object to teach (e.g., 'trash can'): ").strip()
        if not object_name:
            log_action("Object name cannot be empty. Aborting.", is_error=True)
            return

        log_action(f"Attempting to learn new object: '{object_name}'")

        kb = get_knowledge_base()
        if object_name in kb:
            overwrite = input(f"Object '{object_name}' already exists. Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                log_action(f"User chose not to overwrite '{object_name}'. Aborting.")
                return
            log_action(f"User chose to overwrite existing object '{object_name}'.")

        # 2. Guide user to select the region
        print("\nNow, let's capture the object's image. You have 3 seconds...")
        time.sleep(3)

        input("Move mouse to the TOP-LEFT corner of the object, then press Enter...")
        pos1 = pyautogui.position()
        log_action(f"Top-left corner captured at: {pos1}")

        input("Now, move mouse to the BOTTOM-RIGHT corner and press Enter...")
        pos2 = pyautogui.position()
        log_action(f"Bottom-right corner captured at: {pos2}")

        # 3. Calculate region and take screenshot
        left = min(pos1.x, pos2.x)
        top = min(pos1.y, pos2.y)
        width = abs(pos1.x - pos2.x)
        height = abs(pos1.y - pos2.y)

        if width == 0 or height == 0:
            log_action(f"Invalid region: width={width}, height={height}. Aborting.", is_error=True)
            return

        log_action(f"Capturing a {width}x{height} region at ({left}, {top}).")
        screenshot = pyautogui.screenshot(region=(left, top, width, height))

        # 4. Save the screenshot
        safe_filename = f"{object_name.lower().replace(' ', '_')}.png"
        image_path = os.path.join(IMAGES_DIR, safe_filename)
        screenshot.save(image_path)
        log_action(f"Screenshot saved to: {image_path}")

        # 5. Update the knowledge base
        kb[object_name] = image_path
        save_knowledge_base(kb)
        log_action(f"SUCCESS: Knowledge base updated for '{object_name}'.")
        print(f"\nI have learned what '{object_name}' looks like.")

    except pyautogui.FailSafeException:
        log_action("Fail-safe triggered by user. Aborting learning process.", is_error=True)
    except KeyboardInterrupt:
        log_action("Operation cancelled by user (KeyboardInterrupt).", is_error=True)
    except Exception as e:
        log_action(f"An unexpected error occurred during learning: {e}", is_error=True)

if __name__ == "__main__":
    log_action("Learning Mode session started.")
    print("--- Smart Cursor Learning Mode ---")
    learn_object()
    log_action("Learning Mode session finished.")