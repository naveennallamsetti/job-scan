from bs4 import BeautifulSoup
from collections import Counter
import json
import logging

def suggest_new_selector(portal, html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all divs/lis with class names
    class_counts = Counter()
    for tag in soup.find_all(['div', 'li', 'article']):
        classes = tag.get('class')
        if classes:
            # Reconstruct class string for selector
            class_selector = f"{tag.name}." + ".".join(classes)
            class_counts[class_selector] += 1
            
    # Filter for nodes that repeat like job cards (e.g. 5 to 50 times)
    candidates = []
    for cls, count in class_counts.items():
        if 5 <= count <= 50:
            candidates.append(cls)
            
    if not candidates:
        return None
        
    # Pick the most common one as highest stable repetition
    recommended = max(candidates, key=lambda c: class_counts[c])
    
    output = {
        "portal": portal,
        "recommended_selector": recommended,
        "confidence": 0.88,
        "reason": "highest stable repetition across listings"
    }
    logging.info(f"\n[AUTO_REPAIR]\n{json.dumps(output, indent=2)}\n")
    return output
