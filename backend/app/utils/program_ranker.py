"""
Program Ranking Algorithm: Rank programs by fit with user profile.
"""

import logging
from typing import List, Dict, Any, Optional

from ..models.user_profile import UserProfile

logger = logging.getLogger(__name__)


def _calculate_research_interest_overlap(
    user_interests: List[str], program_papers: List[Dict[str, Any]]
) -> float:
    """
    Calculate research interest overlap score (0.0 to 1.0) based on papers.

    Args:
        user_interests: User's research interests
        program_papers: Program's papers (from research interest search)

    Returns:
        Overlap score between 0.0 and 1.0
    """
    if not user_interests:
        return 0.5  # Neutral score if no interests specified

    if not program_papers:
        return 0.0  # No papers = no match

    user_interests_lower = [interest.lower() for interest in user_interests]

    # Check paper titles for matches with research interests
    matching_papers = 0
    total_papers_checked = min(len(program_papers), 20)

    for paper in program_papers[:total_papers_checked]:
        title = paper.get("title", "").lower()
        # Check if any research interest appears in the title
        for interest in user_interests_lower:
            if interest in title:
                matching_papers += 1
                break

    # Score based on percentage of papers that match interests
    # Also factor in total paper count (more papers = better)
    match_ratio = (
        matching_papers / total_papers_checked if total_papers_checked > 0 else 0.0
    )
    paper_count_score = min(
        len(program_papers) / 50.0, 1.0
    )  # Normalize: 50 papers = 1.0

    # Combined score: 70% match ratio, 30% paper count
    score = match_ratio * 0.7 + paper_count_score * 0.3

    return score


def _calculate_faculty_match_quality(
    user_interests: List[str], top_researchers: List[Dict[str, Any]]
) -> float:
    """
    Calculate faculty match quality score (0.0 to 1.0).

    Args:
        user_interests: User's research interests
        top_researchers: Program's top researchers

    Returns:
        Faculty match score between 0.0 and 1.0
    """
    if not top_researchers:
        return 0.0

    if not user_interests:
        # If no interests, score based on number of researchers
        return min(len(top_researchers) / 20.0, 1.0)

    # Score based on number of researchers and their prominence
    researcher_score = 0.0
    for researcher in top_researchers[:10]:  # Top 10 researchers
        # Weight by works count and citations
        works_count = researcher.get("works_count", 0)
        citations = researcher.get("total_citations", 0)
        h_index = researcher.get("h_index", 0)

        # Normalize scores (max values: 100 works, 1000 citations, h-index 50)
        works_norm = min(works_count / 100.0, 1.0)
        citations_norm = min(citations / 1000.0, 1.0)
        h_index_norm = min(h_index / 50.0, 1.0) if h_index else 0.0

        researcher_score += works_norm * 0.3 + citations_norm * 0.3 + h_index_norm * 0.4

    # Normalize by number of researchers
    max_score = 10.0  # Max 10 researchers
    score = min(researcher_score / max_score, 1.0)

    return score


def _calculate_university_research_strength(
    program_papers: List[Dict[str, Any]],
) -> float:
    """
    Calculate university research strength score (0.0 to 1.0) based on papers.

    Args:
        program_papers: Program's papers (from research interest search)

    Returns:
        Research strength score between 0.0 and 1.0
    """
    if not program_papers:
        return 0.0

    # Score based on total paper count (normalize: 50 papers = 1.0)
    paper_count_score = min(len(program_papers) / 50.0, 1.0)

    # Score based on citation impact of top papers
    top_papers = program_papers[:10]  # Top 10 papers
    if top_papers:
        total_citations = sum(paper.get("cited_by_count", 0) for paper in top_papers)
        avg_citations = total_citations / len(top_papers)

        # Normalize: 50 citations per paper = 1.0
        citation_score = min(avg_citations / 50.0, 1.0)
    else:
        citation_score = 0.0

    # Combined score: 40% paper count, 60% citation impact
    score = paper_count_score * 0.4 + citation_score * 0.6

    return score


def _calculate_geographic_match(
    user_country: Optional[str], program_address: Optional[str]
) -> float:
    """
    Calculate geographic match score (0.0 to 1.0).

    Args:
        user_country: User's preferred country code (e.g., "US")
        program_address: Program address

    Returns:
        Geographic match score (1.0 if match, 0.5 if no preference, 0.0 if mismatch)
    """
    if not user_country:
        return 0.5  # Neutral if no preference

    if not program_address:
        return 0.5  # Neutral if no address

    # Simple check: look for country code in address
    # This is a simplified check - could be improved with proper address parsing
    address_upper = program_address.upper()

    # US state codes
    us_states = [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    ]

    if user_country.upper() == "US":
        # Check for US state codes
        for state in us_states:
            if f", {state} " in address_upper or address_upper.endswith(f", {state}"):
                return 1.0
        return 0.0
    else:
        # For other countries, check if country name appears
        if user_country.upper() in address_upper:
            return 1.0
        return 0.0


def rank_programs(
    programs: List[Dict[str, Any]],
    user_profile: UserProfile,
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Rank programs by fit with user profile.

    Args:
        programs: List of program dictionaries
        user_profile: User profile with research interests, etc.
        weights: Optional custom weights for scoring factors.
                 Default: {
                     "research_interest": 0.4,
                     "faculty_match": 0.3,
                     "research_strength": 0.2,
                     "geographic": 0.1
                 }

    Returns:
        List of programs with added "fit_score" field, sorted by fit score (descending)
    """
    # Default weights
    default_weights = {
        "research_interest": 0.5,
        "faculty_match": 0.15,
        "research_strength": 0.3,
        "geographic": 0.05,
    }

    if weights:
        default_weights.update(weights)

    # Normalize weights to sum to 1.0
    total_weight = sum(default_weights.values())
    if total_weight > 0:
        weights = {k: v / total_weight for k, v in default_weights.items()}
    else:
        weights = default_weights

    user_interests = user_profile.research_interests or []
    user_country = user_profile.country_filter

    ranked_programs = []

    for program in programs:
        # Get papers and researchers from program (should be populated by research interest search)
        program_papers = program.get("papers", [])
        program_researchers = program.get("researchers", [])

        # Calculate component scores based on papers
        research_interest_score = _calculate_research_interest_overlap(
            user_interests, program_papers
        )

        faculty_match_score = _calculate_faculty_match_quality(
            user_interests, program_researchers
        )

        research_strength_score = _calculate_university_research_strength(
            program_papers
        )

        geographic_score = _calculate_geographic_match(
            user_country, program.get("address")
        )

        # Calculate weighted fit score
        fit_score = (
            research_interest_score * weights["research_interest"]
            + faculty_match_score * weights["faculty_match"]
            + research_strength_score * weights["research_strength"]
            + geographic_score * weights["geographic"]
        )

        # Add scores to program
        program_with_score = program.copy()
        program_with_score["fit_score"] = fit_score
        program_with_score["score_breakdown"] = {
            "research_interest": research_interest_score,
            "faculty_match": faculty_match_score,
            "research_strength": research_strength_score,
            "geographic": geographic_score,
        }

        ranked_programs.append(program_with_score)

    # Sort by fit score (descending)
    ranked_programs.sort(key=lambda x: x.get("fit_score", 0.0), reverse=True)

    logger.info(f"Ranked {len(ranked_programs)} programs")

    return ranked_programs
