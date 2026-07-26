import re
from typing import Optional

COUNTRY_TO_LOCATIONS = {
    "India": ["Pune", "Bengaluru", "Bangalore", "Gurugram", "Mumbai", "Delhi"]
}


def extract_experience(text: str) -> tuple[Optional[str], Optional[int]]:
    if not text:
        return (None, None)
    pattern = r"(\d+)\+?\s*years?"

    matches = re.findall(pattern, text, re.IGNORECASE)

    if not matches:
        return (None, None)

    max_years = max(int(x) for x in matches)

    return (f"{max_years}+ years", max_years)
