"""
Pydantic models for accredited programs.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AccreditedProgram(BaseModel):
    """Model for an accredited clinical psychology program."""

    id: str = Field(..., description="Unique program identifier")
    university_name: str = Field(..., description="Name of the university")
    program_type: str = Field(default="Clinical Ph.D.", description="Type of program")
    accreditation_sources: List[str] = Field(
        default_factory=list,
        description="List of accreditation sources (APA, PCSAS, or both)",
    )
    address: Optional[str] = Field(default=None, description="Program address")
    website: Optional[str] = Field(default=None, description="Program website URL")
    website_source: Optional[str] = Field(
        default=None,
        description="Source of website URL (pcsas, openalex, existing)",
    )
    accreditation_status: str = Field(
        default="Accredited", description="Current accreditation status"
    )
    date_of_initial_accreditation: Optional[str] = Field(
        default=None, description="Date of initial accreditation"
    )
    next_site_visit_year: Optional[int] = Field(
        default=None, description="Year of next scheduled site visit"
    )
    student_outcomes_link: Optional[str] = Field(
        default=None, description="Link to student outcomes data (PCSAS only)"
    )
    openalex_institution_id: Optional[str] = Field(
        default=None, description="OpenAlex institution ID (cached)"
    )
    research_strengths: Optional[Dict[str, Any]] = Field(
        default=None, description="Cached research strengths data from OpenAlex"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "program-1",
                "university_name": "University of California, Berkeley",
                "program_type": "Clinical Ph.D.",
                "accreditation_sources": ["APA", "PCSAS"],
                "address": "2121 Berkeley Way, #3302, Berkeley, CA 94720-1650",
                "website": "https://psychology.berkeley.edu/",
                "accreditation_status": "Accredited",
                "date_of_initial_accreditation": "February 01, 1948",
                "next_site_visit_year": 2033,
                "student_outcomes_link": "https://pcsas.org/...",
                "openalex_institution_id": "https://openalex.org/I123456",
                "research_strengths": {
                    "top_topics": ["Clinical Psychology", "Cognitive Neuroscience"],
                    "top_researchers": [...],
                    "recent_papers": [...],
                },
            }
        }
