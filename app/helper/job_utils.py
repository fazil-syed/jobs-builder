import re
from typing import Optional

COUNTRY_TO_LOCATIONS = {
    "India": ["Pune", "Bengaluru", "Bangalore", "Gurugram", "Mumbai", "Delhi"]
}

# No real engineering requirement asks for more than this. Guards against
# incidental large numbers on the page (e.g. "50,000 years" never appears,
# but "25000 years of history" style copy can).
CAP = 40

# Matches "<n> years" style figures, optionally tied to experience wording.
_EXPERIENCE = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:-|–|to)?\s*\d?\s*(?:-\s*)?(?:years?|yrs?)"
    r"(?:\s*(?:of\s+)?(?:relevant\s+|hands[- ]on\s+|professional\s+)?"
    r"(?:experience|exp\b|work experience|industry experience))?",
    re.IGNORECASE,
)

# Company-age / heritage phrasing that yields false "<n> years" matches.
_NOT_ABOUT_EXPERIENCE = re.compile(
    r"(?:founded|established|operating|history|old|since|anniversary|celebrat)",
    re.IGNORECASE,
)


def extract_experience(text: str) -> tuple[Optional[str], Optional[int]]:
    if not text:
        return (None, None)

    max_years = None

    for match in _EXPERIENCE.finditer(text):
        years = int(match.group(1))
        if years > CAP:
            continue

        # Check the surrounding sentence: if it talks about company age and
        # this match does not itself say "experience", skip it.
        context = text[max(0, match.start() - 60) : match.end() + 20]
        if _NOT_ABOUT_EXPERIENCE.search(context) and not re.search(
            r"(experience|exp\b)", match.group(0), re.IGNORECASE
        ):
            continue

        max_years = years if max_years is None else max(max_years, years)

    if max_years is None:
        return (None, None)

    return (f"{max_years}+", max_years)
