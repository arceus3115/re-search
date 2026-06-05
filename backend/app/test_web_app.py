from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest
from .main import app

client = TestClient(app)


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
    payload = response.json()
    assert "programs" in payload
    assert isinstance(payload["programs"], list)
    assert len(payload["programs"]) >= 40


def test_get_pcsas_data_error(monkeypatch):
    from app.utils.exceptions import ScrapingError
    from app.scrapers import pcsas_scraper

    def _fail(*args, **kwargs):
        raise ScrapingError("PCSAS table missing")

    monkeypatch.setattr(pcsas_scraper, "scrape_pcsas", _fail)
    response = client.get("/api/v1/pcsas")
    assert response.status_code == 502
    assert "PCSAS table missing" in response.json()["detail"]


# ClinicalTrials.gov API Tests


def test_search_clinical_trials_by_pi_missing_param():
    """Test that missing pi_name parameter returns 422."""
    response = client.get("/api/v1/clinicaltrials/search-by-pi")
    assert response.status_code == 422  # Validation error


def test_search_clinical_trials_by_pi_basic():
    """Test basic PI search endpoint (integration test - requires network)."""
    response = client.get(
        "/api/v1/clinicaltrials/search-by-pi?pi_name=Sanjay+Mathew&limit=5"
    )

    # Should succeed (200) or fail with API error (503)
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "trials" in data
        assert "total_count" in data
        assert "pi_name" in data
        assert data["pi_name"] == "Sanjay Mathew"
        assert isinstance(data["trials"], list)
        assert isinstance(data["total_count"], int)
        assert data["total_count"] == len(data["trials"])


def test_search_clinical_trials_by_pi_with_status_filter():
    """Test PI search with status filter."""
    response = client.get(
        "/api/v1/clinicaltrials/search-by-pi"
        "?pi_name=Sanjay+Mathew"
        "&limit=5"
        "&status_filter=RECRUITING,ACTIVE_NOT_RECRUITING"
    )

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "trials" in data
        # Verify all trials match the status filter
        for trial in data["trials"]:
            status = trial.get("overall_status", "").upper()
            assert "RECRUITING" in status or "ACTIVE_NOT_RECRUITING" in status


def test_search_clinical_trials_by_pi_pagination():
    """Test PI search with pagination parameters."""
    response = client.get(
        "/api/v1/clinicaltrials/search-by-pi"
        "?pi_name=Sanjay+Mathew"
        "&page_size=10"
        "&limit=20"
    )

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "trials" in data
        assert len(data["trials"]) <= 20  # Should respect limit


def test_search_clinical_trials_by_pi_invalid_page_size():
    """Test that invalid page_size returns 422."""
    response = client.get(
        "/api/v1/clinicaltrials/search-by-pi"
        "?pi_name=Test&page_size=200"  # Exceeds max of 100
    )
    assert response.status_code == 422


def test_search_clinical_trials_by_pi_empty_results():
    """Test search with PI name that returns no results."""
    response = client.get(
        "/api/v1/clinicaltrials/search-by-pi?pi_name=Nonexistent+Person+XYZ123"
    )

    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert "trials" in data
        assert "total_count" in data
        assert data["total_count"] == 0
        assert len(data["trials"]) == 0


@patch("app.utils.clinicaltrials_client._cache_request")
def test_search_clinical_trials_by_pi_mocked(mock_cache_request):
    """Test PI search with mocked API response."""
    # Mock API response
    mock_response = {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {"nctId": "NCT12345678"},
                    "statusModule": {"overallStatus": "RECRUITING"},
                    "contactsLocationsModule": {
                        "overallOfficials": [
                            {"name": "Test PI", "role": "PRINCIPAL_INVESTIGATOR"}
                        ]
                    },
                }
            }
        ],
        "nextPageToken": None,
    }
    mock_cache_request.return_value = mock_response

    from app.utils.clinicaltrials_client import search_trials_by_pi_name_advanced

    trials = search_trials_by_pi_name_advanced("Test PI", limit=1)

    assert len(trials) == 1
    assert (
        trials[0]["protocolSection"]["identificationModule"]["nctId"] == "NCT12345678"
    )


@patch("app.utils.clinicaltrials_client._cache_request")
def test_search_clinical_trials_by_pi_pagination_mocked(mock_cache_request):
    """Test pagination with mocked API responses."""
    # Mock first page response
    first_page = {
        "studies": [
            {"protocolSection": {"identificationModule": {"nctId": f"NCT{i:08d}"}}}
            for i in range(5)
        ],
        "nextPageToken": "token123",
    }

    # Mock second page response
    second_page = {
        "studies": [
            {"protocolSection": {"identificationModule": {"nctId": f"NCT{i:08d}"}}}
            for i in range(5, 8)
        ],
        "nextPageToken": None,
    }

    # Set up mock to return different responses
    mock_cache_request.side_effect = [first_page, second_page]

    from app.utils.clinicaltrials_client import search_trials_by_pi_name_advanced

    trials = search_trials_by_pi_name_advanced("Test PI", limit=10, page_size=5)

    # Should have fetched from both pages
    assert len(trials) == 8
    assert mock_cache_request.call_count == 2


@patch("app.utils.clinicaltrials_client._cache_request")
def test_search_clinical_trials_by_pi_api_error(mock_cache_request):
    """Test handling of API errors."""
    from app.utils.exceptions import ClinicalTrialsAPIError
    from app.utils.clinicaltrials_client import search_trials_by_pi_name_advanced

    # Mock API error
    mock_cache_request.side_effect = ClinicalTrialsAPIError("API request failed")

    with pytest.raises(ClinicalTrialsAPIError):
        search_trials_by_pi_name_advanced("Test PI")
