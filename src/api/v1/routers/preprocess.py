from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from src.schemas.preprocess import TextCleanRequest, TextCleanResponse
from src.services.chunking_service import ChunkingService
from src.services.text_cleaning_service import TextCleaningService

router = APIRouter()
cleaner = TextCleaningService()
chunker = ChunkingService()


class NormalizeRequest(BaseModel):
    text: str
    targetFormat: str = "plain"


class NormalizeResponse(BaseModel):
    normalizedText: str
    originalFormat: str
    targetFormat: str


class ChunkRequest(BaseModel):
    text: str
    chunkSize: int = 1000
    overlap: int = 100


class ChunkResponse(BaseModel):
    chunks: List[str]
    totalChunks: int
    chunkSize: int
    overlap: int


@router.post("/text-clean", response_model=TextCleanResponse)
async def text_clean(req: TextCleanRequest):
    cleaned, changes = cleaner.clean(req.text, req.options)
    return TextCleanResponse(cleanedText=cleaned, changesApplied=changes)


@router.post("/normalize", response_model=NormalizeResponse)
async def normalize(req: NormalizeRequest):
    normalized = req.text.strip()
    return NormalizeResponse(
        normalizedText=normalized,
        originalFormat="unknown",
        targetFormat=req.targetFormat,
    )


@router.post("/chunk", response_model=ChunkResponse)
async def chunk(req: ChunkRequest):
    chunks = chunker.chunk(req.text, req.chunkSize, req.overlap)
    return ChunkResponse(
        chunks=chunks,
        totalChunks=len(chunks),
        chunkSize=req.chunkSize,
        overlap=req.overlap,
    )
