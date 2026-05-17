import json
import re
from typing import List
from app.config.config import settings

from ddgs import DDGS



def generate_greenhouse_urls() -> List[str]:
    ddgs= DDGS()
    results = ddgs.text(query=settings.SEARCH_QUERY,max_results=100)

    greenhouse_links = []

    for result in results:
        link = result.get("href","")
        match = re.search(
                    r"boards\.greenhouse\.io/([^/]+)",
                    link
                )
        
        if match:
            company_code = match.group(1)
            gen_url = f"https://boards-api.greenhouse.io/v1/boards/{company_code}/jobs"
            greenhouse_links.append(gen_url)
            
    greenhouse_links = {*greenhouse_links} #convert to set
    greenhouse_links = [*greenhouse_links] # back to list
    
    return greenhouse_links
    