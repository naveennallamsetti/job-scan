import httpx
import xml.etree.ElementTree as ET
import json
import re
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
from backend.database import add_log

# User Profile Skills for matching
PROFILE_SKILLS = [
    "AWS", "Kubernetes", "Docker", "Jenkins", "Terraform", "Ansible", 
    "GitLab CI/CD", "GitHub Actions", "Linux", "Python", "Bash", 
    "Helm", "ArgoCD", "Prometheus", "Grafana"
]

PROFILE_ROLES = [
    "AWS DevOps Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "AWS Cloud Engineer",
    "Site Reliability Engineer",
    "Platform Engineer",
    "Infrastructure Engineer",
    "Build & Release Engineer",
    "CI/CD Engineer",
    "Kubernetes Engineer"
]

PORTAL_MAPPINGS = {
    # Indian Job Portals
    "Naukri.com": ("naukri.com", "job-listings"),
    "Foundit (formerly Monster India)": ("foundit.in", "/job/"),
    "TimesJobs": ("timesjobs.com", "job-detail"),
    "Shine": ("shine.com", "/jobs/"),
    "Freshersworld": ("freshersworld.com", "/jobs/"),
    "Cutshort": ("cutshort.io", "/job/"),
    "Hirect": ("hirect.in", "/job/"),
    "Instahyre": ("instahyre.com", "job-"),
    "IIMJobs": ("iimjobs.com", "/j/"),
    "Hirist": ("hirist.tech", "/j/"),

    # Global Job Portals
    "LinkedIn Jobs": ("linkedin.com", "jobs/view"),
    "Indeed": ("indeed.com", "viewjob"),
    "Glassdoor Jobs": ("glassdoor.com", "job-listing"),
    "ZipRecruiter": ("ziprecruiter.com", "/jobs/"),
    "CareerBuilder": ("careerbuilder.com", "/job/"),
    "SimplyHired": ("simplyhired.com", "/job/"),
    "Dice": ("dice.com", "job-detail"),

    # Remote Job Portals
    "Wellfound (AngelList)": ("wellfound.com", "/jobs/"),
    "Remote OK": ("remoteok.com", "remote-jobs"),
    "We Work Remotely": ("weworkremotely.com", "remote-jobs"),
    "FlexJobs": ("flexjobs.com", "/jobs/"),
    "Remotive": ("remotive.com", "remote-jobs"),
    "Working Nomads": ("workingnomads.com", "/jobs/"),

    # DevOps / Cloud Focused Platforms
    "DevOps Jobs": ("devopsjobs.io", "/jobs/"),
    "Cloud Careers Hub": ("cloudcareershub.com", "/jobs/"),
    "Linux Foundation Jobs": ("jobs.linuxfoundation.org", "/jobs/"),
    "CNCF Job Board": ("gitjobs.dev", "/jobs/")
}

def check_url_is_expired(url, job_dict=None):
    # Skip checking if it's not a direct target URL or an advertisement/click tracker
    low_url = url.lower()
    if any(ad in low_url for ad in ["doubleclick", "googleadservices", "google.com/aclick", "bing.com/aclick", "ad.doubleclick"]):
        return True
        
    try:
        import hashlib
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        import warnings
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        with httpx.Client(headers=headers, timeout=5.0, follow_redirects=True, verify=False) as client:
            r = client.get(url)
            final_url = str(r.url).lower()
            
            # 1. Check if final URL indicates an expired redirect (e.g. contains expJD or redirect to search page)
            if "expjd" in final_url or "expired" in final_url:
                print(f"[VERIFY] Job URL {url} redirected to expired URL: {final_url}")
                return True
                
            # If a Naukri job-listings URL redirected to a general search page
            if "naukri.com" in low_url and "job-listings" in low_url:
                if "job-listings" not in final_url:
                    print(f"[VERIFY] Naukri job URL {url} redirected to non-listing page: {final_url}")
                    return True
            
            if r.status_code == 200:
                html_lower = r.text.lower()
                
                # Special logic for Naukri to bypass the hydration/stream skeleton block and fetch true posting date
                if "naukri.com" in final_url or "naukri.com" in low_url:
                    import re
                    naukri_match = re.search(r"-(\d{10,15})(?:\?|$)", url)
                    if not naukri_match:
                        naukri_match = re.search(r"-(\d{10,15})(?:\?|$)", final_url)
                    if naukri_match:
                        job_id = naukri_match.group(1)
                        try:
                            api_url = f"https://www.naukri.com/jobapi/v1/job/{job_id}"
                            api_headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "application/json, text/plain, */*",
                                "Accept-Language": "en-US,en;q=0.9",
                                "Client-Id": "d3skt0p",
                                "Appid": "109",
                                "Systemid": "109"
                            }
                            api_r = client.get(api_url, headers=api_headers)
                            if api_r.status_code == 200:
                                api_data = api_r.json()
                                job_data = api_data.get("job", {})
                                if job_data:
                                    is_expired = job_data.get("isExpiredJob", False)
                                    status_id = job_data.get("statusId", 1)
                                    if is_expired or status_id != 1:
                                        print(f"[VERIFY] Naukri Job {url} is expired in API (isExpiredJob={is_expired}, statusId={status_id})")
                                        return True
                                    
                                    add_date_str = job_data.get("addDate")
                                    if add_date_str:
                                        try:
                                            dt_part = add_date_str.split('.')[0]
                                            dt = datetime.strptime(dt_part, "%Y-%m-%d %H:%M:%S")
                                            delta = datetime.now() - dt
                                            days = delta.days
                                            hours = delta.seconds // 3600
                                            if days > 0:
                                                posted_ago = f"{days} day{'s' if days > 1 else ''} ago"
                                            else:
                                                posted_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                                            
                                            print(f"[VERIFY] Parsed Naukri post date for {url}: {posted_ago}")
                                            if job_dict:
                                                job_dict["posted_ago"] = posted_ago
                                        except Exception as parse_err:
                                            print(f"[VERIFY] Error parsing addDate {add_date_str}: {parse_err}")
                            elif api_r.status_code in [404, 410]:
                                print(f"[VERIFY] Naukri Job API {api_url} returned {api_r.status_code}")
                                return True
                        except Exception as api_err:
                            print(f"[VERIFY] Naukri Job API fetch failed for {url}: {api_err}")

                # 2. Check for expiration phrases in the HTML content
                expiration_phrases = [
                    "job you are looking for is expired",
                    "this job is no longer accepting applications",
                    "job is no longer accepting applications",
                    "applications closed",
                    "job expired",
                    "no longer accepting applications",
                    "similar jobs below you may consider",
                    "this job has expired",
                    "the job you are looking for is expired",
                    "we are no longer accepting applications",
                    "no longer accepting responses"
                ]
                for phrase in expiration_phrases:
                    if phrase in html_lower:
                        print(f"[VERIFY] Job URL {url} is expired (matched phrase: '{phrase}')")
                        return True
                        
                # Try to extract the real posting date from the HTML to fix the 24h age filter issue
                import re
                html_clean = re.sub(r"<!--.*?-->", "", r.text)
                
                # List of regexes to try on html content
                date_patterns = [
                    # Pattern 1: generic label "posted/active/created/published/added: X days ago" (no colon required)
                    r"(?i)(?:posted|active|created|published|added)\s*(?:on|at)?\s*[:\-]?\s*([\d\w\s+–\-]+(?:ago|yesterday|today|day|week|month|year|just now)s?)",
                    # Pattern 2: generic label with absolute dates: "posted on April 15, 2026", "published 12 May 2026", "created 2026-04-10"
                    r"(?i)(?:posted|active|created|published|added)\s*(?:on|at)?\s*[:\-]?\s*([a-z]{3,9}\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[a-z]{3,9},?\s+\d{4}|\d{4}-\d{2}-\d{2})",
                    # Pattern 3: LinkedIn "posted-time-ago__text" element content
                    r'(?i)class="[^"]*posted-time-ago__text[^"]*"[^>]*>\s*([^<\n\r]+)',
                    # Pattern 4: LinkedIn time tag or generic listdate
                    r'(?i)class="[^"]*(?:main-job-card__listdate|aside-job-card__listdate|job-card__listdate)[^"]*"[^>]*>\s*([^<\n\r]+)',
                    # Pattern 5: Bare relative date: e.g. "3 days ago", "12 hours ago", "yesterday", "today", "just now"
                    r"(?i)(?:>|\b)(\d+\s+(?:hour|hr|h|day|dy|d|week|wk|w|month|mo|m|year|yr|y)s?\s+ago|yesterday|today|just now)(?:<|\b)"
                ]
                
                real_posted = None
                for pat in date_patterns:
                    match_posted = re.search(pat, html_clean)
                    if match_posted:
                        candidate = match_posted.group(1).strip()
                        # Clean up trailing html tags or double quotes/special characters
                        candidate = re.split(r'[<"\'\{\}]', candidate)[0].strip()
                        if candidate and len(candidate) < 30:
                            real_posted = candidate
                            break
                            
                if real_posted:
                    print(f"[VERIFY] Extracted real posting date from {url}: '{real_posted}'")
                    if job_dict and (not job_dict.get("posted_ago") or job_dict.get("posted_ago") in ["Recently", "time-ago"]):
                        job_dict["posted_ago"] = real_posted
            elif r.status_code in [404, 410]:
                print(f"[VERIFY] Job URL {url} returned status {r.status_code} (Not Found)")
                return True
    except Exception as e:
        # If check fails due to SSL, network error or timeout, we don't mark as expired to be safe
        print(f"[VERIFY] Check URL failed for {url}: {e}")
        
    return False

def is_older_than_30_days(posted_ago):
    if not posted_ago:
        return False
    text = posted_ago.strip()
    
    # Try parsing absolute date first (e.g. "Apr 13, 2026")
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt)
            delta = datetime.now() - dt
            return delta.days > 30
        except ValueError:
            continue
            
    # Try with stripped punctuation for formats like "May 14 2026"
    cleaned = re.sub(r'[^\w\s]', '', text).strip()
    for fmt in ("%b %d %Y", "%B %d %Y", "%d %b %Y", "%d %B %Y"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            delta = datetime.now() - dt
            return delta.days > 30
        except ValueError:
            continue
            
    # Fall back to relative age check
    low_text = text.lower()
    low_text = re.sub(r"\b(a|an)\b", "1", low_text)
    match = re.search(r"(\d+)\s*(hour|hr|h|day|dy|d|week|wk|w|month|mo|m|year|yr|y)s?", low_text)
    if match:
        value = int(match[1])
        unit = match[2]
        if unit.startswith("d") and value > 30:
            return True
        if unit.startswith("w") and value >= 4:
            return True
        if unit.startswith("m") and value >= 1:
            return True
        if unit.startswith("y"):
            return True
    return False

def is_job_valid(title, description, posted_ago):
    if is_older_than_30_days(posted_ago):
        return False
    
    # Check for expiration keywords
    text_to_check = (title + " " + (description or "")).lower()
    for exp_kw in ["no longer accepting", "expired", "closed", "applications closed", "inactive"]:
        if exp_kw in text_to_check:
            return False
            
    return True

def calculate_match_score(title, description, tags):
    score = 65  # Base match score
    text = (title + " " + description).lower()
    
    matched_skills = []
    for skill in PROFILE_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text) or any(skill.lower() == t.lower() for t in tags):
            score += 3
            matched_skills.append(skill)
            
    # Add bonus for target DevOps titles
    for title_kw in ["devops", "sre", "kubernetes", "terraform", "platform", "cloud"]:
        if title_kw in title.lower():
            score += 4
            break
            
    score = min(score, 98)
    score = max(score, 65)
    return score, matched_skills

def generate_tailored_documents(job):
    company = job.get("company", "the Employer")
    title = job.get("title", "DevOps Engineer")
    
    cover_letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {title} position at {company}. With 3.8 years of hands-on experience as an AWS DevOps Engineer, specializing in cloud infrastructure orchestration, container systems management, and CI/CD pipelines automation, I am excited about the opportunity to contribute to your team.

At Yokra Solutions, I led the deployment of production-grade AWS EKS clusters utilizing IAM Roles for Service Accounts (IRSA) for pod-level security, and structured Terraform infrastructure automation. Additionally, I automated rolling microservice deployments via zero-downtime Ansible playbooks. My background in maintaining Prometheus and Grafana alerting stacks directly maps to your operational monitoring needs.

I would welcome the opportunity to discuss how my AWS cloud experience and DevOps prep skills can deliver immediate value to {company}.

Sincerely,
Naveen Kumar
naveendevops589@gmail.com | 3.8 Years Experience"""

    resume = f"""NAVEEN KUMAR - AWS DevOps Engineer | 3.8 Years
naveendevops589@gmail.com | Hyderabad, India

TAILORED PROFILE FOR {company.upper()}
Dynamic and results-driven AWS DevOps Engineer with 3.8 years of experience automating infrastructure provisioning, container orchestration, and continuous integration workflows. Highly proficient in EKS, Terraform, Ansible, and Prometheus stacks.

CORE COMPETENCIES
- AWS Services: EKS, EC2, VPC routing, S3 versioning, IAM security, DynamoDB state locking
- Container & IaC: Kubernetes, Docker, Helm, ArgoCD, Terraform, Ansible
- Monitoring & CI/CD: Prometheus, Grafana, Jenkins Pipelines, GitHub Actions

PROFESSIONAL EXPERIENCE
Yokra Solutions - DevOps Engineer (2022-Present)
- Provisioned secure AWS EKS Kubernetes clusters utilizing IAM OIDC federation (IRSA).
- Created Terraform infrastructure-as-code modules with DynamoDB-backed state locking.
- Optimized multi-branch Jenkins pipelines, reducing deployment feedback loops.
- Set up Prometheus alert managers monitoring 40+ microservices.

Krify Technologies - Junior DevOps Engineer (2021-2022)
- Managed resource requests/limits configurations on Dev environments.
- Implemented multi-stage Docker builds reducing image sizes by 60%.
"""
    return cover_letter, resume

def fetch_wwr_jobs():
    jobs = []
    try:
        url = "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"
        r = httpx.get(url, timeout=10.0)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for item in root.findall(".//item")[:15]:
                title = item.find("title").text
                link = item.find("link").text
                description = item.find("description").text or ""
                
                parts = title.split(":")
                company = parts[0].strip() if len(parts) > 1 else "WWR Employer"
                role = parts[1].strip() if len(parts) > 1 else title
                
                tags = ["Kubernetes", "DevOps", "AWS"]
                pub_date_node = item.find("pubDate")
                posted_ago = "Recently"
                if pub_date_node is not None:
                    try:
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(pub_date_node.text)
                        delta = datetime.now(dt.tzinfo) - dt
                        days = delta.days
                        hours = delta.seconds // 3600
                        if days > 0:
                            posted_ago = f"{days} day{'s' if days > 1 else ''} ago"
                        else:
                            posted_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                    except Exception:
                        pass
                
                if not is_job_valid(role, description, posted_ago):
                    continue
                score, matched = calculate_match_score(role, description, tags)
                
                import hashlib
                url_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                job_id = "wwr-" + url_hash[:16]
                jobs.append({
                    "id": job_id,
                    "title": role,
                    "company": company,
                    "location": "Remote",
                    "portal": "We Work Remotely",
                    "posted_ago": posted_ago,
                    "salary": "N/A",
                    "match_score": score,
                    "tags": matched[:4] if matched else tags,
                    "description": re.sub("<[^<]+?>", "", description)[:300] + "...",
                    "url": link,
                    "experience_required": "3+ Years"
                })
    except Exception as e:
        print(f"Error fetching WWR: {e}")
    return jobs

def fetch_remotive_jobs():
    jobs = []
    try:
        url = "https://remotive.com/api/remote-jobs?category=devops&limit=15"
        r = httpx.get(url, timeout=10.0)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("jobs", [])[:15]:
                title = item.get("title", "")
                company = item.get("company_name", "")
                link = item.get("url", "")
                description = item.get("description", "")
                salary = item.get("salary", "N/A")
                location = item.get("candidate_required_location", "Remote")
                
                tags = item.get("tags", [])
                pub_date_str = item.get("publication_date", "")
                posted_ago = "Recently"
                if pub_date_str:
                    try:
                        if "z" in pub_date_str.lower() or "+" in pub_date_str:
                            dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                            delta = datetime.now(dt.tzinfo) - dt
                        else:
                            dt = datetime.fromisoformat(pub_date_str)
                            delta = datetime.now() - dt
                        days = delta.days
                        hours = delta.seconds // 3600
                        if days > 0:
                            posted_ago = f"{days} day{'s' if days > 1 else ''} ago"
                        else:
                            posted_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                    except Exception:
                        pass
                
                if not is_job_valid(title, description, posted_ago):
                    continue
                score, matched = calculate_match_score(title, description, tags)
                
                import hashlib
                url_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                job_id = "remotive-" + str(item.get("id", url_hash[:16]))
                jobs.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "portal": "Remotive",
                    "posted_ago": posted_ago,
                    "salary": salary if salary else "N/A",
                    "match_score": score,
                    "tags": matched[:4] if matched else tags[:3],
                    "description": re.sub("<[^<]+?>", "", description)[:300] + "...",
                    "url": link,
                    "experience_required": "3+ Years"
                })
    except Exception as e:
        print(f"Error fetching Remotive: {e}")
    return jobs

def fetch_remoteok_jobs():
    jobs = []
    try:
        # Remote OK requires a valid User-Agent to avoid getting 403 blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url = "https://remoteok.com/api?tag=devops"
        r = httpx.get(url, headers=headers, timeout=12.0)
        if r.status_code == 200:
            data = r.json()
            # The first item is a legal notice/statistics metadata block, so skip it
            for item in data[1:16]:
                title = item.get("position", "")
                company = item.get("company", "")
                link = item.get("url", "")
                description = item.get("description", "")
                salary = item.get("salary", "N/A")
                location = item.get("location", "Remote")
                
                tags = item.get("tags", [])
                pub_date_str = item.get("date", "")
                posted_ago = "Recently"
                if pub_date_str:
                    try:
                        if "z" in pub_date_str.lower() or "+" in pub_date_str:
                            dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                            delta = datetime.now(dt.tzinfo) - dt
                        else:
                            dt = datetime.fromisoformat(pub_date_str)
                            delta = datetime.now() - dt
                        days = delta.days
                        hours = delta.seconds // 3600
                        if days > 0:
                            posted_ago = f"{days} day{'s' if days > 1 else ''} ago"
                        else:
                            posted_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
                    except Exception:
                        pass
                
                if not is_job_valid(title, description, posted_ago):
                    continue
                score, matched = calculate_match_score(title, description, tags)
                
                import hashlib
                url_hash = hashlib.md5(link.encode('utf-8')).hexdigest()
                job_id = "remoteok-" + str(item.get("id", url_hash[:16]))
                jobs.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": location if location else "Remote",
                    "portal": "Remote OK",
                    "posted_ago": posted_ago,
                    "salary": salary if salary else "N/A",
                    "match_score": score,
                    "tags": matched[:4] if matched else tags[:3],
                    "description": re.sub("<[^<]+?>", "", description)[:300] + "...",
                    "url": link,
                    "experience_required": "3+ Years"
                })
    except Exception as e:
        print(f"Error fetching Remote OK: {e}")
    return jobs

def extract_posted_ago(snippet):
    if not snippet:
        return "Recently"
    # Check for relative date patterns like "2 hours ago", "5 days ago", "1 week ago", "3d ago", "2h ago"
    match = re.search(r"\b(\d+)\s*(hour|hr|h|day|dy|d|week|wk|w|month|mo|m|year|yr|y)s?\s+ago\b", snippet, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    prefix_match = re.match(r"^\s*([\w\s,]+?\d{4}|\d+\s+\w+\s+ago|\d+\s+\w+\s+seconds?\s+ago)\s*[-·|]", snippet, re.IGNORECASE)
    if prefix_match:
        return prefix_match.group(1).strip()
    days_ago_match = re.search(r"\b\d+\s+days?\s+ago\b", snippet, re.IGNORECASE)
    if days_ago_match:
        return days_ago_match.group(0).strip()
    if "yesterday" in snippet.lower():
        return "1 day ago"
    return "Recently"

def fetch_yahoo_jobs(portal_name, keywords="AWS DevOps Engineer", past_24h=True):
    jobs = []
    if portal_name not in PORTAL_MAPPINGS:
        return jobs
        
    domain, path_filter = PORTAL_MAPPINGS[portal_name]
    
    import random
    import time
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    # Split path_filter by slash and quote each segment separately to avoid Yahoo 500 syntax crashes
    path_segments = [p for p in path_filter.split('/') if p] if path_filter else []
    query_parts = [f'"{domain}"'] + [f'"{seg}"' for seg in path_segments] + [f'"{keywords}"']
    query = " ".join(query_parts)
    
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://search.yahoo.com/search?p={encoded_query}"
    if past_24h:
        search_url += "&btf=d"
    
    max_retries = 4
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
            print(f"[FETCHER] Yahoo search attempt {attempt + 1} for {portal_name}: {search_url}")
            with httpx.Client(headers=headers, timeout=15.0) as client:
                r = client.get(search_url)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    # Search all h3 elements instead of strictly class='title' for stability
                    h3s = soup.find_all('h3')
                    
                    found_any = False
                    for h3 in h3s[:10]:  # Process top 10 results
                        a_tag = h3.find('a') or h3.find_parent('a')
                        if not a_tag or 'RU=' not in a_tag.get('href', ''):
                            continue
                        
                        # Decode the Yahoo redirect URL
                        redirect_url = a_tag['href']
                        try:
                            target_url = urllib.parse.unquote(redirect_url.split('RU=')[1].split('/RK=')[0])
                        except Exception:
                            target_url = redirect_url
                        
                        # Exclude sponsored ads or other sites that do not have the domain in their host/netloc
                        parsed_target = urllib.parse.urlparse(target_url)
                        if domain not in parsed_target.netloc.lower():
                            continue
                            
                        # Enforce path_filter in target_url if configured to avoid grabbing general search landing pages
                        if path_filter and path_filter.lower() not in target_url.lower():
                            continue
                        
                        # Clean up title and company from search title
                        raw_title = h3.text
                        title = raw_title
                        company = portal_name.split(".")[0]
                        
                        # Try parsing out company and title (e.g. "Capnexus hiring AWS DevOps Lead")
                        for sep in [" hiring ", " at ", " | ", " - "]:
                            if sep in raw_title:
                                parts = raw_title.split(sep)
                                if sep == " hiring ":
                                    company = parts[0].strip()
                                    title = parts[1].strip()
                                else:
                                    title = parts[0].strip()
                                    company = parts[1].strip()
                                break
                                
                        # Clean up brand strings
                        title = re.sub(r"\b(LinkedIn|Naukri|Indeed|Glassdoor|Monster|Shine|TimesJobs|Foundit)\b.*", "", title, flags=re.IGNORECASE).strip(" |-,")
                        company = re.sub(r"\b(LinkedIn|Naukri|Indeed|Glassdoor|Monster|Shine|TimesJobs|Foundit)\b.*", "", company, flags=re.IGNORECASE).strip(" |-,")
                        
                        # Parse snippet
                        snippet = ""
                        comp_text = h3.find_parent('div').find_next_sibling('div', class_='compText') if h3.find_parent('div') else None
                        if comp_text:
                            snippet = comp_text.text
                        else:
                            li_container = h3.find_parent('li')
                            p_tag = li_container.find('p') if li_container else None
                            if p_tag:
                                snippet = p_tag.text
                                
                        # Calculate relevance score
                        posted_ago = extract_posted_ago(snippet)
                        if past_24h:
                            low_posted = posted_ago.lower()
                            if any(x in low_posted for x in ["day", "week", "month", "year"]) or re.search(r"\d{4}", low_posted):
                                if "1 day" not in low_posted and "yesterday" not in low_posted:
                                    posted_ago = "1 day ago"

                        if not is_job_valid(title, snippet, posted_ago):
                            continue
                            
                        score, matched = calculate_match_score(title, snippet, [])
                        
                        # Deduplicate and build item with deterministic MD5 hash
                        import hashlib
                        url_hash = hashlib.md5(target_url.encode('utf-8')).hexdigest()
                        job_id = f"sch-{portal_name.lower().replace(' ', '').replace('.com', '')}-{url_hash[:16]}"
                        
                        job_item = {
                            "id": job_id,
                            "title": title,
                            "company": company,
                            "location": "India (Remote)" if "remote" in snippet.lower() or "remote" in title.lower() else "India",
                            "portal": portal_name,
                            "posted_ago": posted_ago,
                            "salary": "₹18-35 LPA" if "LPA" in snippet or "Lakh" in snippet else "N/A",
                            "match_score": score,
                            "tags": matched[:4] if matched else ["AWS", "DevOps"],
                            "description": snippet if snippet else f"AWS DevOps role listed on {portal_name}. Key requirements: AWS, Kubernetes, Terraform.",
                            "url": target_url,
                            "experience_required": "3.8 Years"
                        }
                        
                        # Live check to verify job has not expired on the target portal and enrich the true posting date
                        if check_url_is_expired(target_url, job_item):
                            continue
                            
                        if past_24h:
                            low_posted = job_item["posted_ago"].lower()
                            if any(x in low_posted for x in ["day", "week", "month", "year"]) or re.search(r"\d{4}", low_posted):
                                if "1 day" not in low_posted and "yesterday" not in low_posted:
                                    job_item["posted_ago"] = "1 day ago"

                        # Re-verify freshness using the newly extracted true posting date from the webpage
                        if not is_job_valid(title, snippet, job_item["posted_ago"]):
                            continue
                            
                        jobs.append(job_item)
                        found_any = True
                    
                    if found_any:
                        break
                    else:
                        print(f"[FETCHER] No links matching {domain} under H3 elements for {portal_name}.")
                        break
                elif r.status_code == 500:
                    wait_time = (attempt + 1) * 4 + random.uniform(1, 3)
                    print(f"[FETCHER] Yahoo search returned 500 for {portal_name}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[FETCHER] Yahoo search failed with status {r.status_code} for {portal_name}.")
                    break
        except Exception as e:
            print(f"[FETCHER] Error fetching from Yahoo for {portal_name}: {e}")
            time.sleep(2)
            
    return jobs

def crawl_single_portal_worker(portal_name, past_24h=True):
    from backend.database import update_portal_scan_status
    import time
    from datetime import datetime
    
    start_time = time.time()
    now_iso = datetime.now().isoformat()
    
    # Update status to running
    update_portal_scan_status(portal_name, "running")
    
    jobs = []
    try:
        # Add random delay for Yahoo scrapers to avoid rate limits
        if portal_name not in ["We Work Remotely", "Remotive", "Remote OK"]:
            import random
            time.sleep(random.uniform(0.5, 3.0))
            
            # Select a random role to query
            role = random.choice(PROFILE_ROLES)
            print(f"[FETCHER] Crawling {portal_name} concurrently using keyword: {role}")
            jobs = fetch_yahoo_jobs(portal_name, keywords=role, past_24h=past_24h)
        else:
            print(f"[FETCHER] Crawling {portal_name} concurrently via direct feed")
            if portal_name == "We Work Remotely":
                jobs = fetch_wwr_jobs()
            elif portal_name == "Remotive":
                jobs = fetch_remotive_jobs()
            elif portal_name == "Remote OK":
                jobs = fetch_remoteok_jobs()
                
        duration = round(time.time() - start_time, 2)
        update_portal_scan_status(
            portal_name, 
            "success", 
            jobs_found=len(jobs), 
            last_scan_time=now_iso, 
            duration=duration
        )
        return jobs
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        print(f"[FETCHER] Error crawling {portal_name}: {e}")
        update_portal_scan_status(
            portal_name, 
            "failed", 
            jobs_found=0, 
            duration=duration, 
            error_message=str(e)
        )
        return []

def fetch_all_jobs(portal_to_scan=None, past_24h=True):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    if portal_to_scan:
        print(f"[FETCHER] Running targeted concurrent scan for: {portal_to_scan}")
        return crawl_single_portal_worker(portal_to_scan, past_24h)
        
    print("[FETCHER] Starting concurrent scan across all 27 portals...")
    all_portals = [
        "LinkedIn Jobs", "Naukri.com", "Indeed", "Glassdoor Jobs", "Dice",
        "We Work Remotely", "Remotive", "Remote OK", "Wellfound (AngelList)",
        "Foundit (formerly Monster India)", "TimesJobs", "Shine", "Freshersworld",
        "Cutshort", "Hirect", "Instahyre", "IIMJobs", "Hirist", "ZipRecruiter",
        "CareerBuilder", "SimplyHired", "FlexJobs", "Working Nomads", "DevOps Jobs",
        "Cloud Careers Hub", "Linux Foundation Jobs", "CNCF Job Board"
    ]
    
    all_jobs = []
    # Using 5 workers to keep rate limit safe but parallelized
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(crawl_single_portal_worker, p, past_24h): p for p in all_portals}
        for future in as_completed(futures):
            portal = futures[future]
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"[FETCHER] Exception returned from worker for {portal}: {e}")
                
    return all_jobs
