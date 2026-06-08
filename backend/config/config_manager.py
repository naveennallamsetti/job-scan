import json
import os

CONFIG_DIR = os.path.dirname(__file__)
ACTIVE_FILE = os.path.join(CONFIG_DIR, "selectors_active.json")

def get_active_selector(portal):
    try:
        with open(ACTIVE_FILE, "r") as f:
            data = json.load(f)
            # Support both old string format and new dict format for backward compatibility
            val = data.get(portal.lower())
            if isinstance(val, str):
                return {"primary": val, "structural": None}
            return val or {"primary": None, "structural": None}
    except:
        return {"primary": None, "structural": None}
