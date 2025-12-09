"""
Trial alignment analyzer for matching clinical trials with user interests.
"""

import logging
from typing import List, Dict, Any, Optional
import re

from ..utils.ai_client import get_ai_client
from ..utils.exceptions import AIGenerationError

logger = logging.getLogger(__name__)


def calculate_trial_alignment_score(
    trial: Dict[str, Any], user_interests: List[str], use_ai: bool = True
) -> float:
    """
    Calculate alignment score between a clinical trial and user interests.

    Args:
        trial: Trial dictionary (formatted from ClinicalTrials.gov)
        user_interests: List of user's research interests
        use_ai: Whether to use AI for semantic similarity (default: True)

    Returns:
        Alignment score between 0.0 and 1.0
    """
    if not user_interests:
        return 0.0

    # Extract text from trial
    title = trial.get("title", "").lower()
    brief_summary = (
        trial.get("brief_summary", "").lower() if trial.get("brief_summary") else ""
    )
    detailed_description = (
        trial.get("detailed_description", "").lower()
        if trial.get("detailed_description")
        else ""
    )
    conditions = [c.lower() for c in trial.get("conditions", [])]
    interventions = []
    for interv in trial.get("interventions", []):
        if isinstance(interv, dict):
            interventions.append(interv.get("name", "").lower())
            if interv.get("description"):
                interventions.append(interv.get("description", "").lower())
        else:
            interventions.append(str(interv).lower())

    trial_text = f"{title} {brief_summary} {detailed_description} {' '.join(conditions)} {' '.join(interventions)}"

    # Keyword matching (40% weight)
    keyword_matches = 0
    for interest in user_interests:
        interest_lower = interest.lower()
        # Check for exact matches and partial matches
        if interest_lower in trial_text:
            keyword_matches += 1
        # Also check for word boundaries
        elif re.search(rf"\b{re.escape(interest_lower)}\b", trial_text):
            keyword_matches += 1

    keyword_score = keyword_matches / len(user_interests) if user_interests else 0.0
    keyword_score = min(keyword_score, 1.0)  # Cap at 1.0

    # Semantic similarity using AI (40% weight)
    semantic_score = 0.0
    if use_ai and (brief_summary or detailed_description):
        try:
            ai_client = get_ai_client()
            summary_text = (
                brief_summary[:500]
                if brief_summary
                else detailed_description[:500]
                if detailed_description
                else ""
            )

            prompt = f"""Rate the alignment between these research interests and this clinical trial on a scale of 0.0 to 1.0.

User's Research Interests: {", ".join(user_interests)}

Trial Title: {trial.get("title", "")}
Trial Conditions: {", ".join(conditions[:5])}
Trial Summary: {summary_text}

Respond with only a number between 0.0 and 1.0 representing the alignment score."""

            response = ai_client.generate_text(
                prompt=prompt, max_tokens=10, temperature=0.3
            )

            # Extract number from response
            try:
                semantic_score = float(response.strip())
                semantic_score = max(0.0, min(1.0, semantic_score))  # Clamp to [0, 1]
            except ValueError:
                logger.warning(
                    f"Could not parse semantic score from AI response: {response}"
                )
                semantic_score = 0.0
        except (AIGenerationError, Exception) as e:
            logger.debug(f"AI semantic analysis failed, using keyword score only: {e}")
            semantic_score = 0.0

    # Trial status (10% weight) - active/recruiting trials are more relevant
    status = trial.get("overall_status", "").upper()
    status_score = 0.0
    if "RECRUITING" in status:
        status_score = 1.0
    elif "ACTIVE_NOT_RECRUITING" in status or "ENROLLING_BY_INVITATION" in status:
        status_score = 0.8
    elif "ACTIVE" in status:
        status_score = 0.6
    elif "COMPLETED" in status:
        status_score = 0.4
    else:
        status_score = 0.2

    # Trial phase (10% weight) - later phases indicate more established research
    phase = trial.get("phase", "").upper()
    phase_score = 0.0
    if (
        "PHASE 3" in phase
        or "PHASE III" in phase
        or "PHASE 4" in phase
        or "PHASE IV" in phase
    ):
        phase_score = 1.0
    elif "PHASE 2" in phase or "PHASE II" in phase:
        phase_score = 0.8
    elif "PHASE 1" in phase or "PHASE I" in phase:
        phase_score = 0.6
    elif "EARLY PHASE 1" in phase:
        phase_score = 0.4
    else:
        phase_score = 0.5  # Unknown phase gets middle score

    # Weighted combination
    final_score = (
        keyword_score * 0.4
        + semantic_score * 0.4
        + status_score * 0.1
        + phase_score * 0.1
    )

    return round(final_score, 3)


def extract_trial_themes(trial: Dict[str, Any]) -> List[str]:
    """
    Extract key research themes from a clinical trial.

    Args:
        trial: Trial dictionary

    Returns:
        List of key themes
    """
    themes = []

    # Use conditions as primary themes
    conditions = trial.get("conditions", [])
    if conditions:
        themes.extend(conditions[:5])  # Top 5 conditions

    # Extract from interventions
    interventions = trial.get("interventions", [])
    for interv in interventions[:3]:  # Top 3 interventions
        if isinstance(interv, dict):
            interv_name = interv.get("name", "")
            if interv_name:
                themes.append(interv_name)
        else:
            themes.append(str(interv))

    # Extract from title (simple keyword extraction)
    title = trial.get("title", "")
    if title:
        # Simple approach: use significant words from title
        words = title.split()
        # Filter out common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "study",
            "trial",
            "clinical",
        }
        significant_words = [
            w.lower() for w in words if w.lower() not in stop_words and len(w) > 3
        ]
        themes.extend(significant_words[:3])

    return list(set(themes))[:5]  # Remove duplicates, limit to 5


def match_user_experiences_to_trials(
    user_experiences: Dict[str, Any], trials: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Match user experiences to relevant clinical trials.

    Args:
        user_experiences: Dictionary with user experience data (CV, publications, etc.)
        trials: List of trial dictionaries

    Returns:
        List of trials with matched experiences added
    """
    # Extract experience keywords
    experience_text = ""
    if user_experiences.get("cv_accomplishments"):
        experience_text += user_experiences["cv_accomplishments"].lower() + " "
    if user_experiences.get("publications"):
        for pub in user_experiences["publications"][:5]:
            if isinstance(pub, dict):
                experience_text += (
                    pub.get("title", "") or pub.get("raw", "")
                ).lower() + " "
            else:
                experience_text += str(pub).lower() + " "
    if user_experiences.get("presentations"):
        experience_text += " ".join(user_experiences["presentations"][:5]).lower() + " "

    # Match experiences to each trial
    for trial in trials:
        matches = []
        trial_text = (
            trial.get("title", "")
            + " "
            + (trial.get("brief_summary", "") or "")
            + " "
            + " ".join(trial.get("conditions", []))
        ).lower()

        # Look for common clinical methodologies/techniques
        clinical_methods = [
            "cbt",
            "cognitive behavioral therapy",
            "dbt",
            "dialectical behavior therapy",
            "exposure therapy",
            "mindfulness",
            "clinical assessment",
            "diagnostic",
            "treatment",
            "intervention",
            "therapy",
            "psychotherapy",
            "clinical trial",
        ]
        for method in clinical_methods:
            if method.lower() in experience_text and method.lower() in trial_text:
                matches.append(f"{method} experience")

        # Look for condition matches
        conditions = trial.get("conditions", [])
        for condition in conditions:
            if condition.lower() in experience_text:
                matches.append(f"Experience with {condition}")

        # Look for research area matches
        if user_experiences.get("research_interests"):
            for interest in user_experiences["research_interests"]:
                if interest.lower() in trial_text:
                    matches.append(f"Research in {interest}")

        trial["user_experience_matches"] = list(set(matches))[
            :5
        ]  # Remove duplicates, limit to 5

    return trials


def identify_trial_contribution_opportunities(
    trials: List[Dict[str, Any]], user_interests: List[str]
) -> List[str]:
    """
    Identify opportunities to contribute to clinical trials.

    Args:
        trials: List of trial dictionaries
        user_interests: User's research interests

    Returns:
        List of contribution opportunity descriptions
    """
    opportunities = []

    # Analyze top trials for contribution opportunities
    top_trials = sorted(
        trials, key=lambda t: t.get("alignment_score", 0.0), reverse=True
    )[:3]

    for trial in top_trials:
        title = trial.get("title", "")
        conditions = trial.get("conditions", [])
        status = trial.get("overall_status", "")

        if not title:
            continue

        # Use AI to identify contribution opportunities
        try:
            ai_client = get_ai_client()
            prompt = f"""Based on this clinical trial, suggest 1-2 specific ways a researcher with interests in {", ".join(user_interests)} could contribute to or participate in this trial.

Trial Title: {title}
Conditions: {", ".join(conditions[:5])}
Status: {status}
Phase: {trial.get("phase", "Unknown")}

Provide 1-2 brief, specific suggestions (one sentence each) for how to contribute to this trial."""

            response = ai_client.generate_text(
                prompt=prompt, max_tokens=150, temperature=0.7
            )

            # Split into individual opportunities
            opps = [
                o.strip()
                for o in response.split("\n")
                if o.strip() and not o.strip().startswith("#")
            ]
            opportunities.extend(opps[:2])  # Max 2 per trial

        except (AIGenerationError, Exception) as e:
            logger.debug(
                f"Could not generate contribution opportunities for trial: {e}"
            )
            # Fallback: generic opportunity
            if conditions:
                opportunities.append(
                    f"Contribute to {title} by working with {conditions[0]} patients"
                )

    return opportunities[:5]  # Limit to top 5


def analyze_trial_alignment(
    trials: List[Dict[str, Any]],
    user_interests: List[str],
    user_experiences: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Analyze and score trials for alignment with user interests.

    Args:
        trials: List of trial dictionaries
        user_interests: User's research interests
        user_experiences: Optional user experience data

    Returns:
        List of trials with alignment scores and analysis added
    """
    if not trials:
        return []

    # Calculate alignment scores
    for trial in trials:
        trial["alignment_score"] = calculate_trial_alignment_score(
            trial, user_interests
        )
        trial["key_themes"] = extract_trial_themes(trial)

    # Match user experiences if provided
    if user_experiences:
        trials = match_user_experiences_to_trials(user_experiences, trials)

    # Sort by alignment score (descending), then by status (active trials first)
    def sort_key(t):
        score = t.get("alignment_score", 0.0)
        status = t.get("overall_status", "").upper()
        # Boost active/recruiting trials
        status_boost = 0.1 if "RECRUITING" in status or "ACTIVE" in status else 0.0
        return score + status_boost

    trials = sorted(trials, key=sort_key, reverse=True)

    return trials
