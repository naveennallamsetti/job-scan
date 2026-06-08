import re
from datetime import datetime
from dateutil import parser

def hard_normalize(text: str) -> str:
    if not text: return ""
    t = text.lower()
    t = re.sub(r'\b(inc|llc|ltd|corp|co|corporation)\b\.?$', '', t).strip()
    t = re.sub(r'[^a-z0-9]', '', t)
    return t

def soft_normalize_title(title: str) -> str:
    if not title: return ""
    t = title.split('(')[0] 
    t = t.split('-')[0]     
    return t.strip()

def normalize_date_iso(date_str: str):
    if not date_str:
        return None
    try:
        # Use dateutil parser to safely attempt to grab ISO date
        dt = parser.parse(str(date_str))
        return dt.isoformat() + "Z"
    except:
        return date_str
