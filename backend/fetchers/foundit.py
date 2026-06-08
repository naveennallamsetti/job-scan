import urllib.parse
from bs4 import BeautifulSoup
import uuid
import logging

from backend.config.config_manager import get_active_selector

def fetch_jobs(keywords, past_24h=True):
    from backend.fetcher import fetch_job_page_html
    encoded_keywords = urllib.parse.quote(keywords)
    url = f"https://www.foundit.in/srp/results?query={encoded_keywords}"
    
    html = fetch_job_page_html(url, use_playwright_fallback=True, verification_selector=get_active_selector('foundit'), portal_name='foundit')
    if not html: return []
        
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    for card in soup.find_all('div', class_='job-tittle'):
        try:
            title_tag = card.find('h3').find('a') if card.find('h3') else None
            title = title_tag.text.strip() if title_tag else "Unknown Title"
            job_url = title_tag['href'] if title_tag and 'href' in title_tag.attrs else None
            
            comp_tag = card.find('span', class_='company-name')
            company = comp_tag.text.strip() if comp_tag else "Unknown Company"
            
            date_tag = card.find('span', class_='time')
            posted_ago_text = date_tag.text.strip() if date_tag else None
            
            if job_url:
                jobs.append({
                    "id": str(uuid.uuid4()), "title": title, "company": company,
                    "location": "Remote", "portal": "Foundit", "url": job_url,
                    "posted_ago": posted_ago_text, "description": ""
                })
        except Exception:
            continue
    return jobs
