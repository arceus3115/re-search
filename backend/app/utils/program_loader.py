"""
Program loader for accredited Clinical Psychology programs.
Uses the unified aggregated APA + PCSAS dataset for all consumers.
"""

import logging
from typing import Any, Dict, List

from ..scrapers import pcsas_scraper

logger = logging.getLogger(__name__)


def _to_standard_format(program: Dict[str, Any]) -> Dict[str, Any]:
    sources = program.get("accreditation_sources", [])
    status_parts = []
    if "APA" in sources:
        status_parts.append("APA Accredited")
    if "PCSAS" in sources:
        status_parts.append("PCSAS Accredited")

    return {
        "id": program.get("id"),
        "program_name": program.get("program_type", "Clinical Ph.D."),
        "university": program.get("university_name", ""),
        "website": program.get("website") or "",
        "accreditation_status": ", ".join(status_parts)
        or program.get("accreditation_status", "Accredited"),
        "student_outcomes_link": program.get("student_outcomes_link") or "",
        "address": program.get("address") or "",
        "accreditation_sources": sources,
        "website_source": program.get("website_source"),
        "openalex_institution_id": program.get("openalex_institution_id"),
        "next_site_visit_year": program.get("next_site_visit_year"),
    }


def load_apa_programs() -> List[Dict[str, Any]]:
    """Load APA-accredited programs from the unified aggregated dataset."""
    from .program_aggregator import get_aggregated_programs

    programs = get_aggregated_programs(use_cache=True)
    return [
        _to_standard_format(program)
        for program in programs
        if "APA" in program.get("accreditation_sources", [])
    ]


def load_pcsas_programs() -> List[Dict[str, Any]]:
    """
    Load PCSAS accredited programs using the scraper.
    Converts to standardized format.
    """
    try:
        raw_programs = pcsas_scraper.scrape_pcsas()
        standardized = []
        for program in raw_programs:
            standardized.append(
                {
                    "program_name": program.get("program_name", "N/A"),
                    "university": program.get("program_name", "N/A"),
                    "website": program.get("website") or "",
                    "accreditation_status": program.get(
                        "accreditation_status", "PCSAS Accredited"
                    ),
                    "student_outcomes_link": program.get("student_outcomes_link") or "",
                    "review_date": program.get("review_date"),
                    "notes": None,
                }
            )
        return standardized
    except Exception as exc:
        logger.warning(f"Error loading PCSAS programs: {exc}")
        return []


def load_all_accredited_programs() -> List[Dict[str, Any]]:
    """
    Load all accredited Clinical Psychology programs from the unified aggregator.
    """
    from .program_aggregator import get_aggregated_programs

    programs = get_aggregated_programs(use_cache=True)
    return [_to_standard_format(program) for program in programs]
