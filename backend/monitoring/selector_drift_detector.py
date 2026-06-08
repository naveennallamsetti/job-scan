import json
import logging

def detect_selector_drift(portal, expected_selector, extracted_jobs, dom_classification):
    # Expected jobs > 0 implies we assume the portal has jobs if it's a valid page
    if extracted_jobs == 0 and dom_classification.get("classification") == "VALID_JOB_PAGE":
        output = {
            "portal": portal,
            "status": "SELECTOR_DRIFT_DETECTED",
            "old_selector": expected_selector,
            "suggested_candidates": [] # Will be populated by auto_repair_suggester
        }
        logging.warning(f"\n[SELECTOR_DRIFT]\n{json.dumps(output, indent=2)}\n")
        return output
    return None
