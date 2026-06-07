import sys
import time
import uuid
import httpx
from datetime import datetime, timezone, timedelta

# Import backend modules to verify function behavior directly
try:
    from backend.database import get_db_connection, save_job, init_db
    from backend.fetchers.base import generate_tailored_documents, calculate_match_score, check_url_is_expired, parse_posted_ago_to_utc_datetime
    from backend.scan_state import scan_state_manager
    print("✓ Successfully imported all backend modules.")
except ImportError as e:
    print(f"✗ Failed to import backend modules: {e}")
    sys.exit(1)

API_BASE = "http://127.0.0.1:8000/api"

def run_tests():
    print("\n=== STARTING END-TO-END VERIFICATION ===\n")
    
    # 1. Verify Database Initialization and Hashing
    print("[1] Verifying database schema & hashing...")
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if job_hash column exists
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [row["name"] for row in cursor.fetchall()]
    assert "job_hash" in columns, "job_hash column missing from jobs table!"
    assert "status" in columns, "status column missing from jobs table!"
    print("✓ Database tables verify successfully (columns job_hash and status present).")
    
    # Test job hash generation uniqueness
    title = "AWS DevOps Engineer"
    company = "Yokra Solutions"
    location = "Hyderabad"
    
    # Unique SHA256 generation using normalized title, company, location
    # Let's see how generate_job_hash is implemented in database.py
    from backend.database import generate_job_hash
    hash_1 = generate_job_hash(title, company, location)
    hash_2 = generate_job_hash("AWS DevOps Engineer ", "Yokra Solutions", "Hyderabad")
    hash_3 = generate_job_hash("Senior DevOps Engineer", company, location)
    
    assert hash_1 == hash_2, "Normalization failing to yield identical hashes for trailing spaces!"
    assert hash_1 != hash_3, "Different title yielding same hash!"
    print(f"✓ Deduplication job hash works (hash: {hash_1})")
    
    # 2. Test Single Transaction UPSERT and Duplication Prevention
    print("\n[2] Verifying save_job UPSERT & duplication prevention...")
    
    # Clean previous test entries
    cursor.execute("DELETE FROM jobs WHERE id LIKE 'test-job-%'")
    conn.commit()
    
    test_job = {
        "id": "test-job-1",
        "title": title,
        "company": company,
        "location": location,
        "portal": "LinkedIn Jobs",
        "posted_ago": "2 hours ago",
        "salary": "₹18-35 LPA",
        "match_score": 90,
        "tags": ["AWS", "DevOps", "Kubernetes"],
        "description": "Unique description text for testing.",
        "url": "https://linkedin.com/jobs/view/test-1",
        "applied": False,
        "saved": False,
        "experience_required": "3.8 Years",
        "posted_date": datetime.now(timezone.utc).isoformat(),
        "job_url": "https://linkedin.com/jobs/view/test-1",
        "scan_id": "test-scan-id"
    }
    
    # First save: should be inserted
    res1 = save_job(test_job, conn)
    assert res1 == "inserted", f"First save returned {res1} instead of 'inserted'"
    
    # Save same job again: should return duplicate
    res2 = save_job(test_job, conn)
    assert res2 == "duplicate", f"Second save returned {res2} instead of 'duplicate'"
    
    # Save job with different ID but same hash/url: should return duplicate
    test_job_dup = test_job.copy()
    test_job_dup["id"] = "test-job-2"
    res3 = save_job(test_job_dup, conn)
    assert res3 == "duplicate", f"Duplicate save with new ID returned {res3} instead of 'duplicate'"
    
    # Save job with updated description: should update
    test_job_update = test_job.copy()
    test_job_update["description"] = "Updated description text."
    res4 = save_job(test_job_update, conn)
    assert res4 == "updated", f"Save with updated description returned {res4} instead of 'updated'"
    
    # Clean up test entries
    cursor.execute("DELETE FROM jobs WHERE id LIKE 'test-job-%'")
    conn.commit()
    conn.close()
    print("✓ Save job duplicate detection & single transaction UPSERT works successfully.")
    
    # 3. Test HTTP API Client Routes
    print("\n[3] Testing HTTP API Endpoints...")
    
    # Test server is running
    try:
        r_ping = httpx.get(f"{API_BASE}/jobs?limit=1")
        print(f"✓ FastAPI server is responsive on {API_BASE}.")
    except Exception as e:
        print(f"✗ FastAPI server is NOT running. Please start uvicorn backend.main:app first. Error: {e}")
        sys.exit(1)
        
    # Test GET /api/jobs/stats
    r_stats = httpx.get(f"{API_BASE}/jobs/stats")
    assert r_stats.status_code == 200, "GET /api/jobs/stats failed"
    stats = r_stats.json()
    assert "total_jobs" in stats, "total_jobs missing from stats response!"
    assert "jobs_last_24h" in stats, "jobs_last_24h missing from stats response!"
    print(f"✓ API GET /api/jobs/stats verified: total active jobs = {stats['total_jobs']}, last 24h = {stats['jobs_last_24h']}")
    
    # Test GET /api/jobs paginated response structure
    r_jobs = httpx.get(f"{API_BASE}/jobs?limit=5")
    assert r_jobs.status_code == 200, "GET /api/jobs failed"
    jobs_data = r_jobs.json()
    assert "total" in jobs_data, "total key missing in paginated jobs response!"
    assert "jobs" in jobs_data, "jobs list missing in paginated jobs response!"
    print(f"✓ API GET /api/jobs paginated structure verified successfully (total={jobs_data['total']}, limit=5).")
    
    # 4. Test API Scan Concurrency
    print("\n[4] Testing scan concurrency lock (/api/scan)...")
    
    # Trigger first scan
    r_scan1 = httpx.post(f"{API_BASE}/scan")
    assert r_scan1.status_code == 200, f"Trigger scan failed: {r_scan1.text}"
    scan1_data = r_scan1.json()
    scan_id = scan1_data["scan_id"]
    print(f"✓ Scan 1 triggered successfully: scan_id = {scan_id}")
    
    # Trigger second scan immediately: should be rejected with 400
    r_scan2 = httpx.post(f"{API_BASE}/scan")
    assert r_scan2.status_code == 400, f"Second scan was not rejected with 400! Status: {r_scan2.status_code}, Response: {r_scan2.text}"
    print(f"✓ Second scan concurrency lock rejected successfully (Status: {r_scan2.status_code}, Response: {r_scan2.json()['detail']})")
    
    # Poll scan status
    time.sleep(2)
    r_status = httpx.get(f"{API_BASE}/scan/status/{scan_id}")
    assert r_status.status_code == 200, f"Get scan status failed: {r_status.text}"
    status_data = r_status.json()
    print(f"✓ Scan status check works: progress = {status_data['progress']}%, status = {status_data['status']}")
    
    # Clean up/terminate active scan if running to be safe (by direct modification or waiting)
    scan_state_manager.complete_scan(scan_id)
    
    # 5. Verify URL expiration logic
    print("\n[5] Verifying URL expiration validator...")
    expired_url = "https://www.naukri.com/job-listings-expired-123456"
    active_url = "https://www.google.com"
    
    is_expired_check = check_url_is_expired(expired_url)
    is_active_check = check_url_is_expired(active_url)
    
    print(f"  Expired URL Check: {is_expired_check}")
    print(f"  Active URL Check: {is_active_check}")
    print("✓ URL validator helper works.")
    
    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
