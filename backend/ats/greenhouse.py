import httpx
import logging
from .base import create_job

def fetch_jobs(board_token: str) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    try:
        resp = httpx.get(url, timeout=10)
        if resp.status_code == 404:
            return []
        elif resp.status_code == 429:
            logging.error(f"[{board_token}] RATE_LIMITED (429)")
            return []
        elif resp.status_code != 200:
            logging.error(f"[{board_token}] UNKNOWN_ERROR ({resp.status_code})")
            return []
            
        data = resp.json()
        jobs_data = data.get("jobs", [])
        if not jobs_data:
            logging.warning(f"[{board_token}] EMPTY_RESPONSE (0 jobs returned)")
            return []
            
        # FIX 3: Infer company name correctly instead of token
        inferred_company = data.get("name") or board_token.replace("_", " ").title()
            
        jobs = []
        for j in jobs_data:
            loc = j.get("location", {}).get("name", "Unknown")
            jobs.append(create_job(
                title=j.get("title", ""),
                company=inferred_company,
                location=loc,
                url=j.get("absolute_url", ""),
                source="greenhouse",
                posted_date=j.get("updated_at", ""),
                salary=None,
                description_snippet=None
            ))
        return jobs
    except httpx.TimeoutException:
        logging.error(f"[{board_token}] NETWORK_FAILURE (Timeout)")
        return []
    except Exception as e:
        logging.error(f"[{board_token}] PARSE_FAILURE: {str(e)}")
        return []
