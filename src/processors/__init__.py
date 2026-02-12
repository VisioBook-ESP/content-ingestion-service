"""Processors module for file content extraction."""

from src.processors.base import BaseProcessor
from src.processors.docx_processor import DocxProcessor
from src.processors.html_processor import HTMLProcessor
from src.processors.ocr_processor import OCRProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.processor_factory import ProcessorFactory
from src.processors.txt_processor import TextProcessor

__all__ = [
    "BaseProcessor",
    "PDFProcessor",
    "TextProcessor",
    "DocxProcessor",
    "HTMLProcessor",
    "OCRProcessor",
    "ProcessorFactory",
]
