"""
Institution ID discovery helper for finding OpenAlex institution IDs.
Used by the paper-based PI discovery system.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

from ..utils import openalex_client

logger = logging.getLogger(__name__)


def _find_institution_id(university_name: str, website: str) -> Optional[str]:
    """
    Find OpenAlex institution ID from university name or website.
    """
    # Try searching by name first
    from urllib.parse import urlencode

    query_params = urlencode({"search": university_name})
    search_url = f"{openalex_client.OPENALEX_BASE}/institutions?{query_params}"

    try:
        data = openalex_client.cache_request(search_url)
        results = data.get("results", [])

        if results:
            # Try to match by name similarity or website
            for inst in results:
                inst_name = inst.get("display_name", "").lower()
                inst_url = inst.get("homepage_url", "").lower()

                # Check if name matches or website domain matches
                if (
                    university_name.lower() in inst_name
                    or inst_name in university_name.lower()
                ):
                    return inst.get("id")

                # Check website domain match
                if website:
                    try:
                        website_domain = urlparse(website).netloc.lower()
                        if inst_url and website_domain in inst_url:
                            return inst.get("id")
                    except Exception:
                        pass

            # If no exact match, return first result
            return results[0].get("id")

    except Exception as e:
        logger.debug(f"Error searching for institution {university_name}: {e}")

    return None
