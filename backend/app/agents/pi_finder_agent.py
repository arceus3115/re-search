"""
PI Finder Agent: Finds PIs at accredited Clinical Psychology programs
matching user specialties and techniques.
"""

import logging
from typing import List, Dict, Any, Optional

from ..utils.program_loader import load_all_accredited_programs
from ..utils import openalex_client
from ..pi_finder.status_checker import check_phd_student_status
from ..pi_finder.faculty_discovery import _find_institution_id
from ..models.pi_candidate import PI_Candidate
from ..utils.exceptions import OpenAlexAPIError

logger = logging.getLogger(__name__)

# Technique keyword mappings
TECHNIQUE_KEYWORDS = {
    "mri": [
        "mri",
        "magnetic resonance imaging",
        "fmri",
        "functional mri",
        "neuroimaging",
        "structural mri",
    ],
    "fmri": [
        "fmri",
        "functional mri",
        "functional magnetic resonance imaging",
        "bold",
        "brain imaging",
    ],
    "eeg": [
        "eeg",
        "electroencephalography",
        "electroencephalogram",
        "brain waves",
        "electrophysiology",
    ],
    "fnirs": [
        "fnirs",
        "f nirs",
        "functional near-infrared spectroscopy",
        "near-infrared",
    ],
    "pet": ["pet", "positron emission tomography", "pet scan"],
    "meg": ["meg", "magnetoencephalography", "magnetoencephalogram"],
    "tms": ["tms", "transcranial magnetic stimulation"],
    "eye tracking": ["eye tracking", "eye-tracking", "gaze", "pupillometry"],
    "behavioral": ["behavioral", "behavioral assessment", "behavioral tasks"],
    "cognitive testing": [
        "cognitive testing",
        "cognitive assessment",
        "neuropsychological testing",
    ],
}


class PIFinderAgent:
    """
    Agent for finding PIs matching user's research specialties and techniques.
    Uses web scraping and Google search to find faculty at accredited programs.
    """

    def __init__(self):
        """Initialize PI Finder Agent."""
        pass

    async def find_pis(
        self,
        specialties: List[str],
        techniques: List[str] = None,
        country_filter: Optional[str] = None,
    ) -> List[PI_Candidate]:
        """
        Find PIs at accredited programs matching specialties and techniques.

        Process:
        1. Load accredited Clinical Psychology programs
        2. For each program:
           a. Search for faculty via Google search (institution + clinical psychology + faculty)
           b. Match specialties and techniques in their research
           c. Verify acceptance status via web scraping
           d. Rank by relevance

        Args:
            specialties: List of research specialties (e.g., ["memory", "trauma"])
            techniques: List of techniques used (e.g., ["MRI", "EEG"])
            country_filter: Optional country code filter

        Returns:
            List of PI_Candidate objects ranked by relevance
        """
        if not specialties:
            logger.warning("No specialties provided for PI search")
            return []

        techniques = techniques or []
        logger.info(
            f"PI Finder Agent: Searching for PIs with specialties={specialties}, techniques={techniques}"
        )

        # 1. Load accredited programs
        programs = load_all_accredited_programs()
        logger.info(f"Loaded {len(programs)} accredited programs")

        all_candidates = []

        # 2. Process each program
        for idx, program in enumerate(programs):
            if idx % 10 == 0:
                logger.info(
                    f"Processing program {idx + 1}/{len(programs)}: {program.get('university', 'Unknown')}"
                )

            try:
                university_name = program.get(
                    "university", program.get("program_name", "Unknown")
                )
                program_website = program.get("website", "")

                if not program_website or program_website == "N/A":
                    continue

                # a. Search for faculty via Google search
                faculty = await self._search_faculty_google(
                    university_name=university_name,
                    program_website=program_website,
                    specialties=specialties,
                )

                if not faculty:
                    continue

                logger.info(
                    f"Found {len(faculty)} potential faculty for {university_name}"
                )

                # b. Match specialties and techniques, verify acceptance
                for faculty_member in faculty:
                    candidate = await self._process_faculty_member(
                        faculty_member=faculty_member,
                        program=program,
                        specialties=specialties,
                        techniques=techniques,
                        country_filter=country_filter,
                    )

                    if candidate:
                        all_candidates.append(candidate)

            except Exception as e:
                logger.warning(
                    f"Error processing program {program.get('university', 'Unknown')}: {e}"
                )
                continue

        # Rank candidates by relevance
        ranked = self._rank_candidates(all_candidates, specialties, techniques)
        logger.info(f"PI Finder Agent: Found {len(ranked)} total candidates")

        return ranked

    async def _search_faculty_google(
        self, university_name: str, program_website: str, specialties: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search for Clinical Psychology faculty using OpenAlex.

        Strategy:
        Use OpenAlex to find authors at institution matching specialties
        """
        faculty_list = []
        seen_names = set()

        # Use OpenAlex to find faculty
        try:
            # Find institution ID in OpenAlex
            institution_id = _find_institution_id(university_name, program_website)
            if institution_id:
                # Search for authors with clinical psychology at this institution
                authors = openalex_client.find_faculty_at_institution(
                    institution_id=institution_id,
                    field_concepts=["clinical psychology", "psychology"],
                    limit=50,
                )

                # Filter authors by specialty match (basic check)
                for author in authors:
                    author_name = author.get("display_name", "")
                    if not author_name:
                        continue

                    # Skip if already found via Playwright
                    if author_name.lower() in seen_names:
                        continue

                    author_concepts = [
                        c.get("display_name", "").lower()
                        for c in author.get("x_concepts", [])
                    ]
                    author_research_text = " ".join(author_concepts).lower()

                    # Check if any specialty matches
                    specialty_match = any(
                        specialty.lower() in author_research_text
                        for specialty in specialties
                    )

                    # Include if specialty matches or if we have few results
                    if specialty_match or len(faculty_list) < 20:
                        seen_names.add(author_name.lower())
                        faculty_list.append(
                            {
                                "name": author_name,
                                "openalex_id": author.get("id"),
                                "institution": university_name,
                                "email": author.get("email"),
                                "source": "openalex",
                                "research_interests": [
                                    c.get("display_name")
                                    for c in author.get("x_concepts", [])[:5]
                                    if c.get("display_name")
                                ],
                            }
                        )
        except Exception as e:
            logger.debug(f"Error in OpenAlex search for {university_name}: {e}")

        logger.info(f"Found {len(faculty_list)} total faculty for {university_name}")
        return faculty_list

    async def _process_faculty_member(
        self,
        faculty_member: Dict[str, Any],
        program: Dict[str, Any],
        specialties: List[str],
        techniques: List[str],
        country_filter: Optional[str],
    ) -> Optional[PI_Candidate]:
        """
        Process a faculty member: match specialties/techniques, verify acceptance.

        Returns PI_Candidate if relevant, None otherwise.
        """
        faculty_name = faculty_member.get("name", "")
        if not faculty_name:
            return None

        program_website = program.get("website", "")

        # Get full author data from OpenAlex if available
        openalex_id = faculty_member.get("openalex_id")
        author_data = None
        if openalex_id:
            author_data = openalex_client.get_author_details(openalex_id)

        # Match specialties and techniques
        specialty_match = self._match_specialties(
            faculty_member, specialties, author_data
        )
        technique_match = (
            self._match_techniques(faculty_member, techniques, author_data)
            if techniques
            else {"has_match": True, "score": 1.0}
        )

        # Both specialties AND techniques must match (if techniques provided)
        if techniques and not technique_match.get("has_match"):
            return None

        if not specialty_match.get("has_match"):
            return None

        # Verify acceptance status
        status_info = check_phd_student_status(
            institution_homepage=program_website,
            author_name=faculty_name,
            author_data=author_data or faculty_member,
            research_interests=specialties,
        )

        # Get institution/country info
        country = None
        institution_id = ""
        if author_data:
            institutions = author_data.get("last_known_institutions", [])
            if institutions:
                inst = institutions[0]
                institution_id = inst.get("id", "")
                if inst.get("id"):
                    try:
                        inst_meta = openalex_client.get_institution_metadata(
                            inst.get("id").split("/")[-1]
                        )
                        country = inst_meta.get("country_code") if inst_meta else None
                    except (OpenAlexAPIError, Exception) as e:
                        logger.debug(f"Could not fetch institution metadata: {e}")
                        pass

        # Filter by country
        if country_filter and country:
            if country.upper() != country_filter.upper():
                return None

        # Calculate relevance score
        relevance_score = (
            specialty_match.get("score", 0.0) * 0.6
            + technique_match.get("score", 0.0) * 0.4
        ) * 100

        # Boost if accepting students
        if status_info.get("acceptance_status") == "yes":
            relevance_score += 20

        # Build topics list
        topics = specialty_match.get("matched_specialties", [])
        if author_data:
            author_concepts = [
                c.get("display_name") for c in author_data.get("x_concepts", [])[:5]
            ]
            topics.extend([t for t in author_concepts if t not in topics])

        if not topics:
            topics = ["Clinical Psychology"]

        # Create PI_Candidate
        candidate = PI_Candidate(
            name=faculty_name,
            openalex_id=openalex_id or "",
            institution=program.get("university", ""),
            institution_id=institution_id,
            institution_homepage=program_website,
            relevance_score=relevance_score,
            topics=topics[:5],
            email=faculty_member.get("email")
            or (author_data.get("email") if author_data else None),
            accepting_phd_students=status_info.get("acceptance_status") == "yes",
            research_description=status_info.get("research_description"),
            lab_goals=status_info.get("lab_goals"),
            acceptance_status=status_info.get("acceptance_status", "unknown"),
            acceptance_confidence=status_info.get("acceptance_confidence", 0.0),
            personal_homepage=status_info.get("personal_homepage"),
            recent_publications_count=author_data.get("works_count", 0)
            if author_data
            else 0,
            country=country,
            page_topic_matches=status_info.get("topic_matches", {}).get(
                "matched_topics", []
            ),
        )

        return candidate

    def _match_specialties(
        self,
        faculty_data: Dict[str, Any],
        specialties: List[str],
        author_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Match faculty specialties with user specialties.

        Returns: {
            "has_match": bool,
            "score": float (0.0-1.0),
            "matched_specialties": List[str]
        }
        """
        matched = []
        score = 0.0

        # Check research interests from faculty data
        research_interests = faculty_data.get("research_interests", [])
        research_text = " ".join([r.lower() for r in research_interests])

        # Check author concepts if available
        if author_data:
            author_concepts = author_data.get("x_concepts", [])
            concept_names = [c.get("display_name", "").lower() for c in author_concepts]
            research_text += " " + " ".join(concept_names)

        # Match each specialty
        for specialty in specialties:
            specialty_lower = specialty.lower()
            if specialty_lower in research_text:
                matched.append(specialty)
                score += 1.0
            # Also check for related terms
            elif any(
                term in research_text
                for term in [
                    specialty_lower + " ",
                    specialty_lower + ",",
                    specialty_lower + ".",
                ]
            ):
                matched.append(specialty)
                score += 0.8

        # Normalize score
        if specialties:
            score = score / len(specialties)

        return {
            "has_match": len(matched) > 0,
            "score": min(score, 1.0),
            "matched_specialties": matched,
        }

    def _match_techniques(
        self,
        faculty_data: Dict[str, Any],
        techniques: List[str],
        author_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Match faculty techniques with user techniques.

        Checks:
        1. Recent papers for technique keywords
        2. Lab website for technique mentions
        3. OpenAlex work concepts related to techniques

        Returns: {
            "has_match": bool,
            "score": float (0.0-1.0),
            "matched_techniques": List[str]
        }
        """
        matched = []
        score = 0.0

        if not techniques:
            return {"has_match": True, "score": 1.0, "matched_techniques": []}

        # Get technique keywords for each technique
        all_technique_keywords = []
        technique_mapping = {}
        for tech in techniques:
            tech_lower = tech.lower()
            keywords = TECHNIQUE_KEYWORDS.get(tech_lower, [tech_lower])
            all_technique_keywords.extend(keywords)
            technique_mapping[tech_lower] = keywords

        # Check recent papers if author_data available
        papers_text = ""
        if author_data:
            openalex_id = author_data.get("id")
            if openalex_id:
                try:
                    works = openalex_client.get_author_works(openalex_id, per_page=20)
                    for work in works[:10]:  # Check top 10 papers
                        title = work.get("title", "").lower()
                        abstract = (
                            work.get("abstract", "").lower()
                            if work.get("abstract")
                            else ""
                        )
                        papers_text += " " + title + " " + abstract

                        # Check concepts for technique-related terms
                        concepts = work.get("concepts", [])
                        for concept in concepts:
                            concept_name = concept.get("display_name", "").lower()
                            papers_text += " " + concept_name
                except (OpenAlexAPIError, Exception) as e:
                    logger.debug(
                        f"Error fetching author works for technique matching: {e}"
                    )
                    pass

        # Check research interests
        research_interests = faculty_data.get("research_interests", [])
        research_text = " ".join([r.lower() for r in research_interests])

        # Combine all text to search
        all_text = (papers_text + " " + research_text).lower()

        # Match techniques
        for tech in techniques:
            tech_lower = tech.lower()
            keywords = technique_mapping.get(tech_lower, [tech_lower])

            # Check if any keyword appears
            if any(keyword in all_text for keyword in keywords):
                matched.append(tech)
                score += 1.0

        # Normalize score
        if techniques:
            score = score / len(techniques)

        return {
            "has_match": len(matched) > 0,
            "score": min(score, 1.0),
            "matched_techniques": matched,
        }

    def _rank_candidates(
        self,
        candidates: List[PI_Candidate],
        specialties: List[str],
        techniques: List[str],
    ) -> List[PI_Candidate]:
        """
        Rank candidates by relevance.

        Factors:
        1. Acceptance status (yes > unknown > no)
        2. Specialty match score
        3. Technique match score
        4. Publication count
        """
        # Candidates already have relevance_score from _process_faculty_member
        # Additional ranking: boost accepting students
        for candidate in candidates:
            if candidate.accepting_phd_students:
                candidate.relevance_score += 30
            elif candidate.acceptance_status == "no":
                candidate.relevance_score -= 20

        # Sort by relevance score
        ranked = sorted(candidates, key=lambda x: x.relevance_score, reverse=True)
        return ranked
