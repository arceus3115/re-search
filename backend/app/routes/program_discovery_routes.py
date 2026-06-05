"""
Routes for Program Discovery.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from ..utils.program_aggregator import get_aggregated_programs, aggregate_programs
from ..utils.program_ranker import rank_programs
from ..utils.research_interest_searcher import (
    search_papers_by_interests,
    extract_universities_from_papers,
    match_universities_to_programs,
)
from ..storage.profile_storage import ProfileStorage

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_user_profile(profile_id: Optional[str] = None):
    """
    Get user profile. If profile_id is not provided, get the first available profile.

    Args:
        profile_id: Optional profile ID. If None, gets the first available profile.

    Returns:
        UserProfile or None
    """
    try:
        if profile_id:
            logger.debug(f"Fetching profile by ID: {profile_id}")
            profile = ProfileStorage.get(profile_id)
            if profile:
                logger.debug(f"Found profile by ID: {profile_id}")
            else:
                logger.debug(f"Profile not found by ID: {profile_id}")
            return profile

        # Get first available profile (for now - in production, use session/auth)
        # This is a simple implementation - in production, you'd get the profile from the session
        logger.debug("Fetching first available profile")
        profile = ProfileStorage.get_first()
        if profile:
            logger.debug(f"Found first available profile: {profile.name}")
        else:
            logger.debug("No profiles available")
        return profile
    except Exception as e:
        logger.error(f"Error getting user profile: {e}", exc_info=True)
        return None


@router.get("/programs/discover")
async def discover_programs(
    profile_id: Optional[str] = Query(
        None,
        description="User profile ID (optional, uses first available if not provided)",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(25, ge=1, le=100, description="Results per page"),
    min_fit_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum fit score"),
    use_cache: bool = Query(True, description="Use cached data if available"),
) -> Dict[str, Any]:
    """
    Get ranked programs based on user profile.

    Returns paginated list of programs ranked by fit with user's research interests.
    """
    logger.info(
        f"Program discovery request: profile_id={profile_id}, page={page}, per_page={per_page}, min_fit_score={min_fit_score}"
    )

    try:
        # Get user profile
        logger.debug(f"Fetching user profile: profile_id={profile_id}")
        user_profile = _get_user_profile(profile_id)

        if not user_profile:
            logger.warning(f"No user profile found: profile_id={profile_id}")
            raise HTTPException(
                status_code=404,
                detail="User profile not found. Please create a profile first. You can create one in the 'User Profile' tab.",
            )

        logger.info(
            f"Found user profile: name={user_profile.name}, program_type={user_profile.program_type}"
        )

        # Get research interests
        research_interests = user_profile.research_interests or []
        if not research_interests:
            logger.warning(
                f"User profile found but has no research interests: profile_id={profile_id or 'first'}"
            )
            raise HTTPException(
                status_code=400,
                detail="User profile must have research interests to discover programs. Please add research interests to your profile in the 'User Profile' tab.",
            )

        logger.info(
            f"User profile has {len(research_interests)} research interests: {research_interests}"
        )

        # Search papers by research interests
        logger.info(f"Searching papers for interests: {research_interests}")
        try:
            papers = search_papers_by_interests(
                research_interests=research_interests,
                program_type=user_profile.program_type or "Clin Psych PhD",
                from_year=2010,
                per_interest=100,
                use_cache=use_cache,
            )
            logger.info(f"Found {len(papers)} papers matching research interests")
        except Exception as e:
            logger.error(f"Error searching papers: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to search papers: {str(e)}"
            )

        if not papers:
            logger.warning("No papers found for research interests")
            return {
                "programs": [],
                "pagination": {
                    "page": 1,
                    "per_page": per_page,
                    "total_count": 0,
                    "total_pages": 1,
                    "has_next": False,
                    "has_previous": False,
                },
            }

        # Extract universities from papers
        logger.debug("Extracting universities from papers")
        try:
            university_data = extract_universities_from_papers(papers)
            logger.info(
                f"Extracted {len(university_data)} unique universities from papers"
            )
        except Exception as e:
            logger.error(f"Error extracting universities: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract universities from papers: {str(e)}",
            )

        # Get accredited programs
        logger.debug("Loading accredited programs")
        try:
            accredited_programs = get_aggregated_programs(use_cache=use_cache)
            logger.info(f"Loaded {len(accredited_programs)} accredited programs")
        except Exception as e:
            logger.error(f"Error loading accredited programs: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to load accredited programs: {str(e)}"
            )

        # Match universities to programs
        logger.debug("Matching universities to accredited programs")
        try:
            matched_programs_dict = match_universities_to_programs(
                university_data, accredited_programs
            )
            logger.info(
                f"Matched {len(matched_programs_dict)} programs to universities"
            )
        except Exception as e:
            logger.error(f"Error matching universities to programs: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to match universities to programs: {str(e)}",
            )

        # Convert to list of programs with papers/researchers attached
        # Only include programs that were matched to universities from papers
        programs_with_research = []
        for program_id, program_data in matched_programs_dict.items():
            program = program_data["program"].copy()
            program["papers"] = program_data["papers"]
            program["researchers"] = program_data["researchers"]
            program["paper_count"] = program_data["paper_count"]
            programs_with_research.append(program)

        # Only matched programs are included - unmatched programs are excluded
        logger.info(
            f"Including {len(programs_with_research)} matched programs in results (excluding unmatched programs)"
        )

        # Rank programs
        logger.debug("Ranking programs by fit score")
        try:
            ranked_programs = rank_programs(programs_with_research, user_profile)
            logger.info(f"Ranked {len(ranked_programs)} programs")
        except Exception as e:
            logger.error(f"Error ranking programs: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to rank programs: {str(e)}"
            )

        # Filter by minimum fit score
        if min_fit_score > 0:
            before_filter = len(ranked_programs)
            ranked_programs = [
                p for p in ranked_programs if p.get("fit_score", 0.0) >= min_fit_score
            ]
            logger.info(
                f"Filtered programs: {before_filter} -> {len(ranked_programs)} (min_fit_score={min_fit_score})"
            )

        # Calculate pagination
        total_count = len(ranked_programs)
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        if page > total_pages and total_pages > 0:
            logger.warning(
                f"Requested page {page} exceeds total pages {total_pages}, adjusting to last page"
            )
            page = total_pages

        # Slice results for requested page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_programs = ranked_programs[start_idx:end_idx]
        logger.info(
            f"Returning page {page}/{total_pages}: {len(paginated_programs)} programs (total: {total_count})"
        )

        # Prepare programs for list view (keep summary data, remove full paper lists)
        for program in paginated_programs:
            # Create research summary with researcher names and paper summaries
            paper_count = program.get("paper_count", 0)
            researchers = program.get("researchers", [])
            top_papers = program.get("papers", [])[:3]

            if paper_count > 0:
                # Get top researcher names (top 3-5)
                top_researcher_names = [
                    r.get("name", "") for r in researchers[:5] if r.get("name")
                ]
                researcher_names_str = (
                    ", ".join(top_researcher_names) if top_researcher_names else "N/A"
                )

                # Get paper summaries from abstracts (truncate to ~150 chars each)
                paper_summaries = []
                for paper in top_papers[:3]:
                    title = paper.get("title", "")
                    abstract = paper.get("abstract", "")

                    if abstract:
                        # Truncate abstract to ~150 characters, ending at word boundary
                        summary = abstract[:150].strip()
                        if len(abstract) > 150:
                            # Find last space before 150 chars to avoid cutting words
                            last_space = summary.rfind(" ")
                            if last_space > 100:  # Only use if we have enough text
                                summary = summary[:last_space]
                            summary += "..."
                        paper_summaries.append(f"{title}: {summary}")
                    elif title:
                        # Fallback to just title if no abstract
                        paper_summaries.append(title[:100])

                # Build research summary
                summary_parts = [f"Found {paper_count} relevant papers."]

                if researcher_names_str and researcher_names_str != "N/A":
                    summary_parts.append(f"Top researchers: {researcher_names_str}.")

                if paper_summaries:
                    summary_parts.append(f"Key papers: {' | '.join(paper_summaries)}")

                program["research_summary"] = " ".join(summary_parts)
            else:
                program["research_summary"] = (
                    "No relevant papers found for this program."
                )

            # Keep top papers with URLs for linking, and top researcher names for list view
            program["top_papers"] = top_papers
            program["top_researchers"] = [
                r.get("name", "") for r in researchers[:5] if r.get("name")
            ]
            program["top_researchers_count"] = len(researchers)

            # Remove full paper/researcher lists from list view (can be fetched separately)
            if "papers" in program:
                del program["papers"]
            if "researchers" in program:
                del program["researchers"]

        return {
            "programs": paginated_programs,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }
    except HTTPException as he:
        # Re-raise HTTP exceptions (they already have proper status codes and messages)
        logger.warning(
            f"HTTP exception in discover_programs: {he.status_code} - {he.detail}"
        )
        raise
    except Exception as e:
        logger.error(f"Unexpected error discovering programs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while discovering programs. Please check the server logs for details. Error: {str(e)}",
        )


@router.get("/programs/{program_id}/research")
async def get_program_research(
    program_id: str,
    use_cache: bool = Query(True, description="Use cached data if available"),
) -> Dict[str, Any]:
    """
    Get detailed research information for a specific program.

    Returns OpenAlex research data, top researchers, and papers.
    """
    try:
        # Get user profile for research interests
        user_profile = _get_user_profile()
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found. Please create a profile first.",
            )

        research_interests = user_profile.research_interests or []
        if not research_interests:
            raise HTTPException(
                status_code=400, detail="User profile must have research interests."
            )

        # Get aggregated programs
        programs = get_aggregated_programs(use_cache=use_cache)

        # Find program by ID
        program = next((p for p in programs if p.get("id") == program_id), None)

        if not program:
            raise HTTPException(status_code=404, detail="Program not found")

        # Search papers by research interests
        papers = search_papers_by_interests(
            research_interests=research_interests,
            program_type=user_profile.program_type or "Clin Psych PhD",
            from_year=2010,
            per_interest=100,
            use_cache=use_cache,
        )

        # Extract universities from papers
        university_data = extract_universities_from_papers(papers)

        # Match to this specific program
        matched_programs_dict = match_universities_to_programs(
            university_data,
            [program],  # Just this one program
        )

        # Get research data for this program
        if program_id in matched_programs_dict:
            program_data = matched_programs_dict[program_id]
            research_data = {
                "papers": program_data["papers"],
                "paper_count": program_data["paper_count"],
                "top_papers": program_data["top_papers"],
                "researchers": program_data["researchers"],
                "institution_names": program_data["institution_names"],
            }
        else:
            # No papers found for this program
            research_data = {
                "papers": [],
                "paper_count": 0,
                "top_papers": [],
                "researchers": [],
                "institution_names": [],
            }

        return {
            "program_id": program_id,
            "university_name": program.get("university_name"),
            "research": research_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting program research: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get program research")


@router.post("/programs/refresh")
async def refresh_programs(apa_pdf_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Manually refresh cached program data.

    This will re-parse the APA PDF and re-scrape PCSAS data.
    """
    try:
        logger.info("Refreshing program data...")

        # Re-aggregate programs (this will bypass cache)
        programs = aggregate_programs(apa_pdf_path=apa_pdf_path, use_cache=False)

        return {
            "message": "Program data refreshed successfully",
            "total_programs": len(programs),
            "apa_only": sum(
                1
                for p in programs
                if "APA" in p.get("accreditation_sources", [])
                and "PCSAS" not in p.get("accreditation_sources", [])
            ),
            "pcsas_only": sum(
                1
                for p in programs
                if "PCSAS" in p.get("accreditation_sources", [])
                and "APA" not in p.get("accreditation_sources", [])
            ),
            "both": sum(
                1
                for p in programs
                if "APA" in p.get("accreditation_sources", [])
                and "PCSAS" in p.get("accreditation_sources", [])
            ),
        }
    except Exception as e:
        logger.error(f"Error refreshing programs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to refresh program data")


@router.get("/programs/stats")
async def get_program_stats(
    use_cache: bool = Query(True, description="Use cached data if available"),
) -> Dict[str, Any]:
    """
    Get statistics about accredited programs.

    Returns counts of programs by accreditation source.
    """
    try:
        programs = get_aggregated_programs(use_cache=use_cache)

        apa_count = sum(
            1 for p in programs if "APA" in p.get("accreditation_sources", [])
        )
        pcsas_count = sum(
            1 for p in programs if "PCSAS" in p.get("accreditation_sources", [])
        )
        both_count = sum(
            1
            for p in programs
            if "APA" in p.get("accreditation_sources", [])
            and "PCSAS" in p.get("accreditation_sources", [])
        )
        with_website = sum(1 for p in programs if p.get("website"))
        website_coverage_pct = round(
            (with_website / len(programs) * 100) if programs else 0.0, 1
        )

        cache_dir = Path(__file__).parent.parent.parent / ".cache"
        pcsas_cache = next(cache_dir.glob("pcsas_*.json"), None)
        aggregated_cache = cache_dir / "programs" / "aggregated_programs.json"

        return {
            "total_programs": len(programs),
            "apa_accredited": apa_count,
            "pcsas_accredited": pcsas_count,
            "both_accredited": both_count,
            "apa_only": apa_count - both_count,
            "pcsas_only": pcsas_count - both_count,
            "programs_with_website": with_website,
            "website_coverage_pct": website_coverage_pct,
            "last_pcsas_scrape_at": pcsas_cache.stat().st_mtime
            if pcsas_cache
            else None,
            "last_aggregated_at": aggregated_cache.stat().st_mtime
            if aggregated_cache.exists()
            else None,
        }
    except Exception as e:
        logger.error(f"Error getting program stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get program statistics")
