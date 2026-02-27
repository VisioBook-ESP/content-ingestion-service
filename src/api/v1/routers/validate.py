import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Query, UploadFile
from pydantic import BaseModel

from src.processors.docx_processor import DocxProcessor
from src.processors.html_processor import HTMLProcessor
from src.processors.ocr_processor import OCRProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.processor_factory import ProcessorFactory
from src.processors.txt_processor import TextProcessor

router = APIRouter()

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
    ".html",
    ".htm",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
    ".gif",
    ".webp",
}
DEFAULT_MAX_SIZE_MB = 50

processor_factory = ProcessorFactory(
    [
        PDFProcessor(),
        TextProcessor(),
        DocxProcessor(),
        HTMLProcessor(),
        OCRProcessor(),
    ]
)


class ValidationResponse(BaseModel):
    valid: bool
    fileName: str
    fileSize: int
    fileType: str
    errors: list[str]


@router.post("/", response_model=ValidationResponse)
async def validate(
    file: UploadFile = File(...),
    max_size_mb: Optional[float] = Query(
        default=DEFAULT_MAX_SIZE_MB, description="Taille max en MB"
    ),
):
    """Valide un fichier avant ingestion : format, taille, lisibilite."""
    errors = []
    file_name = file.filename or "unknown"
    ext = os.path.splitext(file_name)[1].lower()

    # 1. Format supporte
    if ext not in SUPPORTED_EXTENSIONS:
        accepted = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        errors.append(f"Format non supporte: '{ext}'. Formats acceptes: {accepted}")

    # 2. Lire le contenu et verifier la taille
    content = await file.read()
    file_size = len(content)
    max_bytes = int((max_size_mb or DEFAULT_MAX_SIZE_MB) * 1024 * 1024)

    if file_size == 0:
        errors.append("Le fichier est vide")
    elif file_size > max_bytes:
        errors.append(
            f"Fichier trop volumineux: {file_size / (1024*1024):.1f} MB (max: {max_size_mb} MB)"
        )

    # 3. Tester la lisibilite (extraction de texte)
    if not errors and ext in SUPPORTED_EXTENSIONS:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            processor = processor_factory.get_processor(tmp_path)
            text = processor.extract_text(tmp_path)
            if not text or not text.strip():
                errors.append("Aucun texte extractible du fichier")
        except Exception as e:
            errors.append(f"Fichier illisible: {e}")
        finally:
            os.unlink(tmp_path)

    return ValidationResponse(
        valid=len(errors) == 0,
        fileName=file_name,
        fileSize=file_size,
        fileType=ext,
        errors=errors,
    )
