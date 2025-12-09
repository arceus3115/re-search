"""
PDF Parser for APA Accredited Doctoral Programs.
Extracts program information from the APA PDF document.
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from .exceptions import DocumentParsingError

logger = logging.getLogger(__name__)

# Cache directory for parsed data
_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "programs"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# State names for detecting state headers
US_STATES = [
    "ALABAMA",
    "ALASKA",
    "ARIZONA",
    "ARKANSAS",
    "CALIFORNIA",
    "COLORADO",
    "CONNECTICUT",
    "DELAWARE",
    "FLORIDA",
    "GEORGIA",
    "HAWAII",
    "IDAHO",
    "ILLINOIS",
    "INDIANA",
    "IOWA",
    "KANSAS",
    "KENTUCKY",
    "LOUISIANA",
    "MAINE",
    "MARYLAND",
    "MASSACHUSETTS",
    "MICHIGAN",
    "MINNESOTA",
    "MISSISSIPPI",
    "MISSOURI",
    "MONTANA",
    "NEBRASKA",
    "NEVADA",
    "NEW HAMPSHIRE",
    "NEW JERSEY",
    "NEW MEXICO",
    "NEW YORK",
    "NORTH CAROLINA",
    "NORTH DAKOTA",
    "OHIO",
    "OKLAHOMA",
    "OREGON",
    "PENNSYLVANIA",
    "RHODE ISLAND",
    "SOUTH CAROLINA",
    "SOUTH DAKOTA",
    "TENNESSEE",
    "TEXAS",
    "UTAH",
    "VERMONT",
    "VIRGINIA",
    "WASHINGTON",
    "WEST VIRGINIA",
    "WISCONSIN",
    "WYOMING",
    "PUERTO RICO",
    "DISTRICT OF COLUMBIA",
]


def _extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file using PyPDF2.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as string

    Raises:
        DocumentParsingError: If PDF reading fails
    """
    if PyPDF2 is None:
        raise DocumentParsingError(
            "PyPDF2 is not installed. Please install it: pip install PyPDF2"
        )

    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_parts = []

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    text_parts.append(text)
                    logger.debug(
                        f"Extracted {len(text)} characters from page {page_num + 1}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Error extracting text from page {page_num + 1}: {e}"
                    )
                    continue

            full_text = "\n".join(text_parts)
            logger.info(
                f"Extracted {len(full_text)} total characters from {len(pdf_reader.pages)} pages"
            )
            return full_text

    except FileNotFoundError:
        raise DocumentParsingError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        logger.error(f"Error reading PDF file {pdf_path}: {e}", exc_info=True)
        raise DocumentParsingError(f"Failed to read PDF file: {e}") from e


def _parse_date(date_str: str) -> Optional[str]:
    """
    Parse date string and return in standardized format.

    Args:
        date_str: Date string (e.g., "March 20, 1985")

    Returns:
        Standardized date string (e.g., "March 20, 1985") or None if invalid
    """
    if not date_str or date_str.strip() == "":
        return None

    # Clean up the date string
    date_str = date_str.strip()

    # Try to parse common date formats
    date_formats = [
        "%B %d, %Y",  # March 20, 1985
        "%b %d, %Y",  # Mar 20, 1985
        "%B %d %Y",  # March 20 1985
        "%b %d %Y",  # Mar 20 1985
        "%m/%d/%Y",  # 03/20/1985
        "%Y-%m-%d",  # 1985-03-20
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Return in standard format: "Month Day, Year"
            return dt.strftime("%B %d, %Y")
        except ValueError:
            continue

    # If no format matches, return as-is (might be already in correct format)
    return date_str


def _parse_year(year_str: str) -> Optional[int]:
    """
    Parse year string and return as integer.

    Args:
        year_str: Year string (e.g., "2023")

    Returns:
        Year as integer or None if invalid
    """
    if not year_str:
        return None

    # Extract digits only
    digits = re.sub(r"\D", "", year_str.strip())

    if digits:
        try:
            year = int(digits)
            # Sanity check: year should be between 1900 and 2100
            if 1900 <= year <= 2100:
                return year
        except ValueError:
            pass

    return None


def _is_state_header(line: str) -> bool:
    """
    Check if a line is a state header.

    Args:
        line: Line of text to check

    Returns:
        True if line appears to be a state header
    """
    line_upper = line.strip().upper()

    # Check if line is just a state name
    if line_upper in US_STATES:
        return True

    # Check if line starts with a state name followed by common separators
    for state in US_STATES:
        if line_upper.startswith(state):
            # Check if it's just the state name or state name with minimal text
            remaining = line_upper[len(state) :].strip()
            if not remaining or remaining in ["", "-", "–", "—"]:
                return True

    return False


def _normalize_university_name(name: str) -> str:
    """
    Normalize university name by cleaning up common issues.

    Args:
        name: Raw university name

    Returns:
        Normalized university name
    """
    if not name:
        return ""

    # Remove extra whitespace
    name = " ".join(name.split())

    # Remove common prefixes/suffixes that might be artifacts
    name = re.sub(
        r"^[A-Z]+\s*$", "", name
    )  # Remove lines that are just uppercase letters

    # Fix common abbreviations
    name = name.replace("Univ.", "University")
    name = name.replace("Univ ", "University ")
    name = name.replace("U.", "University")

    return name.strip()


def _parse_program_entry(
    lines: List[str], start_idx: int
) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Parse a single program entry from lines of text.

    Pattern:
    - University name
    - (Program Type)
    - Address lines (1-3 lines)
    - Date of initial accreditation
    - Accreditation status
    - Next site visit scheduled [year]

    Args:
        lines: List of all text lines
        start_idx: Starting index in lines list

    Returns:
        Tuple of (program dictionary or None, end_index)
    """
    if start_idx >= len(lines):
        return None, start_idx

    idx = start_idx
    university = None
    program_type = "Clinical Ph.D."  # Default
    address_parts = []
    date_of_initial_accreditation = None
    accreditation_status = "Accredited"
    next_site_visit_year = None

    # Skip empty lines and state headers
    while idx < len(lines) and (not lines[idx].strip() or _is_state_header(lines[idx])):
        idx += 1

    if idx >= len(lines):
        return None, idx

    # University name is the first non-empty, non-state line
    university_line = lines[idx].strip()
    if not university_line or len(university_line) < 3:
        return None, idx

    # Check if it's actually a university name (not a header or other text)
    if (
        university_line.upper() in US_STATES
        or "ACCREDITED" in university_line.upper()
        or "PROGRAMS" in university_line.upper()
        or "TRAINING" in university_line.upper()
        or ("PSYCHOLOGY" in university_line.upper() and len(university_line) < 20)
        or "Next site visit" in university_line
        or "site visit scheduled" in university_line.lower()
    ):
        return None, idx

    university = _normalize_university_name(university_line)
    idx += 1

    # Skip empty lines
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    if idx >= len(lines):
        return None, idx

    # Program type is in parentheses on next line
    program_line = lines[idx].strip()
    if program_line.startswith("(") and program_line.endswith(")"):
        program_type_str = program_line[1:-1].strip()
        if "Clinical" in program_type_str:
            program_type = "Clinical Ph.D."
        elif "Counseling" in program_type_str:
            program_type = "Counseling Ph.D."
        elif "School" in program_type_str:
            program_type = "School Ph.D."
        elif "Combined" in program_type_str:
            program_type = program_type_str.replace("Combined, ", "").replace(
                "Combined ", ""
            )
        else:
            program_type = program_type_str
        idx += 1

    # Skip empty lines
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    # Address lines (1-3 lines, until we hit a date)
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue

        # Check if this is a date (indicates end of address)
        date_match = re.search(r"([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})", line)
        if date_match:
            date_of_initial_accreditation = _parse_date(date_match.group(1))
            idx += 1
            break

        # Check if this looks like an address line
        if (
            re.search(r"\d+", line)
            or re.search(
                r"(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Court|Ct|Hall|Building|Blvd|Box|P\.O\.)",
                line,
                re.I,
            )
            or re.search(r"[A-Z]{2}\s+\d{5}", line)  # State + ZIP
            or re.search(r",\s*[A-Z]{2}\s+", line)
        ):  # City, State pattern
            address_parts.append(line)
            idx += 1
        else:
            # Might be a date without month name, or something else
            # Try to detect if it's still address or if we've moved on
            if len(address_parts) > 0 and len(line) < 50:
                # Could still be address, continue
                address_parts.append(line)
                idx += 1
            else:
                # Probably moved past address
                break

    # Combine address parts
    address = ", ".join(address_parts) if address_parts else ""

    # Skip empty lines
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    # Accreditation status
    if idx < len(lines):
        status_line = lines[idx].strip()
        if "Accredited" in status_line:
            if "inactive" in status_line.lower() or "– inactive" in status_line:
                accreditation_status = "Accredited – Inactive"
            elif "contingency" in status_line.lower():
                accreditation_status = "Accredited, on contingency"
            elif "probation" in status_line.lower():
                accreditation_status = "Accredited, on probation"
            else:
                accreditation_status = "Accredited"
        idx += 1

    # Skip empty lines
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    # Next site visit year
    if idx < len(lines):
        visit_line = lines[idx].strip()
        if (
            "Next site visit" in visit_line
            or "site visit scheduled" in visit_line.lower()
        ):
            year_match = re.search(r"20\d{2}", visit_line)
            if year_match:
                next_site_visit_year = _parse_year(year_match.group(0))

    # Validate we have at least a university name
    if university and len(university) > 3:
        # Clean up address
        address = address.strip()
        address = re.sub(r"\s+", " ", address)  # Normalize whitespace
        address = re.sub(r",\s*,", ",", address)  # Remove duplicate commas

        return {
            "university": university,
            "program_type": program_type,
            "address": address,
            "date_of_initial_accreditation": date_of_initial_accreditation or "",
            "accreditation_status": accreditation_status,
            "next_site_visit_year": next_site_visit_year,
        }, idx

    return None, start_idx


def parse_apa_pdf(pdf_path: str, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Parse APA accredited programs PDF and extract program information.

    Args:
        pdf_path: Path to the PDF file
        use_cache: If True, use cached parsed data if available

    Returns:
        List of program dictionaries with university, program_type, address,
        date_of_initial_accreditation, accreditation_status, next_site_visit_year

    Raises:
        DocumentParsingError: If PDF parsing fails
    """
    pdf_path_obj = Path(pdf_path)

    if not pdf_path_obj.exists():
        raise DocumentParsingError(f"PDF file not found: {pdf_path}")

    # Check cache
    cache_file = _CACHE_DIR / f"apa_programs_{pdf_path_obj.stem}.json"

    if use_cache and cache_file.exists():
        try:
            # Check if cache is newer than PDF
            if cache_file.stat().st_mtime > pdf_path_obj.stat().st_mtime:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    logger.info(f"Loaded {len(cached_data)} programs from cache")
                    return cached_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file, will re-parse: {e}")

    # Extract text from PDF
    logger.info(f"Parsing PDF: {pdf_path}")
    text = _extract_text_from_pdf(pdf_path)

    # Split into lines
    lines = text.split("\n")
    logger.info(f"Split into {len(lines)} lines")

    # Find the start of actual program listings (first state header)
    start_idx = 0
    for i, line in enumerate(lines):
        if _is_state_header(line):
            start_idx = i + 1  # Start after the state header
            logger.info(f"Found first state header at line {i}: {line.strip()}")
            break

    # Parse programs starting from first state
    programs = []
    i = start_idx

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Skip state headers (they mark new sections but aren't program entries)
        if _is_state_header(line):
            i += 1
            continue

        # Look for a university name pattern
        # University names typically:
        # - Don't start with numbers
        # - Don't start with parentheses
        # - Are not too long (usually < 80 chars)
        # - Don't contain certain keywords that indicate header text or addresses
        # - Don't look like addresses (P.O. Box, street patterns, etc.)
        is_likely_address = (
            re.match(r"^\d+", line)  # Starts with number
            or line.startswith("P.O.")
            or line.startswith("PO ")  # PO Box
            or re.search(r"\d{5}(-\d{4})?$", line)  # Ends with ZIP code
            or re.search(
                r"(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Court|Ct|Hall|Building|Blvd|Box|Room|Rm)\s*$",
                line,
                re.I,
            )  # Ends with street type
            or re.search(r",\s*[A-Z]{2}\s+\d{5}", line)  # City, State ZIP pattern
            or "College of" in line
            and len(line) < 30  # Short "College of X" is likely part of address
        )

        if (
            not is_likely_address
            and not line.startswith("(")
            and len(line) < 80
            and len(line) > 5
            and not ("ACCREDITED" in line.upper() and "PROGRAM" in line.upper())
            and not ("TRAINING" in line.upper() and "PSYCHOLOGY" in line.upper())
            and "STANDARDS" not in line.upper()
            and "COA" not in line.upper()
            and line.upper() not in US_STATES
        ):
            # This might be a university name, try to parse an entry
            program, end_idx = _parse_program_entry(lines, i)

            if program:
                university = program.get("university", "")
                # Additional validation: must have reasonable university name and address
                if (
                    university
                    and len(university) > 5
                    and len(university) < 100
                    and program.get("address")
                    and len(program.get("address", "")) > 10
                ):
                    programs.append(program)
                    logger.debug(f"Parsed program: {program['university']}")

                    # Advance to where the parser ended
                    i = end_idx
                    continue

        i += 1

    logger.info(f"Parsed {len(programs)} programs from PDF")

    # Save to cache
    if use_cache:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(programs, f, indent=2, ensure_ascii=False)
            logger.info(f"Cached parsed data to {cache_file}")
        except IOError as e:
            logger.warning(f"Failed to write cache file: {e}")

    return programs


def parse_apa_pdf_to_json(
    pdf_path: str, output_path: str, use_cache: bool = True
) -> str:
    """
    Parse APA PDF and save to JSON file.

    Args:
        pdf_path: Path to the PDF file
        output_path: Path to output JSON file
        use_cache: If True, use cached parsed data if available

    Returns:
        Path to the output JSON file

    Raises:
        DocumentParsingError: If PDF parsing fails
    """
    programs = parse_apa_pdf(pdf_path, use_cache=use_cache)

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path_obj, "w", encoding="utf-8") as f:
        json.dump(programs, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(programs)} programs to {output_path}")
    return str(output_path_obj)
