import json
import os
import time

HEALTH_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "source_health.json")

def update_source_health(source_domain, status_type):
    try:
        with open(HEALTH_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
        
    if source_domain not in data:
        data[source_domain] = {"success": 0, "failure": 0, "last_success": 0, "dominant_failure": None, "errors": {}}
        
    stats = data[source_domain]
    
    if status_type == "SUCCESS":
        stats["success"] += 1
        stats["last_success"] = time.time()
    else:
        stats["failure"] += 1
        stats["errors"][status_type] = stats["errors"].get(status_type, 0) + 1
        # Find dominant failure
        stats["dominant_failure"] = max(stats["errors"], key=stats["errors"].get)
        
    with open(HEALTH_FILE, "w") as f:
        json.dump(data, f, indent=2)
