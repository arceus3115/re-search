"""
Unified Generator: Combines email and statement generation using user profile and PI research.
"""

import logging
import re
from typing import Dict, Any, Optional

from ..models.user_profile import UserProfile
from ..utils.ai_client import get_ai_client
from ..utils.exceptions import AIGenerationError

logger = logging.getLogger(__name__)


class UnifiedGenerator:
    """
    Unified generator for emails and statements using profile-based approach.
    """

    def __init__(self):
        """Initialize Unified Generator."""
        self.ai_client = get_ai_client()

    def generate_content(
        self,
        profile: UserProfile,
        pi_research_data: Dict[str, Any],
        format_type: str,
        user_draft: Optional[str] = None,
        word_count_target: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate content (email or statement) using profile and PI research.

        Args:
            profile: UserProfile object
            pi_research_data: PI research data from PIResearchGatherer
            format_type: "email" or "statement"
            user_draft: Optional draft text (for email)
            word_count_target: Target word count (for statement, default 375)

        Returns:
            Dictionary with generated content
        """
        if format_type == "email":
            return self._generate_email(
                profile, pi_research_data, user_draft, word_count_target
            )
        elif format_type == "statement":
            return self._generate_statement(
                profile, pi_research_data, word_count_target or 375
            )
        else:
            raise ValueError(
                f"Invalid format_type: {format_type}. Must be 'email' or 'statement'"
            )

    def _generate_email(
        self,
        profile: UserProfile,
        pi_research_data: Dict[str, Any],
        user_draft: Optional[str],
        word_count_target: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate intro email using profile and PI research.
        """
        logger.info(
            f"Generating email for {profile.name} to {pi_research_data['pi_info']['name']}"
        )

        # Extract PI info
        pi_info = pi_research_data["pi_info"]
        pi_name = pi_info["name"]
        pi_institution = pi_info.get("institution", "Unknown Institution")
        pi_research_summary = pi_info.get("summary", "")

        # Format user experiences from profile
        experiences = []
        if profile.cv_accomplishments:
            experiences.append(
                f"CV/Accomplishments: {profile.cv_accomplishments[:500]}..."
            )
        if profile.publications:
            pub_titles = [
                p.title or p.raw or ""
                for p in profile.publications[:5]
                if p.title or p.raw
            ]
            if pub_titles:
                experiences.append(f"Publications: {', '.join(pub_titles)}")
        if profile.presentations:
            experiences.append(f"Presentations: {', '.join(profile.presentations[:5])}")

        experiences_str = (
            "\n".join(f"- {exp}" for exp in experiences)
            if experiences
            else "None provided"
        )
        interests_str = (
            ", ".join(profile.research_interests)
            if profile.research_interests
            else "Not specified"
        )

        # Build prompt
        prompt = f"""You are helping write a professional introductory email to a professor for a {profile.program_type} program application.

User's Name: {profile.name}
User's draft (if provided): {user_draft or "None provided"}

User's experiences and accomplishments:
{experiences_str}

User's research interests: {interests_str}

PI Information:
- Name: {pi_name}
- Institution: {pi_institution}
- Research Summary: {pi_research_summary}

Recent Research Papers:
"""

        # Add recent papers context
        papers = pi_research_data.get("papers", [])[:5]
        for idx, paper in enumerate(papers, 1):
            prompt += (
                f"\n{idx}. {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')})"
            )
            if paper.get("summary"):
                prompt += f"\n   Summary: {paper.get('summary')}"

        # Add clinical trials context if available
        # NOTE: Clinical trials and NIH projects are used in email/statement generation
        # to provide context about the PI's current research activities
        clinical_trials = pi_research_data.get("clinical_trials", [])
        if clinical_trials:
            # Get top aligned trials (up to 3 for email - keep it concise)
            top_trials = sorted(
                clinical_trials,
                key=lambda t: t.get("alignment_score", 0.0),
                reverse=True,
            )[:3]

            if top_trials:
                prompt += "\n\nClinical Trials:"
                for idx, trial in enumerate(top_trials, 1):
                    nct_id = trial.get("nct_id", "")
                    title = trial.get("title", "")
                    conditions = trial.get("conditions", [])
                    phase = trial.get("phase", "")
                    overall_status = trial.get("overall_status", "")
                    alignment_score = trial.get("alignment_score", 0.0)

                    # Determine if trial is completed
                    is_completed = (
                        "COMPLETED" in overall_status.upper()
                        if overall_status
                        else False
                    )
                    status_note = (
                        " (COMPLETED - refer to as completed, not ongoing)"
                        if is_completed
                        else " (ONGOING)"
                    )

                    trial_str = f"\n{idx}. {title} (NCT ID: {nct_id}, Phase: {phase}, Status: {overall_status}{status_note}"
                    if alignment_score > 0:
                        trial_str += f", Alignment: {alignment_score:.2f}"
                    trial_str += ")"

                    if conditions:
                        trial_str += f"\n   Conditions: {', '.join(conditions[:3])}"

                    prompt += trial_str

        # Add NIH projects context if available
        nih_projects = pi_research_data.get("nih_projects", [])
        if nih_projects:
            # Get top projects (up to 2 for email - keep it concise)
            top_projects = sorted(
                nih_projects,
                key=lambda p: (p.get("fiscal_year") or 0, p.get("award_amount") or 0),
                reverse=True,
            )[:2]

            if top_projects:
                prompt += "\n\nNIH-Funded Projects:"
                for idx, project in enumerate(top_projects, 1):
                    title = project.get("project_title", "")
                    fiscal_year = project.get("fiscal_year", "")
                    pref_terms = project.get("pref_terms", [])
                    award_amount = project.get("award_amount", 0)

                    project_str = f"\n{idx}. {title}"
                    if fiscal_year:
                        project_str += f" (FY {fiscal_year})"
                    if award_amount:
                        project_str += f" - ${award_amount:,.0f}"
                    if pref_terms:
                        project_str += (
                            f"\n   Research Areas: {', '.join(pref_terms[:3])}"
                        )

                    prompt += project_str

        word_target = word_count_target or 300
        prompt += f"""

Requirements:
- Maximum 4 paragraphs
- Professional, concise tone
- Include relevant experiences and accomplishments from the user
- Reference specific research from the PI when relevant
- If clinical trials are mentioned, reference them naturally when they align with user's interests
- IMPORTANT: If a clinical trial status is "COMPLETED", refer to it as "completed" or "completed trial", NOT as "ongoing" or "active"
- If NIH-funded projects are mentioned, reference them to show awareness of their current funding and research areas
- Express genuine interest in their research and current work (including clinical trials and NIH projects if applicable)
- Request information on current work/projects
- Word count: ~{word_target} words (target: {word_target} words)
- Be specific about why you're interested in their lab and how your background aligns
- IMPORTANT: Do not mention or quote more than 3 people in the email. If referencing multiple collaborators, co-authors, or other researchers, limit to the 3 most relevant. Focus primarily on the PI and their work.

Generate the email in this format:
Subject: [email subject line]

Body:
[email body with 4 paragraphs maximum]
"""

        try:
            # Generate email using AI
            response = self.ai_client.generate_text(
                prompt=prompt, max_tokens=800, temperature=0.7
            )

            # Parse response
            email_data = self._parse_email_response(response)

            # Verify word count and paragraph count
            body_word_count = len(email_data["body"].split())
            if body_word_count > 400:
                logger.warning(
                    f"Email body is {body_word_count} words, may need trimming"
                )

            paragraphs = [
                p.strip() for p in email_data["body"].split("\n\n") if p.strip()
            ]
            if len(paragraphs) > 4:
                logger.warning(
                    f"Email has {len(paragraphs)} paragraphs, should be max 4"
                )
                email_data["body"] = "\n\n".join(paragraphs[:4])

            # Check for excessive people mentions (limit to 3)
            # Count mentions of people by looking for patterns like "Dr. X", "Professor Y", "X and Y", etc.
            body_text = email_data["body"]
            # Simple heuristic: count occurrences of "Dr.", "Professor", "Prof.", and "and" patterns
            # This is a rough estimate - we're looking for names that might indicate multiple people
            # Count "Dr." or "Professor" or "Prof." followed by a name pattern
            title_patterns = len(
                re.findall(
                    r"\b(?:Dr\.|Professor|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?",
                    body_text,
                )
            )
            # Count "and" between capitalized words (likely names)
            and_patterns = len(
                re.findall(r"\b[A-Z][a-z]+\s+and\s+[A-Z][a-z]+", body_text)
            )
            # Rough estimate: if we have many title patterns or and patterns, we might have too many mentions
            estimated_mentions = (
                max(title_patterns, and_patterns // 2)
                if and_patterns > 0
                else title_patterns
            )

            if estimated_mentions > 3:
                logger.warning(
                    f"Email may mention more than 3 people (estimated {estimated_mentions} mentions). Regenerating with stricter limit."
                )
                # Regenerate with a more explicit instruction
                prompt_retry = prompt.replace(
                    "- IMPORTANT: Do not mention or quote more than 3 people",
                    "- CRITICAL: Mention ONLY the PI (the professor you're emailing). Do NOT mention any other researchers, collaborators, or co-authors. Focus exclusively on the PI and their work.",
                )
                response = self.ai_client.generate_text(
                    prompt=prompt_retry, max_tokens=800, temperature=0.7
                )
                email_data = self._parse_email_response(response)
                # Re-verify paragraph count
                paragraphs = [
                    p.strip() for p in email_data["body"].split("\n\n") if p.strip()
                ]
                if len(paragraphs) > 4:
                    email_data["body"] = "\n\n".join(paragraphs[:4])

            email_data["word_count"] = len(email_data["body"].split())
            logger.info(f"Generated email with {email_data['word_count']} words")

            return email_data

        except Exception as e:
            logger.error(f"Error generating email: {e}", exc_info=True)
            raise AIGenerationError(f"Failed to generate email: {e}") from e

    def _generate_statement(
        self,
        profile: UserProfile,
        pi_research_data: Dict[str, Any],
        word_count_target: int,
    ) -> Dict[str, Any]:
        """
        Generate statement of interest using profile and PI research.
        """
        logger.info(
            f"Generating statement for {profile.name} about {pi_research_data['pi_info']['name']}"
        )

        # Extract PI info
        pi_info = pi_research_data["pi_info"]
        pi_name = pi_info["name"]
        pi_research_summary = pi_info.get("summary", "")

        # Format user experiences
        experiences = []
        if profile.cv_accomplishments:
            experiences.append(
                f"CV/Accomplishments: {profile.cv_accomplishments[:500]}..."
            )
        if profile.publications:
            pub_titles = [
                p.title or p.raw or ""
                for p in profile.publications[:5]
                if p.title or p.raw
            ]
            if pub_titles:
                experiences.append(f"Publications: {', '.join(pub_titles)}")
        if profile.presentations:
            experiences.append(f"Presentations: {', '.join(profile.presentations[:5])}")

        experiences_str = (
            "\n".join(f"- {exp}" for exp in experiences)
            if experiences
            else "None provided"
        )
        interests_str = (
            ", ".join(profile.research_interests)
            if profile.research_interests
            else "Not specified"
        )

        # Format papers summary
        papers = pi_research_data.get("papers", [])[:5]
        papers_summary_parts = []
        cited_paper_titles = []
        for idx, paper in enumerate(papers, 1):
            title = paper.get("title", "Unknown")
            year = paper.get("year", "")
            papers_summary_parts.append(f"{idx}. {title} ({year})")
            cited_paper_titles.append(title)

            # Add summary if available
            if paper.get("summary"):
                papers_summary_parts[-1] += f"\n   {paper.get('summary')}"

            # Add brief abstract if available
            abstract = paper.get("abstract", "")
            if abstract and len(abstract) > 200:
                abstract_preview = abstract[:200] + "..."
                papers_summary_parts[-1] += f"\n   Abstract excerpt: {abstract_preview}"

        papers_summary = (
            "\n".join(papers_summary_parts)
            if papers_summary_parts
            else "No recent papers provided"
        )

        # Format clinical trials if available
        clinical_trials = pi_research_data.get("clinical_trials", [])
        formatted_trials = ""
        if clinical_trials:
            # Get top aligned trials (up to 5)
            top_trials = sorted(
                clinical_trials,
                key=lambda t: t.get("alignment_score", 0.0),
                reverse=True,
            )[:5]

            trial_parts = []
            for idx, trial in enumerate(top_trials, 1):
                nct_id = trial.get("nct_id", "")
                title = trial.get("title", "")
                conditions = trial.get("conditions", [])
                phase = trial.get("phase", "")
                overall_status = trial.get("overall_status", "")
                brief_summary = trial.get("brief_summary", "")
                alignment_score = trial.get("alignment_score", 0.0)
                key_themes = trial.get("key_themes", [])
                experience_matches = trial.get("user_experience_matches", [])

                # Determine if trial is completed
                is_completed = (
                    "COMPLETED" in overall_status.upper() if overall_status else False
                )
                status_note = (
                    " (COMPLETED - refer to as completed, not ongoing)"
                    if is_completed
                    else " (ONGOING)"
                )

                trial_str = f"{idx}. Trial {nct_id}: {title} (Phase: {phase}, Status: {overall_status}{status_note}, Alignment: {alignment_score:.2f})"

                if conditions:
                    trial_str += f"\n   Conditions: {', '.join(conditions[:5])}"

                if brief_summary:
                    summary_preview = (
                        brief_summary[:300] + "..."
                        if len(brief_summary) > 300
                        else brief_summary
                    )
                    trial_str += f"\n   Summary: {summary_preview}"

                if key_themes:
                    trial_str += f"\n   Key Themes: {', '.join(key_themes[:5])}"

                if experience_matches:
                    trial_str += f"\n   Relevant User Experiences: {', '.join(experience_matches[:3])}"

                trial_parts.append(trial_str)

            formatted_trials = "\n\n".join(trial_parts)

        # Format NIH projects if available
        nih_projects = pi_research_data.get("nih_projects", [])
        formatted_nih_projects = ""
        if nih_projects:
            # Get top projects (up to 5)
            top_projects = sorted(
                nih_projects,
                key=lambda p: (p.get("fiscal_year") or 0, p.get("award_amount") or 0),
                reverse=True,
            )[:5]

            project_parts = []
            for idx, project in enumerate(top_projects, 1):
                title = project.get("project_title", "")
                fiscal_year = project.get("fiscal_year", "")
                pref_terms = project.get("pref_terms", [])
                phr_text = project.get("phr_text", "")
                award_amount = project.get("award_amount", 0)
                activity_code = project.get("activity_code", "")

                project_str = f"{idx}. {title}"
                if fiscal_year:
                    project_str += f" (FY {fiscal_year})"
                if award_amount:
                    project_str += f" - ${award_amount:,.0f}"
                if activity_code:
                    project_str += f" [{activity_code}]"

                if pref_terms:
                    project_str += f"\n   Research Areas: {', '.join(pref_terms[:5])}"

                if phr_text:
                    phr_preview = (
                        phr_text[:300] + "..." if len(phr_text) > 300 else phr_text
                    )
                    project_str += f"\n   Abstract: {phr_preview}"

                project_parts.append(project_str)

            formatted_nih_projects = "\n\n".join(project_parts)

        # Build enhanced prompt with clinical trials
        if formatted_trials:
            # Build alignment section with clinical trials
            alignment_section = "1. ALIGNMENT: Top interests/alignment of clinical trials with user's research interests\n"
            alignment_section += f"   - PI's Clinical Trials:\n   {formatted_trials}\n"
            alignment_section += f"   - User's Research Interests: {interests_str}\n"
            alignment_section += "   - Identify the top 2-3 most aligned clinical trials and explain how they align with the user's interests\n"
            alignment_section += (
                "   - Reference specific trial NCT IDs, conditions, and phases\n"
            )
            alignment_section += "   - IMPORTANT: If a trial status is marked as COMPLETED, refer to it as 'completed' or 'completed trial', NOT as 'ongoing' or 'active'\n"

            # Build connection section
            connection_section = (
                "2. CONNECTION: How user's experiences can be tied to clinical trials\n"
            )
            connection_section += f"   - User's Experiences: {experiences_str}\n"
            connection_section += "   - Connect specific user experiences to conditions, interventions, or methodologies in the PI's clinical trials\n"
            connection_section += "   - Provide concrete examples showing how the user's background applies to clinical work\n"
            connection_section += "   - IMPORTANT: If referencing completed trials, use past tense and refer to them as completed, not ongoing\n"

            # Build building on section
            building_section = "3. BUILDING ON: How to contribute to clinical trials\n"
            building_section += "   - For ongoing trials: Suggest specific ways to contribute to or participate in active clinical trials\n"
            building_section += "   - For completed trials: Reference them as completed work and discuss how to build upon their findings or methodologies\n"
            building_section += (
                "   - Reference specific trial NCT IDs, conditions, and phases\n"
            )
            building_section += (
                "   - Show a clear research trajectory in clinical domains\n"
            )

            # Add NIH projects section if available
            nih_section = ""
            if formatted_nih_projects:
                nih_section = "\n\n4. NIH FUNDING: PI's Current NIH-Funded Projects\n"
                nih_section += f"   - PI's NIH Projects:\n   {formatted_nih_projects}\n"
                nih_section += "   - Reference specific projects, research areas (PrefTerms), and funding amounts\n"
                nih_section += "   - Show awareness of their current funding priorities and research directions\n"

            prompt = f"""Generate a statement of interest that demonstrates:

{alignment_section}

{connection_section}

{building_section}{nih_section}

User's Name: {profile.name}
PI Information:
- Name: {pi_name}
- Research Summary: {pi_research_summary}

PI's Recent Papers:
{papers_summary}

Requirements:
- {word_count_target} words (target range: 250-500 words)
- Academic, research-focused tone
- Mention specific clinical trial NCT IDs, conditions, and phases (if available)
- IMPORTANT: If a clinical trial status is "COMPLETED", refer to it as "completed" or "completed trial", NOT as "ongoing" or "active"
- Reference NIH-funded projects, research areas (PrefTerms), and funding amounts (if available)
- Show deep understanding of PI's research program including clinical trials and NIH funding
- Demonstrate clear research trajectory and fit in clinical domains
- Structure: Opening (50-75 words), Alignment (100-150 words), Connection (100-150 words), Building On (100-150 words){", NIH Funding (50-75 words)" if formatted_nih_projects else ""}, Closing (25-50 words)

Generate a well-structured statement that demonstrates your fit with their research program.
"""
        else:
            # Fallback to original prompt if no clinical trials
            # But still include NIH projects if available
            nih_context = ""
            if formatted_nih_projects:
                nih_context = (
                    f"\n\nPI's NIH-Funded Projects:\n{formatted_nih_projects}\n"
                )

            prompt = f"""You are helping write a statement of interest paragraph for a {profile.program_type} program application.

User's Name: {profile.name}
User's experiences and accomplishments:
{experiences_str}

User's research interests: {interests_str}

PI Information:
- Name: {pi_name}
- Research Summary: {pi_research_summary}

PI's Recent Papers:
{papers_summary}{nih_context}

Requirements:
- {word_count_target} words (target range: 250-500 words)
- Academic, research-focused tone
- Analyze PI's recent research (mention specific papers, methods, or findings when relevant)
- Reference NIH-funded projects and research areas (PrefTerms) if available
- Show clear connection between user's experiences and PI's work
- Demonstrate understanding of synergy and collaboration potential
- Show you've done your homework on their research
- Reference specific research interests and how they align

Generate a single, well-structured paragraph that demonstrates your fit with their research program.
"""

        try:
            # Generate statement using AI
            response = self.ai_client.generate_text(
                prompt=prompt, max_tokens=1200, temperature=0.7
            )

            statement = response.strip()

            # Verify word count
            word_count = len(statement.split())

            if word_count < 250:
                logger.warning(
                    f"Statement is only {word_count} words, below 250 minimum"
                )
            elif word_count > 500:
                logger.warning(f"Statement is {word_count} words, above 500 maximum")

            logger.info(f"Generated statement with {word_count} words")

            return {
                "statement": statement,
                "word_count": word_count,
                "cited_papers": cited_paper_titles,
            }

        except Exception as e:
            logger.error(f"Error generating statement: {e}", exc_info=True)
            raise AIGenerationError(f"Failed to generate statement: {e}") from e

    def enhance_draft(
        self,
        current_draft: str,
        format_type: str,
        profile: Optional[UserProfile] = None,
        pi_research_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Enhance a draft by analyzing weaknesses and generating improvements.

        Args:
            current_draft: Current draft text to enhance
            format_type: "email" or "statement"
            profile: Optional user profile for context
            pi_research_data: Optional PI research data for context

        Returns:
            Dictionary with enhanced_draft, feedback, quality_score, and improvements
        """
        try:
            # Analyze current draft
            analysis_prompt = f"""Analyze this {format_type} draft and identify:
1. Weaknesses (generic statements, missing specifics, unclear connections)
2. Missing elements (specific project references, concrete examples, clear research trajectory)
3. Areas for improvement (tone, structure, clarity, specificity)

Current Draft:
{current_draft}

Provide a structured analysis in JSON format:
{{
    "weaknesses": ["weakness1", "weakness2"],
    "missing_elements": ["element1", "element2"],
    "improvement_areas": ["area1", "area2"],
    "quality_score": 0.0-1.0,
    "specific_suggestions": ["suggestion1", "suggestion2"]
}}"""

            analysis_result = self.ai_client.generate_text(
                prompt=analysis_prompt, max_tokens=500, temperature=0.3
            )

            # Extract analysis (try to parse JSON, fallback to text)
            import json

            try:
                # Try to extract JSON from response
                json_match = re.search(r"\{[^{}]*\}", analysis_result, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    # Fallback: create basic analysis
                    analysis = {
                        "weaknesses": ["Generic statements detected"],
                        "missing_elements": ["Specific project references"],
                        "improvement_areas": ["Clarity and specificity"],
                        "quality_score": 0.6,
                        "specific_suggestions": [
                            "Add specific examples",
                            "Reference concrete projects",
                        ],
                    }
            except (json.JSONDecodeError, AttributeError):
                analysis = {
                    "weaknesses": ["Could not parse analysis"],
                    "missing_elements": [],
                    "improvement_areas": [],
                    "quality_score": 0.5,
                    "specific_suggestions": [],
                }

            # Generate enhanced version
            enhancement_context = ""
            if profile:
                interests_str = (
                    ", ".join(profile.research_interests)
                    if profile.research_interests
                    else "Not specified"
                )
                enhancement_context += f"\nUser's Research Interests: {interests_str}\n"

            if pi_research_data:
                pi_name = pi_research_data.get("pi_info", {}).get("name", "")
                enhancement_context += f"\nPI Name: {pi_name}\n"
                pi_summary = pi_research_data.get("pi_info", {}).get("summary", "")
                if pi_summary:
                    enhancement_context += (
                        f"PI Research Summary: {pi_summary[:300]}...\n"
                    )

            enhancement_prompt = f"""Enhance this {format_type} draft by addressing the identified weaknesses and incorporating improvements.

Current Draft:
{current_draft}

Analysis:
- Weaknesses: {", ".join(analysis.get("weaknesses", []))}
- Missing Elements: {", ".join(analysis.get("missing_elements", []))}
- Improvement Areas: {", ".join(analysis.get("improvement_areas", []))}
- Specific Suggestions: {", ".join(analysis.get("specific_suggestions", []))}
{enhancement_context}

Requirements:
- Maintain the same format ({format_type})
- Address all identified weaknesses
- Add missing elements where appropriate
- Improve clarity, specificity, and impact
- Keep the same general structure and length
- Make improvements concrete and actionable

Generate an enhanced version of the draft:"""

            enhanced_draft = self.ai_client.generate_text(
                prompt=enhancement_prompt, max_tokens=1000, temperature=0.7
            )

            return {
                "enhanced_draft": enhanced_draft.strip(),
                "feedback": {
                    "weaknesses": analysis.get("weaknesses", []),
                    "missing_elements": analysis.get("missing_elements", []),
                    "improvement_areas": analysis.get("improvement_areas", []),
                    "specific_suggestions": analysis.get("specific_suggestions", []),
                },
                "quality_score": analysis.get("quality_score", 0.5),
                "improvements": {
                    "summary": f"Enhanced draft addresses {len(analysis.get('weaknesses', []))} weaknesses and adds {len(analysis.get('missing_elements', []))} missing elements."
                },
            }

        except Exception as e:
            logger.error(f"Error enhancing draft: {e}", exc_info=True)
            raise AIGenerationError(f"Failed to enhance draft: {e}") from e

    def _parse_email_response(self, response: str) -> Dict[str, str]:
        """
        Parse AI response to extract subject and body.

        Expected format:
        Subject: [subject line]

        Body:
        [paragraph 1]

        [paragraph 2]
        ...
        """
        # Try to extract subject
        subject_match = re.search(r"Subject:\s*(.+?)(?:\n|$)", response, re.IGNORECASE)
        subject = (
            subject_match.group(1).strip()
            if subject_match
            else "Inquiry about PhD Program Opportunities"
        )

        # Extract body (everything after "Body:" or after subject)
        body_match = re.search(r"Body:\s*(.+?)$", response, re.IGNORECASE | re.DOTALL)
        if body_match:
            body = body_match.group(1).strip()
        else:
            # If no "Body:" marker, take everything after subject
            if subject_match:
                body = response[subject_match.end() :].strip()
            else:
                body = response.strip()

        # Clean up body (remove extra whitespace)
        body = re.sub(r"\n{3,}", "\n\n", body)  # Max 2 newlines in a row
        body = body.strip()

        return {"subject": subject, "body": body}
