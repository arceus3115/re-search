"""
Routes for unified draft generation.
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, Optional
import logging

from ..agents.unified_generator import UnifiedGenerator
from ..storage import ProfileStorage
from ..utils.exceptions import ProfileNotFoundError, AIGenerationError

logger = logging.getLogger(__name__)

router = APIRouter()


def get_unified_generator():
    """Lazy import to avoid initialization errors."""
    return UnifiedGenerator()


@router.post("/draft/generate")
async def generate_draft(
    profile_id: str = Body(..., description="User profile ID"),
    pi_research_data: Dict[str, Any] = Body(
        ..., description="PI research data from /pi-research/gather"
    ),
    format_type: str = Body(..., description="Format type: 'email' or 'statement'"),
    user_draft: Optional[str] = Body(
        None, description="Optional draft text (for email)"
    ),
    word_count_target: Optional[int] = Body(
        None,
        ge=200,
        le=500,
        description="Target word count (for email: 200-500, for statement: 250-500, default varies by format)",
    ),
) -> Dict[str, Any]:
    """
    Generate draft content (email or statement) using user profile and PI research.

    Requires:
    - profile_id: ID of existing user profile
    - pi_research_data: PI research data from /pi-research/gather endpoint
    - format_type: "email" or "statement"

    Optional:
    - user_draft: Initial draft text (for email)
    - word_count_target: Target word count (for statement, 250-500)

    Returns:
        For email:
        {
            "subject": str,
            "body": str,
            "word_count": int
        }

        For statement:
        {
            "statement": str,
            "word_count": int,
            "cited_papers": List[str]
        }
    """
    try:
        # Get profile
        profile = ProfileStorage.get(profile_id)
        if not profile:
            raise ProfileNotFoundError(f"Profile {profile_id} not found")

        # Validate format type
        if format_type not in ["email", "statement"]:
            raise HTTPException(
                status_code=400, detail="format_type must be 'email' or 'statement'"
            )

        # Generate content
        generator = get_unified_generator()
        result = generator.generate_content(
            profile=profile,
            pi_research_data=pi_research_data,
            format_type=format_type,
            user_draft=user_draft,
            word_count_target=word_count_target,
        )

        return result

    except ProfileNotFoundError as e:
        logger.warning(f"Profile not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except AIGenerationError as e:
        logger.error(f"AI generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate content: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating draft: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error while generating draft"
        )


@router.post("/draft/enhance")
async def enhance_draft(
    current_draft: str = Body(..., description="Current draft text to enhance"),
    format_type: str = Body(..., description="Format type: 'email' or 'statement'"),
    profile_id: Optional[str] = Body(
        None, description="Optional user profile ID for context"
    ),
    pi_research_data: Optional[Dict[str, Any]] = Body(
        None, description="Optional PI research data for context"
    ),
) -> Dict[str, Any]:
    """
    Enhance a draft by analyzing weaknesses and generating improvements.

    Args:
        current_draft: Current draft text to enhance
        format_type: "email" or "statement"
        profile_id: Optional user profile ID for context
        pi_research_data: Optional PI research data for context

    Returns:
        {
            "enhanced_draft": str,
            "feedback": {
                "weaknesses": List[str],
                "missing_elements": List[str],
                "improvement_areas": List[str],
                "specific_suggestions": List[str]
            },
            "quality_score": float,
            "improvements": {
                "summary": str
            }
        }
    """
    try:
        # Validate format type
        if format_type not in ["email", "statement"]:
            raise HTTPException(
                status_code=400, detail="format_type must be 'email' or 'statement'"
            )

        # Get profile if provided
        profile = None
        if profile_id:
            try:
                profile = ProfileStorage.get(profile_id)
            except ProfileNotFoundError:
                logger.warning(
                    f"Profile {profile_id} not found, continuing without profile context"
                )

        # Enhance draft
        generator = get_unified_generator()
        result = generator.enhance_draft(
            current_draft=current_draft,
            format_type=format_type,
            profile=profile,
            pi_research_data=pi_research_data,
        )

        return result

    except AIGenerationError as e:
        logger.error(f"AI generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to enhance draft: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error enhancing draft: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error while enhancing draft"
        )
