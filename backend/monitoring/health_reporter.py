import logging
from backend.monitoring.scraper_metrics import global_metrics

def generate_health_report():
    report = ["\n=== SCRAPER HEALTH REPORT ==="]
    
    for portal, metrics in global_metrics.metrics.items():
        total = metrics["total_requests"]
        if total == 0: continue
            
        if metrics["zero_job_events"] > 0 and metrics["playwright_fallback_count"] == 0:
            status = "FAILING (0 Yield HTTPX)"
            degraded_count += 1
        elif metrics["playwright_fallback_count"] > metrics["httpx_success_count"]:
            status = "DEGRADED"
            degraded_count += 1
        else:
            status = "HEALTHY"
            
        logging.info(f"- {portal.capitalize()}:")
        logging.info(f"  - HTTPX Success: {metrics['httpx_success_count']}/{metrics['total_requests']}")
        logging.info(f"  - Playwright Fallback: {metrics['playwright_fallback_count']}/{metrics['total_requests']}")
        report.append(f"- Status: {status}")
        
    report_text = "\n".join(report) + "\n"
    logging.info(report_text)
    return report_text
