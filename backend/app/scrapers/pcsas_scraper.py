import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from ..utils.exceptions import ScrapingError
from ..utils.url_utils import normalize_url

logger = logging.getLogger(__name__)

PCSAS_URL = "https://pcsas.org/pcsas-accredited-programs/"
MIN_EXPECTED_PROGRAMS = 40

_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)

_HEADER_ALIASES = {
    "program": ("program/university", "program", "university"),
    "outcomes": ("program data", "student outcomes", "outcomes", "program data link"),
    "review_date": ("review date", "accreditation review"),
    "status": ("decision", "status", "accreditation status"),
}


def _get_cache_file() -> Path:
    cache_key = hashlib.md5("pcsas_programs".encode()).hexdigest()
    return _CACHE_DIR / f"pcsas_{cache_key}.json"


def _load_cache(
    cache_file: Path, cache_duration_hours: int
) -> Optional[List[Dict[str, Any]]]:
    if not cache_file.exists():
        return None

    cache_age = time.time() - cache_file.stat().st_mtime
    if cache_age >= (cache_duration_hours * 3600):
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as handle:
            cached_data = json.load(handle)
            if (
                isinstance(cached_data, list)
                and len(cached_data) >= MIN_EXPECTED_PROGRAMS
            ):
                return cached_data
    except (json.JSONDecodeError, IOError):
        pass

    return None


def _map_columns(header_cells: List[Any]) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    for idx, cell in enumerate(header_cells):
        text = cell.get_text(strip=True).lower()
        for key, aliases in _HEADER_ALIASES.items():
            if key in mapping:
                continue
            if any(alias in text for alias in aliases):
                mapping[key] = idx
    return mapping


def _parse_pcsas_table(table) -> List[Dict[str, Any]]:
    rows = table.find_all("tr")
    if len(rows) < 2:
        raise ScrapingError("PCSAS table has no data rows")

    header_cells = rows[0].find_all(["th", "td"])
    column_map = _map_columns(header_cells)

    program_idx = column_map.get("program", 0)
    outcomes_idx = column_map.get("outcomes", 3)
    review_idx = column_map.get("review_date")
    status_idx = column_map.get("status")

    programs_data: List[Dict[str, Any]] = []
    for row in rows[1:]:
        cols = row.find_all("td")
        required_indices = [program_idx, outcomes_idx]
        if max(required_indices) >= len(cols):
            continue

        program_cell = cols[program_idx]
        program_link = program_cell.find("a")
        program_name = (
            program_link.get_text(strip=True)
            if program_link
            else program_cell.get_text(strip=True)
        )
        program_website = normalize_url(
            program_link.get("href") if program_link else None
        )

        outcomes_cell = cols[outcomes_idx]
        outcomes_link = outcomes_cell.find("a")
        student_outcomes_link = normalize_url(
            outcomes_link.get("href") if outcomes_link else None
        )

        entry: Dict[str, Any] = {
            "program_name": program_name or None,
            "website": program_website,
            "student_outcomes_link": student_outcomes_link,
        }

        if review_idx is not None and review_idx < len(cols):
            entry["review_date"] = cols[review_idx].get_text(strip=True) or None
        if status_idx is not None and status_idx < len(cols):
            entry["accreditation_status"] = (
                cols[status_idx].get_text(strip=True) or None
            )

        if entry["program_name"]:
            programs_data.append(entry)

    if len(programs_data) < MIN_EXPECTED_PROGRAMS:
        raise ScrapingError(
            f"PCSAS scrape returned only {len(programs_data)} programs; expected at least {MIN_EXPECTED_PROGRAMS}"
        )

    return programs_data


def scrape_pcsas(
    use_cache: bool = True, cache_duration_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Scrape the PCSAS accredited programs page to extract program information.
    """
    cache_file = _get_cache_file()

    if use_cache:
        cached = _load_cache(cache_file, cache_duration_hours)
        if cached is not None:
            return cached

    try:
        response = requests.get(PCSAS_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        if use_cache and cache_file.exists():
            logger.warning(f"PCSAS fetch failed, using stale cache: {exc}")
            with open(cache_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
        raise ScrapingError(f"Failed to fetch PCSAS page: {exc}") from exc

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")
    if not table:
        if use_cache and cache_file.exists():
            logger.warning("PCSAS table missing, using stale cache")
            with open(cache_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
        raise ScrapingError("PCSAS accredited programs table not found on page")

    programs_data = _parse_pcsas_table(table)

    if use_cache:
        try:
            with open(cache_file, "w", encoding="utf-8") as handle:
                json.dump(programs_data, handle, indent=2, ensure_ascii=False)
        except IOError as exc:
            logger.warning(f"Failed to write PCSAS cache: {exc}")

    return programs_data
