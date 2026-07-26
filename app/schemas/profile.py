from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Person(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    profile_link: Optional[str] = None
