"""
GNOME Theme Studio - Presets Management
Handles persistent storage of theme configurations in presets.json.
"""

import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_FILE = os.path.join(SCRIPT_DIR, "presets.json")


def load_presets() -> dict:
    """Loads all presets from presets.json."""
    if not os.path.exists(PRESETS_FILE):
        return {}
    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading presets: {e}")
        return {}


def save_preset(name: str, config: dict) -> bool:
    """Saves or updates a preset in presets.json."""
    if not name or not name.strip():
        return False
    presets = load_presets()
    presets[name.strip()] = config
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving preset: {e}")
        return False


def delete_preset(name: str) -> bool:
    """Deletes a user preset from presets.json."""
    presets = load_presets()
    if name in presets:
        del presets[name]
        try:
            with open(PRESETS_FILE, "w", encoding="utf-8") as f:
                json.dump(presets, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False
    return False
