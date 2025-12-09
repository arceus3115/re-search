"""
Routes for PI Research Gathering.
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Optional, Dict, Any, List
import logging

from ..agents.pi_research_gatherer import PIResearchGatherer
from ..utils.exceptions import (
    OpenAlexAPIError,
    AIGenerationError,
    ClinicalTrialsAPIError,
    NIHReporterAPIError,
)
from ..utils.model_converters import convert_author_to_response_dict

logger = logging.getLogger(__name__)

router = APIRouter()


def get_pi_research_gatherer():
    """Lazy import to avoid initialization errors."""
    return PIResearchGatherer()


@router.post("/pi-research/gather")
async def gather_pi_research(
    pi_name: Optional[str] = Body(None, description="PI's name"),
    orcid: Optional[str] = Body(None, description="PI's ORCID ID"),
    openalex_id: Optional[str] = Body(None, description="PI's OpenAlex ID"),
    institution: Optional[str] = Body(
        None, description="PI's institution (helps narrow name search)"
    ),
    include_clinical_trials: bool = Body(
        True, description="Whether to include clinical trials"
    ),
    include_nih_projects: bool = Body(
        True, description="Whether to include NIH-funded projects"
    ),
    user_interests: Optional[List[str]] = Body(
        None, description="User's research interests for project/trial alignment"
    ),
    user_experiences: Optional[Dict[str, Any]] = Body(
        None, description="User's experiences for project/trial matching"
    ),
    summary_focus: Optional[str] = Body(
        None,
        description="Summary focus: overview, methodology, findings, applications, trajectory, collaboration",
    ),
) -> Dict[str, Any]:
    """
    Gather research information about a Principal Investigator.

    Search by name, ORCID, or OpenAlex ID. Returns:
    - PI information (name, institution, summary)
    - List of recent papers with summaries and links

    Returns:
        {
            "pi_info": {
                "name": str,
                "institution": str,
                "openalex_id": str,
                "orcid": Optional[str],
                "summary": str
            },
            "papers": [
                {
                    "title": str,
                    "year": int,
                    "doi": Optional[str],
                    "url": Optional[str],
                    "abstract": Optional[str],
                    "summary": str
                }
            ]
        }
    """
    try:
        gatherer = get_pi_research_gatherer()
        author_data = None

        # Try to find PI by provided identifier
        if openalex_id:
            author_data = gatherer.get_pi_by_id(openalex_id)
        elif orcid:
            author_data = gatherer.get_pi_by_orcid(orcid)
        elif pi_name:
            # Name search can return multiple matches
            authors_list = gatherer.search_pi_by_name(pi_name, institution)

            if not authors_list:
                # No matches found
                raise HTTPException(
                    status_code=404,
                    detail="PI not found. Please check the provided information.",
                )

            # If multiple matches, return candidates for selection
            if len(authors_list) > 1:
                candidates = []
                for author in authors_list:
                    try:
                        # Use centralized converter
                        candidate_data = convert_author_to_response_dict(author)
                        candidates.append(candidate_data)
                    except Exception as e:
                        logger.warning(
                            f"Error processing author candidate: {e}", exc_info=True
                        )
                        continue

                return {"multiple_matches": True, "candidates": candidates}

            # Single match - use it
            author_data = authors_list[0]
        else:
            raise HTTPException(
                status_code=400,
                detail="At least one of: pi_name, orcid, or openalex_id must be provided",
            )

        if not author_data:
            raise HTTPException(
                status_code=404,
                detail="PI not found. Please check the provided information.",
            )

        # Get author ID
        author_id = author_data.get("id")
        if not author_id:
            raise HTTPException(
                status_code=500, detail="Could not retrieve author ID from OpenAlex"
            )

        # Get recent papers
        papers = gatherer.get_pi_recent_papers(author_id, limit=10)

        # Generate comprehensive summary (with optional clinical trials and NIH projects)
        result = gatherer.summarize_pi_research(
            author_data=author_data,
            papers=papers,
            user_interests=user_interests,
            user_experiences=user_experiences,
            include_clinical_trials=include_clinical_trials,
            include_nih_projects=include_nih_projects,
            summary_focus=summary_focus,
        )

        return result

    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex API error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="External API unavailable")
    except ClinicalTrialsAPIError as e:
        logger.warning(f"ClinicalTrials.gov API error: {e}", exc_info=True)
        # Continue without clinical trials - don't fail entire request
        # The gatherer should have already handled this gracefully
        pass
    except NIHReporterAPIError as e:
        logger.warning(f"NIH Reporter API error: {e}", exc_info=True)
        # Continue without NIH projects - don't fail entire request
        # The gatherer should have already handled this gracefully
        pass
    except AIGenerationError as e:
        logger.error(f"AI generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate research summary"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error gathering PI research: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to gather PI research")


@router.post("/pi-research/regenerate-summary")
async def regenerate_summary(
    pi_info: Dict[str, Any] = Body(..., description="PI information"),
    papers: List[Dict[str, Any]] = Body(default=[], description="Selected papers"),
    clinical_trials: List[Dict[str, Any]] = Body(
        default=[], description="Selected clinical trials"
    ),
    nih_projects: List[Dict[str, Any]] = Body(
        default=[], description="Selected NIH projects"
    ),
) -> Dict[str, Any]:
    """
    Regenerate PI summary based on selected papers, projects, and trials.

    Accepts filtered data and generates a new summary using only the selected items.

    Returns:
        {
            "pi_info": {
                "name": str,
                "institution": str,
                "summary": str  # Regenerated summary
            }
        }
    """
    try:
        gatherer = get_pi_research_gatherer()

        # Data is already extracted from Body parameters

        if not pi_info:
            raise HTTPException(status_code=400, detail="pi_info is required")

        # Convert papers to author_data format for summarize_pi_research
        # We need to create a minimal author_data structure
        author_data = {
            "id": pi_info.get("openalex_id", ""),
            "display_name": pi_info.get("name", ""),
            "last_known_institution": {"display_name": pi_info.get("institution", "")}
            if pi_info.get("institution")
            else None,
        }

        # Generate new summary with filtered data
        result = gatherer.summarize_pi_research(
            author_data=author_data,
            papers=papers,
            user_interests=None,  # Don't re-analyze alignment, just regenerate summary
            user_experiences=None,
            include_clinical_trials=False,  # Don't fetch new trials, use provided ones
            include_nih_projects=False,  # Don't fetch new projects, use provided ones
            selected_papers=papers,
            selected_trials=clinical_trials,
            selected_nih_projects=nih_projects,
        )

        return {
            "pi_info": {
                "name": pi_info.get("name", ""),
                "institution": pi_info.get("institution", ""),
                "summary": result.get("pi_info", {}).get("summary", ""),
            }
        }

    except AIGenerationError as e:
        logger.error(f"AI generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to regenerate summary")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error regenerating summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to regenerate summary")
