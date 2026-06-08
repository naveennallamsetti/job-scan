import hashlib
import re

def normalize_text(text: str) -> str:
    if not text: return ""
    text = text.lower()
    text = re.sub(r'\b(inc|ltd|llc|corp|co)\b\.?$', '', text).strip()
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def generate_job_fingerprint(title: str, company: str, location: str) -> str:
    norm_title = normalize_text(title)
    norm_company = normalize_text(company)
    norm_loc = normalize_text(location)
    raw = norm_title + norm_company + norm_loc
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def create_job(title: str, company: str, location: str, url: str, source: str, posted_date: str, salary: str = None, description_snippet: str = None) -> dict:
    return {
        "title": title,
        "company": company,
        "location": location,
        "url": url,
        "source": source,
        "posted_date": posted_date,
        "salary": salary,
        "description_snippet": description_snippet,
        "job_fingerprint": generate_job_fingerprint(title, company, location)
    }
