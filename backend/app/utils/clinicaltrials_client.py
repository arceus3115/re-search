"""
ClinicalTrials.gov API client for fetching clinical trials.
"""

import os
import json
import hashlib
import time
import requests
from typing import Optional, List, Dict, Any
import logging

from .exceptions import ClinicalTrialsAPIError

logger = logging.getLogger(__name__)

CLINICALTRIALS_API_URL = "https://clinicaltrials.gov/api/v2/studies"
CLINICALTRIALS_CACHE_TTL = 86400 * 7  # 7 days
MAX_TRIALS_TO_ANALYZE = 15
TOP_TRIALS_FOR_STATEMENT = 5

# Rate limiting state (be conservative with ClinicalTrials.gov)
_last_request_time = 0.0
_MIN_REQUEST_INTERVAL = 0.5  # 0.5 seconds between requests


def _rate_limit():
    """Enforce rate limiting (0.5 seconds between requests)."""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time

    if time_since_last < _MIN_REQUEST_INTERVAL:
        sleep_time = _MIN_REQUEST_INTERVAL - time_since_last
        time.sleep(sleep_time)

    _last_request_time = time.time()


def _get_cache_path(cache_key: str) -> str:
    """Get cache file path for a request."""
    cache_dir = ".cache/clinicaltrials"
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{cache_key}.json")


def _cache_request(
    params: Dict[str, Any], use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Make a cached request to ClinicalTrials.gov API.

    Args:
        params: Request parameters (pageToken will be excluded from cache key)
        use_cache: Whether to use cache (default True)

    Returns:
        JSON response data

    Raises:
        ClinicalTrialsAPIError: If request fails
    """
    # Create cache key from params, excluding pageToken for pagination
    # This allows us to cache the base query and fetch pages separately
    cache_params = {k: v for k, v in params.items() if k != "pageToken"}
    params_str = json.dumps(cache_params, sort_keys=True)
    cache_key = hashlib.md5(params_str.encode()).hexdigest()

    # If this is a paginated request (has pageToken), don't use cache
    # as we want fresh data for each page
    if use_cache and "pageToken" not in params:
        cache_path = _get_cache_path(cache_key)

        # Check cache first
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                    # Check if cache is still valid (TTL)
                    cache_time = os.path.getmtime(cache_path)
                    if time.time() - cache_time < CLINICALTRIALS_CACHE_TTL:
                        logger.debug(
                            f"Using cached ClinicalTrials.gov data: {cache_key}"
                        )
                        return cached_data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error reading cache file {cache_path}: {e}")

    # Enforce rate limiting
    _rate_limit()

    # Make request
    try:
        response = requests.get(
            CLINICALTRIALS_API_URL,
            params=params,
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # Write to cache only for non-paginated requests
        if use_cache and "pageToken" not in params:
            try:
                cache_path = _get_cache_path(cache_key)
                with open(cache_path, "w") as f:
                    json.dump(data, f)
            except IOError as e:
                logger.warning(f"Error writing cache file {cache_path}: {e}")

        return data
    except requests.Timeout as e:
        logger.error("ClinicalTrials.gov API request timeout")
        raise ClinicalTrialsAPIError(f"Request timeout: {e}") from e
    except requests.RequestException as e:
        logger.error(f"ClinicalTrials.gov API request failed: {e}")
        raise ClinicalTrialsAPIError(f"API request failed: {e}") from e
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON response from ClinicalTrials.gov API")
        raise ClinicalTrialsAPIError(f"Invalid API response: {e}") from e


def _fetch_all_pages(
    base_params: Dict[str, Any], max_results: Optional[int] = None, page_size: int = 25
) -> List[Dict[str, Any]]:
    """
    Fetch all pages of results from ClinicalTrials.gov API using pagination.

    Args:
        base_params: Base request parameters (without pageToken or pageSize)
        max_results: Maximum number of results to return (None for all)
        page_size: Number of results per page (default 25, max 100)

    Returns:
        List of all study dictionaries from all pages

    Raises:
        ClinicalTrialsAPIError: If API request fails
    """
    all_studies = []
    page_token = None
    page_size = min(page_size, 100)  # API max is 100

    # Add pageSize to base params
    params = base_params.copy()
    params["pageSize"] = page_size

    try:
        while True:
            # Add pageToken if we have one
            if page_token:
                params["pageToken"] = page_token
            else:
                params.pop("pageToken", None)  # Remove if present

            # Make request (don't cache paginated requests)
            data = _cache_request(params, use_cache=(page_token is None))

            if not data:
                break

            # Extract studies from this page
            studies = data.get("studies", [])
            all_studies.extend(studies)

            logger.debug(
                f"Fetched page with {len(studies)} studies (total: {len(all_studies)})"
            )

            # Check if we have enough results
            if max_results and len(all_studies) >= max_results:
                all_studies = all_studies[:max_results]
                break

            # Check for next page
            page_token = data.get("nextPageToken")
            if not page_token:
                # Last page reached
                break

        logger.info(f"Fetched {len(all_studies)} total studies across all pages")
        return all_studies

    except ClinicalTrialsAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching paginated results: {e}", exc_info=True)
        raise ClinicalTrialsAPIError(f"Failed to fetch paginated results: {e}") from e


def search_trials_by_pi_name_advanced(
    pi_name: str,
    limit: Optional[int] = None,
    page_size: int = 25,
    status_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Search for clinical trials by PI name using the filter.advanced parameter.

    This uses the ClinicalTrials.gov API v2 filter.advanced parameter with
    AREA[ResponsiblePartyInvestigatorFullName] to directly search by PI name.
    Supports pagination to fetch all results.

    Args:
        pi_name: Principal Investigator name (e.g., "Sanjay Mathew")
        limit: Maximum number of trials to return (None for all)
        page_size: Number of results per page (default 25, max 100)
        status_filter: Optional list of statuses to filter (e.g., ["RECRUITING", "ACTIVE_NOT_RECRUITING"])
                      Applied client-side after fetching results

    Returns:
        List of trial dictionaries matching the PI name

    Raises:
        ClinicalTrialsAPIError: If API request fails
    """
    if not pi_name:
        return []

    try:
        logger.info(
            f"Searching ClinicalTrials.gov for trials by PI: {pi_name} (using filter.advanced)"
        )

        # Build the filter.advanced parameter
        # Format: AREA[ResponsiblePartyInvestigatorFullName]{pi_name}
        filter_value = f"AREA[ResponsiblePartyInvestigatorFullName]{pi_name}"

        # Base parameters for the API request
        base_params = {
            "format": "json",
            "filter.advanced": filter_value,
        }

        # Fetch all pages
        all_studies = _fetch_all_pages(
            base_params=base_params, max_results=limit, page_size=page_size
        )

        if not all_studies:
            logger.info(f"No trials found for PI: {pi_name}")
            return []

        # Apply status filter if provided (client-side filtering)
        if status_filter:
            filtered_studies = []
            status_filter_upper = [s.upper() for s in status_filter]

            for study in all_studies:
                protocol_section = study.get("protocolSection", {})
                status_module = protocol_section.get("statusModule", {})
                overall_status = status_module.get("overallStatus", "").upper()

                # Check if status matches any in filter
                if any(status in overall_status for status in status_filter_upper):
                    filtered_studies.append(study)

            logger.info(
                f"Found {len(filtered_studies)} clinical trials for {pi_name} "
                f"(filtered from {len(all_studies)} total by status)"
            )
            return filtered_studies

        logger.info(f"Found {len(all_studies)} clinical trials for {pi_name}")
        return all_studies

    except ClinicalTrialsAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching clinical trials: {e}", exc_info=True)
        raise ClinicalTrialsAPIError(f"Failed to search trials: {e}") from e


def search_trials_by_pi_name(
    pi_name: str,
    institution: Optional[str] = None,
    limit: int = MAX_TRIALS_TO_ANALYZE,
    status_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Search for clinical trials by PI name.

    DEPRECATED: Use search_trials_by_pi_name_advanced() instead for better results.

    Since ClinicalTrials.gov API v2 doesn't support direct PI name search,
    we search by institution and filter client-side for PI matches.

    Args:
        pi_name: Principal Investigator name
        institution: Optional institution name to filter results (required for effective search)
        limit: Maximum number of trials to return
        status_filter: Optional list of statuses to filter (e.g., ["RECRUITING", "ACTIVE_NOT_RECRUITING"])

    Returns:
        List of trial dictionaries matching the PI name

    Raises:
        ClinicalTrialsAPIError: If API request fails
    """
    if not pi_name:
        return []

    # If no institution provided, we can't effectively search
    if not institution:
        logger.warning(
            f"Institution required for clinical trial search. "
            f"Cannot search for trials for PI: {pi_name} without institution."
        )
        return []

    # Default status filter to active trials
    if status_filter is None:
        status_filter = [
            "RECRUITING",
            "ACTIVE_NOT_RECRUITING",
            "ENROLLING_BY_INVITATION",
        ]

    try:
        logger.info(
            f"Searching ClinicalTrials.gov for trials by PI: {pi_name} at institution: {institution}"
        )

        # Search by institution first
        raw_trials = search_trials_by_org(
            org_name=institution, limit=limit * 3
        )  # Get more to filter

        if not raw_trials:
            logger.info(f"No trials found for institution: {institution}")
            return []

        # Filter trials by PI name in overallOfficials
        filtered_trials = []
        pi_name_lower = pi_name.lower()
        pi_name_parts = [
            p.strip() for p in pi_name_lower.split() if len(p.strip()) > 1
        ]  # Split into name parts

        for trial in raw_trials:
            # Check status first (client-side filtering)
            protocol_section = trial.get("protocolSection", {})
            status_module = protocol_section.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "").upper()

            # Filter by status if status_filter provided
            if status_filter:
                status_match = any(s.upper() in overall_status for s in status_filter)
                if not status_match:
                    continue

            # Check if PI name appears in the study data
            contacts_module = protocol_section.get("contactsLocationsModule", {})
            overall_officials = contacts_module.get("overallOfficials", [])

            # Check if any official matches the PI name
            pi_match = False
            for official in overall_officials:
                official_name = official.get("name", "").lower()
                # Check if all significant name parts match
                if all(
                    part in official_name for part in pi_name_parts if len(part) > 2
                ):
                    pi_match = True
                    break
                # Also check reverse (official name parts in PI name)
                official_parts = [
                    p.strip() for p in official_name.split() if len(p.strip()) > 1
                ]
                if len(official_parts) >= 2 and all(
                    part in pi_name_lower for part in official_parts[:2]
                ):
                    pi_match = True
                    break

            if pi_match:
                filtered_trials.append(trial)

            # Stop if we have enough results
            if len(filtered_trials) >= limit:
                break

        logger.info(
            f"Found {len(filtered_trials)} clinical trials for {pi_name} at {institution} (from {len(raw_trials)} total trials)"
        )

        return filtered_trials[:limit]

    except ClinicalTrialsAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching clinical trials: {e}", exc_info=True)
        raise ClinicalTrialsAPIError(f"Failed to search trials: {e}") from e


def search_trials_by_org(
    org_name: str, limit: int = MAX_TRIALS_TO_ANALYZE
) -> List[Dict[str, Any]]:
    """
    Search for clinical trials by organization/institution.

    Note: ClinicalTrials.gov API v2 has limited search capabilities.
    This function attempts to search by organization name using query.term,
    but results may need client-side filtering.

    Args:
        org_name: Organization/institution name
        limit: Maximum number of trials to return

    Returns:
        List of trial dictionaries

    Raises:
        ClinicalTrialsAPIError: If API request fails
    """
    if not org_name:
        return []

    # Try using query.locn for location-based search
    # The API v2 supports query.locn for location terms
    params = {
        "format": "json",
        "query.locn": org_name,  # Search by location
        "pageSize": min(limit, 100),  # API max is 100
    }

    try:
        logger.info(
            f"Searching ClinicalTrials.gov for trials by organization: {org_name}"
        )
        data = _cache_request(params)

        if not data:
            return []

        studies = data.get("studies", [])

        # Filter by organization name in locations (client-side filtering for accuracy)
        filtered_studies = []
        org_name_lower = org_name.lower()

        for study in studies:
            protocol_section = study.get("protocolSection", {})
            contacts_module = protocol_section.get("contactsLocationsModule", {})
            locations = contacts_module.get("locations", [])

            # Check if organization name appears in any location
            for location in locations:
                facility = location.get("facility", "").lower()
                if org_name_lower in facility or facility in org_name_lower:
                    filtered_studies.append(study)
                    break

            if len(filtered_studies) >= limit:
                break

        logger.info(
            f"Found {len(filtered_studies)} clinical trials for {org_name} (from {len(studies)} total studies)"
        )

        return filtered_studies[:limit]
    except ClinicalTrialsAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching clinical trials: {e}", exc_info=True)
        raise ClinicalTrialsAPIError(f"Failed to search trials: {e}") from e


def get_trial_details(nct_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific clinical trial.

    Args:
        nct_id: ClinicalTrials.gov identifier (e.g., "NCT01234567")

    Returns:
        Trial dictionary or None if not found

    Raises:
        ClinicalTrialsAPIError: If API request fails
    """
    if not nct_id:
        return None

    try:
        logger.info(f"Fetching ClinicalTrials.gov trial details: {nct_id}")
        # Try direct API call with NCT ID in URL path if possible
        # Otherwise, we'll need to search and filter
        # For now, return None as direct lookup might not be supported
        # This would require a different endpoint or approach
        logger.warning(
            "Direct NCT ID lookup not fully implemented. Use search_trials_by_pi_name instead."
        )
        return None
    except ClinicalTrialsAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching trial details: {e}", exc_info=True)
        raise ClinicalTrialsAPIError(f"Failed to fetch trial details: {e}") from e


def format_trial_for_display(trial: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a raw ClinicalTrials.gov trial response into a standardized format.

    Args:
        trial: Raw trial dictionary from API

    Returns:
        Formatted trial dictionary
    """
    protocol_section = trial.get("protocolSection", {})
    identification_module = protocol_section.get("identificationModule", {})
    description_module = protocol_section.get("descriptionModule", {})
    conditions_module = protocol_section.get("conditionsModule", {})
    design_module = protocol_section.get("designModule", {})
    status_module = protocol_section.get("statusModule", {})
    sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
    contacts_module = protocol_section.get("contactsLocationsModule", {})

    # Extract conditions
    conditions = conditions_module.get("conditions", [])

    # Extract interventions
    arms_interventions_module = protocol_section.get("armsInterventionsModule", {})
    interventions_list = arms_interventions_module.get("interventions", [])
    interventions = []
    for interv in interventions_list:
        interventions.append(
            {
                "type": interv.get("type", ""),
                "name": interv.get("name", ""),
                "description": interv.get("description", ""),
            }
        )

    # Extract phase
    phases = design_module.get("phases", [])
    phase = phases[0] if phases else None

    # Extract PI name from contacts
    overall_officials = contacts_module.get("overallOfficials", [])
    pi_name = None
    for official in overall_officials:
        if official.get("role") == "PRINCIPAL_INVESTIGATOR":
            pi_name = official.get("name", "")
            break
    if not pi_name and overall_officials:
        pi_name = overall_officials[0].get("name", "")

    # Extract locations
    locations_list = contacts_module.get("locations", [])
    locations = [
        loc.get("facility", "") for loc in locations_list if loc.get("facility")
    ]

    # Extract enrollment
    enrollment_info = status_module.get("enrollmentInfo", {})
    enrollment = enrollment_info.get("count") or enrollment_info.get("target")

    return {
        "nct_id": identification_module.get("nctId", ""),
        "title": identification_module.get("briefTitle", ""),
        "brief_summary": description_module.get("briefSummary", ""),
        "detailed_description": description_module.get("detailedDescription", ""),
        "conditions": conditions,
        "interventions": interventions,
        "phase": phase,
        "overall_status": status_module.get("overallStatus", ""),
        "start_date": status_module.get("startDateStruct", {}).get("date")
        if status_module.get("startDateStruct")
        else None,
        "completion_date": status_module.get("completionDateStruct", {}).get("date")
        if status_module.get("completionDateStruct")
        else None,
        "enrollment": enrollment,
        "lead_sponsor": sponsor_module.get("leadSponsor", {}).get("name")
        if sponsor_module.get("leadSponsor")
        else None,
        "locations": locations,
        "pi_name": pi_name,
    }
