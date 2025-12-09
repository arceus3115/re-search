import requests
from bs4 import BeautifulSoup
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Cache directory for PCSAS data
_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)


def _get_cache_file() -> Path:
    """Get cache file path for PCSAS data."""
    cache_key = hashlib.md5("pcsas_programs".encode()).hexdigest()
    return _CACHE_DIR / f"pcsas_{cache_key}.json"


def scrape_pcsas(
    use_cache: bool = True, cache_duration_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Scrapes the PCSAS accredited programs page to extract program information.

    Args:
        use_cache: If True, use cached data if available and recent
        cache_duration_hours: Hours before cache expires

    Returns:
        List of program dictionaries with program_name, website, student_outcomes_link
    """
    cache_file = _get_cache_file()

    # Check cache first
    if use_cache and cache_file.exists():
        import time

        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < (cache_duration_hours * 3600):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    return cached_data
            except (json.JSONDecodeError, IOError):
                pass  # Cache invalid, continue to scrape

    # Scrape fresh data
    URL = "https://pcsas.org/pcsas-accredited-programs/"
    page = requests.get(URL, timeout=30)
    page.raise_for_status()
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")[1:]  # Skip header row

    programs_data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:  # Ensure there are enough columns
            continue

        # Program/University column
        uni_cell = cols[0]
        uni_link_element = uni_cell.find("a")
        program_name = uni_link_element.text.strip() if uni_link_element else "N/A"
        program_website = uni_link_element["href"] if uni_link_element else "N/A"

        # Student Outcomes Link column
        outcomes_cell = cols[3]
        outcomes_link_element = outcomes_cell.find("a")
        student_outcomes_link = (
            outcomes_link_element["href"] if outcomes_link_element else "N/A"
        )

        programs_data.append(
            {
                "program_name": program_name,
                "website": program_website,
                "student_outcomes_link": student_outcomes_link,
            }
        )

    # Cache the results
    if use_cache:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(programs_data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass  # Cache write failed, but we still have the data

    return programs_data
