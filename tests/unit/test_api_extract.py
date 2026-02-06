"""Unit tests for extract API endpoints."""

import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.routers.extract import router as extract_router


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(extract_router, prefix="/extract")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_txt_content():
    """Sample text file content."""
    return b"Ceci est un texte de test pour l'extraction."


@pytest.fixture
def sample_html_content():
    """Sample HTML file content."""
    return b"""<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><p>Contenu HTML de test.</p></body>
</html>"""


class TestTextExtractionEndpoint:
    """Tests for POST /extract/text endpoint."""

    def test_extract_text_from_txt_file(self, client, sample_txt_content):
        """Test text extraction from TXT file."""
        response = client.post(
            "/extract/text",
            files={"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "texte de test" in data["text"]
        assert data["wordCount"] > 0
        assert data["fileType"] == "txt"

    def test_extract_text_from_html_file(self, client, sample_html_content):
        """Test text extraction from HTML file."""
        response = client.post(
            "/extract/text",
            files={"file": ("test.html", io.BytesIO(sample_html_content), "text/html")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "Contenu HTML" in data["text"]
        assert data["fileType"] == "html"

    def test_extract_text_requires_file(self, client):
        """Test that file is required."""
        response = client.post("/extract/text")

        assert response.status_code == 422

    def test_extract_text_unsupported_format(self, client):
        """Test extraction from unsupported format."""
        response = client.post(
            "/extract/text",
            files={"file": ("test.xyz", io.BytesIO(b"content"), "application/octet-stream")},
        )

        assert response.status_code == 400


class TestMetadataExtractionEndpoint:
    """Tests for POST /extract/metadata endpoint."""

    def test_extract_metadata_from_txt(self, client, sample_txt_content):
        """Test metadata extraction from TXT file."""
        response = client.post(
            "/extract/metadata",
            files={"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "wordCount" in data
        assert "language" in data
        assert data["wordCount"] > 0

    def test_extract_metadata_from_html(self, client, sample_html_content):
        """Test metadata extraction from HTML file."""
        response = client.post(
            "/extract/metadata",
            files={"file": ("test.html", io.BytesIO(sample_html_content), "text/html")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "wordCount" in data

    def test_extract_metadata_structure(self, client, sample_txt_content):
        """Test that metadata has expected structure."""
        response = client.post(
            "/extract/metadata",
            files={"file": ("test.txt", io.BytesIO(sample_txt_content), "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()

        expected_fields = [
            "title",
            "author",
            "language",
            "wordCount",
            "pageCount",
            "createdAt",
            "customFields",
        ]
        for field in expected_fields:
            assert field in data

    def test_extract_metadata_requires_file(self, client):
        """Test that file is required."""
        response = client.post("/extract/metadata")

        assert response.status_code == 422
