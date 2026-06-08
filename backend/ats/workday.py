import httpx
import logging
from .base import create_job

def fetch_jobs(workday_tenant_url: str) -> list:
    url = workday_tenant_url
    payload = {"appliedFacets":{}, "limit":20, "offset":0, "searchText":""}
    try:
        resp = httpx.post(url, json=payload, timeout=10)
        if resp.status_code == 404:
            logging.error(f"[{workday_tenant_url}] SOURCE_INVALID (404)")
            return []
        elif resp.status_code == 429:
            logging.error(f"[{workday_tenant_url}] RATE_LIMITED (429)")
            return []
        elif resp.status_code != 200:
            logging.error(f"[{workday_tenant_url}] UNKNOWN_ERROR ({resp.status_code})")
            return []
            
        data = resp.json()
        jobs_data = data.get("jobPostings", [])
        if not jobs_data:
            logging.warning(f"[{workday_tenant_url}] EMPTY_RESPONSE")
            return []
            
        jobs = []
        for j in jobs_data:
            jobs.append(create_job(
                title=j.get("title", ""),
                company="workday_client",
                location=j.get("locationsText", "Unknown"),
                url=url.split("/wday")[0] + j.get("externalPath", ""),
                source="workday",
                posted_date=j.get("postedOn", ""),
                salary=None,
                description_snippet=None
            ))
        return jobs
    except httpx.TimeoutException:
        logging.error(f"[{workday_tenant_url}] NETWORK_FAILURE (Timeout)")
        return []
    except Exception as e:
        logging.error(f"[{workday_tenant_url}] PARSE_FAILURE: {str(e)}")
        return []
