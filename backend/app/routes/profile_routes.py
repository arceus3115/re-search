"""
Routes for user profile management.
"""

import uuid
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Query

from ..models.user_profile import UserProfile
from ..utils.document_parser import extract_text_from_file
from ..utils.cv_parser import get_cv_parser
from ..agents.pi_research_gatherer import PIResearchGatherer
from ..agents.profile_analyzer import ProfileAnalyzer
from ..storage import ProfileStorage
from ..utils.openalex_client import (
    get_work_by_doi,
    get_works_by_title,
    get_author_details,
    OPENALEX_BASE,
)
from ..utils.model_converters import (
    convert_author_to_response_dict,
    convert_paper_to_response_dict,
)
from ..utils.exceptions import (
    ProfileNotFoundError,
    DocumentParsingError,
    OpenAlexAPIError,
    AIGenerationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Directory for uploaded CV files - use absolute path relative to this file
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "temp"
try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error(f"Failed to create upload directory {UPLOAD_DIR}: {e}", exc_info=True)
    raise


@router.post("/user_profile")
async def create_user_profile(profile: UserProfile) -> Dict[str, str]:
    """
    Create a new user profile.

    Returns:
        {
            "profile_id": str,
            "message": str
        }
    """
    try:
        # Generate unique profile ID
        profile_id = str(uuid.uuid4())

        # Store profile
        ProfileStorage.set(profile_id, profile)

        logger.info(f"Created profile {profile_id} for user: {profile.name}")

        return {
            "profile_id": profile_id,
            "message": "User profile created successfully",
        }
    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create profile")


@router.get("/user_profile/{profile_id}")
async def get_user_profile(profile_id: str) -> UserProfile:
    """
    Get a user profile by ID.

    Returns:
        UserProfile object
    """
    profile = ProfileStorage.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


@router.put("/user_profile/{profile_id}")
async def update_user_profile(profile_id: str, profile: UserProfile) -> Dict[str, str]:
    """
    Update an existing user profile.

    Returns:
        {
            "profile_id": str,
            "message": str
        }
    """
    if not ProfileStorage.exists(profile_id):
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        ProfileStorage.set(profile_id, profile)
        logger.info(f"Updated profile {profile_id}")

        return {"profile_id": profile_id, "message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.post("/profile/cv/upload")
async def upload_cv(
    file: UploadFile = File(..., description="CV file (TXT only)"),
) -> Dict[str, Any]:
    """
    Upload and extract text from a CV file.

    Supported format: TXT only

    Returns:
        {
            "extracted_text": str,
            "file_name": str,
            "file_type": str,
            "file_path": str,
            "presentations": List[str]
        }
    """
    try:
        # Validate file type - only accept .txt files
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""

        logger.info(f"Processing CV upload: filename={file.filename}, ext={file_ext}")

        if file_ext != ".txt":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Only .txt files are supported.",
            )

        file_type = "txt"

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

        logger.info(f"Saving uploaded file to: {file_path}")

        # Save uploaded file
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                file_size = len(content)
                buffer.write(content)
            logger.info(f"Saved uploaded file: {file_path} (size: {file_size} bytes)")
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to save uploaded file: {str(e)}"
            )

        # Extract text from file
        try:
            logger.info(f"Extracting text from file: {file_path}")
            extracted_text = extract_text_from_file(str(file_path))

            if not extracted_text or not extracted_text.strip():
                logger.warning(f"No text extracted from file: {file_path}")
                extracted_text = ""
            else:
                logger.info(
                    f"Successfully extracted {len(extracted_text)} characters from file"
                )

            # Parse CV to extract presentations
            presentations = []

            if extracted_text and extracted_text.strip():
                try:
                    cv_parser = get_cv_parser()
                    logger.info("Parsing CV to extract presentations")

                    # Extract presentations
                    presentations = cv_parser.extract_presentations(extracted_text)
                    logger.info(f"Extracted {len(presentations)} presentations from CV")

                except AIGenerationError as e:
                    logger.warning(f"AI error parsing CV (non-fatal): {e}")
                    # Continue without extracted data - user can still use the text
                except Exception as e:
                    logger.warning(f"Error parsing CV (non-fatal): {e}", exc_info=True)
                    # Continue without extracted data - user can still use the text

            return {
                "extracted_text": extracted_text,
                "file_name": file.filename or "unknown",
                "file_type": file_type,
                "file_path": str(file_path),
                "presentations": presentations,
            }
        except DocumentParsingError as e:
            logger.error(f"Document parsing error: {e}", exc_info=True)
            # Clean up file on error
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass
            raise HTTPException(
                status_code=500, detail=f"Failed to parse document: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error extracting text: {e}", exc_info=True)
            # Clean up file on error
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass
            raise HTTPException(
                status_code=500, detail=f"Failed to extract text from file: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading CV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading CV: {str(e)}")


@router.post("/profile/{profile_id}/cv")
async def update_profile_cv(
    profile_id: str,
    cv_text: str = Body(..., description="CV/accomplishments text"),
    cv_file_path: Optional[str] = Body(None, description="Path to uploaded CV file"),
) -> Dict[str, str]:
    """
    Update the CV/accomplishments for a profile.

    Returns:
        {
            "profile_id": str,
            "message": str
        }
    """
    profile = ProfileStorage.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        # Update CV fields
        profile.cv_accomplishments = cv_text
        profile.cv_file_path = cv_file_path

        ProfileStorage.set(profile_id, profile)

        logger.info(f"Updated CV for profile {profile_id}")

        return {"profile_id": profile_id, "message": "CV updated successfully"}
    except Exception as e:
        logger.error(f"Error updating CV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update CV")


@router.post("/profile/analyze")
async def analyze_profile(
    profile_id: str = Body(..., description="User profile ID to analyze"),
    program_id: Optional[str] = Body(
        None, description="Optional program identifier for program-specific analysis"
    ),
    program_info: Optional[Dict[str, Any]] = Body(
        None,
        description="Optional program information (name, requirements, focus_areas, description)",
    ),
) -> Dict[str, Any]:
    """
    Analyze user profile for strength assessment and program fit.

    Returns:
        {
            "fit_score": float,  # 0.0-1.0 overall fit score
            "strengths": List[str],  # Identified strengths
            "weaknesses": List[str],  # Identified weaknesses
            "recommendations": List[str],  # Actionable improvement recommendations
            "competitiveness": str,  # Competitiveness assessment
            "gap_analysis": Dict[str, Any],  # Missing elements and gaps
            "detailed_scores": Dict[str, float],  # Scores for different aspects
            "program_id": Optional[str]  # Program ID if provided
        }
    """
    try:
        # Get profile
        profile = ProfileStorage.get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Analyze profile
        analyzer = ProfileAnalyzer()
        result = analyzer.analyze_profile(
            profile=profile, program_id=program_id, program_info=program_info
        )

        logger.info(
            f"Profile analysis completed for profile {profile_id}, fit_score: {result.get('fit_score', 0):.2f}"
        )

        return result

    except ProfileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile not found")
    except AIGenerationError as e:
        logger.error(f"AI generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze profile: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze profile")


@router.get("/profile/pi/search")
async def search_pi_for_profile(
    name: str = Query(..., description="PI name to search for"),
    institution: Optional[str] = Query(
        None, description="Optional institution to narrow search"
    ),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results"),
) -> Dict[str, Any]:
    """
    Search for PIs by name (for profile form autocomplete).

    Returns a simplified list of PI candidates with basic info for selection.
    """
    try:
        gatherer = PIResearchGatherer()
        authors_list = gatherer.search_pi_by_name(name, institution)

        if authors_list is None:
            raise HTTPException(status_code=500, detail="Error searching for PI")

        if not authors_list:
            return {"candidates": []}

        # Format candidates for frontend
        candidates = []
        for author_dict in authors_list[:limit]:
            try:
                # Use centralized converter
                candidate_data = convert_author_to_response_dict(author_dict)
                candidates.append(candidate_data)
            except Exception as e:
                logger.warning(f"Error processing author candidate: {e}", exc_info=True)
                continue

        return {"candidates": candidates}
    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex API error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="External API unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching for PI: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search for PI")


@router.get("/profile/pi/{openalex_id}/details")
async def get_pi_details(openalex_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a PI by OpenAlex ID.

    Returns enriched PI data including research summary.
    """
    try:
        # Extract ID if full URL provided
        if "/" in openalex_id:
            pi_id = openalex_id.split("/")[-1]
        else:
            pi_id = openalex_id

        author_data = get_author_details(pi_id)

        if not author_data:
            raise HTTPException(status_code=404, detail="PI not found")

        # Convert to response format using centralized converter
        try:
            author_response = convert_author_to_response_dict(author_data)
            author_name = author_response["name"]
            openalex_id = author_response["openalex_id"]
            orcid = author_data.get("orcid")  # Not in response dict, get directly
            institution_name = author_response["institution"]
            h_index = author_response["h_index"]
            subjects = author_response["subjects"]
        except Exception as e:
            logger.error(f"Error converting author data: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to process author data")

        # Get a brief research summary (we could fetch papers here if needed)
        gatherer = PIResearchGatherer()
        papers = gatherer.get_pi_recent_papers(pi_id, limit=5)
        summary_result = gatherer.summarize_pi_research(author_data, papers)
        research_summary = summary_result.get("pi_info", {}).get("summary", "")

        return {
            "name": author_name,
            "openalex_id": openalex_id,
            "orcid": orcid,
            "institution": institution_name,
            "h_index": h_index,
            "subjects": subjects,
            "research_summary": research_summary,
        }
    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex API error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="External API unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching PI details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch PI details")


@router.get("/profile/publication/search")
async def search_publication_for_profile(
    query: str = Query(..., description="DOI, title, or author name to search for"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results"),
) -> Dict[str, Any]:
    """
    Search for publications by DOI, title, or author (for profile form).

    Returns a list of publication candidates with metadata.
    """
    try:
        publications = []

        # Try DOI first if it looks like a DOI
        if query.startswith("10.") or "doi.org" in query.lower():
            doi_clean = (
                query.replace("https://doi.org/", "")
                .replace("http://dx.doi.org/", "")
                .strip()
            )
            work = get_work_by_doi(doi_clean)
            if work:
                publications.append(_format_publication(work))
                return {"publications": publications}

        # Search by title
        works = get_works_by_title(query, limit=limit)

        for work in works:
            publications.append(_format_publication(work))

        return {"publications": publications}
    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex API error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="External API unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching for publication: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search for publication")


@router.get("/profile/publication/{openalex_id}")
async def get_publication_details(openalex_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a publication by OpenAlex work ID.
    """
    try:
        # Extract ID if full URL provided
        if "/" in openalex_id:
            work_id = openalex_id.split("/")[-1]
        else:
            work_id = openalex_id

        from ..utils.openalex_client import cache_request

        work_data = cache_request(f"{OPENALEX_BASE}/works/{work_id}")

        if not work_data:
            raise HTTPException(status_code=404, detail="Publication not found")

        return _format_publication(work_data)
    except OpenAlexAPIError as e:
        logger.error(f"OpenAlex API error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="External API unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error fetching publication details: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to fetch publication details"
        )


def _format_publication(work: Dict[str, Any]) -> Dict[str, Any]:
    """Format OpenAlex work data into publication format."""
    # Use centralized converter
    return convert_paper_to_response_dict(work)
