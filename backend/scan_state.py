import threading
import uuid
from datetime import datetime

class ScanStateManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.scans = {}

    def start_scan(self, scan_id=None, portal_to_scan=None):
        with self._lock:
            # Check if there is any scan currently running
            for sid, scan in self.scans.items():
                if scan.get("status") == "running":
                    return None
                    
            if not scan_id:
                scan_id = str(uuid.uuid4())
                
            self.scans[scan_id] = {
                "scan_id": scan_id,
                "status": "running",
                "progress": 0,
                "portals_scanned": [],
                "jobs_found": 0,
                "duplicates_skipped": 0,
                "portal_status": {},
                "failed_portals": [],
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "portal_to_scan": portal_to_scan
            }
            return scan_id

    def is_any_scan_running(self):
        with self._lock:
            return any(s.get("status") == "running" for s in self.scans.values())

    def update_portal_status(self, scan_id, portal_name, status, jobs_found=0, duplicates=0, error=None):
        with self._lock:
            if scan_id not in self.scans:
                return
            scan = self.scans[scan_id]
            scan["portal_status"][portal_name] = status
            scan["jobs_found"] += jobs_found
            scan["duplicates_skipped"] += duplicates
            if status == "failed":
                scan["failed_portals"].append(portal_name)
                if error:
                    scan["portal_status"][portal_name] = f"failed: {error}"
            
            if portal_name not in scan["portals_scanned"]:
                scan["portals_scanned"].append(portal_name)
                
            # Recalculate progress
            # Total portals to scan: either 1 or 12
            total_portals = 1 if scan["portal_to_scan"] else 12
            completed_portals = len(scan["portals_scanned"])
            scan["progress"] = min(int((completed_portals / total_portals) * 100), 100)

    def complete_scan(self, scan_id, status="completed"):
        with self._lock:
            if scan_id not in self.scans:
                return
            scan = self.scans[scan_id]
            scan["status"] = status
            scan["progress"] = 100
            scan["completed_at"] = datetime.now().isoformat()
            
            # Log scan history in database
            from backend.database import add_scan_history
            add_scan_history(
                scan_id=scan["scan_id"],
                started_at=scan["started_at"],
                completed_at=scan["completed_at"],
                jobs_found=scan["jobs_found"],
                duplicates=scan["duplicates_skipped"],
                failed_portals=scan["failed_portals"]
            )

    def get_scan_status(self, scan_id):
        with self._lock:
            return self.scans.get(scan_id)

    def get_latest_scan(self):
        with self._lock:
            if not self.scans:
                return None
            # Return the scan with the most recent started_at
            sorted_scans = sorted(self.scans.values(), key=lambda s: s["started_at"], reverse=True)
            return sorted_scans[0]

# Global instance of scan state manager
scan_state_manager = ScanStateManager()
