from bs4 import BeautifulSoup
import re

def classify_dom(html, portal):
    html_lower = html.lower()
    
    # Check Captcha/Bot Blocks
    if "cloudflare" in html_lower or "cf-browser-verification" in html_lower:
        return {"portal": portal, "classification": "BOT_BLOCK_PAGE", "confidence": 0.95, "signals": {"captcha_detected": True}}
    if "captcha" in html_lower or "verify you are human" in html_lower or "security check" in html_lower or "px-captcha" in html_lower:
        return {"portal": portal, "classification": "CAPTCHA_PAGE", "confidence": 0.95, "signals": {"captcha_detected": True}}
        
    # Check Login Wall
    if "sign in" in html_lower and "password" in html_lower and "email" in html_lower:
        # Check if it's explicitly a forced login wall rather than just a header button
        # (This is tricky, but let's assume if it has login forms and no job cards)
        pass # Will defer to keyword density
        
    # Keyword density
    job_keywords = len(re.findall(r'\b(job|role|position|apply)\b', html_lower))
    
    if job_keywords > 5:
        return {
            "portal": portal, 
            "classification": "VALID_JOB_PAGE", 
            "confidence": min(1.0, 0.5 + (job_keywords * 0.05)), 
            "signals": {"job_keywords": job_keywords, "login_form_detected": False, "captcha_detected": False}
        }
        
    return {
        "portal": portal, 
        "classification": "UNKNOWN_PAGE", 
        "confidence": 0.5, 
        "signals": {"job_keywords": job_keywords, "login_form_detected": False, "captcha_detected": False}
    }
