"""
Program loader for accredited Clinical Psychology programs.
Combines PCSAS and APA accredited programs into a unified format.
"""

import json
from typing import List, Dict, Any
from pathlib import Path

# Get the directory where this file is located
_UTILS_DIR = Path(__file__).parent
_DATA_DIR = _UTILS_DIR.parent / "data"
_APA_PROGRAMS_FILE = _DATA_DIR / "apa_programs.json"


def load_apa_programs() -> List[Dict[str, Any]]:
    """
    Load APA accredited programs from JSON file.

    Returns:
        List of program dictionaries with fields:
        - program_name: str
        - university: str
        - website: str
        - accreditation_status: str
        - notes: Optional[str]
    """
    if not _APA_PROGRAMS_FILE.exists():
        return []

    try:
        with open(_APA_PROGRAMS_FILE, "r", encoding="utf-8") as f:
            programs = json.load(f)
        return programs if isinstance(programs, list) else []
    except (json.JSONDecodeError, IOError) as e:
        # Log error but don't crash - just return empty list
        import logging

        logging.getLogger(__name__).warning(f"Error loading APA programs: {e}")
        return []


def load_pcsas_programs() -> List[Dict[str, Any]]:
    """
    Load PCSAS accredited programs using the scraper.
    Converts to standardized format.

    Returns:
        List of program dictionaries in standardized format.
    """
    from ..scrapers import pcsas_scraper

    try:
        raw_programs = pcsas_scraper.scrape_pcsas()
        # Convert to standardized format
        standardized = []
        for program in raw_programs:
            standardized.append(
                {
                    "program_name": program.get("program_name", "N/A"),
                    "university": program.get(
                        "program_name", "N/A"
                    ),  # PCSAS format uses program_name
                    "website": program.get("website", ""),
                    "accreditation_status": "PCSAS Accredited",
                    "student_outcomes_link": program.get("student_outcomes_link", ""),
                    "notes": None,
                }
            )
        return standardized
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(f"Error loading PCSAS programs: {e}")
        return []


def load_all_accredited_programs() -> List[Dict[str, Any]]:
    """
    Load all accredited Clinical Psychology programs (PCSAS + APA).

    Returns:
        Combined list of all accredited programs in standardized format.
    """
    pcsas_programs = load_pcsas_programs()
    apa_programs = load_apa_programs()

    # Combine and deduplicate by website (if same website, prefer PCSAS)
    all_programs = {}

    # Add PCSAS programs first
    for program in pcsas_programs:
        website = program.get("website", "")
        if website and website != "N/A":
            all_programs[website] = program

    # Add APA programs (won't overwrite PCSAS if same website)
    for program in apa_programs:
        website = program.get("website", "")
        if website:
            if website not in all_programs:
                all_programs[website] = program
            else:
                # Merge if both exist - mark as dual accredited
                existing = all_programs[website]
                existing["accreditation_status"] = (
                    f"{existing.get('accreditation_status', '')}, APA Accredited"
                )

    return list(all_programs.values())
