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

import httpx
import logging

global_client = httpx.Client(timeout=15.0, follow_redirects=True)
global_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def fetch_job_page_html(url, use_playwright_fallback=True, verification_selector=None, portal_name="Unknown"):
    try:
        from backend.monitoring.dom_classifier import classify_dom
        from backend.monitoring.scraper_metrics import global_metrics
        from backend.monitoring.dom_fingerprint import verify_structural_fingerprint
        from backend.monitoring.drift_predictor import compute_drift_score, update_selector_memory
        
        primary_selector = verification_selector
        structural_selector = None
        if isinstance(verification_selector, dict):
            primary_selector = verification_selector.get("primary")
            structural_selector = verification_selector.get("structural")

        # ---------------------------------------------------------
        # PHASE A: Pre-emptive Drift Check
        # ---------------------------------------------------------
        score = compute_drift_score(portal_name, "primary")
        if score > 85:
            logging.warning(f"\\n[PREDICTIVE_DRIFT] {portal_name} primary selector has drift score {score:.1f}. Preemptively switching to structural.\\\n")
            primary_selector = None # Force fallback to structural immediately
        elif score > 70:
            logging.warning(f"\\n[PREDICTIVE_DRIFT] {portal_name} primary selector at high risk (score {score:.1f}).\\\n")

        resp = global_client.get(url, headers=global_headers)
        html = resp.text
        dom_health = classify_dom(html, portal_name)
        
        blocked = False
        if resp.status_code in [403, 429] or dom_health["classification"] in ["BOT_BLOCK_PAGE", "CAPTCHA_PAGE"]:
            blocked = True
            
        jobs_found = -1
        
        if primary_selector and not blocked:
            from bs4 import BeautifulSoup
            s = BeautifulSoup(html, 'html.parser')
            jobs_found = len(s.select(primary_selector))
            
            if jobs_found == 0:
                structural_nodes = verify_structural_fingerprint(html, structural_selector)
                if len(structural_nodes) > 0:
                    logging.info(f"\n[ZERO_DRIFT] {portal_name} primary selector failed, structural matched {len(structural_nodes)} jobs.\n")
                    jobs_found = len(structural_nodes)
                else:
                    blocked = True
            
            # Hook memory tracking
            success = jobs_found > 0
            zero_event = (jobs_found == 0 and dom_health["classification"] == "VALID_JOB_PAGE")
            update_selector_memory(portal_name, "primary", success, zero_event)
                
        # If we skipped primary due to score > 85, evaluate structural explicitly
        elif structural_selector and not blocked:
            structural_nodes = verify_structural_fingerprint(html, structural_selector)
            jobs_found = len(structural_nodes)
            if jobs_found == 0:
                blocked = True
                
            success = jobs_found > 0
            zero_event = (jobs_found == 0 and dom_health["classification"] == "VALID_JOB_PAGE")
            update_selector_memory(portal_name, "structural", success, zero_event)

        if use_playwright_fallback and blocked:
            logging.info(f"\nBot block or 0 jobs detected on {url}. Triggering Playwright (Not a failure)...\n")
            from backend.fetchers.playwright_fetcher import fetch_with_playwright_bridged
            pw_html, pw_cookies, pw_ua = fetch_with_playwright_bridged(url)
            
            for c in pw_cookies:
                global_client.cookies.set(c['name'], c['value'], domain=c['domain'])
            global_headers["User-Agent"] = pw_ua
            
            pw_jobs = -1
            if primary_selector:
                from bs4 import BeautifulSoup
                s2 = BeautifulSoup(pw_html, 'html.parser')
                pw_jobs = len(s2.select(primary_selector))
                update_selector_memory(portal_name, "primary", pw_jobs > 0, pw_jobs == 0)
                
            global_metrics.log_cycle(portal_name, resp.status_code, "PLAYWRIGHT", True, max(0, pw_jobs), pw_jobs == 0)
            return pw_html
            
        global_metrics.log_cycle(portal_name, resp.status_code, "HTTPX", True, max(0, jobs_found), jobs_found == 0)
        return html
    except Exception as e:
        if use_playwright_fallback:
            logging.warning(f"HTTPX error {url}: {e}. Bridging Playwright...")
            from backend.fetchers.playwright_fetcher import fetch_with_playwright
            return fetch_with_playwright(url)
        return ""

def crawl_jobs():
    import datetime
    logging.info("Starting a crawl_jobs run.")
    from backend.fetchers.linkedin import fetch_jobs as li_fetch
    from backend.fetchers.naukri import fetch_jobs as nk_fetch
    
    # We will test just linkedin and naukri to avoid a huge log
    all_jobs = []
    
    try:
        j1 = li_fetch("Software Engineer", past_24h=True)
        if j1: all_jobs.extend(j1)
    except Exception as e:
        logging.error(f"Failed li: {e}")
        
    try:
        j2 = nk_fetch("Software Engineer", past_24h=True)
        if j2: all_jobs.extend(j2)
    except Exception as e:
        logging.error(f"Failed nk: {e}")
        
    logging.info(f"Extracted {len(all_jobs)} total jobs.")
    
    from backend.monitoring.health_reporter import generate_health_report
    generate_health_report()
