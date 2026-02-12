from typing import List

from pydantic import BaseModel


class CleanOptions(BaseModel):
    removeExtraSpaces: bool = True
    normalizeQuotes: bool = True
    fixEncoding: bool = True
    removeHeaders: bool = False
    removeFooters: bool = False


class TextCleanRequest(BaseModel):
    text: str
    options: CleanOptions


class TextCleanResponse(BaseModel):
    cleanedText: str
    changesApplied: List[str]
