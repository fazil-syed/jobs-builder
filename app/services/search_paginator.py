"""Paginated search over pinned yahoo results.

Job boards are discovered by running a `site:` search and reading the board slug
out of each hit. A single page is not enough -- one query against SmartRecruiters
returned 140 boards only by walking pages until it stopped yielding new ones.

Engine is pinned deliberately. Of the nine backends ddgs exposes, yahoo is the
only one measured to honour the `page` argument: its engine sends
`payload["b"] = (page - 1) * 7 + 1` and returns genuinely new results each page.
yandex points at a site-search endpoint that returns page-0 results verbatim for
every page, so paging it only re-fetches the same handful of hits. duckduckgo,
brave, mojeek, google, wikipedia and startpage are blocked at the network level
from this host and only burn the timeout.

One query per source. `paginate` walks that query's pages until it stops
yielding new boards, so a single query reaches far deeper than several
phrasings of the same search could.
"""

import re
import time
from typing import Callable, List, Optional

from ddgs import DDGS

# The only engine measured to paginate.
BACKEND = "yahoo"
TIMEOUT = 25

# Region is configurable in principle but not in practice: "us-en" and "in-en"
# both returned identical boards on a clean IP, so there was no evidence to
# prefer one. Left as a constant rather than exposed as config.
REGION = "us-en"

# Runaway guard only. The empty-page streak below is what actually stops a query.
MAX_PAGES = 50

# Stop after this many consecutive pages that add nothing new. A page that
# repeats known slugs counts as empty even though it returned results.
EMPTY_PAGE_LIMIT = 3

# Tolerate a long search outage before abandoning a query. Not consecutive --
# any successful page resets the count, so a flapping engine still gets a
# fair chance across a long run.
FAILURE_LIMIT = 10

# Floor, not a tunable. Yahoo throttles without erroring -- it serves a valid
# page containing no results, so ddgs raises "No results found" rather than
# anything that identifies a rate limit. At 3s every call soft-blocks and
# discovery silently returns nothing; at 8s pages keep succeeding. Do not lower
# this without re-measuring.
SPACING_SECONDS = 8

# Backoff after a failed page. Long, because a throttle needs minutes to clear.
FAILURE_BACKOFF_SECONDS = 60


def paginate(
    query: str,
    regex_pattern: str,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> List[str]:
    """Search page by page until results stop yielding new regex matches.

    Returns the distinct group-1 matches across every page.
    """
    ddgs = DDGS(timeout=TIMEOUT)
    seen: set = set()
    empty_streak = 0
    failures = 0

    for page in range(MAX_PAGES):
        try:
            results = ddgs.text(
                query=query,
                region=REGION,
                max_results=100,
                backend=BACKEND,
                page=page,
            )
        except Exception as err:
            failures += 1

            if failures >= FAILURE_LIMIT:
                print(f"abandoning {query!r} after {failures} failures - {err}")
                break

            time.sleep(FAILURE_BACKOFF_SECONDS)
            continue

        failures = 0

        slugs = [
            match.group(1)
            for result in results
            if (match := re.search(regex_pattern, result.get("href", "")))
        ]

        # A page that only repeats slugs we already have counts as empty.
        new_slugs = [slug for slug in slugs if slug not in seen]
        empty_streak = 0 if new_slugs else empty_streak + 1
        seen.update(slugs)

        if on_progress:
            on_progress(page, len(new_slugs))

        if empty_streak >= EMPTY_PAGE_LIMIT:
            break

        time.sleep(SPACING_SECONDS)

    return sorted(seen)
