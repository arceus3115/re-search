"""
NIH Reporter API client for fetching NIH-funded projects.
"""

import os
import json
import hashlib
import time
import requests
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging

from .exceptions import NIHReporterAPIError

logger = logging.getLogger(__name__)

NIH_REPORTER_API_URL = "https://api.reporter.nih.gov/v2/projects/search"
NIH_REPORTER_CACHE_TTL = 86400 * 7  # 7 days
MAX_PROJECTS_TO_ANALYZE = 25

# Rate limiting state
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
    cache_dir = ".cache/nih_reporter"
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{cache_key}.json")


def _cache_request(
    payload: Dict[str, Any], use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Make a cached POST request to NIH Reporter API.

    Args:
        payload: Request payload (offset will be excluded from cache key for pagination)
        use_cache: Whether to use cache (default True)

    Returns:
        JSON response data

    Raises:
        NIHReporterAPIError: If request fails
    """
    # Create cache key from payload, excluding offset for pagination
    cache_payload = {k: v for k, v in payload.items() if k != "offset"}
    payload_str = json.dumps(cache_payload, sort_keys=True)
    cache_key = hashlib.md5(payload_str.encode()).hexdigest()

    # If this is a paginated request (has offset > 0), don't use cache
    if use_cache and payload.get("offset", 0) == 0:
        cache_path = _get_cache_path(cache_key)

        # Check cache first
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_data = json.load(f)
                    # Check if cache is still valid (TTL)
                    cache_time = os.path.getmtime(cache_path)
                    if time.time() - cache_time < NIH_REPORTER_CACHE_TTL:
                        logger.debug(f"Using cached NIH Reporter data: {cache_key}")
                        return cached_data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error reading cache file {cache_path}: {e}")

    # Enforce rate limiting
    _rate_limit()

    # Make POST request
    try:
        response = requests.post(
            NIH_REPORTER_API_URL,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # Write to cache only for non-paginated requests
        if use_cache and payload.get("offset", 0) == 0:
            try:
                cache_path = _get_cache_path(cache_key)
                with open(cache_path, "w") as f:
                    json.dump(data, f)
            except IOError as e:
                logger.warning(f"Error writing cache file {cache_path}: {e}")

        return data
    except requests.Timeout as e:
        logger.error("NIH Reporter API request timeout")
        raise NIHReporterAPIError(f"Request timeout: {e}") from e
    except requests.RequestException as e:
        logger.error(f"NIH Reporter API request failed: {e}")
        raise NIHReporterAPIError(f"API request failed: {e}") from e
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON response from NIH Reporter API")
        raise NIHReporterAPIError(f"Invalid API response: {e}") from e


def _fetch_all_pages(
    base_payload: Dict[str, Any], max_results: Optional[int] = None, page_size: int = 10
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Fetch all pages of results from NIH Reporter API using pagination.

    Args:
        base_payload: Base request payload (without offset or limit)
        max_results: Maximum number of results to return (None for all)
        page_size: Number of results per page (default 10)

    Returns:
        Tuple of (list of all project dictionaries, metadata from first page)

    Raises:
        NIHReporterAPIError: If API request fails
    """
    all_projects = []
    offset = 0
    page_size = min(page_size, 100)  # Reasonable max
    first_page_meta = None

    # Add limit to base payload
    payload = base_payload.copy()
    payload["limit"] = page_size

    try:
        while True:
            # Add offset to payload
            payload["offset"] = offset

            # Make request (don't cache paginated requests)
            data = _cache_request(payload, use_cache=(offset == 0))

            if not data:
                break

            # Store metadata from first page
            if offset == 0:
                first_page_meta = data.get("meta", {})

            # Extract projects from this page
            results = data.get("results", [])
            all_projects.extend(results)

            logger.debug(
                f"Fetched page with {len(results)} projects (total: {len(all_projects)})"
            )

            # Check if we have enough results
            if max_results and len(all_projects) >= max_results:
                all_projects = all_projects[:max_results]
                break

            # Check if there are more results
            meta = data.get("meta", {})
            total = meta.get("total", 0)
            current_offset = meta.get("offset", 0)

            # If we've fetched all results or got fewer than requested, we're done
            if len(results) < page_size or current_offset + len(results) >= total:
                break

            # Move to next page
            offset += page_size

        logger.info(f"Fetched {len(all_projects)} total projects across all pages")
        return all_projects, first_page_meta

    except NIHReporterAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching paginated results: {e}", exc_info=True)
        raise NIHReporterAPIError(f"Failed to fetch paginated results: {e}") from e


def search_projects_by_project_num(
    project_num: str, use_cache: bool = True
) -> Optional[str]:
    """
    Search for a specific project by project number to get its search URL.

    Args:
        project_num: Core project number (e.g., "R01CA273221")
        use_cache: Whether to use cache (default True)

    Returns:
        Search URL from metadata if found, None otherwise

    Raises:
        NIHReporterAPIError: If API request fails
    """
    if not project_num:
        return None

    try:
        logger.debug(f"Searching NIH Reporter for project URL: {project_num}")

        # Build payload to search by project number
        payload = {
            "criteria": {"project_nums": [project_num]},
            "include_fields": ["CoreProjectNum"],
            "offset": 0,
            "limit": 1,
            "sort_field": "project_start_date",
            "sort_order": "desc",
        }

        # Make request
        data = _cache_request(payload, use_cache=use_cache)

        if not data:
            return None

        # Extract URL from metadata
        meta = data.get("meta", {})
        properties = meta.get("properties", {})
        search_url = properties.get("URL")

        if search_url:
            logger.debug(f"Found search URL for project {project_num}: {search_url}")
            return search_url

        return None

    except NIHReporterAPIError:
        raise
    except Exception as e:
        logger.warning(f"Error getting search URL for project {project_num}: {e}")
        return None


def search_projects_by_pi_name(
    pi_name: str,
    limit: Optional[int] = None,
    page_size: int = 10,
    fetch_project_urls: bool = True,
) -> List[Dict[str, Any]]:
    """
    Search for NIH projects by PI name.

    Args:
        pi_name: Principal Investigator name (e.g., "Sanjay Mathew")
        limit: Maximum number of projects to return (None for all)
        page_size: Number of results per page (default 10)
        fetch_project_urls: Whether to fetch individual project URLs (default True)

    Returns:
        List of project dictionaries matching the PI name, with search_url field populated

    Raises:
        NIHReporterAPIError: If API request fails
    """
    if not pi_name:
        return []

    try:
        logger.info(f"Searching NIH Reporter for projects by PI: {pi_name}")

        # Build the base payload
        base_payload = {
            "criteria": {"fiscal_years": [], "pi_names": [{"any_name": pi_name}]},
            "include_fields": [
                "ApplId",
                "FiscalYear",
                "ProjectSerialNum",
                "Organization",
                "OrganizationType",
                "AwardType",
                "ActivityCode",
                "AwardAmount",
                "ProjectNumSplit",
                "PrincipalInvestigators",
                "ProgramOfficers",
                "CongDist",
                "ProjectStartDate",
                "ProjectEndDate",
                "OpportunityNumber",
                "FullStudySection",
                "AwardNoticeDate",
                "CoreProjectNum",
                "PrefTerms",
                "ProjectTitle",
                "PhrText",
                "SpendingCategoriesDesc",
            ],
            "sort_field": "FiscalYear",
            "sort_order": "desc",
        }

        # Fetch all pages (now returns metadata too)
        all_projects, metadata = _fetch_all_pages(
            base_payload=base_payload, max_results=limit, page_size=page_size
        )

        if not all_projects:
            logger.info(f"No projects found for PI: {pi_name}")
            return []

        # Get overall search URL from metadata
        overall_search_url = None
        if metadata:
            properties = metadata.get("properties", {})
            overall_search_url = properties.get("URL")

        # Fetch individual project URLs if requested
        if fetch_project_urls:
            logger.debug(
                f"Fetching individual project URLs for {len(all_projects)} projects"
            )
            for project in all_projects:
                core_project_num = project.get("core_project_num")
                if core_project_num:
                    # Try to get project-specific URL
                    project_url = search_projects_by_project_num(
                        core_project_num, use_cache=True
                    )
                    if project_url:
                        project["search_url"] = project_url
                    elif overall_search_url:
                        # Fall back to overall search URL
                        project["search_url"] = overall_search_url
                elif overall_search_url:
                    # No project number, use overall search URL
                    project["search_url"] = overall_search_url
        elif overall_search_url:
            # Just use overall search URL for all projects
            for project in all_projects:
                project["search_url"] = overall_search_url

        logger.info(f"Found {len(all_projects)} projects for {pi_name}")
        return all_projects

    except NIHReporterAPIError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching NIH projects: {e}", exc_info=True)
        raise NIHReporterAPIError(f"Failed to search projects: {e}") from e


def format_project_for_display(
    project: Dict[str, Any], pi_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format a raw NIH Reporter project response into a standardized format.

    Args:
        project: Raw project dictionary from API
        pi_name: Optional PI name to include in formatted output

    Returns:
        Formatted project dictionary
    """
    # API returns fields in snake_case format
    # Extract PI name from principal_investigators if not provided
    extracted_pi_name = pi_name
    if not extracted_pi_name:
        principal_investigators = project.get("principal_investigators", [])
        if principal_investigators and len(principal_investigators) > 0:
            # Get first PI's name
            first_pi = principal_investigators[0]
            if isinstance(first_pi, dict):
                extracted_pi_name = first_pi.get("full_name") or first_pi.get(
                    "first_name", ""
                ) + " " + first_pi.get("last_name", "")
            elif isinstance(first_pi, str):
                extracted_pi_name = first_pi

    # Extract organization - API returns as nested dict with org_name
    organization = project.get("organization", {})
    org_name = None
    if organization:
        if isinstance(organization, dict):
            org_name = organization.get("org_name")
        elif isinstance(organization, str):
            org_name = organization

    # Extract PrefTerms - API returns as semicolon-separated string
    pref_terms = project.get("pref_terms", [])
    if isinstance(pref_terms, str):
        # Split by semicolon and clean up
        pref_terms = [term.strip() for term in pref_terms.split(";") if term.strip()]
    elif isinstance(pref_terms, list):
        # Already a list, use as is
        pass
    else:
        pref_terms = []

    # Extract SpendingCategoriesDesc
    spending_categories = project.get("spending_categories_desc", [])
    if isinstance(spending_categories, str):
        spending_categories = [spending_categories]
    elif not isinstance(spending_categories, list):
        spending_categories = []

    # Format dates as YYYY-MM-DD (strip time component if present)
    def format_date(date_str: Optional[str]) -> Optional[str]:
        """Format date string to YYYY-MM-DD format."""
        if not date_str:
            return None
        try:
            # Remove time portion if present
            date_part = str(date_str).split("T")[0].strip()
            # Parse and reformat to ensure YYYY-MM-DD format
            if len(date_part) == 10:
                # Already in YYYY-MM-DD format
                datetime.strptime(date_part, "%Y-%m-%d")
                return date_part
            elif len(date_part) == 7:
                # YYYY-MM format, append -01 for day
                datetime.strptime(date_part, "%Y-%m")
                return f"{date_part}-01"
            else:
                # Try to parse and reformat
                parsed = datetime.strptime(date_part, "%Y-%m-%d")
                return parsed.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            # If parsing fails, return original string
            logger.debug(f"Could not format date: {date_str}")
            return str(date_str) if date_str else None

    formatted_start_date = format_date(project.get("project_start_date"))
    formatted_end_date = format_date(project.get("project_end_date"))

    # Clean PhrText - remove anything before "Project Narrative:"
    phr_text = project.get("phr_text", "")
    if phr_text and isinstance(phr_text, str):
        # Find "Project Narrative:" and keep only text after it
        narrative_marker = "Project Narrative:"
        if narrative_marker in phr_text:
            phr_text = phr_text.split(narrative_marker, 1)[1].strip()
        # Also check for case variations
        narrative_marker_lower = "project narrative:"
        if (
            narrative_marker_lower in phr_text.lower()
            and narrative_marker not in phr_text
        ):
            # Find the position case-insensitively
            idx = phr_text.lower().find(narrative_marker_lower)
            phr_text = phr_text[idx + len(narrative_marker_lower) :].strip()
    else:
        phr_text = phr_text if phr_text else None

    # Extract search_url if present (from API response metadata)
    search_url = project.get("search_url")

    # Return formatted project with snake_case field names (as returned by API)
    return {
        "appl_id": project.get("appl_id"),
        "fiscal_year": project.get("fiscal_year"),
        "project_serial_num": project.get("project_serial_num"),
        "organization": org_name,
        "organization_type": project.get("organization_type"),
        "award_type": project.get("award_type"),
        "activity_code": project.get("activity_code"),
        "award_amount": project.get("award_amount"),
        "project_num_split": project.get("project_num_split"),
        "principal_investigators": project.get("principal_investigators", []),
        "program_officers": project.get("program_officers", []),
        "cong_dist": project.get("cong_dist"),
        "project_start_date": formatted_start_date,
        "project_end_date": formatted_end_date,
        "opportunity_number": project.get("opportunity_number"),
        "full_study_section": project.get("full_study_section"),
        "award_notice_date": project.get("award_notice_date"),
        "core_project_num": project.get("core_project_num"),
        "pref_terms": pref_terms,
        "project_title": project.get("project_title"),
        "phr_text": phr_text,
        "spending_categories_desc": spending_categories,
        "pi_name": extracted_pi_name,
        "search_url": search_url,
    }
