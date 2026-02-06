from typing import Literal, Optional

from pydantic import BaseModel


class IngestionOptions(BaseModel):
    cleanText: bool = True
    extractMetadata: bool = True
    chunkSize: int = 1000
    overlap: int = 100


class IngestionRequest(BaseModel):
    fileId: str
    projectId: str
    options: Optional[IngestionOptions] = IngestionOptions()


class IngestionResponse(BaseModel):
    jobId: str
    status: Literal["queued", "processing", "completed", "failed"]
