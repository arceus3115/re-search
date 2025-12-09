"""
Model conversion utilities to reduce code duplication.
"""

from typing import Dict, Any, Union
import logging

from ..models.author import Author
from ..models.paper import Paper
from ..utils.openalex_client import author_from_dict, paper_from_dict

logger = logging.getLogger(__name__)


def convert_author_to_response_dict(
    author: Union[Author, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Convert Author model or dict to standardized response dictionary.

    Args:
        author: Author model instance or dict from OpenAlex

    Returns:
        Dictionary with standardized author fields
    """
    if isinstance(author, dict):
        # Handle dict input
        last_inst = author.get("last_known_institution")
        institution_name = last_inst.get("display_name") if last_inst else None

        # Extract all affiliated institutions from affiliations array (limit to top 3)
        affiliated_institutions = []
        affiliations = author.get("affiliations", [])
        seen_institutions = set()

        # Add last_known_institution first if it exists (most relevant)
        if institution_name and institution_name not in seen_institutions:
            affiliated_institutions.append(institution_name)
            seen_institutions.add(institution_name.lower())

        # Add unique institutions from affiliations (up to 3 total)
        for aff in affiliations:
            if len(affiliated_institutions) >= 3:
                break
            inst = aff.get("institution", {})
            if inst:
                inst_name = inst.get("display_name")
                if inst_name and inst_name.lower() not in seen_institutions:
                    affiliated_institutions.append(inst_name)
                    seen_institutions.add(inst_name.lower())

        # Limit to top 3 institutions
        affiliated_institutions = affiliated_institutions[:3]

        summary_stats = author.get("summary_stats", {})
        h_index = summary_stats.get("h_index", 0) if summary_stats else 0

        concepts = author.get("x_concepts", [])
        subjects = [
            c.get("display_name", "") for c in concepts[:5] if c.get("display_name")
        ]

        return {
            "name": author.get("display_name", "Unknown"),
            "openalex_id": author.get("id", ""),
            "orcid": author.get("orcid"),
            "institution": institution_name,  # Keep for backward compatibility
            "affiliated_institutions": affiliated_institutions,  # All institutions
            "h_index": h_index,
            "subjects": subjects,
        }
    else:
        # Handle Author model
        return {
            "name": author.display_name or "Unknown",
            "openalex_id": author.id,
            "orcid": author.orcid,
            "institution": author.institution_name,
            "h_index": author.h_index,
            "subjects": author.subjects[:5],
        }


def convert_author_dict_to_model(author_dict: Dict[str, Any]) -> Author:
    """
    Convert author dict to Author model, raising exception on failure.

    Args:
        author_dict: Dictionary from OpenAlex API

    Returns:
        Author model instance

    Raises:
        ValueError: If model creation fails
    """
    # Factory function now always returns Author or raises ValueError
    return author_from_dict(author_dict)


def convert_paper_to_response_dict(
    paper: Union[Paper, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Convert Paper model or dict to standardized response dictionary.

    Args:
        paper: Paper model instance or dict from OpenAlex

    Returns:
        Dictionary with standardized paper fields
    """
    if isinstance(paper, dict):
        # Handle dict input
        title = paper.get("title", "")
        doi = (
            paper.get("doi", "")
            .replace("https://doi.org/", "")
            .replace("http://dx.doi.org/", "")
            if paper.get("doi")
            else None
        )

        primary_location = paper.get("primary_location", {})
        url = primary_location.get("landing_page_url") or primary_location.get(
            "pdf_url"
        )
        if not url:
            url = paper.get("doi", "")
            if url and not url.startswith("http"):
                url = f"https://doi.org/{url}"

        authorships = paper.get("authorships", [])
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in authorships
            if a.get("author", {}).get("display_name")
        ]

        publication_year = paper.get("publication_year")

        venue = primary_location.get("source", {}).get("display_name", "")
        if not venue:
            venue = (
                primary_location.get("source", {})
                .get("host_venue", {})
                .get("display_name", "")
            )

        abstract = paper.get("abstract", "")
        citation_count = paper.get("cited_by_count", 0)
        pub_type = (
            paper.get("type", "").replace("_", " ").title()
            if paper.get("type")
            else None
        )
        openalex_id = paper.get("id", "")

        return {
            "title": title,
            "doi": doi,
            "url": url,
            "authors": authors,
            "publication_year": publication_year,
            "venue": venue,
            "abstract": abstract,
            "citation_count": citation_count,
            "publication_type": pub_type,
            "openalex_id": openalex_id,
        }
    else:
        # Handle Paper model
        return {
            "title": paper.title or paper.display_name or "",
            "doi": paper.doi.replace("https://doi.org/", "").replace(
                "http://dx.doi.org/", ""
            )
            if paper.doi
            else None,
            "url": paper.url,
            "authors": paper.author_names,
            "publication_year": paper.publication_year,
            "venue": paper.venue,
            "abstract": paper.abstract or "",
            "citation_count": paper.cited_by_count or 0,
            "publication_type": paper.type.replace("_", " ").title()
            if paper.type
            else None,
            "openalex_id": paper.id,
        }


def convert_paper_dict_to_model(paper_dict: Dict[str, Any]) -> Paper:
    """
    Convert paper dict to Paper model, raising exception on failure.

    Args:
        paper_dict: Dictionary from OpenAlex API

    Returns:
        Paper model instance

    Raises:
        ValueError: If model creation fails
    """
    # Ensure title or display_name exists before calling factory
    if not paper_dict.get("title") and paper_dict.get("display_name"):
        paper_dict["title"] = paper_dict["display_name"]
    elif not paper_dict.get("display_name") and paper_dict.get("title"):
        paper_dict["display_name"] = paper_dict["title"]

    # Factory function now always returns Paper or raises ValueError
    return paper_from_dict(paper_dict)
