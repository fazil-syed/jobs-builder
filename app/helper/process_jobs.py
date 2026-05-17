from datetime import date
from typing import List

from app.schemas.jobs import CountryEnum, Job


def process_jobs(jobs_list : List[Job],start_date: date,end_date :date = None,location_country: CountryEnum = None,remote : bool = True) -> List[Job]:
    processed_jobs = []
    locations = []
    if location_country:
        locations = COUNTRY_TO_LOCATIONS[location_country]
        locations.append(location_country)
    
    for job in jobs_list:            
        if locations and job.location:
            if not any(location in job.location for location in locations):
                if remote and "Remote" not in job.location:
                    continue
        if end_date:
            if job.published_date and job.published_date.date() > end_date:
                continue
            if job.updated_date and job.updated_date.date() > end_date:
                continue
           
         
        if (job.published_date and job.published_date.date() < start_date) and (job.updated_date and job.updated_date.date() < start_date):
            continue
        
        processed_jobs.append(job)
            
    return processed_jobs
    

COUNTRY_TO_LOCATIONS = {
    "India": [
        "Pune",
        "Bengaluru",
        "Bangalore",
        "Gurugram",
        "Mumbai",
        "Delhi"
    ]
}