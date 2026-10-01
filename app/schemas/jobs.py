from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, StringConstraints

from app.schemas.profile import Person

ExperienceStr = Annotated[
    str, StringConstraints(pattern=r"^(\d+(-\d+)?\+?|\d+\s+to\s+\d+\s+years?)$")
]


class Job(BaseModel):
    apply_link: Optional[str] = None
    job_link: Optional[str] = None
    company_name: Optional[str] = None
    published_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    location: Optional[str] = None
    title: Optional[str] = None
    experience_required: Optional[ExperienceStr] = None
    compensation: Optional[str] = None
    people_to_reach_out: Optional[List[Person]] = None


class CountryEnum(str, Enum):
    INDIA = "India"
