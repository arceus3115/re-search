"""
PI Candidate data model.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class PI_Candidate:
    """Represents a Principal Investigator candidate."""

    name: str
    openalex_id: str
    institution: str
    institution_id: str
    institution_homepage: str
    relevance_score: float
    topics: List[str]
    email: Optional[str] = None
    accepting_phd_students: Optional[bool] = None
    research_description: Optional[str] = None
    lab_goals: Optional[str] = None
    acceptance_status: str = "unknown"  # "yes", "no", or "unknown"
    acceptance_confidence: float = 0.0
    personal_homepage: Optional[str] = None
    recent_publications_count: int = 0
    connection_strength: float = 0.0
    country: Optional[str] = None  # Country code (e.g., "US", "GB")
    top_relevant_papers: Optional[List[Dict]] = field(default_factory=list)
    page_topic_matches: Optional[List[str]] = field(default_factory=list)
    openalex_relevance_score: float = 0.0
