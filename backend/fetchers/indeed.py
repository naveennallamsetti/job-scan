import urllib.parse
from bs4 import BeautifulSoup
import uuid
import logging

from backend.config.config_manager import get_active_selector

def fetch_jobs(keywords, past_24h=True):
    from backend.fetcher import fetch_job_page_html
    encoded_keywords = urllib.parse.quote(keywords)
    url = f"https://www.indeed.com/jobs?q={encoded_keywords}&fromage=1"
    
    html = fetch_job_page_html(url, use_playwright_fallback=True, verification_selector=get_active_selector('indeed'), portal_name='indeed')
    if not html: return []
        
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    for card in soup.find_all('td', class_='resultContent'):
        try:
            # Ignore sponsored
            if card.find('span', class_='sponsoredGray'): continue
                
            title_tag = card.find('h2', class_='jobTitle').find('a') if card.find('h2', class_='jobTitle') else None
            title = title_tag.text.strip() if title_tag else "Unknown Title"
            job_url = "https://www.indeed.com" + title_tag['href'] if title_tag and 'href' in title_tag.attrs else None
            
            comp_tag = card.find('span', class_='companyName') or card.find('span', attrs={'data-testid': 'company-name'})
            company = comp_tag.text.strip() if comp_tag else "Unknown Company"
            
            date_tag = card.find('span', class_='date')
            posted_ago_text = date_tag.text.strip().replace('Posted', '').strip() if date_tag else None
            
            if job_url:
                jobs.append({
                    "id": str(uuid.uuid4()), "title": title, "company": company,
                    "location": "Remote", "portal": "Indeed", "url": job_url,
                    "posted_ago": posted_ago_text, "description": ""
                })
        except Exception:
            continue
    return jobs
