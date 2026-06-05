"""
Download and locate APA accredited doctoral programs PDF.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from .exceptions import DocumentParsingError

logger = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "programs"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_APA_PDF_CACHE = _CACHE_DIR / "apa_doctoral_latest.pdf"

_APA_PDF_URLS = [
    "https://irp.cdn-website.com/a14f9462/files/uploaded/2025+APA+Accredited+Doctoral+Programs-4a2b69d7.pdf",
    "https://irp.cdn-website.com/a14f9462/files/uploaded/2024_APA_Accredited_Doctoral_Programs-f64c182f.pdf",
]

_LOCAL_PDF_NAMES = [
    "2024_APA_Accredited_Doctoral_Programs-f64c182f.pdf",
    "2025_APA_Accredited_Doctoral_Programs.pdf",
]


def _repo_root() -> Path:
    return Path(__file__).parent.parent.parent.parent


def _find_local_pdf() -> Optional[Path]:
    search_dirs = [_repo_root(), _repo_root() / "backend"]
    for directory in search_dirs:
        for name in _LOCAL_PDF_NAMES:
            candidate = directory / name
            if candidate.exists():
                return candidate
    return None


def download_apa_pdf(force: bool = False) -> Path:
    """
    Download the latest APA doctoral programs PDF to the cache directory.

    Returns:
        Path to the cached PDF file.
    """
    if _APA_PDF_CACHE.exists() and not force:
        return _APA_PDF_CACHE

    last_error = None
    for url in _APA_PDF_URLS:
        try:
            logger.info(f"Downloading APA PDF from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            if len(response.content) < 1000:
                raise DocumentParsingError("Downloaded APA PDF appears too small")
            _APA_PDF_CACHE.write_bytes(response.content)
            logger.info(f"Saved APA PDF to {_APA_PDF_CACHE}")
            return _APA_PDF_CACHE
        except Exception as exc:
            last_error = exc
            logger.warning(f"Failed to download APA PDF from {url}: {exc}")

    raise DocumentParsingError(
        f"Could not download APA PDF from any known URL: {last_error}"
    )


def resolve_apa_pdf_path(apa_pdf_path: Optional[str] = None) -> str:
    """
    Resolve a usable APA PDF path: explicit path, local file, or downloaded cache.
    """
    if apa_pdf_path:
        path = Path(apa_pdf_path)
        if path.exists():
            return str(path)
        raise DocumentParsingError(f"APA PDF file not found: {apa_pdf_path}")

    local_pdf = _find_local_pdf()
    if local_pdf:
        return str(local_pdf)

    return str(download_apa_pdf())


def load_apa_programs_fallback() -> List[Dict[str, Any]]:
    """
    Load APA program records from committed JSON when PDF parsing is unavailable.
    """
    fallback_paths = [
        _repo_root() / "clinical_phd_programs.json",
        Path(__file__).parent.parent / "data" / "accredited_programs.json",
    ]

    for path in fallback_paths:
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, IOError) as exc:
            logger.warning(f"Could not read fallback APA data from {path}: {exc}")
            continue

        if not isinstance(data, list) or not data:
            continue

        if "university_name" in data[0]:
            programs = []
            for entry in data:
                if "APA" not in entry.get("accreditation_sources", []):
                    continue
                programs.append(
                    {
                        "university": entry.get("university_name", ""),
                        "program_type": entry.get("program_type", "Clinical Ph.D."),
                        "address": entry.get("address", ""),
                        "date_of_initial_accreditation": entry.get(
                            "date_of_initial_accreditation", ""
                        ),
                        "accreditation_status": entry.get(
                            "accreditation_status", "Accredited"
                        ),
                        "next_site_visit_year": entry.get("next_site_visit_year"),
                    }
                )
            if programs:
                logger.warning(
                    f"Using {len(programs)} APA programs from fallback file {path}"
                )
                return programs

        if "university" in data[0]:
            logger.warning(f"Using {len(data)} APA programs from fallback file {path}")
            return data

    return []
