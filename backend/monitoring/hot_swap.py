import json
import os
import shutil
import time
import logging

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
ACTIVE_FILE = os.path.join(CONFIG_DIR, "selectors_active.json")
VERSIONS_DIR = os.path.join(CONFIG_DIR, "selector_versions")

HEALS_THIS_SESSION = 0
MAX_AUTO_HEALS_PER_SESSION = 3

def apply_new_selector(portal, new_selector):
    global HEALS_THIS_SESSION
    if HEALS_THIS_SESSION >= MAX_AUTO_HEALS_PER_SESSION:
        logging.error(f"[AUTO_HEAL] Max heals ({MAX_AUTO_HEALS_PER_SESSION}) reached for session.")
        return False
        
    portal = portal.lower()
    
    # Backup current active file
    timestamp = int(time.time())
    backup_path = os.path.join(VERSIONS_DIR, f"backup_{timestamp}.json")
    if os.path.exists(ACTIVE_FILE):
        shutil.copy2(ACTIVE_FILE, backup_path)
        
    try:
        with open(ACTIVE_FILE, "r") as f:
            data = json.load(f)
            
        old_selector = data.get(portal)
        data[portal] = new_selector
        
        with open(ACTIVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
        # Also save portal specific version
        portal_v_path = os.path.join(VERSIONS_DIR, f"{portal}_{timestamp}.json")
        with open(portal_v_path, "w") as f:
            json.dump({"portal": portal, "selector": new_selector, "timestamp": timestamp}, f)
            
        HEALS_THIS_SESSION += 1
        logging.info(f"\n[HOT_SWAP] Applied {new_selector} to {portal}. Backup at {backup_path}\n")
        return backup_path
    except Exception as e:
        logging.error(f"Failed to apply selector: {e}")
        return False

def rollback_selector(backup_path):
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, ACTIVE_FILE)
        logging.warning(f"\n[ROLLBACK_TRIGGERED] Reverted to {backup_path}\n")
        return True
    return False
