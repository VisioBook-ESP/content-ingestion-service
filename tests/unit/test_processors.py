"""Unit tests for file processors."""

import pytest
from pathlib import Path

from src.processors.txt_processor import TextProcessor
from src.processors.html_processor import HTMLProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.processor_factory import ProcessorFactory


class TestTextProcessor:
    """Tests for TextProcessor."""

    def test_can_handle_txt_file(self):
        processor = TextProcessor()
        assert processor.can_handle("document.txt") is True
        assert processor.can_handle("DOCUMENT.TXT") is True

    def test_cannot_handle_other_files(self):
        processor = TextProcessor()
        assert processor.can_handle("document.pdf") is False
        assert processor.can_handle("document.html") is False
        assert processor.can_handle("document.docx") is False

    def test_extract_text(self, temp_txt_file):
        processor = TextProcessor()
        text = processor.extract_text(str(temp_txt_file))

        assert "texte de test" in text.lower()
        assert len(text) > 0

    def test_extract_metadata_returns_empty_dict(self, temp_txt_file):
        processor = TextProcessor()
        metadata = processor.extract_metadata(str(temp_txt_file))

        assert metadata == {}


class TestHTMLProcessor:
    """Tests for HTMLProcessor."""

    def test_can_handle_html_files(self):
        processor = HTMLProcessor()
        assert processor.can_handle("page.html") is True
        assert processor.can_handle("page.htm") is True
        assert processor.can_handle("PAGE.HTML") is True

    def test_cannot_handle_other_files(self):
        processor = HTMLProcessor()
        assert processor.can_handle("document.txt") is False
        assert processor.can_handle("document.pdf") is False

    def test_extract_text_removes_scripts(self, temp_html_file):
        processor = HTMLProcessor()
        text = processor.extract_text(str(temp_html_file))

        assert "console.log" not in text
        assert "should be removed" not in text

    def test_extract_text_preserves_content(self, temp_html_file):
        processor = HTMLProcessor()
        text = processor.extract_text(str(temp_html_file))

        assert "Titre Principal" in text
        assert "Premier paragraphe" in text
        assert "texte en gras" in text

    def test_extract_metadata_gets_title(self, temp_html_file):
        processor = HTMLProcessor()
        metadata = processor.extract_metadata(str(temp_html_file))

        assert metadata.get("title") == "Test Document"


class TestPDFProcessor:
    """Tests for PDFProcessor."""

    def test_can_handle_pdf_files(self):
        processor = PDFProcessor()
        assert processor.can_handle("document.pdf") is True
        assert processor.can_handle("DOCUMENT.PDF") is True

    def test_cannot_handle_other_files(self):
        processor = PDFProcessor()
        assert processor.can_handle("document.txt") is False
        assert processor.can_handle("document.html") is False

    def test_extract_text_returns_string(self, temp_pdf_file):
        processor = PDFProcessor()
        text = processor.extract_text(str(temp_pdf_file))

        assert isinstance(text, str)

    def test_extract_metadata_returns_dict(self, temp_pdf_file):
        processor = PDFProcessor()
        metadata = processor.extract_metadata(str(temp_pdf_file))

        assert isinstance(metadata, dict)
        assert "title" in metadata
        assert "author" in metadata
        assert "pages" in metadata


class TestProcessorFactory:
    """Tests for ProcessorFactory."""

    def test_get_processor_for_txt(self):
        factory = ProcessorFactory([TextProcessor(), HTMLProcessor(), PDFProcessor()])
        processor = factory.get_processor("document.txt")

        assert isinstance(processor, TextProcessor)

    def test_get_processor_for_html(self):
        factory = ProcessorFactory([TextProcessor(), HTMLProcessor(), PDFProcessor()])
        processor = factory.get_processor("document.html")

        assert isinstance(processor, HTMLProcessor)

    def test_get_processor_for_pdf(self):
        factory = ProcessorFactory([TextProcessor(), HTMLProcessor(), PDFProcessor()])
        processor = factory.get_processor("document.pdf")

        assert isinstance(processor, PDFProcessor)

    def test_raises_for_unsupported_type(self):
        factory = ProcessorFactory([TextProcessor()])

        with pytest.raises(Exception) as exc_info:
            factory.get_processor("document.xyz")

        assert "Unsupported file type" in str(exc_info.value)

    def test_empty_processors_raises(self):
        factory = ProcessorFactory([])

        with pytest.raises(Exception):
            factory.get_processor("document.txt")
