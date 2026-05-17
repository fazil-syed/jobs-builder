from datetime import date, datetime, timedelta
import json
import re

import requests
from trafilatura import extract

from app.config.config import settings
from app.helper.job_processing import get_page_content, process_jobs
from app.helper.job_utils import extract_experience
from app.schemas.jobs import CountryEnum, JobsList
from app.services.generate_urls import generate_greenhouse_urls, generate_lever_urls
from app.services.extract_jobs import get_jobs_from_greenhouse, get_jobs_from_lever








SALARY_PATTERNS = [
    r'₹\s?[\d,]+(?:\s?-\s?₹?\s?[\d,]+)?',
    r'\$\s?[\d,]+(?:\s?-\s?\$?\s?[\d,]+)?',
    r'[\d,]+\s?(?:LPA|CTC)',
]


def extract_salary(text: str) -> str | None:
    for pattern in SALARY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0)

    return None

if __name__ == "__main__":
    start_date : date = (datetime.now() - timedelta(days=7)).date()
    greenhouse_urls = generate_greenhouse_urls()
    
    jobs = get_jobs_from_greenhouse(urls=greenhouse_urls)
    
    lever_urls = generate_lever_urls()
    
    jobs.extend(get_jobs_from_lever(lever_urls))
    print(f"jobs - {len(jobs)}")
    processed_jobs = process_jobs(jobs_list=jobs,start_date=start_date,location_country=CountryEnum.INDIA)
    
    with open("condition_jobs_all.json","w") as f:
        json.dump(JobsList(jobs=processed_jobs).model_dump(mode="json"),f,indent=4)
    

    
    
    
    

    
