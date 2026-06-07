import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        portal TEXT,
        posted_ago TEXT,
        salary TEXT,
        match_score INTEGER,
        tags TEXT,
        description TEXT,
        url TEXT,
        applied INTEGER DEFAULT 0,
        saved INTEGER DEFAULT 0,
        experience_required TEXT,
        cover_letter TEXT,
        resume_customized TEXT,
        created_at TEXT
    )
    """)
    
    # Create logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        type TEXT,
        description TEXT,
        status TEXT
    )
    """)
    
    # Create portal_scans table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portal_scans (
        portal TEXT PRIMARY KEY,
        jobs_found INTEGER DEFAULT 0,
        last_scan_time TEXT,
        status TEXT DEFAULT 'idle',
        duration REAL DEFAULT 0.0,
        error_message TEXT
    )
    """)

    # Seed default portals if they don't exist
    all_portals = [
        "LinkedIn Jobs", "Naukri.com", "Indeed", "Glassdoor Jobs", "Dice",
        "We Work Remotely", "Remotive", "Remote OK", "Wellfound (AngelList)",
        "Foundit (formerly Monster India)", "TimesJobs", "Shine", "Freshersworld",
        "Cutshort", "Hirect", "Instahyre", "IIMJobs", "Hirist", "ZipRecruiter",
        "CareerBuilder", "SimplyHired", "FlexJobs", "Working Nomads", "DevOps Jobs",
        "Cloud Careers Hub", "Linux Foundation Jobs", "CNCF Job Board"
    ]
    for p in all_portals:
        cursor.execute("""
        INSERT OR IGNORE INTO portal_scans (portal, jobs_found, last_scan_time, status, duration, error_message)
        VALUES (?, 0, NULL, 'idle', 0.0, NULL)
        """, (p,))
    
    conn.commit()
    conn.close()
    purge_simulated_jobs()

def purge_simulated_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First delete static pattern matches
        cursor.execute("""
            DELETE FROM jobs 
            WHERE id LIKE 'sim-%' 
               OR url LIKE '%linkedin jobs.com%' 
               OR url LIKE '%naukari%'
               OR url LIKE '%bing.com/aclick%'
               OR url LIKE '%doubleclick.net%'
               OR url LIKE '%googleadservices.com%'
               OR url LIKE '%google.com/aclick%'
               OR posted_ago LIKE '%month%ago'
               OR posted_ago LIKE '%year%ago'
               OR posted_ago LIKE '%4 weeks%ago'
               OR posted_ago LIKE '%5 weeks%ago'
               OR description LIKE '%no longer accepting%'
               OR description LIKE '%applications closed%'
               OR description LIKE '%job expired%'
               OR description LIKE '%job you are looking for is expired%'
               OR description LIKE '%similar jobs below%'
               OR description LIKE '%this job has expired%'
        """)
        conn.commit()
        deleted_count = cursor.rowcount
        
        # Now dynamically purge based on age limits (older than 30 days)
        cursor.execute("SELECT id, posted_ago, created_at FROM jobs")
        rows = cursor.fetchall()
        
        from backend.fetcher import is_older_than_30_days
        
        to_delete = []
        for r in rows:
            job_id = r["id"]
            posted_ago = r["posted_ago"]
            created_at = r["created_at"]
            
            # Check if posted_ago is older than 30 days
            if is_older_than_30_days(posted_ago):
                to_delete.append(job_id)
                continue
                
            # Also check if created_at (crawl time) is older than 30 days
            if created_at:
                try:
                    dt_str = created_at.split(".")[0]
                    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                    if (datetime.now() - dt).days > 30:
                        to_delete.append(job_id)
                except Exception:
                    pass
                    
        if to_delete:
            cursor.executemany("DELETE FROM jobs WHERE id = ?", [(jid,) for jid in to_delete])
            conn.commit()
            deleted_count += len(to_delete)
            print(f"[DATABASE] Dynamically purged {len(to_delete)} jobs older than 30 days.")
            
        print(f"[DATABASE] Purged legacy simulated and broken links from jobs database. Rows deleted: {deleted_count}")
        
        now_str = datetime.now().strftime("%H:%M:%S")
        cursor.execute(
            "INSERT INTO logs (timestamp, type, description, status) VALUES (?, ?, ?, ?)",
            (now_str, "database", f"Purged legacy simulated and broken links. Rows deleted: {deleted_count}", "success")
        )
        conn.commit()
    except Exception as e:
        print(f"[DATABASE] Error purging simulated jobs: {e}")
    finally:
        conn.close()

def add_log(log_type, description, status="success"):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%H:%M:%S")
    cursor.execute(
        "INSERT INTO logs (timestamp, type, description, status) VALUES (?, ?, ?, ?)",
        (now_str, log_type, description, status)
    )
    conn.commit()
    conn.close()

def get_logs(limit=30):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, type, description, status FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"ts": r["timestamp"], "type": r["type"], "desc": r["description"], "status": r["status"]} for r in rows][::-1]

def get_all_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY match_score DESC")
    rows = cursor.fetchall()
    conn.close()
    
    jobs = []
    for r in rows:
        job = dict(r)
        # Convert applied and saved to boolean
        job["applied"] = bool(job["applied"])
        job["saved"] = bool(job["saved"])
        job["match"] = job["match_score"]
        job["postedAgo"] = job["posted_ago"]
        
        # Add React tracker compatibility keys
        job["company_name"] = job["company"]
        job["position"] = job["title"]
        job["job_portal"] = job["portal"]
        if job["created_at"]:
            try:
                job["applied_date"] = job["created_at"].split("T")[0]
            except:
                job["applied_date"] = datetime.now().strftime("%Y-%m-%d")
        else:
            job["applied_date"] = datetime.now().strftime("%Y-%m-%d")
            
        job["status"] = "Applied"
        job["notes"] = f"Auto-applied. Match Score: {job['match']}%" if job["applied"] else ""
        
        # Parse tags from comma-separated string to list
        if job["tags"]:
            job["tags"] = [t.strip() for t in job["tags"].split(",") if t.strip()]
        else:
            job["tags"] = []
        jobs.append(job)
    return jobs

def save_job(job_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tags_str = ",".join(job_data.get("tags", []))
    now_str = datetime.now().isoformat()
    
    try:
        cursor.execute("""
        INSERT INTO jobs (id, title, company, location, portal, posted_ago, salary, match_score, tags, description, url, applied, saved, experience_required, cover_letter, resume_customized, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            posted_ago=excluded.posted_ago,
            match_score=excluded.match_score,
            tags=excluded.tags,
            description=excluded.description,
            salary=excluded.salary
        """, (
            job_data["id"],
            job_data["title"],
            job_data["company"],
            job_data["location"],
            job_data["portal"],
            job_data["posted_ago"],
            job_data.get("salary", "N/A"),
            job_data.get("match_score", 70),
            tags_str,
            job_data["description"],
            job_data["url"],
            1 if job_data.get("applied", False) else 0,
            1 if job_data.get("saved", False) else 0,
            job_data.get("experience_required", "3+ Years"),
            job_data.get("cover_letter", ""),
            job_data.get("resume_customized", ""),
            now_str
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving job: {e}")
    finally:
        conn.close()

def update_job_status(job_id, field, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    val = 1 if value else 0
    cursor.execute(f"UPDATE jobs SET {field} = ? WHERE id = ?", (val, job_id))
    conn.commit()
    conn.close()

def update_job_details(job_id, cover_letter, resume_customized):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE jobs SET cover_letter = ?, resume_customized = ? WHERE id = ?",
        (cover_letter, resume_customized, job_id)
    )
    conn.commit()
    conn.close()

def update_portal_scan_status(portal, status, jobs_found=None, last_scan_time=None, duration=None, error_message=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        updates = ["status = ?"]
        params = [status]
        
        if jobs_found is not None:
            updates.append("jobs_found = ?")
            params.append(jobs_found)
        if last_scan_time is not None:
            updates.append("last_scan_time = ?")
            params.append(last_scan_time)
        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)
            
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        else:
            if status in ('success', 'running', 'idle'):
                updates.append("error_message = NULL")
                
        params.append(portal)
        cursor.execute(f"UPDATE portal_scans SET {', '.join(updates)} WHERE portal = ?", tuple(params))
        conn.commit()
    except Exception as e:
        print(f"Error updating portal scan status: {e}")
    finally:
        conn.close()

def get_portal_summaries():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        SELECT 
            ps.portal,
            COALESCE(j.cnt, 0) as jobs_found,
            ps.last_scan_time,
            ps.status,
            ps.duration,
            ps.error_message
        FROM portal_scans ps
        LEFT JOIN (
            SELECT portal, COUNT(*) as cnt 
            FROM jobs 
            GROUP BY portal
        ) j ON ps.portal = j.portal
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error getting portal summaries: {e}")
        return []
    finally:
        conn.close()
