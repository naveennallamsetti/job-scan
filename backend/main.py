from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import threading

from backend.database import init_db, get_all_jobs, get_logs, update_job_status, update_job_details, add_log, get_portal_summaries
from backend.scheduler import start_scheduler, stop_scheduler, scan_jobs, run_auto_apply
import backend.scheduler as sched

app = FastAPI(title="Naveen-AI Jarvis Job Agent Backend", version="1.0.0")

# Enable CORS for React frontend on local network
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for mobile/local network sharing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusUpdate(BaseModel):
    value: bool

@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()
    add_log("system", "Jarvis Job Monitoring Agent Core Online.", "success")

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

@app.get("/api/jobs")
def get_jobs_list(portal: Optional[str] = None):
    jobs = get_all_jobs()
    if portal:
        jobs = [j for j in jobs if j.get("portal") == portal]
    return jobs

@app.get("/api/jobs/all")
def get_all_aggregated_jobs():
    return get_all_jobs()

@app.get("/api/jobs/portals")
def get_portals_summary():
    return get_portal_summaries()

@app.get("/api/logs")
def get_logs_list():
    return get_logs()

@app.post("/api/jobs/scan")
def trigger_manual_scan(background_tasks: BackgroundTasks, portal: Optional[str] = None):
    background_tasks.add_task(scan_jobs, portal)
    return {"message": "Manual scan queued successfully."}

@app.post("/api/jobs/apply/{job_id}")
def trigger_manual_apply(job_id: str, background_tasks: BackgroundTasks):
    # Find job and update status
    update_job_status(job_id, "applied", True)
    add_log("apply", f"Manual Application status logged for Job ID: {job_id}")
    return {"message": "Job marked as applied."}

@app.post("/api/jobs/save/{job_id}")
def toggle_job_save(job_id: str, update: StatusUpdate):
    update_job_status(job_id, "saved", update.value)
    return {"message": "Job save state updated."}

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
