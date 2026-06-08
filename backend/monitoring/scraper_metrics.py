import json
import logging

class ScraperMetrics:
    def __init__(self):
        self.metrics = {}

    def log_cycle(self, portal, httpx_status, fetch_mode, parse_success, jobs_extracted, zero_job_event):
        log_data = {
            "portal": portal,
            "httpx_status": httpx_status,
            "fetch_mode": fetch_mode,
            "parse_success": parse_success,
            "jobs_extracted": jobs_extracted,
            "zero_job_event": zero_job_event
        }
        logging.info(f"\n[SCRAPER_METRICS]\n{json.dumps(log_data, indent=2)}\n")
        
        if portal not in self.metrics:
            self.metrics[portal] = {
                "total_requests": 0, "httpx_success_count": 0, "httpx_block_count": 0,
                "playwright_fallback_count": 0, "bridged_session_count": 0,
                "successful_parse_count": 0, "zero_job_events": 0,
                "total_jobs_extracted": 0
            }
            
        m = self.metrics[portal]
        m["total_requests"] += 1
        
        if httpx_status in [200]:
            m["httpx_success_count"] += 1
        elif httpx_status in [403, 429]:
            m["httpx_block_count"] += 1
            
        if fetch_mode == "PLAYWRIGHT":
            m["playwright_fallback_count"] += 1
        elif fetch_mode == "BRIDGED":
            m["bridged_session_count"] += 1
            
        if parse_success:
            m["successful_parse_count"] += 1
        
        if zero_job_event:
            m["zero_job_events"] += 1
            
        m["total_jobs_extracted"] += jobs_extracted

global_metrics = ScraperMetrics()
