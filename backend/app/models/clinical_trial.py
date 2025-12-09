"""
ClinicalTrials.gov Trial model.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class ClinicalTrial(BaseModel):
    """ClinicalTrials.gov Trial model."""

    nct_id: str = Field(..., description="ClinicalTrials.gov identifier (NCT ID)")
    title: str = Field(..., description="Trial title")
    brief_summary: Optional[str] = Field(
        default=None, description="Brief summary/description"
    )
    detailed_description: Optional[str] = Field(
        default=None, description="Detailed description"
    )
    conditions: Optional[List[str]] = Field(
        default=None, description="Medical conditions studied"
    )
    interventions: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Interventions (drug, device, procedure, etc.)"
    )
    phase: Optional[str] = Field(
        default=None, description="Trial phase (Phase I, II, III, IV, etc.)"
    )
    overall_status: Optional[str] = Field(
        default=None,
        description="Current status (RECRUITING, ACTIVE_NOT_RECRUITING, etc.)",
    )
    start_date: Optional[str] = Field(default=None, description="Trial start date")
    completion_date: Optional[str] = Field(
        default=None, description="Expected or actual completion date"
    )
    enrollment: Optional[int] = Field(
        default=None, description="Number of participants enrolled or target enrollment"
    )
    lead_sponsor: Optional[str] = Field(
        default=None, description="Primary sponsor name"
    )
    locations: Optional[List[str]] = Field(
        default=None, description="Trial location facilities"
    )
    pi_name: Optional[str] = Field(
        default=None, description="Principal Investigator name"
    )
    alignment_score: Optional[float] = Field(
        default=None,
        description="Calculated alignment score with user interests (0.0-1.0)",
    )
    key_themes: Optional[List[str]] = Field(
        default=None, description="Key research themes extracted from trial"
    )
    user_experience_matches: Optional[List[str]] = Field(
        default=None, description="User experiences that match this trial"
    )

    class Config:
        extra = "allow"  # Allow additional fields from API
