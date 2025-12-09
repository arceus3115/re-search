"""
Research Interest Searcher: Search OpenAlex by research interests first, then match to programs.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from .openalex_client import (
    search_papers,
    get_concept_ids_from_topics,
    get_field_concept_ids,
)
from .program_aggregator import _normalize_university_name, _find_matching_program

logger = logging.getLogger(__name__)

# Cache directory
_CACHE_DIR = Path(__file__).parent.parent.parent / ".cache" / "programs"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def search_papers_by_interests(
    research_interests: List[str],
    program_type: str = "Clin Psych PhD",
    from_year: int = 2010,
    per_interest: int = 100,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """
    Search OpenAlex for papers matching research interests.

    For clinical psychology programs, requires papers to have Psychology concept tag.

    Args:
        research_interests: List of research interest keywords
        program_type: Type of program (default: "Clin Psych PhD")
        from_year: Minimum publication year
        per_interest: Maximum papers to fetch per interest
        use_cache: If True, use cached data if available

    Returns:
        List of paper dictionaries with their associated institutions
    """
    if not research_interests:
        logger.warning("No research interests provided")
        return []

    # Check cache
    # Create stable cache key from research interests
    interests_str = (
        "_".join(sorted(research_interests)).replace(" ", "_").replace("/", "_")[:100]
    )
    cache_key = f"papers_by_interests_{interests_str}_{program_type.replace(' ', '_')}_{from_year}"
    # Sanitize cache key for filesystem
    cache_key = re.sub(r"[^\w\-_]", "_", cache_key)
    cache_file = _CACHE_DIR / f"{cache_key}.json"

    if use_cache and cache_file.exists():
        try:
            import time

            cache_age = (time.time() - cache_file.stat().st_mtime) / (24 * 3600)  # days
            if cache_age < 30:  # 30 day cache
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    logger.info(
                        f"Loaded {len(cached_data)} papers from cache for interests: {research_interests}"
                    )
                    return cached_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file, will fetch fresh data: {e}")

    # Get Psychology concept ID if clinical psychology program
    psychology_concept_id = None
    if "psych" in program_type.lower() or "clinical" in program_type.lower():
        field_concepts = get_field_concept_ids()
        psychology_concept_id = field_concepts.get("Psychology")
        if not psychology_concept_id:
            # Try to get it directly
            concept_map = get_concept_ids_from_topics(["Psychology"])
            psychology_concept_id = concept_map.get("Psychology")

        if psychology_concept_id:
            logger.info(f"Using Psychology concept filter: {psychology_concept_id}")
        else:
            logger.warning(
                "Could not find Psychology concept ID, proceeding without filter"
            )

    all_papers = []
    seen_paper_ids = set()

    # Search for each research interest
    for interest in research_interests:
        logger.info(f"Searching for papers matching interest: {interest}")

        # Build topic filter
        topic_ids = []
        if psychology_concept_id:
            topic_ids = [psychology_concept_id]

        try:
            # Search papers with this interest
            papers = search_papers(
                search_term=interest,
                from_year=from_year,
                topic_ids=topic_ids,
                page=1,
                per_page=per_interest,
                sort_by="cited_by_count:desc",
            )

            logger.info(f"Found {len(papers)} papers for interest '{interest}'")

            # Add unique papers
            for paper in papers:
                paper_id = paper.get("id", "")
                if paper_id and paper_id not in seen_paper_ids:
                    all_papers.append(paper)
                    seen_paper_ids.add(paper_id)

        except Exception as e:
            logger.error(
                f"Error searching papers for interest '{interest}': {e}", exc_info=True
            )
            continue

    logger.info(f"Total unique papers found: {len(all_papers)}")

    # Cache results
    if use_cache and all_papers:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(all_papers, f, indent=2, ensure_ascii=False)
            logger.info(f"Cached {len(all_papers)} papers")
        except IOError as e:
            logger.warning(f"Failed to write cache file: {e}")

    return all_papers


def extract_universities_from_papers(
    papers: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Extract universities from papers and group papers by institution.

    Args:
        papers: List of paper dictionaries from OpenAlex

    Returns:
        Dictionary mapping normalized institution name to:
        {
            "papers": [...],
            "paper_count": N,
            "top_papers": [...],  # Top 10 by citations
            "institution_names": [...],  # All variant names found
            "openalex_institution_ids": [...]  # OpenAlex IDs
        }
    """
    university_data = defaultdict(
        lambda: {
            "papers": [],
            "institution_names": set(),
            "openalex_institution_ids": set(),
        }
    )

    for paper in papers:
        authorships = paper.get("authorships", [])

        # Extract institutions from all authorships
        paper_institutions = set()
        for authorship in authorships:
            institutions = authorship.get("institutions", [])
            for inst in institutions:
                if not inst:
                    continue

                inst_id = inst.get("id", "")
                inst_name = inst.get("display_name", "")

                if inst_name:
                    # Normalize institution name
                    normalized = _normalize_university_name(inst_name)

                    if normalized:
                        paper_institutions.add(normalized)
                        university_data[normalized]["institution_names"].add(inst_name)
                        if inst_id:
                            university_data[normalized]["openalex_institution_ids"].add(
                                inst_id
                            )

        # Add paper to all its institutions
        for normalized_name in paper_institutions:
            university_data[normalized_name]["papers"].append(paper)

    # Convert sets to lists and add counts
    result = {}
    for normalized_name, data in university_data.items():
        papers_list = data["papers"]
        # Sort papers by citation count
        papers_list.sort(key=lambda p: p.get("cited_by_count", 0), reverse=True)

        result[normalized_name] = {
            "papers": papers_list,
            "paper_count": len(papers_list),
            "top_papers": papers_list[:10],  # Top 10 by citations
            "institution_names": list(data["institution_names"]),
            "openalex_institution_ids": list(data["openalex_institution_ids"]),
        }

    logger.info(
        f"Extracted {len(result)} unique institutions from {len(papers)} papers"
    )

    return result


def match_universities_to_programs(
    university_data: Dict[str, Dict[str, Any]],
    accredited_programs: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Match universities from papers to accredited programs.

    Args:
        university_data: Dictionary from extract_universities_from_papers()
        accredited_programs: List of accredited program dictionaries

    Returns:
        Dictionary mapping program_id to:
        {
            "program": {...},  # Program dict
            "papers": [...],  # All papers for this program
            "paper_count": N,
            "top_papers": [...],  # Top papers
            "researchers": [...],  # Extracted researchers
            "institution_names": [...],  # Matched institution names
        }
    """
    matched_programs = {}

    for normalized_uni_name, uni_data in university_data.items():
        # Try to find matching program
        # We need to search by the original institution names, not normalized
        matching_program = None

        for inst_name in uni_data["institution_names"]:
            matching_program = _find_matching_program(
                inst_name, accredited_programs, threshold=0.85
            )
            if matching_program:
                break

        if not matching_program:
            # Try with normalized name as fallback
            matching_program = _find_matching_program(
                normalized_uni_name, accredited_programs, threshold=0.85
            )

        if matching_program:
            program_id = matching_program.get("id")
            if not program_id:
                continue

            if program_id not in matched_programs:
                matched_programs[program_id] = {
                    "program": matching_program,
                    "papers": [],
                    "institution_names": set(),
                    "researchers": defaultdict(
                        lambda: {
                            "name": "",
                            "openalex_id": "",
                            "works_count": 0,
                            "total_citations": 0,
                            "papers": [],
                        }
                    ),
                }

            # Add papers
            matched_programs[program_id]["papers"].extend(uni_data["papers"])
            matched_programs[program_id]["institution_names"].update(
                uni_data["institution_names"]
            )

            # Extract researchers from papers
            for paper in uni_data["papers"]:
                authorships = paper.get("authorships", [])
                for authorship in authorships:
                    author = authorship.get("author", {})
                    if not author:
                        continue

                    author_id = author.get("id", "")
                    author_name = author.get("display_name", "")

                    if author_id and author_name:
                        researcher = matched_programs[program_id]["researchers"][
                            author_id
                        ]
                        researcher["name"] = author_name
                        researcher["openalex_id"] = author_id
                        researcher["works_count"] += 1
                        researcher["total_citations"] += paper.get("cited_by_count", 0)
                        researcher["papers"].append(paper)

    # Finalize matched programs
    result = {}
    for program_id, data in matched_programs.items():
        papers_list = data["papers"]
        # Sort papers by citation count
        papers_list.sort(key=lambda p: p.get("cited_by_count", 0), reverse=True)

        # Convert researchers to list and sort
        researchers_list = list(data["researchers"].values())
        researchers_list.sort(
            key=lambda r: (r["works_count"], r["total_citations"]), reverse=True
        )

        # Format papers for output
        formatted_papers = []
        for paper in papers_list[:20]:  # Top 20 papers
            # Get abstract from paper
            abstract = paper.get("abstract", "")
            # Get URL - prefer landing page, then PDF, then DOI
            primary_location = paper.get("primary_location", {})
            url = primary_location.get("landing_page_url") or primary_location.get(
                "pdf_url"
            )
            if not url and paper.get("doi"):
                doi = (
                    paper.get("doi", "")
                    .replace("https://doi.org/", "")
                    .replace("http://dx.doi.org/", "")
                )
                if doi:
                    url = f"https://doi.org/{doi}"

            formatted_papers.append(
                {
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi"),
                    "openalex_id": paper.get("id"),
                    "url": url,
                    "publication_year": paper.get("publication_year"),
                    "cited_by_count": paper.get("cited_by_count", 0),
                    "venue": primary_location.get("venue", {}).get("display_name", "")
                    if primary_location
                    else "",
                    "abstract": abstract,
                    "authors": [
                        auth.get("author", {}).get("display_name", "")
                        for auth in paper.get("authorships", [])[:5]
                    ],
                }
            )

        # Format researchers for output
        formatted_researchers = []
        for researcher in researchers_list[:20]:  # Top 20 researchers
            formatted_researchers.append(
                {
                    "openalex_id": researcher["openalex_id"],
                    "name": researcher["name"],
                    "works_count": researcher["works_count"],
                    "total_citations": researcher["total_citations"],
                }
            )

        result[program_id] = {
            "program": data["program"],
            "papers": formatted_papers,
            "paper_count": len(papers_list),
            "top_papers": formatted_papers[:10],
            "researchers": formatted_researchers,
            "institution_names": list(data["institution_names"]),
        }

    logger.info(f"Matched {len(result)} programs to universities from papers")

    return result
