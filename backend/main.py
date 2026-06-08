from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import (
    init_db, get_all_jobs, get_logs, update_job_status, 
    update_job_details, add_log, get_portal_summaries, get_db_connection
)
from backend.scheduler import start_scheduler, stop_scheduler, scan_jobs, run_auto_apply
import backend.scheduler as sched
from backend.scan_state import scan_state_manager
from backend.fetcher import fetch_all_jobs

app = FastAPI(title="JobFusion AI Production Aggregator Backend", version="2.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusUpdate(BaseModel):
    value: bool

@app.on_event("startup")
def startup_event():
    import logging
    from backend.database import get_db_connection, init_db, purge_old_jobs
    
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Recalculate age_days based on posted_date if we had robust backward compatibility here, but purge_old_jobs handles cleanup
    purge_old_jobs()
    
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE age_days <= 1 AND status='active'")
    fresh_jobs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status='archived'")
    archived = cursor.fetchone()[0]
    
    conn.close()
    
    logging.info(f"
[AUDIT]
Total Jobs: {total_jobs}
Fresh Jobs: {fresh_jobs}
Archived: {archived}
")
    
    logging.info(f"
[AUDIT]
Total Jobs: {total_jobs}
Fresh Jobs: {fresh_jobs}
Archived: {archived}
")
        
    start_scheduler()
    add_log("system", "Production Job Monitoring Agent Core Online.", "success")

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

@app.post("/api/scan")
def trigger_manual_scan(background_tasks: BackgroundTasks, portal: Optional[str] = None):
    # Enforce only one active scan
    if scan_state_manager.is_any_scan_running():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan already running"
        )
        
    import uuid
    scan_id = str(uuid.uuid4())
    scan_state_manager.start_scan(scan_id=scan_id, portal_to_scan=portal)
    
    # Run fetcher as a background task
    background_tasks.add_task(fetch_all_jobs, portal_to_scan=portal, past_24h=True, scan_id=scan_id)
    
    return {"scan_id": scan_id}

@app.get("/api/scan/status/{scan_id}")
def get_scan_status(scan_id: str):
    status_info = scan_state_manager.get_scan_status(scan_id)
    if not status_info:
        # Fallback to checking the latest scan if requested 'latest'
        if scan_id == "latest":
            latest = scan_state_manager.get_latest_scan()
            if latest:
                return latest
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan ID not found"
        )
    return status_info

@app.get("/api/jobs")
def get_jobs_list(
    portal: Optional[str] = None,
    min_match: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    offset = (page - 1) * limit
    jobs = get_all_jobs()
    
    # Filter out 'expired' status jobs
    filtered = [j for j in jobs if j.get("status") != "expired"]
    
    if portal:
        portal_list = [p.strip() for p in portal.split(",") if p.strip()]
        filtered = [j for j in filtered if j.get("portal") in portal_list]
    if min_match is not None:
        filtered = [j for j in filtered if j.get("match", 0) >= min_match]
    if search:
        q = search.lower().strip()
        filtered = [
            j for j in filtered
            if q in j.get("title", "").lower() or q in j.get("company", "").lower() or q in j.get("description", "").lower()
        ]
        
    total_count = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "jobs": paginated
    }

@app.get("/api/jobs/recent")
def get_recent_jobs_list(page: int = 1, limit: int = 50):
    offset = (page - 1) * limit
    jobs = get_all_jobs()
    
    now_dt = datetime.now()
    recent = []
    for j in jobs:
        if j.get("status") == "expired":
            continue
        fs = j.get("first_seen")
        if fs:
            try:
                dt_str = fs.split(".")[0]
                dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                if (now_dt - dt).total_seconds() <= 86400: # 24h
                    recent.append(j)
            except Exception:
                pass
                
    total_count = len(recent)
    paginated = recent[offset:offset + limit]
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "jobs": paginated
    }

@app.get("/api/jobs/search")
def get_searched_jobs(
    q: str = "",
    portal: Optional[str] = None,
    match_score: Optional[int] = None,
    location: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    offset = (page - 1) * limit
    jobs = get_all_jobs()
    
    filtered = [j for j in jobs if j.get("status") != "expired"]
    
    if q:
        query = q.lower().strip()
        filtered = [
            j for j in filtered
            if query in j.get("title", "").lower() or query in j.get("company", "").lower() or query in j.get("description", "").lower()
        ]
    if portal:
        portal_list = [p.strip() for p in portal.split(",") if p.strip()]
        filtered = [j for j in filtered if j.get("portal") in portal_list]
    if match_score is not None:
        filtered = [j for j in filtered if j.get("match", 0) >= match_score]
    if location:
        loc = location.lower().strip()
        filtered = [j for j in filtered if loc in j.get("location", "").lower()]
        
    total_count = len(filtered)
    paginated = filtered[offset:offset + limit]
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "jobs": paginated
    }

@app.get("/api/jobs/stats")
def get_jobs_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'active' AND date_verified=1 AND datetime(posted_date) >= datetime('now','-24 hours')")
    total_active = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'expired' OR datetime(posted_date) < datetime('now','-24 hours')")
    total_expired = cursor.fetchone()[0]
    
    cursor.execute("SELECT portal, COUNT(*) FROM jobs WHERE status = 'active' AND date_verified=1 AND datetime(posted_date) >= datetime('now','-24 hours') GROUP BY portal")
    portal_counts = {r[0]: r[1] for r in cursor.fetchall()}
    
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN match_score >= 90 THEN 1 ELSE 0 END) as range_90_100,
            SUM(CASE WHEN match_score >= 80 AND match_score < 90 THEN 1 ELSE 0 END) as range_80_89,
            SUM(CASE WHEN match_score >= 70 AND match_score < 80 THEN 1 ELSE 0 END) as range_70_79,
            SUM(CASE WHEN match_score < 70 THEN 1 ELSE 0 END) as range_60_69
        FROM jobs 
        WHERE status = 'active' AND date_verified=1 AND datetime(posted_date) >= datetime('now','-24 hours')
    """)
    dist_row = cursor.fetchone()
    match_distribution = {
        "90-100": dist_row[0] or 0,
        "80-89": dist_row[1] or 0,
        "70-79": dist_row[2] or 0,
        "<70": dist_row[3] or 0
    }
    
    cursor.execute("SELECT first_seen FROM jobs WHERE status = 'active'")
    rows = cursor.fetchall()
    now_dt = datetime.now()
    recent_count = 0
    for r in rows:
        fs = r[0]
        if fs:
            try:
                dt_str = fs.split(".")[0]
                dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                if (now_dt - dt).total_seconds() <= 86400:
                    recent_count += 1
            except:
                pass
                
    cursor.execute("SELECT completed_at FROM scan_history ORDER BY id DESC LIMIT 1")
    history_row = cursor.fetchone()
    latest_scan_time = history_row[0] if history_row else "Never"
    
    conn.close()
    
    return {
        "total_jobs": total_active,
        "jobs_last_24h": recent_count,
        "portal_counts": portal_counts,
        "match_distribution": match_distribution,
        "expired_jobs": total_expired,
        "latest_scan_time": latest_scan_time
    }

@app.get("/api/jobs/portal/{portal}")
def get_jobs_for_portal_name(portal: str, page: int = 1, limit: int = 50):
    offset = (page - 1) * limit
    jobs = get_all_jobs()
    
    filtered = [j for j in jobs if j.get("status") == "active" and j.get("portal") == portal]
    total_count = len(filtered)
    paginated = filtered[offset:offset + limit]
    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "jobs": paginated
    }

@app.delete("/api/jobs/expired")
def delete_expired_listings():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM jobs WHERE status = 'expired'")
        conn.commit()
        deleted = cursor.rowcount
        return {"message": f"Successfully deleted {deleted} expired jobs."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Legacy API routes kept for backward compatibility
@app.get("/api/jobs/all")
def get_all_aggregated_jobs():
    return get_all_jobs()

@app.get("/api/jobs/portals")
def get_portals_summary():
    return get_portal_summaries()

@app.get("/api/jobs/portal-stats")
def get_jobs_portal_stats():
    return get_portal_summaries()

@app.get("/api/logs")
def get_logs_list():
    return get_logs()

@app.post("/api/jobs/apply/{job_id}")
def trigger_manual_apply(job_id: str, background_tasks: BackgroundTasks):
    update_job_status(job_id, "applied", True)
    add_log("apply", f"Manual Application status logged for Job ID: {job_id}")
    return {"message": "Job marked as applied."}

@app.post("/api/jobs/save/{job_id}")
def toggle_job_save(job_id: str, update: StatusUpdate):
    update_job_status(job_id, "saved", update.value)
    return {"message": "Job save state updated."}

@app.get("/api/debug/raw-jobs")
def debug_raw_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT portal, COUNT(*) as cnt FROM jobs GROUP BY portal")
    rows = cursor.fetchall()
    conn.close()
    return {r["portal"]: r["cnt"] for r in rows}

@app.get("/api/debug/db-count")
def debug_db_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status")
    rows = cursor.fetchall()
    conn.close()
    return {r["status"]: r["cnt"] for r in rows}

@app.get("/api/debug/portal-results")
def debug_portal_results():
    return get_portal_summaries()

@app.get("/api/debug/portal-health")
def get_portal_health_api():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portal_health")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/debug/stale-jobs")
def get_stale_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, posted_date, status FROM jobs WHERE datetime(posted_date) < datetime('now','-24 hours')")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/debug/date-audit")
def date_audit_endpoint():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE datetime(posted_date) >= datetime('now','-24 hours')")
    fresh = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE datetime(posted_date) < datetime('now','-24 hours')")
    stale = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE posted_date IS NULL OR posted_date = ''")
    missing = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_jobs": total,
        "fresh_jobs": fresh,
        "stale_jobs": stale,
        "missing_dates": missing
    }


@app.get("/api/debug/date-validation")
def date_validation_endpoint():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE date_verified = 1")
    checked = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE posted_date IS NULL")
    missing = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'expired' OR datetime(posted_date) < datetime('now','-24 hours')")
    rejected = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'active' AND datetime(posted_date) >= datetime('now','-24 hours')")
    saved = cursor.fetchone()[0]
    conn.close()
    return {
        "jobs_checked": checked + rejected + missing,
        "missing_dates": missing,
        "rejected_old_jobs": rejected,
        "saved_jobs": saved
    }

@app.get("/api/status")
def get_scheduler_status():
    now = datetime.now()
    next_s = sched.next_scan_time
    next_a = sched.next_apply_time
    
    return {
        "is_active": sched.is_running,
        "last_scan": sched.last_scan_time.strftime("%H:%M:%S") if sched.last_scan_time else "Never",
        "last_apply": sched.last_apply_time.strftime("%H:%M:%S") if sched.last_apply_time else "Never",
        "next_scan": next_s.strftime("%H:%M:%S") if next_s else "Calculating...",
        "next_apply": next_a.strftime("%H:%M:%S") if next_a else "Calculating...",
        "secs_until_scan": int((next_s - now).total_seconds()) if next_s else 0,
        "secs_until_apply": int((next_a - now).total_seconds()) if next_a else 0,
    }
