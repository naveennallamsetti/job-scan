import time
import random
import re
import os
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure file logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "scanner.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Import base helpers and individual portal modules
from backend.fetchers.base import parse_posted_ago_to_utc_datetime, generate_tailored_documents, calculate_match_score, check_url_is_expired
from backend.fetchers import (
    linkedin, naukri, indeed, foundit, shine, instahyre,
    cutshort, timesjobs, wellfound, remoteok, dice, glassdoor
)
from backend.database import get_db_connection, save_job, update_portal_scan_status
from backend.scan_state import scan_state_manager

PORTAL_MODULES = {
    "LinkedIn Jobs": linkedin,
    "Naukri.com": naukri,
    "Indeed": indeed,
    "Foundit (formerly Monster India)": foundit,
    "Shine": shine,
    "Instahyre": instahyre,
    "Cutshort": cutshort,
    "TimesJobs": timesjobs,
    "Wellfound (AngelList)": wellfound,
    "Remote OK": remoteok,
    "Dice": dice,
    "Glassdoor Jobs": glassdoor
}

# Profile Roles for querying
from backend.fetchers.base import PROFILE_ROLES

def is_older_than_30_days(posted_ago):
    if not posted_ago:
        return False
    s = posted_ago.lower()
    if any(x in s for x in ["month", "year"]):
        return True
    if "week" in s:
        match = re.search(r"(\d+)\s*week", s)
        if match and int(match.group(1)) >= 4:
            return True
    if "day" in s:
        match = re.search(r"(\d+)\s*day", s)
        if match and int(match.group(1)) > 30:
            return True
    return False

def crawl_single_portal_worker(portal_name, scan_id, past_24h=True):
    start_time = time.time()
    now_iso = datetime.now().isoformat()
    now_utc = datetime.now(timezone.utc)
    
    update_portal_scan_status(portal_name, "running")
    logging.info(f"[FETCHER] Started scanning portal: {portal_name}")
    
    module = PORTAL_MODULES.get(portal_name)
    if not module:
        err_msg = "Fetcher module not found"
        update_portal_scan_status(portal_name, "failed", jobs_found=0, duration=0.0, error_message=err_msg)
        scan_state_manager.update_portal_status(scan_id, portal_name, "failed", error=err_msg)
        logging.error(f"[FETCHER] Failed portal: {portal_name} - {err_msg}")
        return []
        
    jobs = []
    jobs_found = 0
    duplicates = 0
    
    try:
        # Crawl portal using a random DevOps role keyword
        keyword = random.choice(PROFILE_ROLES)
        jobs = module.fetch_jobs(keywords=keyword, past_24h=past_24h)
        
        # Save fresh jobs to database
        conn = get_db_connection()
        for job in jobs:
            posted_ago_str = job.get("posted_ago", "")
            posted_date_dt = parse_posted_ago_to_utc_datetime(posted_ago_str)
            
            # Enforce 24-hour freshness filter
            is_fresh = (posted_date_dt >= now_utc - timedelta(hours=24))
            if is_fresh:
                job["posted_date"] = posted_date_dt.isoformat()
                job["scan_id"] = scan_id
                job["job_url"] = job.get("url") or job.get("job_url")
                
                # Save job (UPSERT logic)
                res = save_job(job, conn=conn)
                if res == "inserted":
                    jobs_found += 1
                elif res == "updated":
                    # An update also counts as found but not duplicated (in the context of new entries)
                    jobs_found += 1
                elif res == "duplicate":
                    duplicates += 1
        conn.commit()
        conn.close()
        
        duration = round(time.time() - start_time, 2)
        update_portal_scan_status(
            portal_name, 
            "success", 
            jobs_found=jobs_found, 
            last_scan_time=now_iso, 
            duration=duration
        )
        
        # Update scan state manager thread-safely
        scan_state_manager.update_portal_status(
            scan_id=scan_id,
            portal_name=portal_name,
            status="completed",
            jobs_found=jobs_found,
            duplicates=duplicates
        )
        
        logging.info(f"[CRAWL VERIFY] Portal: {portal_name}, Fetched: {len(jobs)}, Fresh: {jobs_found}, Duplicates: {duplicates}, Duration: {duration}s")
        return jobs
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        err_msg = str(e)
        update_portal_scan_status(
            portal_name, 
            "failed", 
            jobs_found=0, 
            duration=duration, 
            error_message=err_msg
        )
        scan_state_manager.update_portal_status(
            scan_id=scan_id,
            portal_name=portal_name,
            status="failed",
            error=err_msg
        )
        logging.error(f"[FETCHER] Error crawling {portal_name}: {e}")
        return []

def fetch_all_jobs(portal_to_scan=None, past_24h=True, scan_id=None):
    if not scan_id:
        scan_id = scan_state_manager.start_scan(portal_to_scan=portal_to_scan)
        if not scan_id:
            return {"error": "Scan already running"}
            
    logging.info(f"[FETCHER] Initiating job scan. Scan ID: {scan_id}")
    
    portals_to_run = [portal_to_scan] if portal_to_scan else list(PORTAL_MODULES.keys())
    
    # Run fetchers using ThreadPoolExecutor(max_workers=4) for rate-limit protection
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(crawl_single_portal_worker, p, scan_id, past_24h): p for p in portals_to_run}
        for future in as_completed(futures):
            portal = futures[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"[FETCHER] Uncaught exception in worker for {portal}: {e}")
                
    scan_state_manager.complete_scan(scan_id)
    logging.info(f"[FETCHER] Scan completed. Scan ID: {scan_id}")
    return scan_state_manager.get_scan_status(scan_id)
