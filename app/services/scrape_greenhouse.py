import json
from typing import List
from app.config.config import settings
import requests

from app.schemas.jobs import Job, JobsList


def get_jobs_from_greenhouse(urls: List[str]) -> List[Job]:
    jobs = []
    for url in urls:
        response = requests.get(url)
        data = response.json()
        job_titles = ["Software","Engineering", "Architect", "Developer"]
        try:
            for job in data["jobs"]:
                if any(item in job.get("title") for item in job_titles):
                    jobs.append(Job(
                        apply_link=job.get("absolute_url"),
                        company_name=job.get("company_name"),
                        published_date=job.get("first_published"),
                        updated_date=job.get("updated_at"),
                        title=job.get("title"),
                        location=job.get("location",{}).get("name")
                    ))                    
        except Exception as err:
            print(f"error {err} for url - {url}")
            continue
    return jobs