from pydantic import BaseModel
from typing import Optional


class Job(BaseModel):
    title: str
    company: str
    description: str
    location: str
    url: str
    source: str
    date_posted: Optional[str] = None
