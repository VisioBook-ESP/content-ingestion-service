from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import tempfile
import os

from src.schemas.extract import MetadataResponse
from src.processors.processor_factory import ProcessorFactory
from src.processors.pdf_processor import PDFProcessor
from src.processors.txt_processor import TextProcessor
from src.processors.docx_processor import DocxProcessor
from src.processors.html_processor import HTMLProcessor
from src.services.metadata_extractor import MetadataExtractor


router = APIRouter()
processor_factory = ProcessorFactory([
    PDFProcessor(),
    TextProcessor(),
    DocxProcessor(),
    HTMLProcessor(),
])
metadata_extractor = MetadataExtractor()


class TextExtractionResponse(BaseModel):
    text: str
    wordCount: int
    fileType: str


@router.post("/text", response_model=TextExtractionResponse)
async def extract_text(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".txt"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        processor = processor_factory.get_processor(tmp_path)
        text = processor.extract_text(tmp_path)
        word_count = len(text.split())

        return TextExtractionResponse(
            text=text,
            wordCount=word_count,
            fileType=suffix.lstrip("."),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.unlink(tmp_path)


@router.post("/metadata", response_model=MetadataResponse)
async def extract_metadata(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".txt"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        processor = processor_factory.get_processor(tmp_path)
        text = processor.extract_text(tmp_path)
        metadata = processor.extract_metadata(tmp_path)
        enriched = metadata_extractor.enrich(metadata, text)

        return MetadataResponse(
            title=enriched.get("title"),
            author=enriched.get("author"),
            language=enriched.get("language", "fr"),
            wordCount=enriched.get("wordCount", 0),
            pageCount=enriched.get("pages"),
            createdAt=enriched.get("createdAt"),
            customFields=enriched.get("customFields", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.unlink(tmp_path)