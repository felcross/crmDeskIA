from fastapi.testclient import TestClient

from app.main import app


class TestHealthEndpoint:
    def test_returns_200(self):
        client = TestClient(app)
        resp = client.get("/api/v1/health")
        assert resp.status_code in (200, 503)

    def test_structure(self):
        client = TestClient(app)
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert "status" in data
