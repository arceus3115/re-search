"""
URL normalization helpers for scraped accreditation data.
"""

from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse


def unwrap_safelinks(url: str) -> str:
    """Unwrap Microsoft Outlook Safe Links URLs to the original target."""
    if not url:
        return url

    parsed = urlparse(url)
    if "safelinks.protection.outlook.com" not in parsed.netloc.lower():
        return url

    query = parse_qs(parsed.query)
    wrapped = query.get("url", [None])[0]
    if wrapped:
        return unquote(wrapped)
    return url


def normalize_url(url: Optional[str]) -> Optional[str]:
    """
    Normalize scraped URLs: unwrap Safe Links, trim whitespace, reject placeholders.
    """
    if url is None:
        return None

    cleaned = url.strip()
    if not cleaned or cleaned.upper() == "N/A":
        return None

    cleaned = unwrap_safelinks(cleaned).strip()
    if not cleaned.startswith(("http://", "https://")):
        return None

    return cleaned
