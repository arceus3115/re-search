"""
CV Parser for extracting connected PIs and presentations from CV text.
Uses AI to parse APA-style citations and extract relevant information.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional

from .ai_client import get_ai_client
from .exceptions import AIGenerationError

logger = logging.getLogger(__name__)


class CVParser:
    """
    Parser for extracting structured information from CV text.
    """

    def __init__(self):
        """Initialize CV parser with AI client."""
        self.ai_client = get_ai_client()

    def extract_connected_pis(self, cv_text: str) -> List[Dict[str, Any]]:
        """
        Extract connected PI names from CV text by analyzing papers and presentations.

        Looks for author names in APA-style citations and presentation entries.
        Authors are considered connected PIs if they appear in the user's publications
        or presentations.

        Args:
            cv_text: Raw CV text content

        Returns:
            List of dictionaries with PI information:
            [
                {
                    "name": str,
                    "institution": Optional[str],
                    "relationship_type": Optional[str]  # e.g., "co-author", "collaborator"
                },
                ...
            ]
        """
        if not cv_text or not cv_text.strip():
            return []

        try:
            prompt = f"""Analyze this CV text and extract all unique author names (Principal Investigators, co-authors, collaborators)
from publications and presentations. Focus on identifying people who are likely PIs, mentors, or collaborators.

CV Text:
{cv_text[:8000]}  # Limit to avoid token limits

Instructions:
1. Extract all unique author names from APA-style citations in publications
2. Extract presenter/author names from presentation entries
3. Handle name formats:
   - "LastName, FirstName" (e.g., "Smith, John")
   - "FirstName LastName" (e.g., "John Smith")
   - "LastName, FirstName MiddleInitial" (e.g., "Smith, John A.")
   - "FirstName MiddleInitial LastName" (e.g., "John A. Smith")
4. For each person, try to identify their institution if mentioned
5. Determine relationship type: "co-author", "collaborator", "mentor", "advisor", or "colleague"
6. Exclude the CV owner's name (if you can identify it)
7. Prioritize names that appear multiple times or in recent publications

Return a JSON array of objects with this structure:
[
    {{
        "name": "Full Name (standardized as FirstName LastName)",
        "institution": "Institution name if found, else null",
        "relationship_type": "co-author|collaborator|mentor|advisor|colleague"
    }},
    ...
]

Only include people who are clearly PIs, mentors, or research collaborators.
Exclude generic names or names that appear only once without context.
Return an empty array if no clear PIs/collaborators are found.
Format your response as valid JSON only, no additional text."""

            response = self.ai_client.generate_text(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more consistent extraction
            )

            # Parse JSON response
            pis = self._parse_json_response(response, "connected PIs")

            # Validate and normalize PI data
            validated_pis = []
            seen_names = set()

            for pi in pis:
                if not isinstance(pi, dict):
                    continue

                name = pi.get("name", "").strip()
                if not name or len(name) < 3:
                    continue

                # Normalize name to avoid duplicates
                normalized_name = self._normalize_name(name)
                if normalized_name in seen_names:
                    continue
                seen_names.add(normalized_name)

                validated_pis.append(
                    {
                        "name": name,
                        "institution": pi.get("institution") or None,
                        "relationship_type": pi.get("relationship_type")
                        or "collaborator",
                    }
                )

            logger.info(f"Extracted {len(validated_pis)} connected PIs from CV")
            return validated_pis

        except AIGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error extracting connected PIs from CV: {e}", exc_info=True)
            # Return empty list on error rather than failing
            return []

    def extract_presentations(self, cv_text: str) -> List[str]:
        """
        Extract presentation entries from CV text.

        Looks for sections like "Presentations", "Conference Presentations",
        "Talks", "Posters", etc. and extracts individual presentation entries.

        Args:
            cv_text: Raw CV text content

        Returns:
            List of presentation strings (one per presentation)
        """
        if not cv_text or not cv_text.strip():
            return []

        try:
            prompt = f"""Analyze this CV text and extract all presentation entries.

CV Text:
{cv_text[:8000]}  # Limit to avoid token limits

Instructions:
1. Look for sections titled: "Presentations", "Conference Presentations", "Talks",
   "Posters", "Invited Talks", "Conference Talks", "Symposia", etc.
2. Extract each individual presentation entry
3. Include the full presentation information (title, conference, date, location if available)
4. Preserve APA-style formatting if present
5. Each entry should be a complete, standalone description

Return a JSON array of strings, where each string is one presentation entry:
[
    "Presentation title, Conference Name, Date, Location",
    "Another presentation entry...",
    ...
]

If no presentations are found, return an empty array.
Format your response as valid JSON only, no additional text."""

            response = self.ai_client.generate_text(
                prompt=prompt, max_tokens=2000, temperature=0.3
            )

            # Parse JSON response
            presentations = self._parse_json_response(response, "presentations")

            # Validate and clean presentation strings
            validated_presentations = []
            for pres in presentations:
                if isinstance(pres, str):
                    pres_clean = pres.strip()
                    if pres_clean and len(pres_clean) > 10:  # Minimum length check
                        validated_presentations.append(pres_clean)
                elif isinstance(pres, dict):
                    # If AI returns structured data, try to reconstruct string
                    title = pres.get("title", "")
                    conference = pres.get("conference", "")
                    date = pres.get("date", "")
                    parts = [p for p in [title, conference, date] if p]
                    if parts:
                        validated_presentations.append(", ".join(parts))

            logger.info(
                f"Extracted {len(validated_presentations)} presentations from CV"
            )
            return validated_presentations

        except AIGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error extracting presentations from CV: {e}", exc_info=True)
            # Return empty list on error rather than failing
            return []

    def extract_publications(self, cv_text: str) -> List[Dict[str, Any]]:
        """
        Extract publication entries from CV text.

        This is optional - publications may already be provided separately.
        This method can be used to auto-populate publications if needed.

        Args:
            cv_text: Raw CV text content

        Returns:
            List of publication dictionaries with title, authors, year, etc.
        """
        if not cv_text or not cv_text.strip():
            return []

        try:
            prompt = f"""Analyze this CV text and extract all publication entries in APA format.

CV Text:
{cv_text[:8000]}  # Limit to avoid token limits

Instructions:
1. Look for sections titled: "Publications", "Peer-Reviewed Publications",
   "Journal Articles", "Papers", "Research Publications", etc.
2. Extract each publication in APA citation format
3. Parse each citation to extract: title, authors, year, journal/venue, DOI if available

Return a JSON array of objects:
[
    {{
        "title": "Publication title",
        "authors": ["Author1", "Author2", ...],
        "year": 2023,
        "venue": "Journal or Conference name",
        "doi": "DOI if available, else null",
        "raw": "Full APA citation string"
    }},
    ...
]

If no publications are found, return an empty array.
Format your response as valid JSON only, no additional text."""

            response = self.ai_client.generate_text(
                prompt=prompt, max_tokens=3000, temperature=0.3
            )

            # Parse JSON response
            publications = self._parse_json_response(response, "publications")

            # Validate publication data
            validated_publications = []
            for pub in publications:
                if not isinstance(pub, dict):
                    continue

                # At minimum, need a title or raw citation
                if pub.get("title") or pub.get("raw"):
                    validated_publications.append(
                        {
                            "title": pub.get("title"),
                            "authors": pub.get("authors", []),
                            "year": pub.get("year"),
                            "venue": pub.get("venue"),
                            "doi": pub.get("doi"),
                            "raw": pub.get("raw"),
                        }
                    )

            logger.info(f"Extracted {len(validated_publications)} publications from CV")
            return validated_publications

        except AIGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error extracting publications from CV: {e}", exc_info=True)
            return []

    def _parse_json_response(self, response: str, data_type: str) -> List[Any]:
        """
        Parse JSON response from AI, handling various formats.

        Args:
            response: Raw AI response text
            data_type: Type of data being parsed (for error messages)

        Returns:
            Parsed list (or empty list if parsing fails)
        """
        if not response or not response.strip():
            return []

        # Try to extract JSON from response (may have markdown code blocks or extra text)
        response_clean = response.strip()

        # Remove markdown code blocks if present
        if response_clean.startswith("```"):
            # Extract content between ```json and ```
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_clean, re.DOTALL)
            if match:
                response_clean = match.group(1).strip()
        elif response_clean.startswith("```"):
            # Just ``` without json
            response_clean = re.sub(r"^```\s*", "", response_clean)
            response_clean = re.sub(r"\s*```$", "", response_clean)

        # Try to find JSON array in the response
        json_match = re.search(r"\[.*\]", response_clean, re.DOTALL)
        if json_match:
            response_clean = json_match.group(0)

        try:
            parsed = json.loads(response_clean)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "results" in parsed:
                return parsed["results"]
            elif isinstance(parsed, dict) and "data" in parsed:
                return parsed["data"]
            else:
                logger.warning(
                    f"Unexpected JSON structure for {data_type}: {type(parsed)}"
                )
                return []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {data_type} JSON response: {e}")
            logger.debug(f"Response text: {response_clean[:500]}")
            return []

    def _normalize_name(self, name: str) -> str:
        """
        Normalize a name for duplicate detection.

        Args:
            name: Name string

        Returns:
            Normalized name (lowercase, punctuation removed)
        """
        if not name:
            return ""

        # Convert to lowercase, remove punctuation, normalize spaces
        normalized = name.lower().strip()
        normalized = re.sub(r"[^\w\s]", "", normalized)  # Remove punctuation
        normalized = re.sub(r"\s+", " ", normalized)  # Normalize whitespace
        return normalized


# Singleton instance
_cv_parser: Optional[CVParser] = None


def get_cv_parser() -> CVParser:
    """Get or create singleton CV parser instance."""
    global _cv_parser
    if _cv_parser is None:
        _cv_parser = CVParser()
    return _cv_parser
