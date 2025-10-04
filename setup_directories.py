"""
Setup script to create all necessary directories for TachTachAI framework.
"""
import os

def create_directories():
    """Creates all required directories if they don't exist."""
    directories = [
        "knowledge_base",
        "knowledge_base/visual_baselines",
        "reports",
        "reports/screenshots",
        "reports/history",
        "reports/history/reports",
        "reports/history/recommendations"
    ]

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"[+] Created directory: {directory}")
        else:
            print(f"[+] Directory already exists: {directory}")

    # Create empty JSON files if they don't exist
    json_files = {
        os.path.join("knowledge_base", "kb.json"): {},
        os.path.join("knowledge_base", "scenarios.json"): {}
    }

    import json
    for filepath, default_content in json_files.items():
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                json.dump(default_content, f, indent=4)
            print(f"[+] Created file: {filepath}")
        else:
            print(f"[+] File already exists: {filepath}")

    print("\n[OK] Setup complete! All directories and files are ready.")

if __name__ == "__main__":
    create_directories()
