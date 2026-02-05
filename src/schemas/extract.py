from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MetadataResponse(BaseModel):
    title: Optional[str]
    author: Optional[str]
    language: str
    wordCount: int
    pageCount: Optional[int]
    createdAt: Optional[datetime]
    customFields: dict
