import sqlite3
import os
import json
import hashlib
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return conn

def generate_job_hash(portal, company, title, job_url):
    import hashlib
    import urllib.parse
    
    p = str(portal or '').lower().strip()
    c = str(company or '').lower().strip()
    t = str(title or '').lower().strip()
    
    # URL Normalization
    u = str(job_url or '').strip()
    if u:
        parsed = urllib.parse.urlparse(u)
        # remove tracking params
        qs = urllib.parse.parse_qs(parsed.query)
        cleaned_qs = {k: v for k, v in qs.items() if not k.startswith('utm_') and k not in ['ref', 'trackingId', 'trk', 'sc.keyword', 'fromage']}
        new_query = urllib.parse.urlencode(cleaned_qs, doseq=True)
        # lowercase host, drop fragment
        u = urllib.parse.urlunparse((parsed.scheme, (parsed.netloc or '').lower(), parsed.path, parsed.params, new_query, ''))
    
    hash_input = f"{p}|{c}|{t}|{u}".encode('utf-8')
    return hashlib.sha256(hash_input).hexdigest()

def create_jobs_table(cursor):
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
        created_at TEXT,
        first_seen TEXT,
        last_seen TEXT,
        posted_date TEXT,
        job_url TEXT,
        job_hash TEXT,
        status TEXT DEFAULT 'active',
        resume_hash TEXT,
        date_verified INTEGER DEFAULT 0,
        date_confidence REAL DEFAULT 0,
        date_source TEXT,
        UNIQUE(job_url),
        UNIQUE(job_hash)
    )
    """)

def seed_default_portals(cursor):
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

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Create scan_history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id TEXT UNIQUE,
        started_at TEXT,
        completed_at TEXT,
        jobs_found INTEGER DEFAULT 0,
        duplicates INTEGER DEFAULT 0,
        failed_portals TEXT
    )
    """)
    
    # 2. Check if jobs table exists and verify its schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if job_hash column is in the table
        cursor.execute("PRAGMA table_info(jobs)")
        cols = [r[1] for r in cursor.fetchall()]
        
        need_migration = False
        required_cols = ["job_hash", "first_seen", "last_seen", "status", "resume_hash", "date_verified"]
        for rc in required_cols:
            if rc not in cols:
                need_migration = True
                break
                
        if need_migration:
            print("[DATABASE] Migrating jobs table to add production-grade columns and unique constraints...")
            cursor.execute("ALTER TABLE jobs RENAME TO jobs_old")
            
            # Create new table with final schema
            create_jobs_table(cursor)
            
            # Copy data from jobs_old to jobs
            cursor.execute("SELECT * FROM jobs_old")
            old_rows = cursor.fetchall()
            for row in old_rows:
                r_dict = dict(row)
                
                # Generate unique hash for old jobs
                h = generate_job_hash(r_dict.get("title", ""), r_dict.get("company", ""), r_dict.get("location", ""))
                
                created = r_dict.get("created_at") or datetime.now().isoformat()
                first = r_dict.get("first_seen") or created
                last = r_dict.get("last_seen") or created
                status = r_dict.get("status") or "active"
                
                try:
                    cursor.execute("""
                    INSERT OR IGNORE INTO jobs (
                        id, title, company, location, portal, posted_ago, salary, match_score, 
                        tags, description, url, applied, saved, experience_required, 
                        cover_letter, resume_customized, created_at, first_seen, last_seen, 
                        posted_date, job_url, job_hash, status, resume_hash, date_verified, date_confidence, date_source, age_days, freshness_score
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r_dict.get("id"),
                        r_dict.get("title"),
                        r_dict.get("company"),
                        r_dict.get("location"),
                        r_dict.get("portal"),
                        r_dict.get("posted_ago"),
                        r_dict.get("salary", "N/A"),
                        r_dict.get("match_score", 70),
                        r_dict.get("tags", ""),
                        r_dict.get("description", ""),
                        r_dict.get("url"),
                        r_dict.get("applied", 0),
                        r_dict.get("saved", 0),
                        r_dict.get("experience_required", "3+ Years"),
                        r_dict.get("cover_letter", ""),
                        r_dict.get("resume_customized", ""),
                        created,
                        first,
                        last,
                        r_dict.get("posted_date"),
                        r_dict.get("job_url") or r_dict.get("url"),
                        h,
                        status,
                        r_dict.get("resume_hash"),
                        r_dict.get("date_verified", 0),
                        r_dict.get("date_confidence", 0),
                        r_dict.get("date_source", "")
                    ))
                except Exception as e:
                    print(f"[DATABASE] Migration row error: {e}")
                    
            cursor.execute("DROP TABLE jobs_old")
            print("[DATABASE] Jobs table migration completed successfully.")
    else:
        # Create jobs table from scratch
        create_jobs_table(cursor)
        
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
    
    # Create portal_health table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portal_health (
        portal_name TEXT PRIMARY KEY,
        last_success TEXT,
        last_failure TEXT,
        jobs_found INTEGER DEFAULT 0,
        jobs_saved INTEGER DEFAULT 0,
        jobs_rejected INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0.0
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
    
    # Seed default portals
    seed_default_portals(cursor)
    
    conn.commit()
    conn.close()
    
    # Create logs directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
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
        
        # Dynamically purge based on age limits (older than 30 days)
        cursor.execute("SELECT id, posted_ago, created_at, first_seen FROM jobs")
        rows = cursor.fetchall()
        
        from backend.fetcher import is_older_than_30_days
        
        to_delete = []
        for r in rows:
            job_id = r["id"]
            posted_ago = r["posted_ago"]
            created_at = r["created_at"]
            first_seen = r["first_seen"]
            
            # Check if posted_ago is older than 30 days
            if posted_ago and is_older_than_30_days(posted_ago):
                to_delete.append(job_id)
                continue
                
            # Check if created_at or first_seen is older than 30 days
            ref_date = first_seen or created_at
            if ref_date:
                try:
                    dt_str = ref_date.split(".")[0]
                    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                    if (datetime.now() - dt).days > 30:
                        to_delete.append(job_id)
                except Exception:
                    pass
                    
        if to_delete:
            cursor.executemany("DELETE FROM jobs WHERE id = ?", [(jid,) for jid in to_delete])
            conn.commit()
            deleted_count += len(to_delete)
            
        print(f"[DATABASE] Purged simulated and aged-out links. Rows deleted: {deleted_count}")
        
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
    cursor.execute("SELECT * FROM jobs WHERE status='active' AND age_days <= 1 ORDER BY posted_date DESC")
    rows = cursor.fetchall()
    conn.close()
    
    jobs = []
    for r in rows:
        job = dict(r)
        job["applied"] = bool(job["applied"])
        job["saved"] = bool(job["saved"])
        job["match"] = job["match_score"]
        job["postedAgo"] = job["posted_ago"]
        
        # Add React tracker compatibility keys
        job["company_name"] = job["company"]
        job["position"] = job["title"]
        job["job_portal"] = job["portal"]
        
        ref_date = job.get("first_seen") or job.get("created_at") or datetime.now().isoformat()
        try:
            job["applied_date"] = ref_date.split("T")[0]
        except:
            job["applied_date"] = datetime.now().strftime("%Y-%m-%d")
            
        db_status = job.get("status") or "active"
        if job["applied"] and db_status == "active":
            job["status"] = "Applied"
        else:
            job["status"] = db_status
        job["notes"] = f"Auto-applied. Match Score: {job['match']}%" if job["applied"] else ""
        
        if job["tags"]:
            job["tags"] = [t.strip() for t in job["tags"].split(",") if t.strip()]
        else:
            job["tags"] = []
        jobs.append(job)
    return jobs

def save_job(job_data, conn=None):
    import sqlite3
    from datetime import datetime, timezone
    
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True
        
    cursor = conn.cursor()
    tags_str = ",".join(job_data.get("tags", [])) if isinstance(job_data.get("tags"), list) else job_data.get("tags", "")
    now_str = datetime.now().isoformat()
    posted_date = job_data.get("posted_date")
    job_url = job_data.get("job_url") or job_data.get("url") or None
    
    if not posted_date or not isinstance(posted_date, str):
        if should_close: conn.close()
        return "rejected_missing_date"
        
    if job_data.get("date_verified") != 1:
        if should_close: conn.close()
        return "rejected_unverified_job"

    from datetime import timedelta
    try:
        dt = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt < datetime.now(timezone.utc) - timedelta(hours=24):
            if should_close: conn.close()
            return "rejected_old_job"
    except Exception:
        if should_close: conn.close()
        return "rejected_missing_date"

    # Generate job hash
    job_hash = job_data.get("job_hash")
    if not job_hash:
        job_hash = generate_job_hash(job_data.get("portal"), job_data["company"], job_data["title"], job_url)
        job_data["job_hash"] = job_hash
    age_days = job_data.get("age_days", 0)
    freshness_score = job_data.get("freshness_score", 0)
        
    resume_content = job_data.get("resume_customized") or ""
    res_hash = hashlib.sha256(resume_content.encode('utf-8')).hexdigest() if resume_content else ""
    
    # Check if job already exists
    cursor.execute("SELECT id, description, resume_hash, match_score, cover_letter, resume_customized FROM jobs WHERE job_hash = ? OR job_url = ?", (job_hash, job_url))
    row = cursor.fetchone()
    
    cl = job_data.get("cover_letter") or ""
    res = job_data.get("resume_customized") or ""
    match_score = job_data.get("match_score", 70)
    
    if row:
        existing_id = row[0]
        existing_desc = row[1]
        existing_res_hash = row[2]
        existing_match = row[3]
        existing_cl = row[4]
        existing_res = row[5]
        
        desc_changed = (job_data["description"] != existing_desc)
        res_changed = (res_hash != existing_res_hash) if resume_content else False
        
        if not desc_changed and not res_changed and existing_match:
            try:
                cursor.execute("""
                UPDATE jobs SET
                    posted_ago = ?,
                    last_seen = ?,
                    status = 'active'
                WHERE id = ?
                """, (job_data["posted_ago"], now_str, existing_id))
                if should_close:
                    conn.commit()
                return "duplicate"
            except sqlite3.IntegrityError:
                if should_close:
                    conn.rollback()
                return "duplicate"
        else:
            if not cl or not res:
                from backend.fetchers.base import generate_tailored_documents
                try:
                    cl, res = generate_tailored_documents(job_data)
                    res_hash = hashlib.sha256(res.encode('utf-8')).hexdigest()
                except Exception:
                    pass
            from backend.fetchers.base import calculate_match_score
            match_score, _ = calculate_match_score(job_data["title"], job_data["description"], [])
            
        try:
            cursor.execute("""
            UPDATE jobs SET
                posted_ago = ?,
                posted_date = ?,
                last_seen = ?,
                description = ?,
                salary = ?,
                tags = ?,
                match_score = ?,
                resume_hash = ?,
                cover_letter = ?,
                resume_customized = ?,
                status = 'active',
                date_verified = ?,
                date_confidence = ?,
                date_source = ?,
                age_days = ?,
                freshness_score = ?
            WHERE id = ?
            """, (
                job_data["posted_ago"],
                posted_date,
                now_str,
                job_data["description"],
                job_data.get("salary", "N/A"),
                tags_str,
                match_score,
                res_hash,
                cl,
                res,
                job_data.get("date_verified", 1),
                job_data.get("date_confidence", 1.0),
                job_data.get("date_source", ""),
                job_data.get("age_days", 0),
                job_data.get("freshness_score", 0),
                existing_id
            ))
            if should_close:
                conn.commit()
            return "updated"
        except sqlite3.IntegrityError:
            if should_close:
                conn.rollback()
            return "duplicate"
    else:
        if not cl or not res:
            from backend.fetchers.base import generate_tailored_documents
            try:
                cl, res = generate_tailored_documents(job_data)
                res_hash = hashlib.sha256(res.encode('utf-8')).hexdigest()
            except Exception:
                pass
                
        try:
            cursor.execute("""
            INSERT INTO jobs (
                id, title, company, location, portal, posted_ago, salary, match_score, 
                tags, description, url, applied, saved, experience_required, 
                cover_letter, resume_customized, created_at, first_seen, last_seen, 
                posted_date, job_url, job_hash, status, resume_hash, date_verified, date_confidence, date_source, age_days, freshness_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_data["id"],
                job_data["title"],
                job_data["company"],
                job_data["location"],
                job_data["portal"],
                job_data["posted_ago"],
                job_data.get("salary", "N/A"),
                match_score,
                tags_str,
                job_data["description"],
                job_data["url"],
                1 if job_data.get("applied") else 0,
                1 if job_data.get("saved") else 0,
                job_data.get("experience_required", "3+ Years"),
                cl,
                res,
                now_str,
                now_str,
                now_str,
                posted_date,
                job_url,
                job_hash,
                "active",
                res_hash,
                job_data.get("date_verified", 1),
                job_data.get("date_confidence", 1.0),
                job_data.get("date_source", ""),
                job_data.get("age_days", 0),
                job_data.get("freshness_score", 0)
            ))
            if should_close:
                conn.commit()
            return "inserted"
        except sqlite3.IntegrityError:
            if should_close:
                conn.rollback()
            return "duplicate"
        finally:
            if should_close:
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
            WHERE status = 'active' AND date_verified=1 AND datetime(posted_date) >= datetime('now','-24 hours')
            GROUP BY portal
        ) j ON ps.portal = j.portal
        """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["jobs"] = d["jobs_found"]
            d["total"] = d["jobs_found"]
            result.append(d)
        return result
    except Exception as e:
        print(f"Error getting portal summaries: {e}")
        return []
    finally:
        conn.close()

def add_scan_history(scan_id, started_at, completed_at, jobs_found, duplicates, failed_portals):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if isinstance(failed_portals, list):
            failed_portals_str = ",".join(failed_portals)
        else:
            failed_portals_str = str(failed_portals or "")
            
        cursor.execute("""
        INSERT INTO scan_history (scan_id, started_at, completed_at, jobs_found, duplicates, failed_portals)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (scan_id, started_at, completed_at, jobs_found, duplicates, failed_portals_str))
        conn.commit()
    except Exception as e:
        print(f"[DATABASE] Error adding scan history: {e}")
    finally:
        conn.close()

def get_scan_history(limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT scan_id, started_at, completed_at, jobs_found, duplicates, failed_portals FROM scan_history ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [
            {
                "scan_id": r[0],
                "started_at": r[1],
                "completed_at": r[2],
                "jobs_found": r[3],
                "duplicates": r[4],
                "failed_portals": r[5].split(",") if r[5] else []
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[DATABASE] Error getting scan history: {e}")
        return []
    finally:
        conn.close()

def purge_old_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Expire older than 24h explicitly if age_days is > 1
        cursor.execute("UPDATE jobs SET status = 'expired' WHERE status = 'active' AND age_days > 1")
        
        # Archive > 7 days
        cursor.execute("UPDATE jobs SET status = 'archived' WHERE status = 'expired' AND age_days > 7")
        archived = cursor.rowcount
        
        # Delete > 30 days
        cursor.execute("DELETE FROM jobs WHERE age_days > 30")
        deleted = cursor.rowcount
        
        conn.commit()
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")
    finally:
        conn.close()

def update_portal_health(portal_name, status, jobs_found=0, jobs_saved=0, jobs_rejected=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM portal_health WHERE portal_name = ?", (portal_name,))
        row = cursor.fetchone()
        now_str = datetime.now().isoformat()
        
        if row:
            total_found = row["jobs_found"] + jobs_found
            total_saved = row["jobs_saved"] + jobs_saved
            total_rejected = row["jobs_rejected"] + jobs_rejected
            
            last_success = now_str if status == 'success' else row["last_success"]
            last_failure = now_str if status == 'failed' else row["last_failure"]
            
            success_rate = 0.0
            if total_found > 0:
                success_rate = round((total_saved / total_found) * 100, 2)
                
            cursor.execute("""
                UPDATE portal_health SET
                last_success = ?, last_failure = ?, jobs_found = ?, jobs_saved = ?, jobs_rejected = ?, success_rate = ?
                WHERE portal_name = ?
            """, (last_success, last_failure, total_found, total_saved, total_rejected, success_rate, portal_name))
        else:
            success_rate = 0.0
            if jobs_found > 0:
                success_rate = round((jobs_saved / jobs_found) * 100, 2)
            
            last_success = now_str if status == 'success' else None
            last_failure = now_str if status == 'failed' else None
            
            cursor.execute("""
                INSERT INTO portal_health (portal_name, last_success, last_failure, jobs_found, jobs_saved, jobs_rejected, success_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (portal_name, last_success, last_failure, jobs_found, jobs_saved, jobs_rejected, success_rate))
            
        conn.commit()
    except Exception as e:
        print(f"[HEALTH] Error updating portal health: {e}")
    finally:
        conn.close()
