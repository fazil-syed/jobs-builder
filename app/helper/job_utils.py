import re


COUNTRY_TO_LOCATIONS = {
    "India": [
        "Pune",
        "Bengaluru",
        "Bangalore",
        "Gurugram",
        "Mumbai",
        "Delhi"
    ]
}

def extract_experience(text: str) -> str | None:
    if not text:
        return None
    pattern = r'(\d+)\+?\s*years?'

    matches = re.findall(pattern, text, re.IGNORECASE)

    if not matches:
        return None

    max_years = max(int(x) for x in matches)

    return f"{max_years}+ years"