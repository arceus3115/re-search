"""
Profile Analyzer: Analyzes user profiles for strength assessment and program fit.
"""

import logging
import json
import re
from typing import Dict, Any, Optional

from ..models.user_profile import UserProfile
from ..utils.ai_client import get_ai_client
from ..utils.exceptions import AIGenerationError

logger = logging.getLogger(__name__)


class ProfileAnalyzer:
    """
    Analyzes user profiles to assess strength, program fit, and provide recommendations.
    """

    def __init__(self):
        """Initialize Profile Analyzer."""
        self.ai_client = get_ai_client()

    def analyze_profile(
        self,
        profile: UserProfile,
        program_id: Optional[str] = None,
        program_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze user profile for strength assessment and program fit.

        Args:
            profile: UserProfile object to analyze
            program_id: Optional program identifier (for program-specific analysis)
            program_info: Optional program information dict (name, requirements, focus areas, etc.)

        Returns:
            Dictionary with:
            - fit_score: float (0.0-1.0) - Overall fit score
            - strengths: List[str] - Identified strengths
            - weaknesses: List[str] - Identified weaknesses
            - recommendations: List[str] - Actionable improvement recommendations
            - competitiveness: str - Competitiveness assessment (e.g., "Highly Competitive", "Competitive", "Moderate", "Needs Improvement")
            - gap_analysis: Dict[str, Any] - Missing elements and gaps
            - detailed_scores: Dict[str, float] - Scores for different aspects (publications, research, GPA, etc.)

        Raises:
            AIGenerationError: If AI analysis fails
        """
        try:
            # Build profile summary
            profile_summary = self._build_profile_summary(profile)

            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(
                profile_summary, program_id, program_info
            )

            # Generate analysis
            analysis_result = self.ai_client.generate_text(
                prompt=analysis_prompt, max_tokens=1500, temperature=0.3
            )

            # Parse analysis result
            analysis = self._parse_analysis(analysis_result)

            # Calculate fit score if program info provided
            if program_info:
                analysis["fit_score"] = self._calculate_fit_score(
                    analysis, program_info
                )
            else:
                analysis["fit_score"] = analysis.get(
                    "fit_score", 0.7
                )  # Default general fit score

            # Ensure all required fields are present
            result = {
                "fit_score": analysis.get("fit_score", 0.7),
                "strengths": analysis.get("strengths", []),
                "weaknesses": analysis.get("weaknesses", []),
                "recommendations": analysis.get("recommendations", []),
                "competitiveness": analysis.get("competitiveness", "Moderate"),
                "gap_analysis": analysis.get("gap_analysis", {}),
                "detailed_scores": analysis.get("detailed_scores", {}),
                "program_id": program_id,
            }

            logger.info(
                f"Profile analysis completed for user: {profile.name}, fit_score: {result['fit_score']:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing profile: {e}", exc_info=True)
            raise AIGenerationError(f"Failed to analyze profile: {e}") from e

    def _build_profile_summary(self, profile: UserProfile) -> str:
        """Build a text summary of the user profile for analysis."""
        summary_parts = []

        summary_parts.append(f"Name: {profile.name}")
        summary_parts.append(f"Program Type: {profile.program_type}")

        if profile.research_interests:
            summary_parts.append(
                f"Research Interests: {', '.join(profile.research_interests)}"
            )

        if profile.connected_pis:
            pi_names = [pi.name for pi in profile.connected_pis]
            summary_parts.append(f"Connected PIs: {', '.join(pi_names)}")
            # Add relationship context if available
            for pi in profile.connected_pis:
                if pi.relationship_type or pi.relationship_notes:
                    rel_info = f"  - {pi.name}: {pi.relationship_type or 'Connected'}"
                    if pi.relationship_notes:
                        rel_info += f" ({pi.relationship_notes})"
                    summary_parts.append(rel_info)

        if profile.publications:
            summary_parts.append(f"\nPublications ({len(profile.publications)}):")
            for pub in profile.publications[:10]:  # Limit to first 10 for summary
                pub_str = f"  - {pub.title or pub.raw or 'Untitled'}"
                if pub.publication_year:
                    pub_str += f" ({pub.publication_year})"
                if pub.venue:
                    pub_str += f" - {pub.venue}"
                if pub.citation_count:
                    pub_str += f" ({pub.citation_count} citations)"
                summary_parts.append(pub_str)
            if len(profile.publications) > 10:
                summary_parts.append(f"  ... and {len(profile.publications) - 10} more")

        if profile.presentations:
            summary_parts.append(f"\nPresentations ({len(profile.presentations)}):")
            for pres in profile.presentations[:5]:  # Limit to first 5
                summary_parts.append(f"  - {pres}")
            if len(profile.presentations) > 5:
                summary_parts.append(f"  ... and {len(profile.presentations) - 5} more")

        if profile.cv_accomplishments:
            summary_parts.append("\nCV/Accomplishments (Full Text):")
            # Include full CV text (limit to 8000 chars to stay within token limits, but include much more than before)
            cv_text = (
                profile.cv_accomplishments[:8000]
                if len(profile.cv_accomplishments) > 8000
                else profile.cv_accomplishments
            )
            summary_parts.append(cv_text)
            if len(profile.cv_accomplishments) > 8000:
                summary_parts.append(
                    f"\n  ... (truncated, showing first 8000 of {len(profile.cv_accomplishments)} characters)"
                )
            logger.info(
                f"Including CV text in analysis: {len(cv_text)} characters (of {len(profile.cv_accomplishments)} total)"
            )
        else:
            logger.warning("No CV/accomplishments text found in profile for analysis")

        return "\n".join(summary_parts)

    def _build_analysis_prompt(
        self,
        profile_summary: str,
        program_id: Optional[str],
        program_info: Optional[Dict[str, Any]],
    ) -> str:
        """Build the analysis prompt for Gemini."""
        prompt_parts = []

        prompt_parts.append(
            "Analyze this user profile for graduate program application strength and provide a comprehensive assessment."
        )
        prompt_parts.append("\nUser Profile:")
        prompt_parts.append(profile_summary)

        if program_info:
            prompt_parts.append("\nTarget Program Information:")
            if program_info.get("name"):
                prompt_parts.append(f"Program Name: {program_info['name']}")
            if program_info.get("requirements"):
                prompt_parts.append(f"Requirements: {program_info['requirements']}")
            if program_info.get("focus_areas"):
                prompt_parts.append(
                    f"Focus Areas: {', '.join(program_info['focus_areas']) if isinstance(program_info['focus_areas'], list) else program_info['focus_areas']}"
                )
            if program_info.get("description"):
                prompt_parts.append(f"Description: {program_info['description']}")

        prompt_parts.append("""
Provide a comprehensive analysis in JSON format with the following structure:
{
    "fit_score": 0.0-1.0,  // Overall fit score (0.0 = poor fit, 1.0 = excellent fit)
    "strengths": ["strength1", "strength2", ...],  // List of identified strengths
    "weaknesses": ["weakness1", "weakness2", ...],  // List of identified weaknesses
    "recommendations": ["recommendation1", "recommendation2", ...],  // Actionable improvement suggestions
    "competitiveness": "Highly Competitive" | "Competitive" | "Moderate" | "Needs Improvement",  // Overall competitiveness assessment
    "gap_analysis": {
        "missing_elements": ["element1", "element2", ...],  // Missing elements that would strengthen application
        "areas_for_improvement": ["area1", "area2", ...]  // Areas that need improvement
    },
    "detailed_scores": {
        "publications": 0.0-1.0,  // Score for publication record
        "research_experience": 0.0-1.0,  // Score for research experience
        "academic_performance": 0.0-1.0,  // Score for GPA/academic performance (if available)
        "connections": 0.0-1.0,  // Score for PI connections and networking
        "presentations": 0.0-1.0,  // Score for presentation experience
        "overall_preparation": 0.0-1.0  // Overall preparation score
    }
}

Focus on:
1. Research experience and publications quality/quantity
2. Alignment with program focus and requirements
3. PI connections and networking
4. Academic performance indicators (if available)
5. Presentation and communication skills
6. Overall profile completeness and competitiveness

Provide specific, actionable feedback.
""")

        return "\n".join(prompt_parts)

    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse the AI-generated analysis text into structured data."""
        try:
            # Try to extract JSON from response
            json_match = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", analysis_text, re.DOTALL
            )
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                # Fallback: create basic analysis structure
                logger.warning("Could not parse JSON from analysis, using fallback")
                return {
                    "fit_score": 0.7,
                    "strengths": ["Profile analysis completed"],
                    "weaknesses": ["Could not parse detailed analysis"],
                    "recommendations": ["Review profile data"],
                    "competitiveness": "Moderate",
                    "gap_analysis": {
                        "missing_elements": [],
                        "areas_for_improvement": [],
                    },
                    "detailed_scores": {},
                }
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"JSON parsing error: {e}, using fallback")
            return {
                "fit_score": 0.7,
                "strengths": ["Profile analysis completed"],
                "weaknesses": ["Analysis parsing error"],
                "recommendations": ["Review profile data"],
                "competitiveness": "Moderate",
                "gap_analysis": {"missing_elements": [], "areas_for_improvement": []},
                "detailed_scores": {},
            }

    def _calculate_fit_score(
        self, analysis: Dict[str, Any], program_info: Dict[str, Any]
    ) -> float:
        """
        Calculate program-specific fit score based on analysis and program info.

        This is a simple implementation - can be enhanced with more sophisticated scoring.
        """
        # Use the fit_score from analysis if available
        base_score = analysis.get("fit_score", 0.7)

        # Adjust based on detailed scores if available
        detailed_scores = analysis.get("detailed_scores", {})
        if detailed_scores:
            # Weighted average of detailed scores
            weights = {
                "publications": 0.25,
                "research_experience": 0.25,
                "academic_performance": 0.20,
                "connections": 0.15,
                "presentations": 0.10,
                "overall_preparation": 0.05,
            }

            weighted_sum = 0.0
            total_weight = 0.0

            for key, weight in weights.items():
                if key in detailed_scores:
                    weighted_sum += detailed_scores[key] * weight
                    total_weight += weight

            if total_weight > 0:
                calculated_score = weighted_sum / total_weight
                # Average with base score
                return (base_score + calculated_score) / 2.0

        return base_score
