from typing import List
from urllib.parse import urlparse

from ddgs import DDGS

from app.schemas.profile import Person


def is_valid_linkedin_profile_url(link: str):
    try:
        parsed = urlparse(link)
    except ValueError:
        return False

    domain = parsed.netloc.lower().removeprefix("www.")

    if domain != "linkedin.com" or parsed.scheme not in ("http", "https"):
        return False

    path_parts = [p for p in parsed.path.split("/") if p]

    # must be /in/<something> — path_parts[1] must exist and be non-empty
    return len(path_parts) >= 2 and path_parts[0] == "in" and bool(path_parts[1])


def parse_name_role(title: str) -> dict:

    # Step 1: Cut off at the first "| LinkedIn" — this drops any
    # extra concatenated entries that follow (like the Zimperium ones)
    idx = title.find("| LinkedIn")
    if idx != -1:
        title = title[:idx]
    title = title.strip()

    # Step 2: Split "Name - Rest" on the first " - " only
    parts = title.split(" - ", 1)
    name = parts[0].strip()
    rest = parts[1].strip() if len(parts) > 1 else ""

    # Step 3: Extract role from "rest", dropping the company part
    # Company usually follows " at " or a second " - "
    role = ""
    if rest:
        if " at " in rest:
            role = rest.split(" at ", 1)[0].strip()
        elif " - " in rest:
            role = rest.split(" - ", 1)[0].strip()
        else:
            # No role/company separator found — rest is likely just
            # a company name (e.g. "Ganesh Gopal - Microsoft")
            role = None

    return {"name": name, "role": role}


def fetch_people_at_company(company_name: str, role: str) -> List[Person]:
    ddgs = DDGS()
    query = f'site:linkedin.com/in "{role}" "{company_name}" india'
    try:
        results = ddgs.text(query=query, region="in-en", max_results=20)

        people = []
        for result in results:
            link = result.get("href", "")

            is_valid_profile_link = is_valid_linkedin_profile_url(link=link)
            if not is_valid_profile_link:
                continue
            result_title = result.get("title")
            name_role = parse_name_role(result_title)
            person = Person(
                name=name_role.get("name"),
                role=name_role.get("role"),
                profile_link=link,
            )

            people.append(person)

        return people
    except Exception as err:
        print(err)
        return []


def fetch_people_by_priority(company_name: str) -> List[Person]:
    role1 = "Engineering Manager"
    role2 = "Senior Software Engineer"
    role3 = "Software Engineer"
    ems = fetch_people_at_company(company_name=company_name, role=role1)
    sde_seniors = fetch_people_at_company(company_name=company_name, role=role2)
    sdes = fetch_people_at_company(company_name=company_name, role=role3)
    result = []
    result = filter_by_role(role=role1, people=ems, current_list=result)
    result = filter_by_role(role=role2, people=sde_seniors, current_list=result)
    result = filter_by_role(role=role3, people=sdes, current_list=result)

    return result


def filter_by_role(role, people: List[Person], current_list) -> List[Person]:
    for person in people:
        if len(current_list) >= 5:
            return current_list
        person_role = person.role
        if not person_role:
            continue
        if role.lower() in person_role.lower():
            current_list.append(person)

    return current_list
