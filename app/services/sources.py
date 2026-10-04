"""Registry of job sources.

Each source is one entry: how to discover its API URLs, how to turn its
payload into Job objects, and which HTTP verb the board needs. Adding a
source should mean adding a `generate_*_urls` function, an
`extract_*_jobs` function, and one line here.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from app.schemas.jobs import Job
from app.services.extract_jobs import (
    collect_jobs,
    extract_ashby_jobs,
    extract_greenhouse_jobs,
    extract_lever_jobs,
    extract_smartrecruiters_jobs,
    extract_workable_jobs,
    fetch_smartrecruiters_postings,
)
from app.services.generate_urls import (
    generate_ashby_urls,
    generate_greenhouse_urls,
    generate_lever_urls,
    generate_smartrecruiters_urls,
    generate_workable_urls,
)


@dataclass(frozen=True)
class Source:
    name: str
    generate_urls: Callable[[], List[str]]
    extractor: Callable[..., List[Job]]
    method: str = "GET"
    fetch: Optional[Callable[[str], object]] = None


SOURCES: Tuple[Source, ...] = (
    Source("greenhouse", generate_greenhouse_urls, extract_greenhouse_jobs),
    Source("workable", generate_workable_urls, extract_workable_jobs, "POST"),
    Source("lever", generate_lever_urls, extract_lever_jobs),
    Source("ashby", generate_ashby_urls, extract_ashby_jobs),
    Source(
        "smartrecruiters",
        generate_smartrecruiters_urls,
        extract_smartrecruiters_jobs,
        fetch=fetch_smartrecruiters_postings,
    ),
)


def get_jobs_from_source(source: Source) -> List[Job]:
    return collect_jobs(
        urls=source.generate_urls(),
        extractor=source.extractor,
        method=source.method,
        fetch=source.fetch,
    )


def get_all_jobs() -> List[Job]:
    jobs: List[Job] = []

    for source in SOURCES:
        jobs.extend(get_jobs_from_source(source))

    return jobs
