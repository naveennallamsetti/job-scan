import time
import random
import re
import urllib.parse
import hashlib
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def sanitize_html(text):
    if not text:
        return ""
    # Strip script and style blocks completely
    text = re.sub(r'<(script|style|iframe|object|embed)[^>]*>.*?</\1>', '', text, flags=re.DOTALL|re.IGNORECASE)
    # Strip event handlers (e.g. onload, onerror)
    text = re.sub(r'\bon[a-z]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]*)', '', text, flags=re.IGNORECASE)
    # Strip javascript: URLs
    text = re.sub(r'href\s*=\s*(?:"javascript:[^"]*"|\'javascript:[^\']*\'|javascript:[^\s>]*\b)', '', text, flags=re.IGNORECASE)
    return text

def calculate_match_score(title, description, tags):
    score = 65  # Base match score
    text = (title + " " + (description or "")).lower()
    
    matched_skills = []
    for skill in PROFILE_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text) or any(skill.lower() == t.lower() for t in (tags or [])):
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

def is_job_valid(title, description, posted_ago):
    text_to_check = (title + " " + (description or "")).lower()
    for exp_kw in ["no longer accepting", "expired", "closed", "applications closed", "inactive"]:
        if exp_kw in text_to_check:
            return False
    return True

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

def http_request_with_retry(client, url, method="GET", **kwargs):
    retries = 3
    backoff = 2
    for attempt in range(retries):
        try:
            # Random delay 1-3 seconds between requests (rate limit mitigation)
            time.sleep(random.uniform(1.0, 3.0))
            
            headers = kwargs.get("headers", {})
            if "User-Agent" not in headers:
                headers["User-Agent"] = random.choice(USER_AGENTS)
            kwargs["headers"] = headers
            
            r = client.request(method, url, **kwargs)
            if r.status_code == 200:
                return r
            if r.status_code == 429: # Too many requests
                time.sleep(backoff ** (attempt + 1))
                continue
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(backoff ** (attempt + 1))
    return None

def extract_posted_ago(snippet):
    if not snippet:
        return "Recently"
    match = re.search(r"(\d+\s*(?:day|hour|minute|min|sec|wk|week|month)s?\s*ago)", snippet, re.IGNORECASE)
    if match:
        return match.group(1)
    if "yesterday" in snippet.lower():
        return "Yesterday"
    if "today" in snippet.lower():
        return "Today"
    return "Recently"

def fetch_yahoo_portal_jobs(portal_name, domain, path_filter, keywords, past_24h):
    # Formulate Yahoo query: e.g. "site:linkedin.com/jobs/view" "DevOps Engineer"
    query = f"site:\"{domain}/{path_filter}\" \"{keywords}\""
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://search.yahoo.com/search?p={encoded_query}"
    if past_24h:
        search_url += "&btf=d"
        
    jobs = []
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        with httpx.Client(headers=headers, timeout=15.0) as client:
            r = http_request_with_retry(client, search_url)
            if r and r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                h3s = soup.find_all('h3')
                
                for h3 in h3s[:10]: # Top 10 search results
                    a_tag = h3.find('a') or h3.find_parent('a')
                    if not a_tag or 'RU=' not in a_tag.get('href', ''):
                        continue
                        
                    # Decode Yahoo redirect
                    redirect_url = a_tag['href']
                    try:
                        target_url = urllib.parse.unquote(redirect_url.split('RU=')[1].split('/RK=')[0])
                    except Exception:
                        target_url = redirect_url
                        
                    parsed_target = urllib.parse.urlparse(target_url)
                    if domain not in parsed_target.netloc.lower():
                        continue
                    if path_filter and path_filter.lower() not in target_url.lower():
                        continue
                        
                    raw_title = h3.text
                    title = raw_title
                    company = portal_name.split(".")[0]
                    
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
                            
                    title = re.sub(r"\b(LinkedIn|Naukri|Indeed|Glassdoor|Monster|Shine|TimesJobs|Foundit)\b.*", "", title, flags=re.IGNORECASE).strip(" |-,")
                    company = re.sub(r"\b(LinkedIn|Naukri|Indeed|Glassdoor|Monster|Shine|TimesJobs|Foundit)\b.*", "", company, flags=re.IGNORECASE).strip(" |-,")
                    
                    snippet = ""
                    comp_text = h3.find_parent('div').find_next_sibling('div', class_='compText') if h3.find_parent('div') else None
                    if comp_text:
                        snippet = comp_text.text
                    else:
                        li_container = h3.find_parent('li')
                        p_tag = li_container.find('p') if li_container else None
                        if p_tag:
                            snippet = p_tag.text
                            
                    posted_ago = extract_posted_ago(snippet)
                    if past_24h:
                        low_posted = posted_ago.lower()
                        if any(x in low_posted for x in ["day", "week", "month", "year"]) or re.search(r"\d{4}", low_posted):
                            if "1 day" not in low_posted and "yesterday" not in low_posted:
                                posted_ago = "1 day ago"
                                
                    # Sanitize description
                    clean_desc = sanitize_html(snippet or f"{keywords} role listed on {portal_name}.")
                    
                    if not is_job_valid(title, clean_desc, posted_ago):
                        continue
                        
                    score, matched = calculate_match_score(title, clean_desc, [])
                    
                    url_hash = hashlib.md5(target_url.encode('utf-8')).hexdigest()
                    job_id = f"sch-{portal_name.lower().replace(' ', '').replace('.com', '')}-{url_hash[:16]}"
                    
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "location": "India (Remote)" if "remote" in clean_desc.lower() or "remote" in title.lower() else "India",
                        "portal": portal_name,
                        "posted_ago": posted_ago,
                        "salary": "₹18-35 LPA" if "LPA" in clean_desc or "Lakh" in clean_desc else "N/A",
                        "match_score": score,
                        "tags": matched[:4] if matched else ["AWS", "DevOps"],
                        "description": clean_desc,
                        "url": target_url,
                        "experience_required": "3.8 Years"
                    })
    except Exception as e:
        print(f"[FETCHER] Error in fetch_yahoo_portal_jobs for {portal_name}: {e}")
    return jobs

def parse_posted_ago_to_utc_datetime(posted_ago):
    from datetime import datetime, timezone, timedelta
    import re
    from email.utils import parsedate_to_datetime
    
    now_utc = datetime.now(timezone.utc)
    if not posted_ago:
        return now_utc
        
    text = posted_ago.strip()
    text_lower = text.lower()
    
    # 1. Check for RSS pubDate first (e.g., Sun, 07 Jun 2026...)
    if any(day in text_lower for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]) or "," in text:
        try:
            dt = parsedate_to_datetime(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
            
    # 2. Try parsing ISO formats or other absolute dates
    try:
        clean_iso = text
        if clean_iso.endswith('Z') or clean_iso.endswith('z'):
            clean_iso = clean_iso[:-1] + '+00:00'
        dt = datetime.fromisoformat(clean_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass
        
    # Check other absolute date formats
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
            
    # 3. Relative text parsing
    text_lower = re.sub(r"\b(a|an)\b", "1", text_lower)
    
    if any(w in text_lower for w in ["just now", "today", "active", "recently", "time-ago", "now"]):
        return now_utc
        
    if "yesterday" in text_lower:
        return now_utc - timedelta(days=1)
        
    # Minutes: "X minutes ago", "X mins ago", "Xm ago"
    min_match = re.search(r"(\d+)\s*(minute|min|m)s?(\s+ago)?", text_lower)
    if min_match:
        value = int(min_match.group(1))
        unit = min_match.group(2)
        if unit.startswith("min") or unit == "m":
            return now_utc - timedelta(minutes=value)

    # Hours: "X hours ago", "X hrs ago", "Xh ago"
    hour_match = re.search(r"(\d+)\s*(hour|hr|h)s?(\s+ago)?", text_lower)
    if hour_match:
        value = int(hour_match.group(1))
        return now_utc - timedelta(hours=value)
        
    # Days: "X days ago", "X d ago", "Xd ago"
    day_match = re.search(r"(\d+)\s*(day|dy|d)s?(\s+ago)?", text_lower)
    if day_match:
        value = int(day_match.group(1))
        return now_utc - timedelta(days=value)
        
    # Weeks: "X weeks ago", "X wk ago", "Xw ago"
    week_match = re.search(r"(\d+)\s*(week|wk|w)s?(\s+ago)?", text_lower)
    if week_match:
        value = int(week_match.group(1))
        return now_utc - timedelta(weeks=value)
        
    # Months/years
    month_match = re.search(r"(\d+)\s*(month|mo)s?(\s+ago)?", text_lower)
    if month_match:
        value = int(month_match.group(1))
        return now_utc - timedelta(days=value * 30)
        
    year_match = re.search(r"(\d+)\s*(year|yr|y)s?(\s+ago)?", text_lower)
    if year_match:
        value = int(year_match.group(1))
        return now_utc - timedelta(days=value * 365)
        
    return now_utc

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
                    r"(?i)(?:posted|active|created|published|added)\s*(?:on|at)?\s*[:\-]?\s*([\d\w\s+\-]+(?:ago|yesterday|today|day|week|month|year|just now)s?)",
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


