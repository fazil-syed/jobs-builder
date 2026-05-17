import json

from app.config.config import settings
from app.services.duckduckgosearch import generate_greenhouse_urls
from app.services.scrape_greenhouse import get_jobs_from_greenhouse

if __name__ == "__main__":
    urls = generate_greenhouse_urls()
    jobs = get_jobs_from_greenhouse(urls=urls)
    
  