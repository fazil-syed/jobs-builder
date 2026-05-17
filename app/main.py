from datetime import date, datetime, timedelta
import json

from app.config.config import settings
from app.helper.process_jobs import process_jobs
from app.schemas.jobs import CountryEnum, JobsList
from app.services.duckduckgosearch import generate_greenhouse_urls
from app.services.scrape_greenhouse import get_jobs_from_greenhouse

if __name__ == "__main__":
    start_date : date = (datetime.now() - timedelta(days=7)).date()
    urls = generate_greenhouse_urls()
    jobs = get_jobs_from_greenhouse(urls=urls)
    print(f"jobs - {len(jobs)}")
    processed_jobs = process_jobs(jobs_list=jobs,start_date=start_date,location_country=CountryEnum.INDIA)
    
    with open("condition_jobs_greenhouse.json","w") as f:
        json.dump(JobsList(jobs=processed_jobs).model_dump(mode="json"),f,indent=4)