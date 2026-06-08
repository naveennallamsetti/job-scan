import urllib.parse
from bs4 import BeautifulSoup
import uuid
import logging

from backend.config.config_manager import get_active_selector

def fetch_jobs(keywords, past_24h=True, portal_name='linkedin'):
    from backend.fetcher import fetch_job_page_html
    encoded_keywords = urllib.parse.quote(keywords)
    url = f"https://www.linkedin.com/jobs/search?keywords={encoded_keywords}&f_TPR=r86400"
    
    html = fetch_job_page_html(url, use_playwright_fallback=True, verification_selector=get_active_selector('linkedin'), portal_name='linkedin')
    if not html: return []
        
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    for card in soup.find_all('div', class_=lambda x: x and 'job-search-card' in x):
        try:
            title_tag = card.find('h3', class_='base-search-card__title')
            title = title_tag.text.strip() if title_tag else "Unknown Title"
            job_url = card.find('a', class_='base-card__full-link')['href'] if card.find('a', class_='base-card__full-link') else None
            
            comp_tag = card.find('h4', class_='base-search-card__subtitle')
            company = comp_tag.text.strip() if comp_tag else "Unknown Company"
            
            posted_tag = card.find('time')
            posted_ago_text = posted_tag.text.strip() if posted_tag else None
            
            if job_url:
                jobs.append({
                    "id": str(uuid.uuid4()), "title": title, "company": company,
                    "location": "Remote", "portal": "LinkedIn Jobs", "url": job_url,
                    "posted_ago": posted_ago_text, "description": ""
                })
        except Exception:
            continue
    return jobs
