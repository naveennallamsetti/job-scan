import threading
import time
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.database import get_db_connection, save_job, add_log, update_job_status, update_job_details
from backend.fetcher import fetch_all_jobs, generate_tailored_documents, check_url_is_expired

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(str(msg).encode('ascii', 'replace').decode('ascii'))
        except Exception:
            pass

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
        print("[SCHEDULER] Starting 30-minute job crawl...")
        add_log("scrape", "Starting automated 30-minute scan across configured portals...")
    else:
        print(f"[SCHEDULER] Starting targeted crawl for '{portal_to_scan}'...")
        add_log("scrape", f"Starting manual targeted scan for '{portal_to_scan}'...")
    
    jobs = fetch_all_jobs(portal_to_scan)
    new_jobs_count = 0
    
    # Check against database for duplicates
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for job in jobs:
        cursor.execute("SELECT id FROM jobs WHERE id = ?", (job["id"],))
        exists = cursor.fetchone()
        
        if not exists:
            # Generate tailored docs right away for the new job
            cl, res = generate_tailored_documents(job)
            job["cover_letter"] = cl
            job["resume_customized"] = res
            save_job(job)
            new_jobs_count += 1
            add_log("scrape", f"New job: {job['title']} @ {job['company']} ({job['match_score']}% match) found on {job['portal']}")
        else:
            # Update existing
            save_job(job)
            
    conn.close()
    
    portal_log_name = portal_to_scan if portal_to_scan else "all portals"
    add_log("scrape", f"Crawl complete for {portal_log_name}. Discovered {new_jobs_count} new matching jobs.")
    print(f"[SCHEDULER] Job crawl complete. Discovered {new_jobs_count} new jobs.")

def verify_stored_jobs_freshness():
    global last_verify_time, next_verify_time
    last_verify_time = datetime.now()
    next_verify_time = last_verify_time + timedelta(minutes=60)
    
    print("[SCHEDULER] Starting background stored jobs freshness check...")
    add_log("database", "Starting automated parallel freshness check of stored job URLs...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, url, portal FROM jobs WHERE applied = 0")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    from backend.fetcher import check_url_is_expired, is_older_than_30_days
    
    expired_count = 0
    updated_count = 0
    checked_count = 0
    
    def check_job(job):
        job_id = job["id"]
        title = job["title"]
        company = job["company"]
        url = job["url"]
        portal = job["portal"]
        
        job_dict = {"posted_ago": None}
        try:
            is_expired = check_url_is_expired(url, job_dict)
            return {
                "id": job_id,
                "title": title,
                "company": company,
                "portal": portal,
                "is_expired": is_expired,
                "new_posted_ago": job_dict.get("posted_ago")
            }
        except Exception as e:
            return {
                "id": job_id,
                "title": title,
                "company": company,
                "portal": portal,
                "is_expired": False,
                "new_posted_ago": None,
                "error": str(e)
            }

    # Run checks in parallel using ThreadPoolExecutor
    results = []
    max_workers = 25
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_job, row): row for row in rows}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            checked_count += 1
            if checked_count % 50 == 0:
                print(f"[SCHEDULER] Checked {checked_count}/{len(rows)} URLs...")
                
    # Now process results in the database using a single transaction
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for res in results:
        job_id = res["id"]
        title = res["title"]
        company = res["company"]
        portal = res["portal"]
        is_expired = res["is_expired"]
        new_posted_ago = res["new_posted_ago"]
        
        if is_expired:
            cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            expired_count += 1
            if expired_count <= 25: # Cap detailed logs to prevent bloat
                cursor.execute(
                    "INSERT INTO logs (timestamp, type, description, status) VALUES (?, ?, ?, ?)",
                    (datetime.now().strftime("%H:%M:%S"), "database", f"Purged expired listing: {title} @ {company} ({portal})", "warning")
                )
                safe_print(f"[SCHEDULER] Purged expired listing: {title} @ {company} ({portal})")
        elif new_posted_ago:
            if is_older_than_30_days(new_posted_ago):
                cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                expired_count += 1
                if expired_count <= 25:
                    cursor.execute(
                        "INSERT INTO logs (timestamp, type, description, status) VALUES (?, ?, ?, ?)",
                        (datetime.now().strftime("%H:%M:%S"), "database", f"Purged dynamically aged-out listing (>30 days): {title} @ {company} ({portal})", "warning")
                    )
                    safe_print(f"[SCHEDULER] Purged aged-out listing: {title} @ {company} ({portal}) - {new_posted_ago}")
            else:
                cursor.execute("UPDATE jobs SET posted_ago = ? WHERE id = ?", (new_posted_ago, job_id))
                updated_count += 1
                if updated_count <= 25:
                    safe_print(f"[SCHEDULER] Updated posting age for {title} @ {company}: {new_posted_ago}")
                    
    # Write final summaries
    now_str = datetime.now().strftime("%H:%M:%S")
    cursor.execute(
        "INSERT INTO logs (timestamp, type, description, status) VALUES (?, ?, ?, ?)",
        (now_str, "database", f"Parallel freshness sweep complete. Checked {checked_count} URLs, purged {expired_count} expired/stale listings, updated {updated_count} ages.", "success")
    )
    conn.commit()
    conn.close()
    
    safe_print(f"[SCHEDULER] Parallel freshness sweep complete. Checked {checked_count} URLs, purged {expired_count} expired/stale listings, updated {updated_count} ages.")

def run_auto_apply():
    global last_apply_time, next_apply_time
    last_apply_time = datetime.now()
    next_apply_time = last_apply_time + timedelta(minutes=30)
    
    print("[SCHEDULER] Starting 30-minute auto-apply cycle...")
    
    # Find unapplied jobs with match score >= 85%
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE applied = 0 AND match_score >= 85 ORDER BY match_score DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        job = dict(row)
        # Tailor documents if not already done
        cl, res = generate_tailored_documents(job)
        update_job_details(job["id"], cl, res)
        
        # Update applied status
        update_job_status(job["id"], "applied", True)
        
        # Add detailed apply log
        add_log("apply", f"Auto-applied: {job['title']} @ {job['company']} via {job['portal']}. Resume and cover letter uploaded.")
        safe_print(f"[SCHEDULER] Auto-applied: {job['title']} @ {job['company']}")
    else:
        add_log("apply", "Auto-apply cycle executed. No new jobs above 85% match threshold to apply.", "success")
        print("[SCHEDULER] Auto-apply cycle executed. No eligible jobs found.")

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
                print(f"Error during scan_jobs: {e}")
                add_log("scrape", f"Crawl failed: {e}", "failed")
                next_scan_time = datetime.now() + timedelta(minutes=30)
                
        # Check apply loop (30 minutes)
        if next_apply_time and now >= next_apply_time:
            try:
                run_auto_apply()
            except Exception as e:
                print(f"Error during run_auto_apply: {e}")
                add_log("apply", f"Auto-apply failed: {e}", "failed")
                next_apply_time = datetime.now() + timedelta(minutes=30)
                
        # Check verify loop (60 minutes)
        if next_verify_time and now >= next_verify_time:
            try:
                verify_stored_jobs_freshness()
            except Exception as e:
                print(f"Error during verify_stored_jobs_freshness: {e}")
                add_log("database", f"Freshness sweep failed: {e}", "failed")
                next_verify_time = datetime.now() + timedelta(minutes=60)
                
        time.sleep(5)

def start_scheduler():
    global scheduler_thread, is_running
    if not is_running:
        is_running = True
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
        print("[SCHEDULER] Background daemon thread started.")

def stop_scheduler():
    global is_running
    is_running = False
    print("[SCHEDULER] Stopping background daemon...")
