import pytest
from fastapi.testclient import TestClient
from .web_app import app

client = TestClient(app)
from app.web_app import app


def test_get_fields():
    response = client.get("/api/v1/fields")
    assert response.status_code == 200
    assert "fields" in response.json()
    assert isinstance(response.json()["fields"], dict)


def test_search_papers():
    response = client.get(
        "/api/v1/search?search_term=artificial+intelligence&from_year=2020&country_code=US"
    )
    assert response.status_code == 200
    assert "works" in response.json()
    assert isinstance(response.json()["works"], list)


def test_get_pcsas_data():
    response = client.get("/api/v1/pcsas")
    assert response.status_code == 200
    assert "programs" in response.json()
    assert isinstance(response.json()["programs"], list)
