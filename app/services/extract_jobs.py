import re
from datetime import datetime
from typing import Any, Callable, List

import requests

from app.schemas.jobs import Job

# JOB_TITLES = ["Software", "Engineering", "Architect", "Developer"]
JOB_TITLES = ["Software", "Developer", "Engineer"]
EXCLUDE_KEYWORDS = [
    "Manager",
    "Principle",
    "Principal",
    "Lead",
    "Staff",
    "Civil",
    "Mechanical",
    "Architect",
]

EXCLUDED_COMPANIES = ["jobgether"]


def fetch_json(url: str, method: str):
    if method == "GET":
        response = requests.get(url)
    else:
        response = requests.post(url)
    response.raise_for_status()
    return response.json()


def is_relevant_job(title: str) -> bool:
    title_lower = title.lower()
    has_job_title = any(item.lower() in title_lower for item in JOB_TITLES)
    has_excluded = any(item.lower() in title_lower for item in EXCLUDE_KEYWORDS)
    return has_job_title and not has_excluded


def extract_lever_company_name(hosted_url: str) -> str:
    match = re.search(r"jobs\.lever\.co/([^/]+)", hosted_url)

    return match.group(1) if match else ""


def extract_workable_company_name(url: str) -> str:
    match = re.search(r"apply\.workable\.com/api/v3/accounts/([^/]+)", url)
    return match.group(1) if match else ""


def collect_jobs(
    urls: List[str], extractor: Callable[[Any], List[Job]], method: str = "GET"
) -> List[Job]:

    jobs = []

    for url in urls:
        try:
            data = fetch_json(url, method)
            jobs.extend(extractor(data, url=url))

        except Exception as err:
            print(f"error {err} for url - {url}")

    return jobs


def extract_greenhouse_jobs(data, **kwargs) -> List[Job]:
    jobs = []

    for job in data.get("jobs", []):
        title = job.get("title", "")
        if not is_relevant_job(title):
            continue

        company_name = job.get("company_name")

        if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
            continue
        print(
            f"fetched job - {title} at company {company_name} wiht url {job.get('absolute_url')}"
        )

        jobs.append(
            Job(
                apply_link=job.get("absolute_url"),
                job_link=job.get("absolute_url"),
                company_name=company_name,
                published_date=job.get("first_published"),
                updated_date=job.get("updated_at"),
                title=title,
                location=job.get("location", {}).get("name"),
            )
        )

    return jobs


def extract_lever_jobs(data, **kwargs) -> List[Job]:
    jobs = []

    for job in data:
        title = job.get("text", "")

        if not is_relevant_job(title):
            continue

        company_name = extract_lever_company_name(job.get("hostedUrl", ""))
        if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
            continue

        jobs.append(
            Job(
                apply_link=job.get("applyUrl"),
                job_link=job.get("hostedUrl"),
                company_name=company_name,
                published_date=datetime.fromtimestamp(job.get("createdAt") / 1000),
                title=title,
                location=job.get("categories", {}).get("location"),
            )
        )

    return jobs


def extract_workable_jobs(data, **kwargs) -> List[Job]:

    jobs = []

    for job in data.get("results", []):
        title = job.get("title", "")

        if not is_relevant_job(title):
            continue

        job_code = job.get("shortcode")
        company_name = extract_workable_company_name(url=kwargs.get("url", ""))
        if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
            continue

        job_link = f"https://apply.workable.com/{company_name}/j/{job_code}"
        jobs.append(
            Job(
                apply_link=job_link,
                job_link=job_link,
                company_name=company_name,
                published_date=job.get("published"),
                title=title,
                location=job.get("location", {}).get("city") + "Remote"
                if job.get("remote")
                else "",
            )
        )

    return jobs


def get_jobs_from_greenhouse(urls: List[str]) -> List[Job]:
    return collect_jobs(urls, extract_greenhouse_jobs)


def get_jobs_from_lever(urls: List[str]) -> List[Job]:
    return collect_jobs(urls, extract_lever_jobs)


def get_jobs_from_workable(urls: List[str]) -> List[Job]:
    return collect_jobs(urls=urls, extractor=extract_workable_jobs, method="POST")
