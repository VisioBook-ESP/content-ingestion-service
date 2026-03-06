"""Pytest configuration and shared fixtures."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.schemas.ingest import IngestionOptions  # noqa: E402
from src.schemas.preprocess import CleanOptions  # noqa: E402


@pytest.fixture
def sample_text():
    """Sample text content for testing."""
    return """Ceci est un texte de test pour l'ingestion.

    Il contient plusieurs paragraphes avec des espaces   multiples.

    Le texte peut aussi contenir des "guillemets" français « et » anglais.

    Voici la fin du document."""


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
    <meta name="author" content="Test Author">
</head>
<body>
    <h1>Titre Principal</h1>
    <p>Premier paragraphe de texte.</p>
    <p>Deuxième paragraphe avec <strong>du texte en gras</strong>.</p>
    <script>console.log('should be removed');</script>
</body>
</html>"""


@pytest.fixture
def temp_txt_file(sample_text):
    """Create a temporary text file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(sample_text)
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)


@pytest.fixture
def temp_html_file(sample_html):
    """Create a temporary HTML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(sample_html)
        path = Path(f.name)
    yield path
    if path.exists():
        os.unlink(path)


@pytest.fixture
def temp_pdf_file():
    """Create a temporary valid PDF file using PyMuPDF."""
    import fitz

    doc = fitz.open()
    doc.new_page()
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
        f.write(doc.tobytes())
        path = Path(f.name)
    doc.close()
    yield path
    if path.exists():
        os.unlink(path)


@pytest.fixture
def ingestion_options():
    """Default ingestion options."""
    return IngestionOptions(
        cleanText=True,
        extractMetadata=True,
        chunkSize=100,
        overlap=10,
    )


@pytest.fixture
def clean_options():
    """Default clean options."""
    return CleanOptions(
        removeExtraSpaces=True,
        normalizeQuotes=True,
        fixEncoding=True,
        removeHeaders=False,
        removeFooters=False,
    )


@pytest.fixture
def mock_storage_client():
    """Mock storage client."""
    from tests.mocks import MockStorageClient

    return MockStorageClient()


@pytest.fixture
def mock_db_client():
    """Mock database client."""
    from tests.mocks import MockDatabaseClient

    return MockDatabaseClient()


@pytest.fixture
def mock_processor_factory(temp_txt_file):
    """Mock processor factory."""
    from tests.mocks import MockProcessorFactory

    return MockProcessorFactory()
