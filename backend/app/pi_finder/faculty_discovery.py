"""
Institution ID discovery helper for finding OpenAlex institution IDs.
Used by the paper-based PI discovery system.
"""

import logging
from difflib import SequenceMatcher
from typing import Optional
from urllib.parse import urlencode, urlparse

from ..utils import openalex_client
from ..utils.website_enricher import parse_city_state

logger = logging.getLogger(__name__)

MIN_NAME_SIMILARITY = 0.72


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _normalize_name(name: str) -> str:
    normalized = name.strip().lower()
    for prefix in ("the ", "university of "):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized


def _score_institution_match(
    university_name: str,
    institution: dict,
    website: str = "",
    address: Optional[str] = None,
) -> float:
    inst_name = institution.get("display_name", "")
    name_score = _similarity(
        _normalize_name(university_name), _normalize_name(inst_name)
    )

    website_score = 0.0
    if website:
        try:
            website_domain = urlparse(website).netloc.lower().replace("www.", "")
            inst_url = (institution.get("homepage_url") or "").lower()
            if website_domain and website_domain in inst_url:
                website_score = 0.35
        except Exception:
            pass

    city, state = parse_city_state(address)
    geo = institution.get("geo", {}) or {}
    geo_score = 0.0
    if state and (geo.get("region") or "").upper() == state.upper():
        geo_score += 0.15
    if city and city.lower() in (geo.get("city") or "").lower():
        geo_score += 0.1

    return min(name_score + website_score + geo_score, 1.0)


def _find_institution_id(
    university_name: str,
    website: str = "",
    address: Optional[str] = None,
    cached_institution_id: Optional[str] = None,
) -> Optional[str]:
    """
    Find OpenAlex institution ID from university name, website, and/or address.
    """
    if cached_institution_id:
        return cached_institution_id

    query_params = urlencode({"search": university_name, "per-page": 10})
    search_url = f"{openalex_client.OPENALEX_BASE}/institutions?{query_params}"

    try:
        data = openalex_client.cache_request(search_url)
        results = data.get("results", [])
    except Exception as exc:
        logger.debug(f"Error searching for institution {university_name}: {exc}")
        return None

    if not results:
        return None

    best_match = None
    best_score = 0.0

    for institution in results:
        score = _score_institution_match(
            university_name, institution, website=website, address=address
        )
        if score > best_score:
            best_score = score
            best_match = institution

    if best_match and best_score >= MIN_NAME_SIMILARITY:
        return best_match.get("id")

    return None
