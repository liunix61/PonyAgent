"""Tests for FastAPI server."""

import pytest
from fastapi.testclient import TestClient

from ponyagent.server.api import create_app


class TestServer:
    def test_root(self) -> None:
        client = TestClient(create_app())
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "PonyAgent"
        assert data["version"] == "0.1.0"

    def test_health(self) -> None:
        client = TestClient(create_app())
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_run(self) -> None:
        client = TestClient(create_app())
        resp = client.post("/run", json={"goal": "say hello"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"]
        assert data["steps"] >= 1
        assert isinstance(data["content"], str)
