import json
import re
from typing import List
from app.config.config import settings

from ddgs import DDGS



def generate_api_urls(
    query: str,
    regex_pattern: str,
    url_template: str,
    max_results: int = 100,
) -> List[str]:
    ddgs = DDGS()
    results = ddgs.text(query=query, max_results=max_results)

    urls = set()

    for result in results:
        link = result.get("href", "")

        match = re.search(regex_pattern, link)

        if match:
            company_code = match.group(1)
            urls.add(url_template.format(company_code=company_code))

    return list(urls)

def generate_greenhouse_urls() -> List[str]:
    return generate_api_urls(
        query=settings.GREENHOUSE_SEARCH_QUERY,
        regex_pattern=r"boards\.greenhouse\.io/([^/]+)",
        url_template=settings.GREENHOUSE_URL_TEMPLATE,
    )
    
    
def generate_lever_urls() -> List[str]:
    return generate_api_urls(
        query=settings.LEVER_SEARCH_QUERY,
        regex_pattern=r"jobs\.lever\.co/([^/]+)",
        url_template=settings.LEVER_URL_TEMPLATE,
    )