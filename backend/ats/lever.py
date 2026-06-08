import httpx
import logging
from .base import create_job

def fetch_jobs(site_name: str) -> list:
    url = f"https://api.lever.co/v0/postings/{site_name}?mode=json"
    try:
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 404:
            logging.error(f"[{site_name}] SOURCE_INVALID (404)")
            return []
        elif resp.status_code == 429:
            logging.error(f"[{site_name}] RATE_LIMITED (429)")
            return []
        elif resp.status_code != 200:
            logging.error(f"[{site_name}] UNKNOWN_ERROR ({resp.status_code})")
            return []
            
        data = resp.json()
        if not data:
            logging.warning(f"[{site_name}] EMPTY_RESPONSE (0 jobs returned)")
            return []
            
        jobs = []
        for j in data:
            loc = j.get("categories", {}).get("location", "Unknown")
            # FIX 2: Correct extraction priority
            title = j.get("text") or j.get("position") or j.get("title") or "Unknown"
            company = site_name.replace("-", " ").title()
            
            jobs.append(create_job(
                title=title,
                company=company,
                location=loc,
                url=j.get("hostedUrl", ""),
                source="lever",
                posted_date=str(j.get("createdAt", "")),
                salary=None,
                description_snippet=j.get("descriptionPlain", "")[:200] if j.get("descriptionPlain") else None
            ))
        return jobs
    except httpx.TimeoutException:
        logging.error(f"[{site_name}] NETWORK_FAILURE (Timeout)")
        return []
    except Exception as e:
        logging.error(f"[{site_name}] PARSE_FAILURE: {str(e)}")
        return []
