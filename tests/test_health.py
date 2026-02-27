import os
from fastapi.testclient import TestClient
from api.main import app

# Ensure we use an in-memory database for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

client = TestClient(app)

def test_health_check():
    """Test that the health check endpoint returns 200 OK and expected structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["database"] == "connected"
    assert "timestamp" in data
