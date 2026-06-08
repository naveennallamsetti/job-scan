from bs4 import BeautifulSoup
import logging

def validate_selector_integrity(html, selector):
    soup = BeautifulSoup(html, 'html.parser')
    nodes = soup.select(selector)
    
    if len(nodes) < 3:
        return False, "Less than 3 nodes matched"
        
    valid_count = 0
    for node in nodes:
        text = node.get_text(separator=' ', strip=True)
        # Check text length (title/company heuristic)
        if len(text) < 15:
            continue
        # Check if contains a link
        if not node.find('a', href=True):
            continue
            
        valid_count += 1
        
    # We want at least 3 valid jobs extracted
    if valid_count >= 3:
        return True, "Passed integrity check"
    return False, f"Only {valid_count} nodes had valid job structures"
