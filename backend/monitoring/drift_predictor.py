import json
import os
import time
import hashlib
import logging

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "memory", "selector_memory.json")

def get_selector_id(portal, selector_type):
    s = f"{portal.lower()}_{selector_type.lower()}".encode('utf-8')
    return hashlib.sha256(s).hexdigest()

def update_selector_memory(portal, selector_type, success, zero_jobs):
    sid = get_selector_id(portal, selector_type)
    
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}
        
    if portal not in data:
        data[portal] = {}
        
    if sid not in data[portal]:
        data[portal][sid] = {
            "success": 0,
            "fail": 0,
            "zero_jobs": 0,
            "last_seen_success": time.time(),
            "selector_type": selector_type
        }
        
    stats = data[portal][sid]
    
    if success:
        stats["success"] += 1
        stats["last_seen_success"] = time.time()
    else:
        stats["fail"] += 1
        
    if zero_jobs:
        stats["zero_jobs"] += 1
        
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)
        
def compute_drift_score(portal, selector_type):
    sid = get_selector_id(portal, selector_type)
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
        stats = data.get(portal, {}).get(sid, {})
    except:
        stats = {}
        
    success = stats.get("success", 0)
    fail = stats.get("fail", 0)
    zero = stats.get("zero_jobs", 0)
    
    total = success + fail
    if total == 0:
        return 0
        
    failure_rate = (fail + zero) / total
    age_penalty = max(0, (time.time() - stats.get("last_seen_success", time.time())) / 86400)
    
    score = (failure_rate * 70) + min(age_penalty, 30)
    return min(100, score)
