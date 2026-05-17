from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Job(BaseModel):
    apply_link : Optional[str]
    company_name : Optional[str]
    published_date : Optional[datetime]
    updated_date : Optional[datetime]
    location : Optional[str]
    title : Optional[str]
    
class JobsList(BaseModel):
    jobs : List[Job]