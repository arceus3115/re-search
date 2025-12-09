from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Paper(BaseModel):
    """OpenAlex Work/Paper model with enhanced fields."""

    id: str
    title: Optional[str] = Field(default=None, description="Paper title")
    display_name: Optional[str] = Field(
        default=None,
        description="Display name (usually same as title, fallback if title missing)",
    )
    publication_year: Optional[int] = Field(
        default=None, description="Year of publication"
    )
    authorships: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Author information"
    )
    primary_location: Optional[Dict[str, Any]] = Field(
        default=None, description="Primary publication location"
    )
    doi: Optional[str] = Field(default=None, description="DOI")
    abstract: Optional[str] = Field(default=None, description="Abstract text")
    cited_by_count: Optional[int] = Field(default=0, description="Number of citations")
    concepts: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Research concepts"
    )
    type: Optional[str] = Field(
        default=None, description="Work type (e.g., 'article', 'book')"
    )
    open_access: Optional[Dict[str, Any]] = Field(
        default=None, description="Open access information"
    )

    class Config:
        extra = "allow"  # Allow additional OpenAlex fields

    @property
    def venue(self) -> Optional[str]:
        """Get publication venue from primary_location."""
        if self.primary_location:
            source = self.primary_location.get("source", {})
            if source:
                return source.get("display_name")
        return None

    @property
    def url(self) -> Optional[str]:
        """Get URL from primary_location."""
        if self.primary_location:
            return self.primary_location.get(
                "landing_page_url"
            ) or self.primary_location.get("pdf_url")
        if self.doi and not self.doi.startswith("http"):
            return f"https://doi.org/{self.doi}"
        return None

    @property
    def author_names(self) -> List[str]:
        """Get list of author names from authorships."""
        if self.authorships:
            return [
                a.get("author", {}).get("display_name", "")
                for a in self.authorships
                if a.get("author", {}).get("display_name")
            ]
        return []
