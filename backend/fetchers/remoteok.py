import httpx
from datetime import datetime, timezone, timedelta
import hashlib
from backend.fetchers.base import http_request_with_retry, sanitize_html, calculate_match_score, is_job_valid

def fetch_jobs(keywords, past_24h=True):
    jobs = []
    try:
        tag = str(keywords).lower().replace(" ", "-")
        url = f"https://remoteok.com/api?tag={tag}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        with httpx.Client(headers=headers, timeout=15.0) as client:
            r = http_request_with_retry(client, url)
            if r and r.status_code == 200:
                data = r.json()
                # Skip first item as it is statistics metadata
                for item in data[1:20]:
                    title = item.get("position", "")
                    company = item.get("company", "")
                    link = item.get("url", "")
                    description = item.get("description", "")
                    salary = item.get("salary", "N/A")
                    location = item.get("location", "Remote")
                    
                    tags = item.get("tags", [])
                    pub_date_str = item.get("date", "")
                    posted_ago = None
                    posted_date_dt = None
                    
                    if pub_date_str:
                        try:
                            # format e.g. 2026-06-07T13:40:33+00:00
                            if "z" in pub_date_str.lower():
                                pub_date_str = pub_date_str.replace("Z", "+00:00").replace("z", "+00:00")
                            posted_date_dt = datetime.fromisoformat(pub_date_str)
                            delta = datetime.now(timezone.utc) - posted_date_dt
                            days = delta.days
                            hours = delta.seconds // 3600
                            if days > 0:
                                posted_ago = f"{days} day{'s' if days > 1 else ''} ago"
                            else:
                                posted_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                        except Exception:
                            pass
                            
                    clean_desc = sanitize_html(description or f"{keywords} role listed on Remote OK.")
                    
                    if not is_job_valid(title, clean_desc, posted_ago):
                        continue
                        
                    score, matched = calculate_match_score(title, clean_desc, tags)
                    url_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                    job_id = f"sch-remoteok-{url_hash[:16]}"
                    
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "location": location or "Remote",
                        "portal": "Remote OK",
                        "posted_ago": posted_ago,
                        "posted_date": posted_date_dt.isoformat(),
                        "salary": salary or "N/A",
                        "match_score": score,
                        "tags": matched[:4] if matched else (tags[:4] if tags else ["AWS", "DevOps"]),
                        "description": clean_desc,
                        "url": link,
                        "experience_required": "3+ Years"
                    })
    except Exception as e:
        print(f"[FETCHER] Error in fetch_jobs for Remote OK: {e}")
    return jobs
