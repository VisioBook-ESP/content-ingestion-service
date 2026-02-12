from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MetadataResponse(BaseModel):
    title: Optional[str]
    author: Optional[str]
    language: str
    wordCount: int
    pageCount: Optional[int]
    createdAt: Optional[datetime]
    customFields: dict
