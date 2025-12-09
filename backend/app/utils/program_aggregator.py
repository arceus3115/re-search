"""
Program Aggregator: Merge APA and PCSAS accredited programs.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

from .apa_pdf_parser import parse_apa_pdf
from ..scrapers.pcsas_scraper import scrape_pcsas

logger = logging.getLogger(__name__)

# Data directory
_DATA_DIR = Path(__file__).parent.parent / "data"
_DATA_DIR.mkdir(exist_ok=True)

# Cache directory
_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "programs"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _similarity(a: str, b: str) -> float:
    """
    Calculate similarity between two strings (0.0 to 1.0).

    Args:
        a: First string
        b: Second string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _normalize_university_name(name: str) -> str:
    """
    Normalize university name for comparison.

    Args:
        name: University name

    Returns:
        Normalized name
    """
    if not name:
        return ""

    # Remove common suffixes and prefixes
    name = name.strip()
    name = name.replace("University of ", "")
    name = name.replace("The ", "")
    name = name.replace("Univ.", "University")
    name = name.replace("Univ ", "University ")
    name = name.replace("U.", "University")

    # Remove extra whitespace
    name = " ".join(name.split())

    return name.lower()


def _find_matching_program(
    university_name: str, programs: List[Dict[str, Any]], threshold: float = 0.85
) -> Optional[Dict[str, Any]]:
    """
    Find a matching program in the list by university name.

    Args:
        university_name: Name to search for
        programs: List of programs to search
        threshold: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        Matching program dict or None
    """
    normalized_search = _normalize_university_name(university_name)

    best_match = None
    best_score = 0.0

    for program in programs:
        program_name = (
            program.get("university_name", "")
            or program.get("university", "")
            or program.get("program_name", "")
        )
        normalized_program = _normalize_university_name(program_name)

        score = _similarity(normalized_search, normalized_program)

        if score > best_score and score >= threshold:
            best_score = score
            best_match = program

    return best_match


def aggregate_programs(
    apa_pdf_path: Optional[str] = None, use_cache: bool = True
) -> List[Dict[str, Any]]:
    """
    Aggregate APA and PCSAS accredited programs into a unified list.

    Args:
        apa_pdf_path: Path to APA PDF file (if None, uses default)
        use_cache: If True, use cached data if available

    Returns:
        List of unified program dictionaries with:
        - id: Unique identifier
        - university_name: Normalized university name
        - program_type: Program type (Clinical Ph.D., etc.)
        - accreditation_sources: List of sources (["APA"], ["PCSAS"], or ["APA", "PCSAS"])
        - address: Program address
        - website: Program website URL (from PCSAS if available)
        - accreditation_status: Current accreditation status
        - date_of_initial_accreditation: Initial accreditation date
        - next_site_visit_year: Next site visit year
        - student_outcomes_link: Link to student outcomes (PCSAS only)
    """
    # Check cache
    cache_file = _CACHE_DIR / "aggregated_programs.json"

    if use_cache and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                logger.info(f"Loaded {len(cached_data)} aggregated programs from cache")
                return cached_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file, will re-aggregate: {e}")

    # Load APA programs
    if apa_pdf_path is None:
        # Try to find the PDF in common locations
        pdf_paths = [
            Path(__file__).parent.parent.parent.parent
            / "2024_APA_Accredited_Doctoral_Programs-f64c182f.pdf",
            Path(__file__).parent.parent.parent
            / "2024_APA_Accredited_Doctoral_Programs-f64c182f.pdf",
        ]
        apa_pdf_path = None
        for path in pdf_paths:
            if path.exists():
                apa_pdf_path = str(path)
                break

        if not apa_pdf_path:
            raise FileNotFoundError(
                "APA PDF file not found. Please specify apa_pdf_path."
            )

    logger.info("Loading APA programs from PDF...")
    apa_programs = parse_apa_pdf(apa_pdf_path, use_cache=use_cache)
    logger.info(f"Loaded {len(apa_programs)} APA programs")

    # Load PCSAS programs
    logger.info("Loading PCSAS programs...")
    pcsas_programs = scrape_pcsas(use_cache=use_cache)
    logger.info(f"Loaded {len(pcsas_programs)} PCSAS programs")

    # Create unified programs list
    unified_programs = []
    processed_pcsas = set()  # Track which PCSAS programs we've matched

    # Start with APA programs
    for apa_program in apa_programs:
        university_name = apa_program.get("university", "")
        if not university_name:
            continue

        # Look for matching PCSAS program
        pcsas_match = _find_matching_program(university_name, pcsas_programs)

        # Determine accreditation sources
        accreditation_sources = ["APA"]
        website = None
        student_outcomes_link = None

        if pcsas_match:
            accreditation_sources.append("PCSAS")
            website = pcsas_match.get("website")
            student_outcomes_link = pcsas_match.get("student_outcomes_link")
            processed_pcsas.add(pcsas_match.get("program_name", ""))

        # Create unified program entry
        program_id = f"program-{len(unified_programs) + 1}"

        unified_program = {
            "id": program_id,
            "university_name": university_name,
            "program_type": apa_program.get("program_type", "Clinical Ph.D."),
            "accreditation_sources": accreditation_sources,
            "address": apa_program.get("address", ""),
            "website": website,
            "accreditation_status": apa_program.get(
                "accreditation_status", "Accredited"
            ),
            "date_of_initial_accreditation": apa_program.get(
                "date_of_initial_accreditation", ""
            ),
            "next_site_visit_year": apa_program.get("next_site_visit_year"),
            "student_outcomes_link": student_outcomes_link,
        }

        unified_programs.append(unified_program)

    # Add PCSAS-only programs (not found in APA list)
    for pcsas_program in pcsas_programs:
        program_name = pcsas_program.get("program_name", "")
        if program_name in processed_pcsas:
            continue  # Already processed

        # Check if it's already in unified list (by name similarity)
        already_added = False
        for unified in unified_programs:
            if (
                _similarity(
                    _normalize_university_name(unified["university_name"]),
                    _normalize_university_name(program_name),
                )
                >= 0.85
            ):
                already_added = True
                break

        if not already_added:
            program_id = f"program-{len(unified_programs) + 1}"

            unified_program = {
                "id": program_id,
                "university_name": program_name,
                "program_type": "Clinical Ph.D.",  # PCSAS is clinical-focused
                "accreditation_sources": ["PCSAS"],
                "address": "",  # PCSAS doesn't provide addresses
                "website": pcsas_program.get("website"),
                "accreditation_status": "Accredited",  # PCSAS programs are all accredited
                "date_of_initial_accreditation": "",
                "next_site_visit_year": None,
                "student_outcomes_link": pcsas_program.get("student_outcomes_link"),
            }

            unified_programs.append(unified_program)

    logger.info(f"Aggregated {len(unified_programs)} total programs")
    logger.info(
        f"  - APA only: {sum(1 for p in unified_programs if 'APA' in p['accreditation_sources'] and 'PCSAS' not in p['accreditation_sources'])}"
    )
    logger.info(
        f"  - PCSAS only: {sum(1 for p in unified_programs if 'PCSAS' in p['accreditation_sources'] and 'APA' not in p['accreditation_sources'])}"
    )
    logger.info(
        f"  - Both: {sum(1 for p in unified_programs if 'APA' in p['accreditation_sources'] and 'PCSAS' in p['accreditation_sources'])}"
    )

    # Save to cache
    if use_cache:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(unified_programs, f, indent=2, ensure_ascii=False)
            logger.info(f"Cached aggregated programs to {cache_file}")
        except IOError as e:
            logger.warning(f"Failed to write cache file: {e}")

    # Also save to data directory
    output_file = _DATA_DIR / "accredited_programs.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(unified_programs, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved aggregated programs to {output_file}")
    except IOError as e:
        logger.warning(f"Failed to write data file: {e}")

    return unified_programs


def get_aggregated_programs(use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Get aggregated programs, loading from cache or aggregating if needed.

    Args:
        use_cache: If True, use cached data if available

    Returns:
        List of unified program dictionaries
    """
    cache_file = _CACHE_DIR / "aggregated_programs.json"
    data_file = _DATA_DIR / "accredited_programs.json"

    # Try cache first
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Try data directory
    if data_file.exists():
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Need to aggregate
    return aggregate_programs(use_cache=use_cache)
