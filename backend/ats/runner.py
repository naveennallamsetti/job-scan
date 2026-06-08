from .greenhouse import fetch_jobs as fetch_gh
from .lever import fetch_jobs as fetch_lv
from .workday import fetch_jobs as fetch_wd

def run_all_ats(boards_gh=[], boards_lv=[], urls_wd=[]):
    all_jobs = []
    
    for b in boards_gh:
        all_jobs.extend(fetch_gh(b))
        
    for b in boards_lv:
        all_jobs.extend(fetch_lv(b))
        
    for u in urls_wd:
        all_jobs.extend(fetch_wd(u))
        
    return all_jobs
