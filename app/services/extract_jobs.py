from datetime import datetime
import re
from typing import Any, Callable, List
from app.config.config import settings
import requests

from app.schemas.jobs import Job

JOB_TITLES = ["Software","Engineering", "Architect", "Developer"]


def fetch_json(url: str):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def is_relevant_job(title: str) -> bool:
    return any(item.lower() in title.lower() for item in JOB_TITLES)




def extract_lever_company_name(hosted_url: str) -> str:
    match = re.search(
        r"jobs\.lever\.co/([^/]+)",
        hosted_url
    )

    return match.group(1) if match else ""

def collect_jobs(
    urls: List[str],
    extractor: Callable[[Any], List[Job]]
) -> List[Job]:

    jobs = []

    for url in urls:
        try:
            data = fetch_json(url)
            jobs.extend(extractor(data))

        except Exception as err:
            print(f"error {err} for url - {url}")

    return jobs




def extract_greenhouse_jobs(data) -> List[Job]:
    jobs = []

    for job in data.get("jobs", []):

        title = job.get("title", "")

        if not is_relevant_job(title):
            continue

        jobs.append(
            Job(
                apply_link=job.get("absolute_url"),
                job_link=job.get("absolute_url"),
                company_name=job.get("company_name"),
                published_date=job.get("first_published"),
                updated_date=job.get("updated_at"),
                title=title,
                location=job.get("location", {}).get("name"),
            )
        )

    return jobs


def extract_lever_jobs(data) -> List[Job]:
    jobs = []

    for job in data:

        title = job.get("text", "")

        if not is_relevant_job(title):
            continue

        jobs.append(
            Job(
                apply_link=job.get("applyUrl"),
                job_link=job.get("hostedUrl"),
                company_name=extract_lever_company_name(
                    job.get("hostedUrl", "")
                ),
                published_date=datetime.fromtimestamp(
                    job.get("createdAt") / 1000
                ),
                title=title,
                location=job.get("categories", {}).get("location"),
            )
        )

    return jobs


def get_jobs_from_greenhouse(urls: List[str]) -> List[Job]:
    return collect_jobs(urls, extract_greenhouse_jobs)


def get_jobs_from_lever(urls: List[str]) -> List[Job]:
    return collect_jobs(urls, extract_lever_jobs)