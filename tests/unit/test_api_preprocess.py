"""Unit tests for preprocess API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.v1.routers.preprocess import router as preprocess_router


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(preprocess_router, prefix="/preprocess")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestTextCleanEndpoint:
    """Tests for POST /preprocess/text-clean endpoint."""

    def test_clean_removes_extra_spaces(self, client):
        """Test that text-clean removes extra spaces."""
        response = client.post(
            "/preprocess/text-clean",
            json={
                "text": "Hello    world   with   spaces",
                "options": {
                    "removeExtraSpaces": True,
                    "normalizeQuotes": False,
                    "fixEncoding": False,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "    " not in data["cleanedText"]
        assert "removeExtraSpaces" in data["changesApplied"]

    def test_clean_normalizes_quotes(self, client):
        """Test that text-clean normalizes quotes."""
        response = client.post(
            "/preprocess/text-clean",
            json={
                "text": "Test «guillemets» français",
                "options": {
                    "removeExtraSpaces": False,
                    "normalizeQuotes": True,
                    "fixEncoding": False,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "«" not in data["cleanedText"]
        assert "»" not in data["cleanedText"]

    def test_clean_with_all_options(self, client):
        """Test text-clean with all options enabled."""
        response = client.post(
            "/preprocess/text-clean",
            json={
                "text": "Test   «text»   with   issues",
                "options": {
                    "removeExtraSpaces": True,
                    "normalizeQuotes": True,
                    "fixEncoding": True,
                    "removeHeaders": False,
                    "removeFooters": False,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["changesApplied"]) >= 2

    def test_clean_requires_text(self, client):
        """Test that text field is required."""
        response = client.post(
            "/preprocess/text-clean", json={"options": {"removeExtraSpaces": True}}
        )

        assert response.status_code == 422


class TestNormalizeEndpoint:
    """Tests for POST /preprocess/normalize endpoint."""

    def test_normalize_text(self, client):
        """Test basic text normalization."""
        response = client.post(
            "/preprocess/normalize",
            json={
                "text": "  Text with whitespace  ",
                "targetFormat": "plain",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["normalizedText"] == "Text with whitespace"
        assert data["targetFormat"] == "plain"

    def test_normalize_with_default_format(self, client):
        """Test normalization with default format."""
        response = client.post(
            "/preprocess/normalize",
            json={
                "text": "Some text",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["targetFormat"] == "plain"


class TestChunkEndpoint:
    """Tests for POST /preprocess/chunk endpoint."""

    def test_chunk_text(self, client):
        """Test basic text chunking."""
        text = " ".join([f"word{i}" for i in range(50)])

        response = client.post(
            "/preprocess/chunk",
            json={
                "text": text,
                "chunkSize": 10,
                "overlap": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["chunks"]) > 1
        assert data["totalChunks"] == len(data["chunks"])
        assert data["chunkSize"] == 10
        assert data["overlap"] == 2

    def test_chunk_with_defaults(self, client):
        """Test chunking with default parameters."""
        text = " ".join(["word"] * 2000)

        response = client.post(
            "/preprocess/chunk",
            json={
                "text": text,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chunkSize"] == 1000
        assert data["overlap"] == 100

    def test_chunk_short_text(self, client):
        """Test chunking text shorter than chunk size."""
        response = client.post(
            "/preprocess/chunk",
            json={
                "text": "Short text",
                "chunkSize": 100,
                "overlap": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["totalChunks"] == 1
        assert data["chunks"][0] == "Short text"

    def test_chunk_empty_text(self, client):
        """Test chunking empty text."""
        response = client.post(
            "/preprocess/chunk",
            json={
                "text": "",
                "chunkSize": 10,
                "overlap": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["totalChunks"] == 1
