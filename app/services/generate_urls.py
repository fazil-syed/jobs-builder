from typing import List

from app.config.config import settings
from app.services.search_paginator import paginate


def generate_api_urls(
    query: str,
    regex_pattern: str,
    url_template: str,
) -> List[str]:
    """Discover API URLs by paginating search results and templating the hits."""
    slugs = paginate(
        query=query,
        regex_pattern=regex_pattern,
        on_progress=lambda page, new: print(f"  {query[:52]} page={page} new={new}"),
    )

    return list(dict.fromkeys(url_template.format(company_code=slug) for slug in slugs))


def generate_greenhouse_urls() -> List[str]:
    return generate_api_urls(
        query=settings.GREENHOUSE_SEARCH_QUERY,
        regex_pattern=r"boards\.greenhouse\.io/([^/]+)",
        url_template=settings.GREENHOUSE_URL_TEMPLATE,
    )


def generate_lever_urls() -> List[str]:
    return generate_api_urls(
        query=settings.LEVER_SEARCH_QUERY,
        regex_pattern=r"jobs\.lever\.co/([^/]+)",
        url_template=settings.LEVER_URL_TEMPLATE,
    )


def generate_workable_urls() -> List[str]:
    return generate_api_urls(
        query=settings.WORKABLE_SEARCH_QUERY,
        regex_pattern=r"apply\.workable\.com/([^/]+)",
        url_template=settings.WORKABLE_URL_TEMPLATE,
    )


def generate_ashby_urls() -> List[str]:
    """Discover Ashby job boards via search.

    The company code is the slug on jobs.ashbyhq.com. Slugs are case-sensitive
    and may legitimately contain dots (e.g. "jimdo.com"), so the value is used
    verbatim -- do not normalise case or strip the extension.
    """
    return generate_api_urls(
        query=settings.ASHBY_SEARCH_QUERY,
        regex_pattern=r"jobs\.ashbyhq\.com/([^/?#]+)",
        url_template=settings.ASHBY_URL_TEMPLATE,
    )


def generate_smartrecruiters_urls() -> List[str]:
    """Discover SmartRecruiters boards via search.

    The trailing slash in the pattern is required -- without it the regex
    would swallow the posting id and build a malformed company identifier.
    """
    return generate_api_urls(
        query=settings.SMARTRECRUITERS_SEARCH_QUERY,
        regex_pattern=r"jobs\.smartrecruiters\.com/([^/?#]+)/",
        url_template=settings.SMARTRECRUITERS_URL_TEMPLATE,
    )
