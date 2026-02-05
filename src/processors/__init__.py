"""Processors module for file content extraction."""

from src.processors.base import BaseProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.txt_processor import TextProcessor
from src.processors.docx_processor import DocxProcessor
from src.processors.html_processor import HTMLProcessor
from src.processors.processor_factory import ProcessorFactory

__all__ = [
    "BaseProcessor",
    "PDFProcessor",
    "TextProcessor",
    "DocxProcessor",
    "HTMLProcessor",
    "ProcessorFactory",
]
