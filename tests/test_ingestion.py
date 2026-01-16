"""Tests for content ingestion endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient

from src.models.schemas import ContentType, IngestionStatus


@pytest.mark.asyncio
async def test_ingest_url_content(client: AsyncClient):
    """Test ingesting URL content."""
    payload = {
        "content_type": ContentType.URL,
        "source": "https://example.com/article",
        "metadata": {
            "author": "John Doe",
            "tags": ["test", "example"],
        },
    }

    response = await client.post("/api/v1/ingest", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    assert "id" in data
    assert data["status"] == IngestionStatus.PENDING
    assert data["message"] == "Content ingestion started"


@pytest.mark.asyncio
async def test_ingest_text_content(client: AsyncClient):
    """Test ingesting text content."""
    payload = {
        "content_type": ContentType.TEXT,
        "source": "This is a test content to be ingested.",
        "metadata": {"category": "test"},
    }

    response = await client.post("/api/v1/ingest", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    data = response.json()
    assert "id" in data
    assert data["status"] == IngestionStatus.PENDING


@pytest.mark.asyncio
async def test_get_ingestion_status_not_found(client: AsyncClient):
    """Test getting status of non-existent content."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/ingest/{fake_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_list_ingested_content(client: AsyncClient):
    """Test listing ingested content."""
    # First, ingest some content
    payload = {
        "content_type": ContentType.TEXT,
        "source": "Test content",
    }
    await client.post("/api/v1/ingest", json=payload)

    # List all content
    response = await client.get("/api/v1/ingest")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_ingested_content_with_pagination(client: AsyncClient):
    """Test listing ingested content with pagination."""
    response = await client.get("/api/v1/ingest?skip=0&limit=10")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_ingest_invalid_content_type(client: AsyncClient):
    """Test ingesting with invalid content type."""
    payload = {
        "content_type": "invalid_type",
        "source": "test",
    }

    response = await client.post("/api/v1/ingest", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
