"""
Enrich accredited programs with website URLs using OpenAlex institution lookup.
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

from . import openalex_client
from .url_utils import normalize_url

logger = logging.getLogger(__name__)

MIN_NAME_SIMILARITY = 0.72
MIN_CONFIDENCE = 0.65


def _normalize_university_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    name = name.replace("University of ", "")
    name = name.replace("The ", "")
    name = name.replace("Univ.", "University")
    name = name.replace("Univ ", "University ")
    name = name.replace("U.", "University")
    return " ".join(name.split()).lower()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def parse_city_state(address: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Extract city and state abbreviation from an APA-style address."""
    if not address:
        return None, None

    match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s+\d{5}", address)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    state_match = re.search(r",\s*([A-Z]{2})\s+\d{5}", address)
    if state_match:
        return None, state_match.group(1).strip()

    return None, None


def _score_institution(
    university_name: str,
    institution: Dict[str, Any],
    city: Optional[str],
    state: Optional[str],
) -> float:
    inst_name = institution.get("display_name", "")
    name_score = _similarity(_normalize_university_name(university_name), inst_name)

    geo = institution.get("geo", {}) or {}
    inst_city = (geo.get("city") or "").lower()
    inst_region = (geo.get("region") or "").upper()

    geo_score = 0.0
    if state and inst_region == state.upper():
        geo_score += 0.25
    if city and inst_city and city.lower() in inst_city:
        geo_score += 0.15

    homepage = institution.get("homepage_url")
    homepage_score = 0.1 if homepage else 0.0

    return min(name_score * 0.7 + geo_score + homepage_score, 1.0)


def find_program_website(
    university_name: str,
    address: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], float]:
    """
    Find a likely program/university homepage via OpenAlex.

    Returns:
        Tuple of (website_url, openalex_institution_id, confidence)
    """
    if not university_name:
        return None, None, 0.0

    city, state = parse_city_state(address)
    query_params = urlencode({"search": university_name, "per-page": 10})
    search_url = f"{openalex_client.OPENALEX_BASE}/institutions?{query_params}"

    try:
        data = openalex_client.cache_request(search_url)
    except Exception as exc:
        logger.debug(f"OpenAlex institution search failed for {university_name}: {exc}")
        return None, None, 0.0

    best_website = None
    best_id = None
    best_score = 0.0

    for institution in data.get("results", []):
        score = _score_institution(university_name, institution, city, state)
        if score <= best_score:
            continue

        homepage = normalize_url(institution.get("homepage_url"))
        if not homepage:
            continue

        if score < MIN_NAME_SIMILARITY:
            continue

        best_score = score
        best_website = homepage
        best_id = institution.get("id")

    if best_score >= MIN_CONFIDENCE:
        return best_website, best_id, best_score

    return None, best_id, best_score


def enrich_program_websites(programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fill missing program websites using OpenAlex where possible."""
    enriched_count = 0

    for program in programs:
        existing_website = normalize_url(program.get("website"))
        if existing_website:
            program["website"] = existing_website
            if not program.get("website_source"):
                if "PCSAS" in program.get("accreditation_sources", []):
                    program["website_source"] = "pcsas"
                else:
                    program["website_source"] = (
                        program.get("website_source") or "existing"
                    )
            continue

        website, institution_id, confidence = find_program_website(
            program.get("university_name", ""),
            program.get("address"),
        )

        if website:
            program["website"] = website
            program["website_source"] = "openalex"
            program["website_confidence"] = round(confidence, 3)
            enriched_count += 1
            if institution_id:
                program["openalex_institution_id"] = institution_id
        else:
            program["website"] = None
            if institution_id and confidence > 0:
                program["openalex_institution_id"] = institution_id

        outcomes = normalize_url(program.get("student_outcomes_link"))
        program["student_outcomes_link"] = outcomes

    logger.info(f"Enriched {enriched_count} programs with OpenAlex website data")
    return programs
