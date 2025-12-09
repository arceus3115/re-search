from pydantic import BaseModel
from typing import List


class PI(BaseModel):
    name: str
    email: str
    university: str
    research_interests: List[str]
