"""
PI Research Gatherer: Collects and summarizes PI research information from OpenAlex.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from urllib.parse import urlencode

from ..utils.openalex_client import get_author_details, OPENALEX_BASE, cache_request
from ..utils.ai_client import get_ai_client
from ..utils.exceptions import (
    OpenAlexAPIError,
    AIGenerationError,
    ClinicalTrialsAPIError,
    NIHReporterAPIError,
)
from ..utils.clinicaltrials_client import (
    search_trials_by_pi_name_advanced,
    format_trial_for_display,
)
from ..utils.nih_reporter_client import (
    search_projects_by_pi_name,
    format_project_for_display,
)
from ..utils.trial_analyzer import analyze_trial_alignment

logger = logging.getLogger(__name__)


def _parse_trial_date(date_str: Optional[str]) -> datetime:
    """
    Parse a trial date string that may be in YYYY-MM-DD or YYYY-MM format.

    Args:
        date_str: Date string in various formats

    Returns:
        datetime object, or datetime(1900, 1, 1) if parsing fails
    """
    if not date_str:
        return datetime(1900, 1, 1)

    # Remove time portion if present
    date_part = date_str.split("T")[0].strip()

    try:
        # Try YYYY-MM-DD format first
        if len(date_part) == 10:
            return datetime.strptime(date_part, "%Y-%m-%d")
        # Try YYYY-MM format
        elif len(date_part) == 7:
            return datetime.strptime(date_part, "%Y-%m")
        # Try other formats if needed
        else:
            return datetime.strptime(date_part, "%Y-%m-%d")
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse date: {date_str}, using default")
        return datetime(1900, 1, 1)


class PIResearchGatherer:
    """
    Gathers research information about a Principal Investigator.
    """

    def __init__(self):
        """Initialize PI Research Gatherer."""
        self.ai_client = get_ai_client()

    def search_pi_by_name(
        self, name: str, institution: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for a PI by name (and optionally institution).

        Args:
            name: PI's name
            institution: Optional institution name to narrow search

        Returns:
            List of author data dictionaries (can be empty or contain multiple matches)

        Raises:
            OpenAlexAPIError: If API request fails
        """
        try:
            # Build search query - search by name first
            query = f'display_name.search:"{name}"'

            # Search for authors
            params = {
                "filter": query,
                "per-page": 25,  # Get more results to filter by institution
                "sort": "works_count:desc",
            }
            q = urlencode(params)
            url = f"{OPENALEX_BASE}/authors?{q}"

            logger.info(
                f"Searching for PI: {name} at {institution or 'any institution'}"
            )
            data = cache_request(url)
            authors = data.get("results", [])

            if not authors:
                logger.warning(f"No authors found for: {name}")
                return []

            # If institution filter provided, filter by checking all affiliations
            if institution:
                filtered_authors = []
                institution_lower = institution.lower()

                for author in authors:
                    # Check last_known_institution
                    last_inst = author.get("last_known_institution")
                    if last_inst:
                        last_inst_name = last_inst.get("display_name", "").lower()
                        if (
                            institution_lower in last_inst_name
                            or last_inst_name in institution_lower
                        ):
                            filtered_authors.append(author)
                            continue

                    # Check all affiliations if not found in last_known_institution
                    affiliations = author.get("affiliations", [])
                    for aff in affiliations:
                        aff_inst = aff.get("institution", {})
                        if aff_inst:
                            aff_name = aff_inst.get("display_name", "").lower()
                            if (
                                institution_lower in aff_name
                                or aff_name in institution_lower
                            ):
                                filtered_authors.append(author)
                                break

                authors = filtered_authors if filtered_authors else authors
                logger.info(
                    f"Filtered to {len(authors)} author(s) matching institution: {institution}"
                )

            logger.info(f"Found {len(authors)} author(s) for: {name}")
            return authors[:5]  # Return top 5

        except OpenAlexAPIError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error searching for PI by name: {e}", exc_info=True
            )
            raise OpenAlexAPIError(f"Failed to search for PI: {e}") from e

    def get_pi_by_id(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """
        Get PI information by OpenAlex ID.

        Args:
            openalex_id: OpenAlex author ID (full URL or short ID)

        Returns:
            Author data dictionary or None if not found
        """
        try:
            author_data = get_author_details(openalex_id)
            if author_data:
                logger.info(
                    f"Retrieved author by ID: {author_data.get('display_name')}"
                )
            return author_data
        except OpenAlexAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting PI by ID: {e}", exc_info=True)
            raise OpenAlexAPIError(f"Failed to get PI by ID: {e}") from e

    def get_pi_by_orcid(self, orcid: str) -> Optional[Dict[str, Any]]:
        """
        Get PI information by ORCID.

        Args:
            orcid: ORCID ID (with or without https://orcid.org/)

        Returns:
            Author data dictionary or None if not found
        """
        try:
            # Clean ORCID format
            if orcid.startswith("https://"):
                orcid_id = orcid.split("/")[-1]
            elif orcid.startswith("orcid.org/"):
                orcid_id = orcid.split("/")[-1]
            else:
                orcid_id = orcid

            # Search by ORCID
            params = {"filter": f"orcid:https://orcid.org/{orcid_id}", "per-page": 1}
            q = urlencode(params)
            url = f"{OPENALEX_BASE}/authors?{q}"

            logger.info(f"Searching for PI by ORCID: {orcid_id}")
            data = cache_request(url)
            authors = data.get("results", [])

            if not authors:
                logger.warning(f"No author found for ORCID: {orcid_id}")
                return None

            author = authors[0]
            logger.info(f"Found author by ORCID: {author.get('display_name')}")
            return author

        except OpenAlexAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting PI by ORCID: {e}", exc_info=True)
            raise OpenAlexAPIError(f"Failed to get PI by ORCID: {e}") from e

    def get_pi_recent_papers(
        self, author_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get papers by a PI, prioritized by impact (citations) then recency.

        Args:
            author_id: OpenAlex author ID
            limit: Maximum number of papers to return

        Returns:
            List of paper dictionaries, sorted by citations (highest first), then by publication date (most recent first)
        """
        try:
            # Get works by author
            if "/" in author_id:
                author_id_short = author_id.split("/")[-1]
            else:
                author_id_short = author_id

            # Get more works than needed to allow for better sorting
            fetch_limit = min(limit * 3, 50)  # Fetch more to sort, but cap at 50

            # Get works sorted by citations (most cited first)
            params = {
                "filter": f"author.id:{author_id_short}",
                "per-page": fetch_limit,
                "sort": "cited_by_count:desc",
            }
            q = urlencode(params)
            url = f"{OPENALEX_BASE}/works?{q}"

            logger.info(f"Fetching papers for author: {author_id_short}")
            data = cache_request(url)
            works = data.get("results", [])

            # Sort by citations first (highest first), then by year (most recent first)
            works.sort(
                key=lambda w: (
                    w.get("cited_by_count", 0) or 0,
                    w.get("publication_year", 0) or 0,
                ),
                reverse=True,
            )

            return works[:limit]

        except OpenAlexAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting PI papers: {e}", exc_info=True)
            return []

    def summarize_paper(self, paper: Dict[str, Any]) -> str:
        """
        Generate a brief summary of a paper using AI.

        Args:
            paper: Paper dictionary from OpenAlex

        Returns:
            Brief summary string
        """
        try:
            title = paper.get("title", "Unknown Title")
            abstract = paper.get("abstract", "")
            year = paper.get("publication_year", "")

            # If no abstract, use title only
            if not abstract:
                return f"Research on {title} ({year})"

            # Generate brief summary using AI
            prompt = f"""Summarize this research paper in 2-3 sentences:

Title: {title}
Year: {year}
Abstract: {abstract[:1000]}

Provide a concise summary focusing on the main research question and findings."""

            summary = self.ai_client.generate_text(
                prompt=prompt, max_tokens=150, temperature=0.7
            )

            return summary.strip()

        except AIGenerationError:
            # Fallback to simple description
            title = paper.get("title", "Unknown Title")
            year = paper.get("publication_year", "")
            return f"Research on {title} ({year})"
        except Exception as e:
            logger.warning(f"Unexpected error summarizing paper: {e}", exc_info=True)
            # Fallback to simple description
            title = paper.get("title", "Unknown Title")
            year = paper.get("publication_year", "")
            return f"Research on {title} ({year})"

    def get_pi_clinical_trials(
        self, pi_name: str, institution: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get clinical trials for a PI using the advanced filter.advanced search.

        Args:
            pi_name: PI's name (middle names/initials will be removed for search)
            institution: Optional institution name (not required for search, kept for compatibility)

        Returns:
            List of formatted trial dictionaries (all trials, regardless of status)
        """
        try:
            # Remove middle names/initials for search (e.g., "Sanjay J. Mathew" -> "Sanjay Mathew")
            # Split name into parts and take first and last
            name_parts = pi_name.strip().split()
            if len(name_parts) >= 2:
                # Take first and last name, ignore middle names/initials
                search_name = f"{name_parts[0]} {name_parts[-1]}"
            else:
                # If only one part, use as is
                search_name = pi_name

            logger.info(
                f"Searching for clinical trials with name: {search_name} (original: {pi_name})"
            )

            # Search for trials by PI name using advanced filter
            # Don't filter by status - return all trials so frontend can display them
            raw_trials = search_trials_by_pi_name_advanced(
                pi_name=search_name,
                limit=25,
                page_size=25,
                status_filter=None,  # Return all trials, not just active ones
            )

            if not raw_trials:
                logger.info(f"No clinical trials found for {search_name}")
                return []

            # Format trials
            formatted_trials = [format_trial_for_display(t) for t in raw_trials]

            # Show top 5 regardless of date, then only show additional items within past 7 years
            seven_years_ago = datetime.now() - timedelta(days=7 * 365)
            filtered_trials = []

            for idx, trial in enumerate(formatted_trials):
                # Always include first 5 items
                if idx < 5:
                    filtered_trials.append(trial)
                    continue

                # For items beyond top 5, only include if within past 7 years
                trial_date = None
                if trial.get("start_date"):
                    trial_date = _parse_trial_date(trial.get("start_date"))
                elif trial.get("completion_date"):
                    trial_date = _parse_trial_date(trial.get("completion_date"))

                # Include trial if date is within past 7 years or if no date available (to be safe)
                if not trial_date or trial_date >= seven_years_ago:
                    filtered_trials.append(trial)

            logger.info(
                f"Found {len(formatted_trials)} clinical trials for {search_name}, showing {len(filtered_trials)} (top 5 + recent)"
            )

            return filtered_trials

        except ClinicalTrialsAPIError:
            raise
        except Exception as e:
            logger.warning(
                f"Unexpected error fetching clinical trials: {e}", exc_info=True
            )
            return []  # Return empty list on error, don't fail entire process

    def get_pi_nih_projects(
        self, pi_name: str, institution: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get NIH-funded projects for a PI using the NIH Reporter API.

        Args:
            pi_name: PI's name (middle names/initials will be removed for search)
            institution: Optional institution name (not required for search, kept for compatibility)

        Returns:
            List of formatted project dictionaries
        """
        try:
            # Remove middle names/initials for search (e.g., "Sanjay J. Mathew" -> "Sanjay Mathew")
            # Split name into parts and take first and last
            name_parts = pi_name.strip().split()
            if len(name_parts) >= 2:
                # Take first and last name, ignore middle names/initials
                search_name = f"{name_parts[0]} {name_parts[-1]}"
            else:
                # If only one part, use as is
                search_name = pi_name

            logger.info(
                f"Searching for NIH projects with name: {search_name} (original: {pi_name})"
            )

            # Search for projects by PI name
            raw_projects = search_projects_by_pi_name(
                pi_name=search_name, limit=25, page_size=10
            )

            if not raw_projects:
                logger.info(f"No NIH projects found for {search_name}")
                return []

            # Format projects
            formatted_projects = [
                format_project_for_display(p, pi_name=search_name) for p in raw_projects
            ]

            # Show top 5 regardless of date, then only show additional items within past 7 years
            seven_years_ago = datetime.now() - timedelta(days=7 * 365)
            filtered_projects = []

            for idx, project in enumerate(formatted_projects):
                # Always include first 5 items
                if idx < 5:
                    filtered_projects.append(project)
                    continue

                # For items beyond top 5, only include if within past 7 years
                project_start_date = project.get("project_start_date")
                if project_start_date:
                    # Parse the date - it may be in various formats
                    try:
                        # Try parsing as YYYY-MM-DD or YYYY-MM
                        date_part = (
                            project_start_date.split("T")[0].strip()
                            if isinstance(project_start_date, str)
                            else str(project_start_date)
                        )
                        if len(date_part) == 10:
                            proj_date = datetime.strptime(date_part, "%Y-%m-%d")
                        elif len(date_part) == 7:
                            proj_date = datetime.strptime(date_part, "%Y-%m")
                        else:
                            proj_date = datetime.strptime(date_part, "%Y-%m-%d")

                        # Include project if start date is within past 7 years
                        if proj_date >= seven_years_ago:
                            filtered_projects.append(project)
                    except (ValueError, AttributeError):
                        # If date parsing fails, include the project to be safe
                        logger.debug(
                            f"Could not parse project_start_date: {project_start_date}, including project anyway"
                        )
                        filtered_projects.append(project)
                else:
                    # If no start date, include the project to be safe
                    filtered_projects.append(project)

            logger.info(
                f"Found {len(formatted_projects)} NIH projects for {search_name}, showing {len(filtered_projects)} (top 5 + recent)"
            )

            return filtered_projects

        except NIHReporterAPIError:
            raise
        except Exception as e:
            logger.warning(
                f"Unexpected error fetching NIH projects: {e}", exc_info=True
            )
            return []  # Return empty list on error, don't fail entire process

    def summarize_pi_research(
        self,
        author_data: Dict[str, Any],
        papers: List[Dict[str, Any]],
        user_interests: Optional[List[str]] = None,
        user_experiences: Optional[Dict[str, Any]] = None,
        include_clinical_trials: bool = True,
        include_nih_projects: bool = True,
        selected_papers: Optional[List[Dict[str, Any]]] = None,
        selected_trials: Optional[List[Dict[str, Any]]] = None,
        selected_nih_projects: Optional[List[Dict[str, Any]]] = None,
        summary_focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of PI's research.

        Args:
            author_data: Author data dictionary from OpenAlex
            papers: List of recent papers
            user_interests: Optional user research interests for trial alignment
            user_experiences: Optional user experience data for matching
            include_clinical_trials: Whether to fetch and include clinical trials
            include_nih_projects: Whether to fetch and include NIH projects
            selected_papers: Optional list of selected papers to use for summary
            selected_trials: Optional list of selected trials to use for summary
            selected_nih_projects: Optional list of selected NIH projects to use for summary
            summary_focus: Optional focus for summary (overview, methodology, findings, applications, trajectory, collaboration)

        Returns:
            Dictionary with PI info, papers, and optionally clinical trials and NIH projects
        """
        try:
            # Extract basic PI info
            name = author_data.get("display_name", "Unknown")
            openalex_id = author_data.get("id", "")

            # Get institution
            institution = None
            last_known_institution = author_data.get("last_known_institution")
            if last_known_institution:
                institution = last_known_institution.get("display_name")

            # Get ORCID
            orcid = None
            ids = author_data.get("ids", {})
            if "orcid" in ids:
                orcid = ids["orcid"]

            # Generate research summary
            concepts = author_data.get("x_concepts", [])
            concept_names = [c.get("display_name", "") for c in concepts[:5]]

            # Papers are already sorted by citations (highest first), then by year (most recent first)
            # Separate into top impactful papers and recent papers for balanced summary
            top_impactful_papers = [
                p for p in papers[:5] if (p.get("cited_by_count", 0) or 0) > 0
            ]
            recent_papers = sorted(
                papers, key=lambda p: (p.get("publication_year", 0) or 0), reverse=True
            )[:5]

            # Use selected papers if provided, otherwise use all papers
            papers_for_summary = (
                selected_papers if selected_papers is not None else papers
            )

            # Build papers summary with both impactful and recent papers
            prioritized_papers_text = ""
            if papers_for_summary:
                # Recalculate impactful and recent papers from selected papers if provided
                if selected_papers is not None:
                    # Re-sort selected papers by citations and date
                    sorted_by_citations = sorted(
                        papers_for_summary,
                        key=lambda p: (p.get("cited_by_count", 0) or 0),
                        reverse=True,
                    )
                    sorted_by_date = sorted(
                        papers_for_summary,
                        key=lambda p: (p.get("publication_year", 0) or 0),
                        reverse=True,
                    )
                    top_impactful_papers = sorted_by_citations[:3]
                    recent_papers = sorted_by_date[:3]

                # Include top impactful papers with citation counts
                impactful_list = []
                for p in top_impactful_papers[:3]:  # Top 3 most cited
                    title = p.get("title", "")
                    citations = p.get("cited_by_count", 0) or 0
                    year = p.get("publication_year", "")
                    if title:
                        impactful_list.append(
                            f"- {title} ({year}, {citations} citations)"
                        )

                # Include recent papers (if not already in impactful list)
                recent_list = []
                for p in recent_papers[:3]:  # Top 3 most recent
                    title = p.get("title", "")
                    year = p.get("publication_year", "")
                    citations = p.get("cited_by_count", 0) or 0
                    if title and title not in [
                        p.get("title", "") for p in top_impactful_papers[:3]
                    ]:
                        recent_list.append(f"- {title} ({year}, {citations} citations)")

                all_papers = impactful_list + recent_list
                prioritized_papers_text = "\n".join(
                    all_papers[:5]
                )  # Max 5 papers total

            # Fetch NIH projects early to include in summary prompt
            nih_projects = []
            if include_nih_projects:
                try:
                    if selected_nih_projects is not None:
                        nih_projects = selected_nih_projects
                    else:
                        nih_projects = self.get_pi_nih_projects(
                            pi_name=name, institution=institution
                        )
                        # Sort by fiscal year (descending) or project start date
                        nih_projects.sort(
                            key=lambda p: (
                                p.get("fiscal_year") or 0,
                                p.get("project_start_date") or "",
                            ),
                            reverse=True,
                        )
                except NIHReporterAPIError as e:
                    logger.warning(f"Could not fetch NIH projects: {e}")
                    nih_projects = []
                except Exception as e:
                    logger.warning(
                        f"Unexpected error fetching NIH projects: {e}", exc_info=True
                    )
                    nih_projects = []

            # Build NIH projects summary for prompt
            # NOTE: Clinical trials and NIH projects are included in the summary generation
            # to provide comprehensive context about the PI's research activities
            nih_projects_text = ""
            if nih_projects:
                nih_parts = []
                for project in nih_projects[:5]:  # Top 5 most recent
                    title = project.get("project_title", "")
                    fiscal_year = project.get("fiscal_year", "")
                    pref_terms = project.get("pref_terms", [])
                    phr_text = project.get("phr_text", "")
                    award_amount = project.get("award_amount", 0)

                    project_str = f"- {title}"
                    if fiscal_year:
                        project_str += f" (FY {fiscal_year})"
                    if award_amount:
                        project_str += f" - ${award_amount:,.0f}"
                    if pref_terms:
                        project_str += (
                            f"\n  Research Areas: {', '.join(pref_terms[:5])}"
                        )
                    if phr_text:
                        # Truncate PhrText to first 200 chars for prompt
                        phr_preview = (
                            phr_text[:200] + "..." if len(phr_text) > 200 else phr_text
                        )
                        project_str += f"\n  Abstract: {phr_preview}"

                    nih_parts.append(project_str)

                nih_projects_text = "\n".join(nih_parts)

            summary_prompt = f"""Summarize this researcher's research focus in exactly 150 words:

Name: {name}
Institution: {institution or "Unknown"}
Research Areas: {", ".join(concept_names) if concept_names else "Not specified"}
Key Papers (prioritized by impact and recency):
{prioritized_papers_text if prioritized_papers_text else "No papers"}
{
                f'''
NIH-Funded Projects:
{nih_projects_text}
'''
                if nih_projects_text
                else ""
            }

Requirements:
- Exactly 150 words (not less, not more)
- Prioritize the most impactful papers (highest citations) first, then incorporate recent work
- Balance discussion of their most cited work with their latest research contributions
- Weight the summary based on how impactful the top papers are - if they have very high citations, focus more on those
- Then move to broader research areas and general research focus
- Be concise and specific
- Create a balanced mix that highlights both their significant contributions and recent work"""

            try:
                research_summary = self.ai_client.generate_text(
                    prompt=summary_prompt, max_tokens=200, temperature=0.7
                )
            except AIGenerationError:
                # Fallback summary
                research_summary = f"{name} is a researcher at {institution or 'an unknown institution'}. "
                if concept_names:
                    research_summary += (
                        f"Their research focuses on {', '.join(concept_names[:3])}."
                    )
                else:
                    research_summary += "Research areas not specified."
            except Exception as e:
                logger.warning(
                    f"Unexpected error generating research summary: {e}", exc_info=True
                )
                # Fallback summary
                research_summary = f"{name} is a researcher at {institution or 'an unknown institution'}. "
                if concept_names:
                    research_summary += (
                        f"Their research focuses on {', '.join(concept_names[:3])}."
                    )
                else:
                    research_summary += "Research areas not specified."

            # Process papers with summaries - show top 5 regardless of date, then only show additional items within past 7 years
            current_year = datetime.now().year
            year_threshold = current_year - 7

            papers_with_summaries = []
            for idx, paper in enumerate(papers_for_summary):
                # Always include first 5 items
                should_include = idx < 5

                # For items beyond top 5, only include if within past 7 years
                if not should_include:
                    publication_year = paper.get("publication_year")
                    should_include = (
                        publication_year and publication_year >= year_threshold
                    ) or not publication_year

                if should_include:
                    paper_data = {
                        "title": paper.get("title", "Unknown Title"),
                        "year": paper.get("publication_year"),
                        "doi": None,
                        "url": None,
                        "abstract": paper.get("abstract", ""),
                        "summary": self.summarize_paper(paper),
                    }

                    # Get DOI
                    external_ids = paper.get("ids", {})
                    if "doi" in external_ids:
                        paper_data["doi"] = external_ids["doi"]

                    # Get primary URL
                    primary_location = paper.get("primary_location")
                    if primary_location:
                        paper_data["url"] = primary_location.get("landing_page_url")

                    papers_with_summaries.append(paper_data)

            # Use selected trials if provided, otherwise fetch new ones
            clinical_trials = []
            trial_alignment_summary = None
            if selected_trials is not None:
                # Use provided selected trials
                clinical_trials = selected_trials
            elif include_clinical_trials:
                try:
                    # Fetch clinical trials (all trials, regardless of status)
                    all_trials = self.get_pi_clinical_trials(
                        pi_name=name, institution=institution
                    )

                    # Filter to only active/ongoing trials for alignment analysis
                    active_statuses = [
                        "RECRUITING",
                        "ACTIVE_NOT_RECRUITING",
                        "ENROLLING_BY_INVITATION",
                    ]
                    active_trials = [
                        trial
                        for trial in all_trials
                        if trial.get("overall_status", "").upper() in active_statuses
                    ]

                    # Analyze alignment if user interests provided and we have active trials
                    if active_trials and user_interests:
                        clinical_trials = analyze_trial_alignment(
                            trials=active_trials,
                            user_interests=user_interests,
                            user_experiences=user_experiences,
                        )

                        # Sort by alignment_score (descending), then by start_date (most recent first)
                        clinical_trials.sort(
                            key=lambda t: (
                                t.get("alignment_score") or 0,
                                _parse_trial_date(t.get("start_date")),
                            ),
                            reverse=True,
                        )

                        # Generate alignment summary for top trials
                        top_trials = [
                            t
                            for t in clinical_trials[:3]
                            if t.get("alignment_score", 0) > 0.3
                        ]
                        if top_trials:
                            trial_titles = [t.get("title", "") for t in top_trials]
                            trial_nct_ids = [t.get("nct_id", "") for t in top_trials]
                            trial_alignment_summary = (
                                f"Top {len(top_trials)} aligned clinical trials: "
                                f"{', '.join([f'{t} ({n})' for t, n in zip(trial_titles[:3], trial_nct_ids[:3])])}"
                            )
                    else:
                        # If no alignment analysis needed, use all trials (not just active)
                        # Sort by start_date (most recent first)
                        all_trials.sort(
                            key=lambda t: _parse_trial_date(t.get("start_date")),
                            reverse=True,
                        )
                        clinical_trials = all_trials

                except ClinicalTrialsAPIError as e:
                    logger.warning(f"Could not fetch clinical trials: {e}")
                    # Continue without clinical trials
                    clinical_trials = []

            result = {
                "pi_info": {
                    "name": name,
                    "institution": institution,
                    "openalex_id": openalex_id,
                    "orcid": orcid,
                    "summary": research_summary.strip(),
                },
                "papers": papers_with_summaries,
            }

            # Add clinical trials if available
            if clinical_trials:
                result["clinical_trials"] = clinical_trials
                if trial_alignment_summary:
                    result["trial_alignment_summary"] = trial_alignment_summary

            # Add NIH projects if available
            if nih_projects:
                result["nih_projects"] = nih_projects

            return result

        except Exception as e:
            logger.error(f"Error summarizing PI research: {e}", exc_info=True)
            raise
