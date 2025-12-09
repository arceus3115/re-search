"""
Routes for PI Finder Agent.
"""

from fastapi import APIRouter, Query, Body, HTTPException
from typing import List, Optional, Dict, Any
import logging

from ..utils.exceptions import OpenAlexAPIError

logger = logging.getLogger(__name__)

router = APIRouter()


def get_pi_finder_agent():
    """Lazy import to avoid initialization errors."""
    from ..agents.pi_finder_agent import PIFinderAgent

    return PIFinderAgent()


@router.post("/agents/pi-finder/search")
async def pi_finder_agent_search(
    specialties: List[str] = Body(
        ..., description="Research specialties (e.g., memory, trauma, depression)"
    ),
    techniques: List[str] = Body(
        default=[], description="Techniques used (e.g., MRI, EEG, fMRI)"
    ),
    country_filter: Optional[str] = Body(
        None, description="Country code filter (e.g., US, GB)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Results per page"),
) -> Dict[str, Any]:
    """
    PI Finder Agent: Find PIs matching specialties and techniques.

    Searches accredited Clinical Psychology programs for faculty matching:
    - Research specialties (e.g., memory, trauma, depression, anxiety)
    - Techniques (e.g., MRI, EEG analysis, fMRI)

    Returns paginated list of PI candidates ranked by relevance.
    """
    try:
        # Find PIs using the agent
        pi_finder_agent = get_pi_finder_agent()
        candidates = await pi_finder_agent.find_pis(
            specialties=specialties,
            techniques=techniques,
            country_filter=country_filter,
        )

        # Calculate pagination
        total_count = len(candidates)
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        if page > total_pages and total_pages > 0:
            page = total_pages

        # Slice results for requested page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_candidates = candidates[start_idx:end_idx]

        # Convert PI_Candidate objects to dicts for JSON response
        candidates_dicts = [
            {
                "name": c.name,
                "openalex_id": c.openalex_id,
                "institution": c.institution,
                "institution_id": c.institution_id,
                "institution_homepage": c.institution_homepage,
                "relevance_score": c.relevance_score,
                "topics": c.topics,
                "email": c.email,
                "accepting_phd_students": c.accepting_phd_students,
                "research_description": c.research_description,
                "lab_goals": c.lab_goals,
                "acceptance_status": c.acceptance_status,
                "acceptance_confidence": c.acceptance_confidence,
                "personal_homepage": c.personal_homepage,
                "recent_publications_count": c.recent_publications_count,
                "country": c.country,
                "page_topic_matches": c.page_topic_matches or [],
            }
            for c in paginated_candidates
        ]

        return {
            "candidates": candidates_dicts,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }
    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex API error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="External API unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching for PIs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search for PIs")
