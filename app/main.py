from datetime import date, datetime, timedelta

from ddgs import DDGS
from jinja2 import Environment, FileSystemLoader

from app.helper.job_processing import process_jobs
from app.helper.profile_processing import fetch_people_by_priority
from app.schemas.jobs import CountryEnum
from app.services.extract_jobs import (
    get_jobs_from_greenhouse,
    get_jobs_from_lever,
    get_jobs_from_workable,
)
from app.services.generate_urls import (
    generate_greenhouse_urls,
    generate_lever_urls,
    generate_workable_urls,
)


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
    workable_urls = generate_workable_urls()

    jobs.extend(get_jobs_from_workable(urls=workable_urls))

    jobs.extend(get_jobs_from_lever(lever_urls))

    unique_company_names = {job.company_name for job in jobs}
    people_at_company_map = {}
    for company in unique_company_names:
        people_at_company_map[company] = fetch_people_by_priority(company_name=company)

    processed_jobs = process_jobs(
        jobs_list=jobs,
        start_date=start_date,
        location_country=CountryEnum.INDIA,
        experience_only=False,
        max_experience=3,
        remote_allowed=False,
        people_at_company_map=people_at_company_map,
    )
    print(processed_jobs)
    newsletter_html = render_newsletter(jobs=processed_jobs)
    with open("letter.html", "w") as f:
        print(newsletter_html, file=f, flush=True)

    # post email

    # url = settings.POST_URL
    # today = datetime.today()
    # title = (
    #     f"Engineering Jobs - {start_date.strftime('%d')} - {today.strftime('%d %b %Y')}"
    # )

    # payload = {"title": title, "content": newsletter_html}
    # headers = {"x-api-key": settings.JOBS_AUTH_KEY}
    # response = requests.post(url=url, json=payload, headers=headers)

    # print(response.text)
