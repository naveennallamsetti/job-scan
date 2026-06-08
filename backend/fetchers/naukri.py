import urllib.parse
from bs4 import BeautifulSoup
import uuid
import logging
import json

from backend.config.config_manager import get_active_selector

def fetch_jobs(keywords, location='Worldwide', past_24h=False, portal_name='naukri'):
    from backend.fetcher import fetch_job_page_html
    
    encoded_keywords = urllib.parse.quote(keywords.replace(" ", "-"))
    # jobAge=1 ensures Naukri strictly searches 1 day old
    url = f"https://www.naukri.com/{encoded_keywords}-jobs?jobAge=1"
    
    html = fetch_job_page_html(url, use_playwright_fallback=True, verification_selector=get_active_selector('naukri'), portal_name='naukri')
    if not html:
        logging.error("[NAUKRI] Failed to fetch main search page.")
        return []
        
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    # We restrict to listContainer to avoid "Similar Jobs" or "Recommended Jobs" blocks
    list_container = soup.find('div', class_='listContainer') or soup.find('div', id='listContainer')
    if not list_container:
        # Fallback to main article wrapper if strict container not found
        list_container = soup
        
    job_cards = list_container.find_all('article', class_='jobTuple') or list_container.find_all('div', class_=lambda x: x and 'jobTuple' in x)
    
    for card in job_cards:
        try:
            title_tag = card.find('a', class_='title')
            title = title_tag.text.strip() if title_tag else "Unknown Title"
            job_url = title_tag['href'] if title_tag and 'href' in title_tag.attrs else None
            
            comp_tag = card.find('a', class_='comp-name')
            company = comp_tag.text.strip() if comp_tag else "Unknown Company"
            
            loc_tag = card.find('span', class_='locWdth')
            location = loc_tag.text.strip() if loc_tag else "Unknown Location"
            
            posted_tag = card.find('span', class_='job-post-day')
            posted_ago_text = posted_tag.text.strip() if posted_tag else None
            
            if job_url:
                jobs.append({
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "company": company,
                    "location": location,
                    "portal": "Naukri.com",
                    "url": job_url,
                    "posted_ago": posted_ago_text, # will be overwritten by detail page
                    "description": "" # detail page will fill if needed
                })
        except Exception as e:
            continue
            
    return jobs
