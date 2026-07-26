import re
from datetime import datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator

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


class JobsList(BaseModel):
    jobs: List[Job]


class CountryEnum(str, Enum):
    INDIA = "India"


# LLM Extraction Schemas


class JobPosting(BaseModel):
    title: Optional[str] = Field(default=None, description="Job title")
    location: Optional[str] = Field(default=None, description="Job location")
    experience_required: Optional[ExperienceStr] = Field(
        default=None,
        description=("Years of experience only. Allowed: 3, 3-5, 5+, 3 to 5 years"),
    )
    compensation: Optional[str] = Field(
        default=None, description="Salary or compensation if present"
    )

    @field_validator("experience_required", mode="before")
    @classmethod
    def normalize_experience(cls, value):
        if value is None:
            return value

        text = str(value).lower().strip()

        # 3-5
        match = re.search(r"(\d+)\s*-\s*(\d+)", text)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        # 3 to 5 years
        match = re.search(r"(\d+)\s+to\s+(\d+)", text)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        # 5+ years
        match = re.search(r"(\d+)\s*\+", text)
        if match:
            return f"{match.group(1)}+"

        # minimum of 3 years
        match = re.search(r"(\d+)\s+years?", text)
        if match:
            return match.group(1)

        raise ValueError("Could not parse experience")
