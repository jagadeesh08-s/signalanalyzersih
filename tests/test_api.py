"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestAPIEndpoints:
    """Test FastAPI endpoints."""

    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data

    def test_list_analyses_empty(self):
        """Test listing analyses when empty."""
        response = client.get("/api/v1/analysis")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)

    def test_get_stats(self):
        """Test dashboard stats endpoint."""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_analyses" in data
        assert "signals_processed" in data
        assert "average_snr" in data
        assert "most_detected_modulation" in data

    def test_ml_eval(self):
        """Test ML evaluation endpoint."""
        response = client.get("/api/v1/ml/eval")
        assert response.status_code == 200
        data = response.json()
        assert "accuracy" in data
        assert "classes" in data
        assert "confusion_matrix" in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])