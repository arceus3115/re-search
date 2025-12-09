"""
NIH Reporter Project model.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class NIHProject(BaseModel):
    """NIH Reporter Project model."""

    appl_id: Optional[str] = Field(default=None, description="Application ID")
    fiscal_year: Optional[int] = Field(
        default=None, description="Fiscal year of the award"
    )
    project_serial_num: Optional[str] = Field(
        default=None, description="Project serial number"
    )
    organization: Optional[str] = Field(default=None, description="Organization name")
    organization_type: Optional[str] = Field(
        default=None, description="Type of organization"
    )
    award_type: Optional[str] = Field(default=None, description="Type of award")
    activity_code: Optional[str] = Field(default=None, description="Activity code")
    award_amount: Optional[float] = Field(default=None, description="Award amount")
    project_num_split: Optional[str] = Field(
        default=None, description="Project number split"
    )
    principal_investigators: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Principal investigators"
    )
    program_officers: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Program officers"
    )
    cong_dist: Optional[str] = Field(default=None, description="Congressional district")
    project_start_date: Optional[str] = Field(
        default=None, description="Project start date"
    )
    project_end_date: Optional[str] = Field(
        default=None, description="Project end date"
    )
    opportunity_number: Optional[str] = Field(
        default=None, description="Opportunity number"
    )
    full_study_section: Optional[str] = Field(
        default=None, description="Full study section"
    )
    award_notice_date: Optional[str] = Field(
        default=None, description="Award notice date"
    )
    core_project_num: Optional[str] = Field(
        default=None, description="Core project number"
    )
    pref_terms: Optional[List[str]] = Field(
        default=None, description="Preferred terms (research areas)"
    )
    project_title: Optional[str] = Field(default=None, description="Project title")
    phr_text: Optional[str] = Field(
        default=None, description="Public Health Relevance text (project abstract)"
    )
    spending_categories_desc: Optional[List[str]] = Field(
        default=None, description="Spending categories description"
    )
    pi_name: Optional[str] = Field(
        default=None, description="Principal Investigator name (extracted)"
    )
    search_url: Optional[str] = Field(
        default=None, description="NIH Reporter search URL for this project"
    )

    class Config:
        extra = "allow"  # Allow additional fields from API
