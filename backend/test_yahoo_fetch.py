import httpx
import urllib.parse
from bs4 import BeautifulSoup

import httpx
import urllib.parse
from bs4 import BeautifulSoup

import httpx
import urllib.parse
from bs4 import BeautifulSoup

import httpx
from bs4 import BeautifulSoup
import time
import random
import urllib.parse

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def test_yahoo_robust(query):
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://search.yahoo.com/search?p={encoded_query}"
    print(f"\nQuerying Yahoo: {query}")
    
    # Retry loop
    max_retries = 5
    for attempt in range(max_retries):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none"
        }
        try:
            with httpx.Client(headers=headers, timeout=15.0) as client:
                r = client.get(search_url)
                print(f"  Attempt {attempt + 1}: Status {r.status_code}")
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    h3s = soup.find_all('h3')
                    print(f"  All H3 elements found: {len(h3s)}")
                    valid_links = 0
                    for h in h3s[:8]:
                        a = h.find('a') or h.find_parent('a')
                        if a and 'RU=' in a.get('href', ''):
                            redirect_url = a['href']
                            try:
                                target_url = urllib.parse.unquote(redirect_url.split('RU=')[1].split('/RK=')[0])
                            except:
                                target_url = redirect_url
                            print(f"    - Title: {h.text.strip()}")
                            print(f"      Link: {target_url}")
                            valid_links += 1
                    if valid_links > 0:
                        return True
                    else:
                        print("    No links with RU= found under H3s.")
                elif r.status_code == 500:
                    # Patient exponential backoff with jitter
                    wait_time = (attempt + 1) * 5 + random.uniform(2, 5)
                    print(f"  Received 500, sleeping {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"  Received status {r.status_code}")
                    break
        except Exception as e:
            print(f"  Error on attempt {attempt + 1}: {e}")
            time.sleep(3)
    return False

from backend.fetcher import fetch_wwr_jobs, fetch_remotive_jobs, fetch_remoteok_jobs

def test_feeds():
    print("Testing We Work Remotely RSS Feed...")
    wwr = fetch_wwr_jobs()
    print(f"  Result count: {len(wwr)}")
    if wwr:
        print(f"  First job: {wwr[0]['title']} at {wwr[0]['company']}")
        
    print("\nTesting Remotive API...")
    rem = fetch_remotive_jobs()
    print(f"  Result count: {len(rem)}")
    if rem:
        print(f"  First job: {rem[0]['title']} at {rem[0]['company']}")
        
    print("\nTesting Remote OK API...")
    rok = fetch_remoteok_jobs()
    print(f"  Result count: {len(rok)}")
    if rok:
        print(f"  First job: {rok[0]['title']} at {rok[0]['company']}")

test_feeds()

















