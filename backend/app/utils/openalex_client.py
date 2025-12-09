import os
import json
import hashlib
import requests
from urllib.parse import urlencode
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import logging

from .exceptions import OpenAlexAPIError

if TYPE_CHECKING:
    from ..models.author import Author
    from ..models.institution import Institution
    from ..models.paper import Paper

logger = logging.getLogger(__name__)

OPENALEX_BASE = "https://api.openalex.org"
DEFAULT_TIMEOUT = 30  # seconds


def cache_request(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Make a cached request to OpenAlex API.

    Args:
        url: API URL to request
        timeout: Request timeout in seconds

    Returns:
        JSON response data

    Raises:
        OpenAlexAPIError: If request fails
    """
    os.makedirs(".cache", exist_ok=True)
    fname = f".cache/{hashlib.md5(url.encode()).hexdigest()}.json"

    # Check cache first
    if os.path.exists(fname):
        try:
            with open(fname, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file {fname}: {e}")
            # Continue to make request if cache read fails

    # Make request with timeout
    try:
        res = requests.get(url, timeout=timeout)
        res.raise_for_status()  # Raise exception for bad status codes
        data = res.json()

        # Write to cache
        try:
            with open(fname, "w") as f:
                json.dump(data, f)
        except IOError as e:
            logger.warning(f"Error writing cache file {fname}: {e}")
            # Continue even if cache write fails

        return data
    except requests.Timeout as e:
        logger.error(f"OpenAlex API request timeout: {url}")
        raise OpenAlexAPIError(f"Request timeout: {e}") from e
    except requests.RequestException as e:
        logger.error(f"OpenAlex API request failed: {url}, error: {e}")
        raise OpenAlexAPIError(f"API request failed: {e}") from e
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from OpenAlex API: {url}")
        raise OpenAlexAPIError(f"Invalid API response: {e}") from e


def get_concept_ids_from_topics(topics, field_level_only: bool = True):
    """
    Get concept IDs from topic search terms.
    Filters for Field-level concepts (level 0 or 1) by default.

    Args:
        topics: List of topic search terms
        field_level_only: If True, only return Field-level concepts (level 0 or 1)

    Returns:
        Mapping of topic -> concept ID (full URL format)
    """
    import logging

    logger = logging.getLogger(__name__)

    mapping = {}
    for t in topics:
        try:
            data = cache_request(f"{OPENALEX_BASE}/concepts?{urlencode({'search': t})}")
            if data.get("results"):
                concepts = data["results"]

                if field_level_only:
                    # Filter for Field-level concepts (level 0 or 1)
                    # Level 0 = Field-level (e.g., Psychology, Neuroscience)
                    # Level 1 = Subfield-level (e.g., Clinical Psychology)
                    field_level_concepts = [
                        c for c in concepts if c.get("level", 999) in [0, 1]
                    ]

                    if field_level_concepts:
                        # Prefer exact match (case-insensitive) first, then prefer level 0 over level 1
                        # This ensures "Clinical Psychology" matches "Clinical Psychology" (level 1)
                        # rather than "Psychology" (level 0) when searching for "Clinical Psychology"
                        topic_lower = t.lower()
                        exact_match = None
                        for c in field_level_concepts:
                            if c.get("display_name", "").lower() == topic_lower:
                                exact_match = c
                                break

                        if exact_match:
                            concept = exact_match
                        else:
                            # No exact match, prefer level 0 (Field-level) over level 1 (Subfield-level)
                            field_level_concepts.sort(key=lambda x: x.get("level", 999))
                            concept = field_level_concepts[0]

                        concept_id = concept.get("id")
                        concept_level = concept.get("level")
                        mapping[t] = concept_id
                        logger.info(
                            f"Mapped topic '{t}' to Field-level concept (level {concept_level}): {concept_id}"
                        )
                    else:
                        # No Field-level concept found, try to find parent Field-level concept
                        # Look for concepts with ancestors that are Field-level
                        for concept in concepts:
                            ancestors = concept.get("ancestors", [])
                            for ancestor in ancestors:
                                if ancestor.get("level", 999) in [0, 1]:
                                    concept_id = ancestor.get("id")
                                    concept_level = ancestor.get("level")
                                    mapping[t] = concept_id
                                    logger.info(
                                        f"Mapped topic '{t}' to parent Field-level concept (level {concept_level}): {concept_id}"
                                    )
                                    break
                            if t in mapping:
                                break

                        if t not in mapping:
                            logger.warning(
                                f"No Field-level concept found for topic '{t}', skipping"
                            )
                else:
                    # Return first result without filtering
                    concept_id = concepts[0].get("id")
                    mapping[t] = concept_id
                    logger.info(f"Mapped topic '{t}' to concept: {concept_id}")
            else:
                logger.warning(f"No concept found for topic: {t}")
        except OpenAlexAPIError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error searching for concept '{t}': {e}", exc_info=True
            )
            # Continue with other topics even if one fails
    return mapping


def get_primary_field_concept(program_type: str) -> Optional[str]:
    """
    Get the primary field concept ID for a program type.
    Returns the main concept ID (e.g., Psychology for Clin Psych PhD).
    """
    import logging

    logger = logging.getLogger(__name__)

    # Map program types to primary field concepts
    field_mapping = {
        "Clin Psych PhD": "psychology",
        "Clinical Psychology PhD": "psychology",
        "Experimental Psych PhD": "psychology",
        "Cognitive Psych PhD": "psychology",
        "Neuroscience PhD": "neuroscience",
        "Psychology PhD": "psychology",
    }

    # Get the field name
    field_name = None
    for key, value in field_mapping.items():
        if key.lower() in program_type.lower() or program_type.lower() in key.lower():
            field_name = value
            break

    if not field_name:
        logger.warning(f"No field mapping found for program type: {program_type}")
        return None

    logger.info(f"Getting concept ID for field: {field_name}")

    # Get concept ID - try multiple search terms to find the right concept
    search_terms = [field_name]
    if field_name == "psychology":
        search_terms = ["Psychology", "psychology"]  # Try capitalized first

    concept_map = get_concept_ids_from_topics(search_terms)
    concept_id = concept_map.get(field_name) or (
        list(concept_map.values())[0] if concept_map else None
    )

    if concept_id:
        logger.info(f"Found field concept ID: {concept_id} for {field_name}")
    else:
        logger.error(f"Could not find concept ID for field: {field_name}")

    return concept_id


def get_authors_by_concept(concept_id, limit=50):
    """
    Get authors by concept ID. Handles both full URL and ID-only formats.
    """
    # Extract ID part if full URL provided and convert to lowercase
    if "/" in concept_id:
        concept_id_short = concept_id.split("/")[-1].lower()
    else:
        concept_id_short = concept_id.lower()

    authors, cursor = [], "*"
    while len(authors) < limit and cursor:
        # Try with short ID format (lowercase)
        q = urlencode(
            {
                "filter": f"concepts.id:{concept_id_short}",
                "per-page": 25,
                "cursor": cursor,
            }
        )
        data = cache_request(f"{OPENALEX_BASE}/authors?{q}")
        authors += data.get("results", [])
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break
    return authors[:limit]


def get_institution_metadata(inst_id):
    return cache_request(f"{OPENALEX_BASE}/institutions/{inst_id}")


def get_work_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetch a work by DOI."""
    if not doi or not doi.startswith("10."):
        return None
    # Remove any URL prefix
    doi_clean = (
        doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "").strip()
    )
    data = cache_request(f"{OPENALEX_BASE}/works/doi:{doi_clean}")
    return data if data else None


def get_work_by_url(url: str) -> Optional[Dict[str, Any]]:
    """Fetch a work by URL."""
    if not url:
        return None
    # OpenAlex uses URL encoding
    url_encoded = url.replace(":", "%3A").replace("/", "%2F")
    data = cache_request(f"{OPENALEX_BASE}/works/{url_encoded}")
    return data if data else None


def get_works_by_title(title: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for works by title."""
    if not title:
        return []
    q = urlencode({"search": title, "per-page": limit})
    data = cache_request(f"{OPENALEX_BASE}/works?{q}")
    return data.get("results", [])


def get_authors_by_work_id(work_id: str) -> List[Dict[str, Any]]:
    """Get all authors of a specific work."""
    if not work_id:
        return []
    # Extract work ID if full URL provided
    if "/" in work_id:
        work_id = work_id.split("/")[-1]

    work = cache_request(f"{OPENALEX_BASE}/works/W{work_id}")
    if not work or "authorships" not in work:
        return []

    return [
        authorship.get("author", {})
        for authorship in work["authorships"]
        if authorship.get("author")
    ]


def get_author_details(author_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific author."""
    if not author_id:
        return None
    # Extract author ID if full URL provided
    if "/" in author_id:
        author_id = author_id.split("/")[-1]

    data = cache_request(f"{OPENALEX_BASE}/authors/{author_id}")
    return data if data else None


def get_author_works(
    author_id: str, page: int = 1, per_page: int = 25
) -> List[Dict[str, Any]]:
    """Get works by a specific author with pagination."""
    if not author_id:
        return []
    # Extract author ID if full URL provided
    if "/" in author_id:
        author_id = author_id.split("/")[-1]

    # Calculate cursor for pagination (OpenAlex uses cursor-based pagination)
    # For simplicity, we'll use page-based approach with cursor
    cursor = "*"
    # Skip pages (OpenAlex doesn't support page numbers directly, so we iterate)
    for _ in range(page - 1):
        q = urlencode(
            {
                "filter": f"author.id:A{author_id}",
                "per-page": per_page,
                "cursor": cursor,
            }
        )
        data = cache_request(f"{OPENALEX_BASE}/works?{q}")
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            return []

    # Get the actual page
    q = urlencode(
        {"filter": f"author.id:A{author_id}", "per-page": per_page, "cursor": cursor}
    )
    data = cache_request(f"{OPENALEX_BASE}/works?{q}")
    return data.get("results", [])


def get_top_works(search_term: str, top_x: int = 10) -> List[Dict[str, Any]]:
    """Get top works by search term, sorted by relevance."""
    if not search_term:
        return []
    q = urlencode(
        {"search": search_term, "per-page": top_x, "sort": "relevance_score:desc"}
    )
    data = cache_request(f"{OPENALEX_BASE}/works?{q}")
    return data.get("results", [])


def search_papers(
    search_term: str,
    from_year: int = 1980,
    country_code: Optional[str] = None,
    topic_ids: List[str] = [],
    page: int = 1,
    per_page: int = 25,
    sort_by: str = "cited_by_count:desc",  # Sort by citations to get top papers
) -> List[Dict[str, Any]]:
    """Search for academic papers with filters. Sorted by citation count by default.

    Uses concepts.id filter for concept filtering (works with Field-level concepts).
    - Uses title_and_abstract.search for text search (with quote())
    - Uses concepts.id for concept filtering (Field-level concepts)
    - Uses publication_year:> (not >=) for year filter
    - Filter string goes in filter param, no separate search param
    """
    import logging
    from urllib.parse import quote

    logger = logging.getLogger(__name__)

    filters = []

    # Use title_and_abstract.search format from working branch (with quote)
    filters.append(f"title_and_abstract.search:{quote(search_term)}")

    # Use > instead of >= for year (from working branch)
    if from_year:
        filters.append(f"publication_year:>{from_year}")
    if country_code:
        filters.append(f"institutions.country_code:{country_code}")
    if topic_ids:
        # Extract IDs if full URLs provided and convert to lowercase
        clean_topic_ids = []
        for tid in topic_ids:
            if "/" in tid:
                # Extract ID and convert to lowercase (OpenAlex uses lowercase IDs)
                clean_id = tid.split("/")[-1].lower()
            else:
                clean_id = tid.lower()
            clean_topic_ids.append(clean_id)
        # Use pipe for OR logic within concepts
        # Since we're using Field-level concepts, concepts.id will filter by field
        concept_filters = "|".join(clean_topic_ids)
        filters.append(f"concepts.id:{concept_filters}")

    filter_str = ",".join(filters) if filters else None

    # Build query params - filter goes in filter param, no separate search param
    query_params = {
        "per-page": per_page,
        "page": page,
        "sort": sort_by,
    }
    if filter_str:
        query_params["filter"] = filter_str

    q = urlencode(query_params)
    url = f"{OPENALEX_BASE}/works?{q}"
    logger.info(f"Search papers URL: {url}")
    logger.info(f"Filter string: {filter_str}")
    data = cache_request(url)
    return data.get("results", [])


def find_faculty_at_institution(
    institution_id: str, field_concepts: List[str] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Find faculty/researchers at an institution who work in specified fields.

    Args:
        institution_id: OpenAlex institution ID (can be full URL or just ID)
        field_concepts: List of concept names to search for (e.g., ["clinical psychology"])
        limit: Maximum number of authors to return

    Returns:
        List of author dictionaries from OpenAlex
    """
    # Extract ID if full URL provided
    if "/" in institution_id:
        inst_id = institution_id.split("/")[-1]
    else:
        inst_id = institution_id

    # Build filter
    filters = [f"last_known_institution.id:{inst_id}"]

    # Add concept filters if provided
    if field_concepts:
        # Get concept IDs for the field concepts
        concept_map = get_concept_ids_from_topics(field_concepts)
        concept_ids = list(concept_map.values())

        if concept_ids:
            # Use OR logic for concepts (author has any of these concepts)
            # Convert to lowercase (OpenAlex uses lowercase IDs)
            concept_id_strings = []
            for cid in concept_ids:
                if "/" in cid:
                    concept_id_strings.append(cid.split("/")[-1].lower())
                else:
                    concept_id_strings.append(cid.lower())
            concept_filter = "|".join(concept_id_strings)
            filters.append(f"concepts.id:{concept_filter}")

    filter_str = ",".join(filters)

    query_params = {
        "filter": filter_str,
        "per-page": min(limit, 25),
        "sort": "works_count:desc",  # Prioritize prolific researchers
    }

    q = urlencode(query_params)
    url = f"{OPENALEX_BASE}/authors?{q}"

    try:
        data = cache_request(url)
        authors = data.get("results", [])

        # Filter to likely faculty (have recent publications, institution affiliation)
        # Authors are already sorted by works_count, so take top results
        return authors[:limit]
    except OpenAlexAPIError:
        raise
    except Exception as e:
        logger.warning(
            f"Unexpected error finding faculty at institution {institution_id}: {e}",
            exc_info=True,
        )
        return []


def get_fields() -> Dict[str, Any]:
    """Get available academic fields/concepts from OpenAlex."""
    # Return top-level concepts as fields
    data = cache_request(f"{OPENALEX_BASE}/concepts?per-page=200&sort=works_count:desc")
    fields = {}
    for concept in data.get("results", [])[:50]:  # Top 50 by works count
        fields[concept.get("display_name", "")] = {
            "id": concept.get("id", ""),
            "display_name": concept.get("display_name", ""),
            "description": concept.get("description", ""),
        }
    return fields


def get_field_concept_ids() -> Dict[str, str]:
    """
    Get concept IDs for Field-level concepts: Psychology, Neuroscience.
    Returns mapping: field_name -> concept_id (full URL format).
    """
    import logging

    logger = logging.getLogger(__name__)

    field_names = ["Psychology", "Neuroscience"]
    concept_map = get_concept_ids_from_topics(field_names)

    # Cache for future use
    _FIELD_CONCEPT_CACHE = concept_map.copy()

    logger.info(f"Found field concepts: {list(concept_map.keys())}")
    return concept_map


def get_subfield_concept_ids() -> Dict[str, str]:
    """
    Get concept IDs for Subfield-level concepts: Clinical Psychology, Cognitive Neuroscience.
    Returns mapping: subfield_name -> concept_id (full URL format).
    """
    import logging

    logger = logging.getLogger(__name__)

    subfield_names = ["Clinical Psychology", "Cognitive Neuroscience"]
    concept_map = get_concept_ids_from_topics(subfield_names)

    # Cache for future use
    _SUBFIELD_CONCEPT_CACHE = concept_map.copy()

    logger.info(f"Found subfield concepts: {list(concept_map.keys())}")
    return concept_map


def search_works_at_institution(
    institution_id: str,
    topic_keywords: List[str],
    field_concept_ids: List[str],
    subfield_concept_ids: List[str],
    from_year: int = 2010,
    per_page: int = 100,
    sort_by: str = "relevance_score:desc",
) -> List[Dict[str, Any]]:
    """
    Search for works at a specific institution matching:
    - Title/abstract contains topic keywords
    - Concepts include: (Field = Psychology OR Neuroscience) OR (Subfield = Clinical Psychology OR Cognitive Neuroscience)
    - Citation percentile > 50%

    Args:
        institution_id: OpenAlex institution ID (full URL or short ID like "I123456")
        topic_keywords: List of topic keywords to search in title/abstract
        field_concept_ids: List of field-level concept IDs (Psychology, Neuroscience)
        subfield_concept_ids: List of subfield-level concept IDs (Clinical Psychology, Cognitive Neuroscience)
        from_year: Minimum publication year
        per_page: Number of results per page
        sort_by: Sort order (default: relevance_score:desc)

    Returns:
        List of work dictionaries sorted by relevance/citation count
    """
    import logging
    from urllib.parse import quote

    logger = logging.getLogger(__name__)

    # Extract institution ID if full URL provided
    if "/" in institution_id:
        inst_id = institution_id.split("/")[-1]
    else:
        inst_id = institution_id

    # Extract short IDs from concept lists and convert to lowercase
    # OpenAlex uses lowercase IDs (e.g., c15744967 not C15744967)
    field_ids = []
    for cid in field_concept_ids:
        if "/" in cid:
            field_ids.append(cid.split("/")[-1].lower())
        else:
            field_ids.append(cid.lower())

    subfield_ids = []
    for cid in subfield_concept_ids:
        if "/" in cid:
            subfield_ids.append(cid.split("/")[-1].lower())
        else:
            subfield_ids.append(cid.lower())

    # Combine all concept IDs (Field OR Subfield) - works must have at least one
    all_concept_ids = field_ids + subfield_ids
    if not all_concept_ids:
        logger.warning("No concept IDs provided for filtering")
        return []

    all_works = []
    seen_work_ids = set()

    # Strategy 1: Try combined topic search (e.g., "Memory and Trauma")
    combined_search = " and ".join(topic_keywords)
    logger.info(
        f"Searching for works at institution {inst_id} with combined topics: {combined_search}"
    )

    filters = []

    # Use authorships.institutions.lineage (not institutions.id) - matches working example
    filters.append(f"authorships.institutions.lineage:{inst_id}")

    # Title/abstract search for combined topics
    filters.append(f"title_and_abstract.search:{quote(combined_search)}")

    # Year filter
    if from_year:
        filters.append(f"publication_year:>{from_year}")

    # Filter by citation percentile > 50%
    filters.append("cited_by_percentile_year:>50")

    # Concept filter: Field OR Subfield (all concepts combined with OR)
    # Use concepts.id filter (works with Field-level concepts)
    concept_filter = "|".join(all_concept_ids)
    filters.append(f"concepts.id:{concept_filter}")

    filter_str = ",".join(filters)

    query_params = {
        "filter": filter_str,
        "per-page": per_page,
        "sort": sort_by,
    }

    q = urlencode(query_params)
    url = f"{OPENALEX_BASE}/works?{q}"
    logger.info(f"Combined topics search URL: {url}")
    logger.info(f"Filter string: {filter_str}")

    try:
        data = cache_request(url)
        works = data.get("results", [])
        logger.info(
            f"Found {len(works)} works with combined topics '{combined_search}' at institution {inst_id}"
        )

        # Add unique works
        for work in works:
            work_id = work.get("id", "")
            if work_id and work_id not in seen_work_ids:
                all_works.append(work)
                seen_work_ids.add(work_id)
    except Exception as e:
        logger.error(
            f"Error searching works with combined topics at institution {inst_id}: {e}",
            exc_info=True,
        )

    # Strategy 2: If we got few results, also try individual topic searches
    if len(all_works) < 10 and len(topic_keywords) > 1:
        logger.info(
            f"Only found {len(all_works)} works with combined search, trying individual topics"
        )

        for topic in topic_keywords:
            logger.info(
                f"Searching for works at institution {inst_id} with topic: {topic}"
            )

            filters = []

            # Institution filter using lineage
            filters.append(f"authorships.institutions.lineage:{inst_id}")

            # Title/abstract search for individual topic
            filters.append(f"title_and_abstract.search:{quote(topic)}")

            # Year filter
            if from_year:
                filters.append(f"publication_year:>{from_year}")

            # Filter by citation percentile > 50%
            filters.append("cited_by_percentile_year:>50")

            # Concept filter: Field OR Subfield
            # Use concepts.id filter (works with Field-level concepts)
            concept_filter = "|".join(all_concept_ids)
            filters.append(f"concepts.id:{concept_filter}")

            filter_str = ",".join(filters)

            query_params = {
                "filter": filter_str,
                "per-page": per_page,
                "sort": sort_by,
            }

            q = urlencode(query_params)
            url = f"{OPENALEX_BASE}/works?{q}"
            logger.info(f"Individual topic search URL: {url}")

            try:
                data = cache_request(url)
                works = data.get("results", [])
                logger.info(
                    f"Found {len(works)} works for topic '{topic}' at institution {inst_id}"
                )

                # Add unique works
                for work in works:
                    work_id = work.get("id", "")
                    if work_id and work_id not in seen_work_ids:
                        all_works.append(work)
                        seen_work_ids.add(work_id)
            except Exception as e:
                logger.error(
                    f"Error searching works for topic '{topic}' at institution {inst_id}: {e}",
                    exc_info=True,
                )
                continue

    # Sort all works by citation count and return
    all_works.sort(key=lambda w: w.get("cited_by_count", 0), reverse=True)
    logger.info(f"Total unique works found: {len(all_works)}")
    return all_works


# Factory functions to convert OpenAlex dicts to Pydantic models
def author_from_dict(author_data: Dict[str, Any]) -> "Author":
    """
    Convert OpenAlex author dict to Author model.

    Args:
        author_data: Dictionary from OpenAlex API

    Returns:
        Author model instance

    Raises:
        ValueError: If model validation fails
    """
    from ..models.author import Author

    try:
        return Author.model_validate(author_data)
    except Exception as e:
        logger.error(f"Error creating Author model: {e}", exc_info=True)
        raise ValueError(f"Invalid author data: {e}") from e


def institution_from_dict(institution_data: Dict[str, Any]) -> "Institution":
    """
    Convert OpenAlex institution dict to Institution model.

    Args:
        institution_data: Dictionary from OpenAlex API

    Returns:
        Institution model instance

    Raises:
        ValueError: If model validation fails
    """
    from ..models.institution import Institution

    try:
        return Institution.model_validate(institution_data)
    except Exception as e:
        logger.error(f"Error creating Institution model: {e}", exc_info=True)
        raise ValueError(f"Invalid institution data: {e}") from e


def paper_from_dict(work_data: Dict[str, Any]) -> "Paper":
    """
    Convert OpenAlex work dict to Paper model.

    Args:
        work_data: Dictionary from OpenAlex API

    Returns:
        Paper model instance

    Raises:
        ValueError: If model validation fails
    """
    from ..models.paper import Paper

    try:
        # Ensure title or display_name exists
        if not work_data.get("title") and work_data.get("display_name"):
            work_data["title"] = work_data["display_name"]
        elif not work_data.get("display_name") and work_data.get("title"):
            work_data["display_name"] = work_data["title"]

        return Paper.model_validate(work_data)
    except Exception as e:
        logger.error(f"Error creating Paper model: {e}", exc_info=True)
        raise ValueError(f"Invalid paper data: {e}") from e
