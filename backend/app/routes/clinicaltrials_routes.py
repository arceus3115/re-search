"""
Routes for ClinicalTrials.gov API integration.
"""

from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional, List, Dict, Any
import logging

from ..utils.clinicaltrials_client import (
    search_trials_by_pi_name,
    search_trials_by_pi_name_advanced,
    search_trials_by_org,
    get_trial_details,
    format_trial_for_display,
)
from ..utils.exceptions import ClinicalTrialsAPIError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/clinicaltrials/search")
async def search_clinical_trials(
    pi_name: Optional[str] = Body(None, description="PI's name to search for"),
    institution: Optional[str] = Body(
        None, description="Institution name to filter results"
    ),
    org_name: Optional[str] = Body(
        None, description="Organization name to search for (alternative to PI name)"
    ),
    limit: int = Body(
        15, ge=1, le=50, description="Maximum number of trials to return"
    ),
    status_filter: Optional[List[str]] = Body(
        None,
        description="Status filter (e.g., ['RECRUITING', 'ACTIVE_NOT_RECRUITING'])",
    ),
) -> Dict[str, Any]:
    """
    Search for clinical trials by PI name or organization.

    Useful for debugging and manual exploration of ClinicalTrials.gov data.

    Returns:
        {
            "trials": List[Dict],
            "total_count": int
        }
    """
    if not pi_name and not org_name:
        raise HTTPException(
            status_code=400, detail="Either pi_name or org_name is required"
        )

    try:
        if pi_name:
            trials = search_trials_by_pi_name(
                pi_name=pi_name,
                institution=institution,
                limit=limit,
                status_filter=status_filter,
            )
        else:
            trials = search_trials_by_org(org_name=org_name, limit=limit)

        # Format trials for response
        formatted_trials = [format_trial_for_display(t) for t in trials]

        return {"trials": formatted_trials, "total_count": len(formatted_trials)}

    except ClinicalTrialsAPIError as e:
        logger.error(f"ClinicalTrials.gov API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail="ClinicalTrials.gov API unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching clinical trials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search clinical trials")


@router.get("/clinicaltrials/search-by-pi")
async def search_clinical_trials_by_pi(
    pi_name: str = Query(
        ..., description="PI's name to search for (e.g., 'Sanjay Mathew')"
    ),
    page_size: int = Query(25, ge=1, le=100, description="Number of results per page"),
    limit: Optional[int] = Query(
        None, ge=1, description="Maximum number of trials to return (None for all)"
    ),
    status_filter: Optional[str] = Query(
        None,
        description="Comma-separated status filter (e.g., 'RECRUITING,ACTIVE_NOT_RECRUITING')",
    ),
) -> Dict[str, Any]:
    """
    Search for clinical trials by Principal Investigator name using filter.advanced.

    This endpoint uses the ClinicalTrials.gov API v2 filter.advanced parameter
    to directly search by PI name. Supports pagination and status filtering.

    Args:
        pi_name: Principal Investigator name (required)
        page_size: Number of results per page (default 25, max 100)
        limit: Maximum number of trials to return (None for all)
        status_filter: Comma-separated list of statuses to filter

    Returns:
        {
            "trials": List[Dict] - Formatted trial data,
            "total_count": int - Total number of trials found,
            "pi_name": str - The PI name searched
        }
    """
    try:
        # Parse status filter if provided
        status_list = None
        if status_filter:
            status_list = [s.strip() for s in status_filter.split(",") if s.strip()]

        # Use the advanced search function
        trials = search_trials_by_pi_name_advanced(
            pi_name=pi_name, limit=limit, page_size=page_size, status_filter=status_list
        )

        # Format trials for response
        formatted_trials = [format_trial_for_display(t) for t in trials]

        return {
            "trials": formatted_trials,
            "total_count": len(formatted_trials),
            "pi_name": pi_name,
        }

    except ClinicalTrialsAPIError as e:
        logger.error(f"ClinicalTrials.gov API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail=f"ClinicalTrials.gov API unavailable: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching clinical trials: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to search clinical trials: {str(e)}"
        )


@router.get("/clinicaltrials/{nct_id}")
async def get_clinical_trial_details(nct_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific clinical trial by NCT ID.

    Args:
        nct_id: ClinicalTrials.gov identifier (e.g., "NCT01234567" or "01234567")

    Returns:
        Trial details dictionary
    """
    try:
        trial = get_trial_details(nct_id)

        if not trial:
            raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")

        return format_trial_for_display(trial)

    except ClinicalTrialsAPIError as e:
        logger.error(f"ClinicalTrials.gov API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail="ClinicalTrials.gov API unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching trial details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch trial details")
