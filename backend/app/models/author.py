from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Author(BaseModel):
    """OpenAlex Author model with enhanced fields."""

    id: str
    display_name: str
    orcid: Optional[str] = None
    last_known_institution: Optional[Dict[str, Any]] = Field(
        default=None, description="Last known institution information"
    )
    summary_stats: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Summary statistics including h_index, works_count, citation_count",
    )
    x_concepts: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Research concepts/subjects"
    )
    affiliations: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Institution affiliations"
    )
    works_count: Optional[int] = Field(
        default=None, description="Total number of works"
    )
    citation_count: Optional[int] = Field(
        default=None, description="Total citation count"
    )
    email: Optional[str] = Field(default=None, description="Email address")

    class Config:
        extra = "allow"  # Allow additional OpenAlex fields

    @property
    def h_index(self) -> int:
        """Get h-index from summary_stats."""
        if self.summary_stats:
            return self.summary_stats.get("h_index", 0)
        return 0

    @property
    def institution_name(self) -> Optional[str]:
        """Get institution name from last_known_institution."""
        if self.last_known_institution:
            return self.last_known_institution.get("display_name")
        return None

    @property
    def subjects(self) -> List[str]:
        """Get list of research subjects from x_concepts."""
        if self.x_concepts:
            return [
                c.get("display_name", "")
                for c in self.x_concepts
                if c.get("display_name")
            ]
        return []
