from pydantic import BaseModel, Field
from typing import List, Optional


class ConnectedPI(BaseModel):
    """Represents a connected PI with their OpenAlex ID or name."""

    name: str
    openalex_id: Optional[str] = None
    institution: Optional[str] = None
    # Enhanced fields for relationship context
    relationship_type: Optional[str] = Field(
        default=None,
        description="Type of relationship (e.g., mentor, collaborator, advisor)",
    )
    relationship_notes: Optional[str] = Field(
        default=None, description="Notes about the relationship"
    )
    connection_date: Optional[str] = Field(
        default=None, description="Date of connection (YYYY-MM-DD or free text)"
    )
    connection_location: Optional[str] = Field(
        default=None, description="Location where connection was made"
    )
    # Enriched data from OpenAlex (not user-editable, populated via search)
    h_index: Optional[int] = Field(default=None, description="PI's h-index")
    research_summary: Optional[str] = Field(
        default=None, description="Brief summary of PI's research"
    )
    subjects: Optional[List[str]] = Field(
        default=None, description="Research subjects/areas"
    )


class Publication(BaseModel):
    """Represents a publication (can be identified by DOI, URL, or title)."""

    title: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    # If user provides raw string, store it here
    raw: Optional[str] = None
    # Enhanced fields for rich publication data
    authors: Optional[List[str]] = Field(
        default=None, description="List of author names"
    )
    publication_year: Optional[int] = Field(
        default=None, description="Year of publication"
    )
    venue: Optional[str] = Field(
        default=None, description="Journal, conference, or venue name"
    )
    abstract: Optional[str] = Field(default=None, description="Publication abstract")
    citation_count: Optional[int] = Field(
        default=None, description="Number of citations"
    )
    publication_type: Optional[str] = Field(
        default=None, description="Type (journal, conference, preprint, etc.)"
    )
    openalex_id: Optional[str] = Field(default=None, description="OpenAlex work ID")
    # User-defined organization fields
    tags: Optional[List[str]] = Field(
        default=None, description="User-defined tags/categories"
    )


class UserProfile(BaseModel):
    """User profile for personalized PI matching."""

    name: str
    connected_pis: List[ConnectedPI] = Field(
        default_factory=list, description="List of directly connected PIs"
    )
    research_interests: List[str] = Field(
        default_factory=list, description="List of research interests/topics"
    )
    publications: List[Publication] = Field(
        default_factory=list, description="List of user's authored publications"
    )
    presentations: List[str] = Field(
        default_factory=list, description="List of presentations"
    )
    program_type: str = Field(
        default="Clin Psych PhD", description="Type of program user is interested in"
    )
    country_filter: Optional[str] = Field(
        default=None,
        description="Optional country code to filter PIs by (e.g., 'US', 'GB', 'CA')",
    )
    cv_accomplishments: Optional[str] = Field(
        default=None,
        description="CV/accomplishments text (can be extracted from document or typed)",
    )
    cv_file_path: Optional[str] = Field(
        default=None, description="Path to uploaded CV file (if uploaded)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Doe",
                "connected_pis": [
                    {
                        "name": "Dr. John Smith",
                        "openalex_id": "A123456789",
                        "institution": "University X",
                    }
                ],
                "research_interests": [
                    "cognitive psychology",
                    "memory",
                    "neuroscience",
                ],
                "publications": [
                    {"title": "A Study of Memory", "doi": "10.1234/example"},
                    {"raw": "Memory and Cognition 2023"},
                ],
                "presentations": ["SPSP 2024", "APS 2023"],
                "program_type": "Clin Psych PhD",
            }
        }
