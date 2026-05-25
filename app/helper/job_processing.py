from datetime import date
from typing import List

from playwright.sync_api import Page, sync_playwright
from trafilatura import extract

from app.helper.job_utils import COUNTRY_TO_LOCATIONS, extract_experience
from app.schemas.jobs import CountryEnum, Job


def process_jobs(
    jobs_list: List[Job],
    start_date: date,
    end_date: date = None,
    location_country: CountryEnum = None,
    remote_allowed: bool = True,
    experience_only: bool = False,
    max_experience: int = None,
) -> List[Job]:
    processed_jobs = []
    locations = []
    if location_country:
        locations = COUNTRY_TO_LOCATIONS[location_country].copy()
        locations.append(location_country)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page.route(
            "**/*",
            lambda route: (
                route.abort()
                if route.request.resource_type
                in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            ),
        )
        for job in jobs_list:
            if locations and job.location:
                if not any(location in job.location for location in locations):
                    if remote_allowed and "Remote" not in job.location:
                        continue
            if end_date:
                if job.published_date and job.published_date.date() > end_date:
                    continue
                if job.updated_date and job.updated_date.date() > end_date:
                    continue

            if job.published_date and job.published_date.date() < start_date:
                continue
            if job.job_link:
                html = get_page_content(page=page, url=job.job_link)
                extracted_content = extract(filecontent=html, output_format="markdown")
                experience_required, experience_years = extract_experience(
                    extracted_content
                )
                job.experience_required = experience_required

                if (
                    experience_years and max_experience
                ) and experience_years > max_experience:
                    continue

                if experience_only and not experience_years:
                    continue

            processed_jobs.append(job)

    return processed_jobs


def get_page_content(page: Page, url: str) -> str:
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=10000)

        # Skip failed responses
        if not response or response.status >= 400:
            print(f"Bad response for {url}")
            return ""

        # Wait only if body is not ready
        page.wait_for_selector("body", timeout=3000)

        return page.content()

    except Exception as e:
        print(f"Failed {url}: {e}")
        return ""
