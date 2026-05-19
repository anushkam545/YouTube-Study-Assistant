"""
API Tests - YouTube Study Assistant
Tests for all API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "endpoints" in response.json()


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_info():
    """Test API info endpoint"""
    response = client.get("/api/info")
    assert response.status_code == 200
    assert "app_name" in response.json()


def test_transcript_invalid_url():
    """Test transcript endpoint with invalid URL"""
    response = client.post(
        "/api/transcript",
        json={"youtube_url": "https://invalid-url.com"}
    )
    assert response.status_code == 400
    assert "Invalid YouTube URL" in response.json()["detail"]


def test_transcript_missing_url():
    """Test transcript endpoint with missing URL"""
    response = client.post("/api/transcript", json={})
    assert response.status_code == 422  # Validation error


# Note: Real YouTube URL test would require internet connection
# This is a placeholder for integration testing
def test_transcript_valid_url_mock():
    """
    Test transcript endpoint with valid URL (mock)
    
    For real testing, replace with actual YouTube URL
    Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
    """
    # Skip this test in automated runs
    pytest.skip("Requires internet connection and valid YouTube URL")
