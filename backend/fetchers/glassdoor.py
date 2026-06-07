from backend.fetchers.base import fetch_yahoo_portal_jobs

def fetch_jobs(keywords, past_24h=True):
    return fetch_yahoo_portal_jobs(
        portal_name="Glassdoor Jobs",
        domain="glassdoor.com",
        path_filter="job-listing",
        keywords=keywords,
        past_24h=past_24h
    )
