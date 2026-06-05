"""
Topic relevance matcher for checking if faculty research aligns with user interests.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def check_topic_relevance(
    page_content: str, research_interests: List[str]
) -> Dict[str, Any]:
    """
    Check if page content mentions any of the user's research interests.

    Args:
        page_content: Text content from faculty page
        research_interests: List of user's research interest keywords/topics

    Returns:
        Dictionary with:
        - has_match: bool
        - matched_topics: List[str] (topics that matched)
        - confidence: float (0.0-1.0, based on match quality and count)
        - match_contexts: List[str] (snippets showing where matches occurred)
    """
    if not page_content or not research_interests:
        return {
            "has_match": False,
            "matched_topics": [],
            "confidence": 0.0,
            "match_contexts": [],
        }

    page_content_lower = page_content.lower()
    matched_topics = []
    match_contexts = []
    total_match_score = 0.0

    for topic in research_interests:
        if not topic or len(topic.strip()) < 2:
            continue

        topic_lower = topic.lower().strip()

        # Exact phrase match (higher weight)
        exact_pattern = r"\b" + re.escape(topic_lower) + r"\b"
        exact_matches = list(re.finditer(exact_pattern, page_content_lower))
        exact_count = len(exact_matches)

        # Partial word match (lower weight, but still counts)
        partial_pattern = topic_lower
        partial_matches = list(
            re.finditer(re.escape(partial_pattern), page_content_lower)
        )
        partial_count = len(partial_matches) - exact_count  # Don't double count

        # Related terms (check for common variations)
        related_terms = _get_related_terms(topic_lower)
        related_count = 0
        for related in related_terms:
            related_pattern = r"\b" + re.escape(related) + r"\b"
            if re.search(related_pattern, page_content_lower):
                related_count += 1

        # Calculate match score for this topic
        # Exact matches worth more than partial matches
        topic_score = (
            (exact_count * 2.0) + (partial_count * 0.5) + (related_count * 1.0)
        )

        if topic_score > 0:
            matched_topics.append(topic)
            total_match_score += topic_score

            # Extract context around first match for user visibility
            if exact_matches or partial_matches:
                first_match = exact_matches[0] if exact_matches else partial_matches[0]
                start = max(0, first_match.start() - 50)
                end = min(len(page_content), first_match.end() + 50)
                context = page_content[start:end].strip()
                match_contexts.append(f"...{context}...")

    # Calculate confidence
    # Base confidence on: number of matches, match quality, coverage
    match_ratio = (
        len(matched_topics) / len(research_interests) if research_interests else 0
    )
    quality_score = (
        min(total_match_score / max(len(research_interests), 1), 2.0) / 2.0
    )  # Normalize to 0-1

    confidence = (match_ratio * 0.5) + (quality_score * 0.5)
    confidence = min(confidence, 1.0)

    return {
        "has_match": len(matched_topics) > 0,
        "matched_topics": matched_topics,
        "confidence": confidence,
        "match_contexts": match_contexts[:3],  # Limit to 3 contexts
    }


def _get_related_terms(topic: str) -> List[str]:
    """
    Get related terms/variations for a topic keyword.
    """
    related_map = {
        "memory": [
            "memory",
            "memories",
            "remembering",
            "recall",
            "encoding",
            "retrieval",
        ],
        "trauma": ["trauma", "traumatic", "ptsd", "post-traumatic", "trauma-informed"],
        "anxiety": ["anxiety", "anxious", "worry", "stress", "fear"],
        "depression": ["depression", "depressive", "mood", "mental health"],
        "therapy": [
            "therapy",
            "therapeutic",
            "treatment",
            "intervention",
            "counseling",
        ],
        "cognitive": ["cognitive", "cognition", "thinking", "mental processes"],
        "behavioral": ["behavioral", "behavior", "behaviour", "behavioural"],
        "clinical": ["clinical", "clinically", "clinical psychology"],
        "psychology": ["psychology", "psychological", "psychologist"],
    }

    # Check if topic is in our map
    topic_lower = topic.lower()
    if topic_lower in related_map:
        # Return all related terms except the topic itself
        return [term for term in related_map[topic_lower] if term != topic_lower]

    # Generic variations
    variations = []
    if topic_lower.endswith("y"):
        variations.append(topic_lower[:-1] + "ies")  # memory -> memories
    if topic_lower.endswith("s"):
        variations.append(topic_lower[:-1])  # memories -> memory

    return variations
