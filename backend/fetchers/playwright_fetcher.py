import logging
from playwright.sync_api import sync_playwright
import time

def fetch_with_playwright(url, wait_for_selector=None):
    html = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Anti-bot sleep
            time.sleep(2)
            
            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=5000)
                except:
                    pass
            
            html = page.content()
            browser.close()
    except Exception as e:
        logging.error(f"[PLAYWRIGHT] Error fetching {url}: {e}")
    return html


def fetch_with_playwright_bridged(url):
    from playwright.sync_api import sync_playwright
    import time
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle")
        time.sleep(3) # Wait for cloudflare/captcha clear
        html = page.content()
        cookies = context.cookies()
        browser.close()
        return html, cookies, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
