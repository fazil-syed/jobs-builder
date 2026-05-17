from datetime import date, datetime, timedelta
import re
from jinja2 import Environment, FileSystemLoader
import requests
from app.config.config import settings

from app.helper.job_processing import process_jobs
from app.schemas.jobs import CountryEnum
from app.services.generate_urls import generate_greenhouse_urls, generate_lever_urls
from app.services.extract_jobs import get_jobs_from_greenhouse, get_jobs_from_lever


SALARY_PATTERNS = [
    r"₹\s?[\d,]+(?:\s?-\s?₹?\s?[\d,]+)?",
    r"\$\s?[\d,]+(?:\s?-\s?\$?\s?[\d,]+)?",
    r"[\d,]+\s?(?:LPA|CTC)",
]


def extract_salary(text: str) -> str | None:
    for pattern in SALARY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0)

    return None


def render_newsletter(jobs: list) -> str:
    env = Environment(loader=FileSystemLoader("app/static/template"))
    template = env.get_template("weekly_jobs_newsletter.html")
    return template.render(
        jobs=jobs,
        title="Weekly Engineering Jobs",
    )


if __name__ == "__main__":
    start_date: date = (datetime.now() - timedelta(days=7)).date()
    greenhouse_urls = generate_greenhouse_urls()

    jobs = get_jobs_from_greenhouse(urls=greenhouse_urls)

    lever_urls = generate_lever_urls()

    jobs.extend(get_jobs_from_lever(lever_urls))
    processed_jobs = process_jobs(
        jobs_list=jobs,
        start_date=start_date,
        location_country=CountryEnum.INDIA,
        experience_only=True,
        max_experience=3,
    )

    newsletter_html = render_newsletter(jobs=processed_jobs)

    # post email

    url = settings.POST_URL
    title = "Engineering Jobs - 10-17 May 2026"

    payload = {"title": title, "content": newsletter_html}
    headers = {"x-api-key": settings.JOBS_AUTH_KEY}
    response = requests.post(url=url, json=payload, headers=headers)
