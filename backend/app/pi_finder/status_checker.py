import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Tuple, List
from .web_scraper import (
    discover_professor_urls,
    extract_research_description,
    extract_lab_goals,
)
from .topic_matcher import check_topic_relevance
import re
import logging

logger = logging.getLogger(__name__)


def extract_acceptance_status(
    page_url: str, author_name: str
) -> Tuple[Optional[str], float]:
    """
    Extract student acceptance status from a page with confidence score.

    Returns:
        Tuple of (status, confidence) where:
        - status: "yes", "no", or "unknown"
        - confidence: float between 0.0 and 1.0
    """
    if not page_url:
        return ("unknown", 0.0)

    try:
        response = requests.get(page_url, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return ("unknown", 0.0)

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text().lower()

        # Positive indicators (accepting students)
        positive_patterns = [
            r"accepting\s+(?:phd\s+)?students",
            r"currently\s+accepting\s+(?:phd\s+)?students",
            r"phd\s+(?:positions\s+)?(?:are\s+)?available",
            r"recruiting\s+(?:phd\s+)?students",
            r"seeking\s+(?:phd\s+)?students",
            r"open\s+to\s+(?:phd\s+)?applicants",
            r"taking\s+(?:on\s+)?(?:new\s+)?students",
            r"accepting\s+applications",
        ]

        # Negative indicators (not accepting)
        negative_patterns = [
            r"not\s+accepting\s+(?:phd\s+)?students",
            r"no\s+(?:phd\s+)?positions?\s+(?:available|open)",
            r"not\s+(?:currently\s+)?recruiting",
            r"not\s+taking\s+(?:on\s+)?(?:new\s+)?students",
            r"closed\s+to\s+applications",
        ]

        positive_matches = sum(
            1 for pattern in positive_patterns if re.search(pattern, text)
        )
        negative_matches = sum(
            1 for pattern in negative_patterns if re.search(pattern, text)
        )

        # Check proximity to author name (more relevant if near name)
        name_in_text = author_name.lower() in text
        name_context_score = 1.2 if name_in_text else 0.8

        if positive_matches > negative_matches:
            confidence = min(0.5 + (positive_matches * 0.15) * name_context_score, 1.0)
            return ("yes", confidence)
        elif negative_matches > positive_matches:
            confidence = min(0.5 + (negative_matches * 0.15) * name_context_score, 1.0)
            return ("no", confidence)
        else:
            # Check for dates/deadlines which might indicate active recruitment
            date_patterns = [
                r"application\s+deadline",
                r"fall\s+20\d{2}",
                r"spring\s+20\d{2}",
                r"starting\s+(?:fall|spring)\s+20\d{2}",
            ]
            has_dates = any(re.search(pattern, text) for pattern in date_patterns)
            if has_dates:
                return ("yes", 0.4)

            return ("unknown", 0.2)

    except Exception:
        return ("unknown", 0.0)


def check_phd_student_status(
    institution_homepage: str,
    author_name: str,
    author_data: Optional[Dict] = None,
    research_interests: Optional[List[str]] = None,
) -> Dict[str, any]:
    """
    Enhanced function to check if a PI is accepting PhD students and research topic relevance.
    Uses the web scraper to find the best page and extracts comprehensive information.

    Args:
        institution_homepage: URL to institution/department homepage
        author_name: Name of the faculty member
        author_data: Optional OpenAlex author data
        research_interests: Optional list of user's research interests for topic matching

    Returns a dictionary with:
    - acceptance_status: "yes", "no", or "unknown"
    - acceptance_confidence: float 0.0-1.0
    - research_description: Optional[str]
    - lab_goals: Optional[str]
    - personal_homepage: Optional[str]
    - university_page: Optional[str]
    - topic_matches: Dict with has_match, matched_topics, confidence, match_contexts
    """
    result = {
        "acceptance_status": "unknown",
        "acceptance_confidence": 0.0,
        "research_description": None,
        "lab_goals": None,
        "personal_homepage": None,
        "university_page": None,
        "topic_matches": {
            "has_match": False,
            "matched_topics": [],
            "confidence": 0.0,
            "match_contexts": [],
        },
    }

    if not institution_homepage:
        return result

    # Use web scraper to discover URLs
    discovered_urls = discover_professor_urls(
        author_name, author_data or {}, institution_homepage
    )

    result["personal_homepage"] = discovered_urls.get("personal_homepage")
    result["university_page"] = discovered_urls.get("university_page")

    # Try best_match URL first, then fallback to others
    best_url = discovered_urls.get("best_match")

    # Collect all page content for topic matching
    all_page_content = ""

    if best_url:
        # Get page content for topic matching
        try:
            response = requests.get(best_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                all_page_content = soup.get_text()
        except Exception:
            pass

        # Extract acceptance status
        status, confidence = extract_acceptance_status(best_url, author_name)
        result["acceptance_status"] = status
        result["acceptance_confidence"] = confidence

        # Extract research description
        research_desc = extract_research_description(best_url, author_name)
        if research_desc:
            result["research_description"] = research_desc
            all_page_content += " " + research_desc

        # Extract lab goals
        lab_goals = extract_lab_goals(best_url)
        if lab_goals:
            result["lab_goals"] = lab_goals
            all_page_content += " " + lab_goals

    # If we didn't get good results from best_match, try personal homepage separately
    if result["acceptance_status"] == "unknown" and result["personal_homepage"]:
        try:
            response = requests.get(
                result["personal_homepage"], timeout=10, allow_redirects=True
            )
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                all_page_content += " " + soup.get_text()
        except Exception:
            pass

        status, confidence = extract_acceptance_status(
            result["personal_homepage"], author_name
        )
        if confidence > result["acceptance_confidence"]:
            result["acceptance_status"] = status
            result["acceptance_confidence"] = confidence

    # Check topic relevance if research interests provided
    if research_interests and all_page_content:
        topic_matches = check_topic_relevance(all_page_content, research_interests)
        result["topic_matches"] = topic_matches
        logger.info(
            f"Topic matching for {author_name}: {len(topic_matches.get('matched_topics', []))} matches"
        )

    return result
