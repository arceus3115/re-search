from pydantic import BaseModel, Field
from typing import Optional, List


class Institution(BaseModel):
    """OpenAlex Institution model with enhanced fields."""

    id: str
    display_name: str
    country_code: Optional[str] = Field(
        default=None, description="Country code (e.g., 'US', 'GB')"
    )
    ror: Optional[str] = Field(default=None, description="ROR ID")
    homepage_url: Optional[str] = Field(
        default=None, description="Institution homepage URL"
    )
    type: Optional[str] = Field(
        default=None, description="Institution type (e.g., 'education', 'company')"
    )
    lineage: Optional[List[str]] = Field(
        default=None, description="Institution hierarchy/lineage"
    )

    class Config:
        extra = "allow"  # Allow additional OpenAlex fields
