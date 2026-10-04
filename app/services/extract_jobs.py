import re
import time
from datetime import datetime
from typing import Any, Callable, List, Optional

import requests

from app.config.config import settings
from app.schemas.jobs import Job

TITLE_KEYWORDS = [
    "software",
    "engineer",
    "engineering",
    "developer",
    "backend",
    "back-end",
    "frontend",
    "front-end",
    "full stack",
    "full-stack",
    "platform",
    "devops",
    "sre",
    "automation engineer",
]
EXCLUDE_KEYWORDS = [
    "manager",
    "principle",
    "principal",
    "lead",
    "staff",
    "civil",
    "mechanical",
    "architect",
]

EXCLUDED_COMPANIES = ["jobgether"]

# Every outbound HTTP call gets an explicit timeout so a stalled socket cannot
# hang the run indefinitely.
DEFAULT_HTTP_TIMEOUT = 30
RETRY_BACKOFF_SECONDS = 2


def fetch_json(
    url: str,
    method: str,
    timeout: int = DEFAULT_HTTP_TIMEOUT,
    retries: int = 2,
):
    """Fetch JSON with an explicit timeout and a couple of retries.

    Without a timeout, requests blocks indefinitely on a stalled socket and the
    whole run hangs. Retries absorb the transient connection resets and 429s
    that come with hammering several job boards in quick succession.
    """
    last_error = None

    for attempt in range(retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as err:
            last_error = err

            if attempt < retries:
                time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))

    raise last_error


def is_relevant_job(title: str) -> bool:
    title_lower = title.lower()
    has_job_title = any(item in title_lower for item in TITLE_KEYWORDS)
    has_excluded = any(item in title_lower for item in EXCLUDE_KEYWORDS)
    return has_job_title and not has_excluded


def build_workable_location(job: dict) -> str:
    location_data = job.get("location") or {}
    city = location_data.get("city")
    country = location_data.get("country")
    base_location = city or country or ""

    if job.get("remote"):
        return f"{base_location} Remote".strip() if base_location else "Remote"

    return base_location


def extract_lever_company_name(hosted_url: str) -> str:
    match = re.search(r"jobs\.lever\.co/([^/]+)", hosted_url)

    return match.group(1) if match else ""


def extract_workable_company_name(url: str) -> str:
    match = re.search(r"apply\.workable\.com/api/v3/accounts/([^/]+)", url)
    return match.group(1) if match else ""


def extract_ashby_company_name(url: str) -> str:
    match = re.search(r"posting-api/job-board/([^/?#]+)", url)
    return match.group(1) if match else ""


def build_ashby_location(job: dict) -> str:
    base_location = (job.get("location") or "").strip()

    if job.get("isRemote"):
        return f"{base_location} Remote".strip() if base_location else "Remote"

    return base_location


def parse_iso_datetime(value: Any):
    """Parse an ISO-8601 timestamp, tolerating junk.

    Ashby and Greenhouse both return ISO-8601 with a UTC offset, e.g.
    2026-07-06T13:13:54.171+00:00. Returns None rather than raising, so one
    malformed date cannot discard an otherwise valid job.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def build_smartrecruiters_location(job: dict) -> str:
    """SmartRecruiters nests location; fullLocation is the human-readable form."""
    location_data = job.get("location") or {}

    base_location = (
        location_data.get("fullLocation")
        or location_data.get("city")
        or location_data.get("country")
        or ""
    )

    if location_data.get("remote"):
        return f"{base_location} Remote".strip() if base_location else "Remote"

    return base_location


def build_smartrecruiters_job_link(company_code: str, job_id: Any) -> Optional[str]:
    if not job_id:
        return None
    return f"https://jobs.smartrecruiters.com/{company_code}/{job_id}"


def extract_smartrecruiters_company_code(url: str) -> str:
    match = re.search(r"/v1/companies/([^/?]+)", url)
    return match.group(1) if match else ""


def fetch_smartrecruiters_postings(url: str) -> List[dict]:
    """Fetch every posting for a board, following pagination.

    SmartRecruiters silently caps `limit` at 100, so boards with more postings
    than that need an explicit `offset` loop. No other source paginates, which
    is why this lives here rather than in `collect_jobs`.
    """
    postings: List[dict] = []
    offset = 0
    page_size = 100

    while True:
        separator = "&" if "?" in url else "?"
        page_url = f"{url}{separator}limit={page_size}&offset={offset}"

        try:
            data = fetch_json(page_url, method="GET")
        except Exception as err:
            # Keep whatever earlier pages returned rather than discarding the
            # whole board over a failed page.
            print(f"error fetching smartrecruiters page - {page_url}, error - {err}")
            break

        content = data.get("content") or []
        postings.extend(content)

        total_found = data.get("totalFound") or 0
        offset += page_size

        if not content or offset >= total_found:
            break

    if not postings:
        print(f"smartrecruiters board returned no postings - {url}")

    return postings


def extract_smartrecruiters_jobs(data, **kwargs) -> List[Job]:
    jobs = []
    company_code = extract_smartrecruiters_company_code(kwargs.get("url", ""))

    if not company_code:
        return jobs

    postings = list(iter_job_records(data, "content"))

    for posting in postings:
        try:
            title = posting.get("name") or ""

            if not is_relevant_job(title):
                continue

            company_name = (posting.get("company") or {}).get("name") or company_code

            if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
                continue

            job_link = build_smartrecruiters_job_link(
                company_code=company_code, job_id=posting.get("id")
            )

            if not job_link:
                continue

            jobs.append(
                Job(
                    apply_link=job_link,
                    job_link=job_link,
                    company_name=company_name,
                    published_date=parse_iso_datetime(posting.get("releasedDate")),
                    title=title,
                    location=build_smartrecruiters_location(job=posting),
                )
            )
        except Exception as err:
            # posting may not be a dict, so read the title defensively -- an
            # unguarded .get() here would raise inside the handler itself.
            title_hint = (
                posting.get("name") if isinstance(posting, dict) else repr(posting)
            )
            print(
                "error parsing smartrecruiters job "
                f"for url - {kwargs.get('url', '')}, "
                f"title - {title_hint}, error - {err}"
            )

    return jobs


def iter_job_records(data: Any, key: Optional[str] = None):
    """Yield the job records from an API payload, skipping anything unusable.

    Tolerates a null/empty/scalar envelope and non-dict records. Without this,
    a payload of `null` or a bare list raises out of the extractor and is
    caught by collect_jobs' blanket except, discarding the entire board rather
    than the one bad record.
    """
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = data.get(key) or [] if key else []
    else:
        records = []

    for record in records:
        if isinstance(record, dict):
            yield record


def collect_jobs(
    urls: List[str],
    extractor: Callable[[Any], List[Job]],
    method: str = "GET",
    fetch: Optional[Callable[[str], Any]] = None,
) -> List[Job]:

    jobs = []

    for url in urls:
        try:
            data = fetch(url) if fetch else fetch_json(url, method)
            jobs.extend(extractor(data, url=url))

        except Exception as err:
            print(f"error {err} for url - {url}")

    return jobs


def extract_greenhouse_jobs(data, **kwargs) -> List[Job]:
    jobs = []

    for job in iter_job_records(data, "jobs"):
        try:
            title = job.get("title") or ""

            if not is_relevant_job(title):
                continue

            company_name = job.get("company_name")

            if not company_name:
                continue

            if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
                continue

            print(
                f"fetched job - {title} at company {company_name} "
                f"wiht url {job.get('absolute_url')}"
            )

            jobs.append(
                Job(
                    apply_link=job.get("absolute_url"),
                    job_link=job.get("absolute_url"),
                    company_name=company_name,
                    published_date=parse_iso_datetime(job.get("first_published")),
                    updated_date=parse_iso_datetime(job.get("updated_at")),
                    title=title,
                    location=(job.get("location") or {}).get("name"),
                )
            )
        except Exception as err:
            # job may not be a dict, so avoid an unguarded .get() in the handler.
            title_hint = job.get("title") if isinstance(job, dict) else repr(job)
            print(
                "error parsing greenhouse job "
                f"for url - {kwargs.get('url', '')}, "
                f"title - {title_hint}, error - {err}"
            )

    return jobs


def extract_lever_jobs(data, **kwargs) -> List[Job]:
    jobs = []

    for job in iter_job_records(data):
        title = job.get("text", "")

        if not is_relevant_job(title):
            continue

        company_name = extract_lever_company_name(job.get("hostedUrl") or "")

        if not company_name:
            continue

        if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
            continue

        created_at = job.get("createdAt")

        jobs.append(
            Job(
                apply_link=job.get("applyUrl"),
                job_link=job.get("hostedUrl"),
                company_name=company_name,
                published_date=(
                    datetime.fromtimestamp(created_at / 1000) if created_at else None
                ),
                title=title,
                location=(job.get("categories") or {}).get("location"),
            )
        )

    return jobs


def extract_workable_jobs(data, **kwargs) -> List[Job]:

    jobs = []
    company_name = extract_workable_company_name(url=kwargs.get("url", ""))

    if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
        return jobs

    for job in iter_job_records(data, "results"):
        try:
            title = job.get("title", "")

            if not is_relevant_job(title):
                continue

            job_code = job.get("shortcode")
            job_link = f"https://apply.workable.com/{company_name}/j/{job_code}"
            location = build_workable_location(job=job)

            jobs.append(
                Job(
                    apply_link=job_link,
                    job_link=job_link,
                    company_name=company_name,
                    published_date=job.get("published"),
                    title=title,
                    location=location,
                )
            )
        except Exception as err:
            # job may not be a dict, so avoid an unguarded .get() in the handler.
            title_hint = job.get("title") if isinstance(job, dict) else repr(job)
            print(
                "error parsing workable job "
                f"for url - {kwargs.get('url', '')}, "
                f"title - {title_hint}, error - {err}"
            )

    return jobs


def extract_ashby_jobs(data, **kwargs) -> List[Job]:
    jobs = []
    company_name = extract_ashby_company_name(url=kwargs.get("url", ""))

    if not company_name:
        return jobs

    if any(item.lower() in company_name.lower() for item in EXCLUDED_COMPANIES):
        return jobs

    # `or []` rather than a get() default: the default only applies when the key
    # is absent, not when the API returns an explicit null.
    for job in iter_job_records(data, "jobs"):
        try:
            title = job.get("title") or ""

            if not is_relevant_job(title):
                continue

            job_link = job.get("jobUrl")
            if not job_link:
                continue

            jobs.append(
                Job(
                    apply_link=job.get("applyUrl") or job_link,
                    job_link=job_link,
                    company_name=company_name,
                    published_date=parse_iso_datetime(job.get("publishedAt")),
                    updated_date=parse_iso_datetime(job.get("updatedAt")),
                    title=title,
                    location=build_ashby_location(job=job),
                )
            )
        except Exception as err:
            # job may not be a dict, so avoid an unguarded .get() in the handler.
            title_hint = job.get("title") if isinstance(job, dict) else repr(job)
            print(
                "error parsing ashby job "
                f"for url - {kwargs.get('url', '')}, "
                f"title - {title_hint}, error - {err}"
            )

    return jobs


def get_jobs_from_greenhouse(urls: List[str]) -> List[Job]:
    return collect_jobs(urls, extract_greenhouse_jobs)


def get_jobs_from_lever(urls: List[str]) -> List[Job]:
    return collect_jobs(urls, extract_lever_jobs)


def get_jobs_from_workable(urls: List[str]) -> List[Job]:
    return collect_jobs(urls=urls, extractor=extract_workable_jobs, method="POST")


def get_jobs_from_smartrecruiters(urls: List[str]) -> List[Job]:
    return collect_jobs(
        urls=urls,
        extractor=extract_smartrecruiters_jobs,
        fetch=fetch_smartrecruiters_postings,
    )
