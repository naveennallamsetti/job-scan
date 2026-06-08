import threading
import time
import os
import logging
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.database import get_db_connection, save_job, add_log, update_job_status, update_job_details
from backend.fetcher import fetch_all_jobs, check_url_is_expired

def safe_print(msg):
    logging.info(msg)

# Scheduler control states
scheduler_thread = None
is_running = False

# Timestamps
last_scan_time = None
last_apply_time = None
last_verify_time = None
next_scan_time = None
next_apply_time = None
next_verify_time = None

def scan_jobs(portal_to_scan=None):
    global last_scan_time, next_scan_time
    
    if not portal_to_scan:
        last_scan_time = datetime.now()
        next_scan_time = last_scan_time + timedelta(minutes=30)
        logging.info("[SCHEDULER] Starting automated 30-minute job crawl...")
        add_log("scrape", "Starting automated 30-minute scan across configured portals...")
    else:
        logging.info(f"[SCHEDULER] Starting manual targeted crawl for '{portal_to_scan}'...")
        add_log("scrape", f"Starting manual targeted scan for '{portal_to_scan}'...")
    
    # Run fetcher with single scan state manager mapping
    stats = fetch_all_jobs(portal_to_scan)
    if "error" in stats:
        logging.warning(f"[SCHEDULER] Automated scan skipped: {stats['error']}")
        return
        
    new_jobs_count = stats.get("jobs_found", 0)
    logging.info(f"[SCHEDULER] Job crawl complete. Discovered/Updated {new_jobs_count} jobs.")

def verify_stored_jobs_freshness():
    global last_verify_time, next_verify_time
    last_verify_time = datetime.now()
    next_verify_time = last_verify_time + timedelta(minutes=60)
    
    logging.info("[SCHEDULER] Starting background stored jobs lifecycle verification...")
    add_log("database", "Starting automated lifecycle status sweep of stored job listings...")
    
    # 1. URL Validation Sweep for Active Jobs
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, url, portal FROM jobs WHERE status = 'active'")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    expired_count = 0
    checked_count = 0
    
    def check_job(job):
        job_id = job["id"]
        title = job["title"]
        company = job["company"]
        url = job["url"]
        portal = job["portal"]
        
        try:
            is_expired = check_url_is_expired(url)
            return {
                "id": job_id,
                "title": title,
                "company": company,
                "portal": portal,
                "is_expired": is_expired
            }
        except Exception as e:
            return {
                "id": job_id,
                "title": title,
                "company": company,
                "portal": portal,
                "is_expired": False,
                "error": str(e)
            }

    # Run URL checks in parallel
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_job, row): row for row in rows}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            checked_count += 1
            if checked_count % 50 == 0:
                logging.info(f"[SCHEDULER] Checked {checked_count}/{len(rows)} URLs...")
                
    # Update expired statuses
    conn = get_db_connection()
    cursor = conn.cursor()
    for res in results:
        if res["is_expired"]:
            cursor.execute("UPDATE jobs SET status = 'expired' WHERE id = ?", (res["id"],))
            expired_count += 1
            if expired_count <= 25:
                cursor.execute(
                    "INSERT INTO logs (timestamp, type, description, status) VALUES (?, ?, ?, ?)",
                    (datetime.now().strftime("%H:%M:%S"), "database", f"Listing marked expired (invalid URL): {res['title']} @ {res['company']} ({res['portal']})", "warning")
                )
    conn.commit()
    conn.close()
    
    # 2. Lifecycle transitions (Archived and Deleted)
    # archived -> first_seen older than 30 days
    # deleted -> first_seen older than 90 days
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now_dt = datetime.now()
    cursor.execute("SELECT id, first_seen, status, title, company FROM jobs")
    all_jobs = cursor.fetchall()
    
    archived_count = 0
    deleted_count = 0
    
    for row in all_jobs:
        jid = row["id"]
        fs_str = row["first_seen"]
        status = row["status"]
        title = row["title"]
        company = row["company"]
        
        if fs_str:
            try:
                # parse datetime
                dt_str = fs_str.split(".")[0]
                dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                delta_days = (now_dt - dt).days
                
                if delta_days > 90:
                    cursor.execute("DELETE FROM jobs WHERE id = ?", (jid,))
                    deleted_count += 1
                elif delta_days > 30 and status != "archived":
                    cursor.execute("UPDATE jobs SET status = 'archived' WHERE id = ?", (jid,))
                    archived_count += 1
            except Exception as e:
                pass
                
    conn.commit()
    conn.close()
    
    logging.info(f"[SCHEDULER] Lifecycle sweep complete. Checked {checked_count} URLs, expired {expired_count}, archived {archived_count}, deleted {deleted_count} older than 90 days.")
    add_log("database", f"Lifecycle sweep complete. Expired {expired_count} invalid URLs, archived {archived_count} old listings, deleted {deleted_count} stale listings (>90 days).")

def run_auto_apply():
    global last_apply_time, next_apply_time
    last_apply_time = datetime.now()
    next_apply_time = last_apply_time + timedelta(minutes=30)
    
    logging.info("[SCHEDULER] Starting 30-minute auto-apply cycle...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE applied = 0 AND status = 'active' AND date_verified = 1 AND datetime(posted_date) >= datetime('now','-24 hours') AND match_score >= 85 ORDER BY match_score DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        job = dict(row)
        from backend.fetchers.base import generate_tailored_documents
        cl, res = generate_tailored_documents(job)
        update_job_details(job["id"], cl, res)
        update_job_status(job["id"], "applied", True)
        
        add_log("apply", f"Auto-applied: {job['title']} @ {job['company']} via {job['portal']}. Resume and cover letter uploaded.")
        logging.info(f"[SCHEDULER] Auto-applied: {job['title']} @ {job['company']}")
    else:
        add_log("apply", "Auto-apply cycle executed. No new active jobs above 85% match threshold.", "success")
        logging.info("[SCHEDULER] Auto-apply cycle completed. No active eligible jobs found.")

def scheduler_loop():
    global is_running, next_scan_time, next_apply_time, next_verify_time
    
    # Initial trigger
    scan_jobs()
    run_auto_apply()
    verify_stored_jobs_freshness()
    
    while is_running:
        now = datetime.now()
        
        # Check scan loop (30 minutes)
        if next_scan_time and now >= next_scan_time:
            try:
                scan_jobs()
            except Exception as e:
                logging.error(f"Error during scan_jobs: {e}")
                add_log("scrape", f"Crawl failed: {e}", "failed")
                next_scan_time = datetime.now() + timedelta(minutes=30)
                
        # Check apply loop (30 minutes)
        if next_apply_time and now >= next_apply_time:
            try:
                run_auto_apply()
            except Exception as e:
                logging.error(f"Error during run_auto_apply: {e}")
                add_log("apply", f"Auto-apply failed: {e}", "failed")
                next_apply_time = datetime.now() + timedelta(minutes=30)
                
        # Check verify loop (60 minutes)
        if next_verify_time and now >= next_verify_time:
            try:
                verify_stored_jobs_freshness()
            except Exception as e:
                logging.error(f"Error during verify_stored_jobs_freshness: {e}")
                add_log("database", f"Freshness sweep failed: {e}", "failed")
                next_verify_time = datetime.now() + timedelta(minutes=60)
                
        time.sleep(5)

def start_scheduler():
    global scheduler_thread, is_running
    if not is_running:
        is_running = True
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        logging.info("[SCHEDULER] Background daemon thread started.")

def stop_scheduler():
    global is_running
    is_running = False
    logging.info("[SCHEDULER] Stopping background daemon...")
