import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
import re
import time


def find_faculty_directory_url(institution_homepage: str) -> Optional[str]:
    """
    Try to find the faculty directory URL from an institution homepage.
    Common patterns: /faculty, /people, /directory, /staff
    """
    if not institution_homepage:
        return None

    potential_paths = [
        "/faculty",
        "/people",
        "/directory",
        "/staff",
        "/about/faculty",
        "/academics/faculty",
        "/department/faculty",
    ]

    for path in potential_paths:
        try:
            url = urljoin(institution_homepage.rstrip("/"), path)
            response = requests.get(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                # Check if the page contains faculty-related content
                soup = BeautifulSoup(response.text, "html.parser")
                text = soup.get_text().lower()
                if any(
                    keyword in text
                    for keyword in ["faculty", "professor", "directory", "staff"]
                ):
                    return url
        except Exception:
            continue

    return None


def extract_domain_and_base(url: str) -> tuple:
    """Extract domain and base URL from a full URL."""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc
    return domain, base_url


def construct_personal_page_urls(
    author_name: str, institution_homepage: str
) -> List[str]:
    """
    Construct potential personal page URLs based on common patterns.
    """
    urls = []
    if not institution_homepage or not author_name:
        return urls

    domain, base_url = extract_domain_and_base(institution_homepage)

    # Extract potential username from author name (first initial + last name)
    name_parts = author_name.lower().split()
    if len(name_parts) >= 2:
        first_initial = name_parts[0][0]
        last_name = name_parts[-1]
        username_variants = [
            f"{first_initial}{last_name}",
            f"{name_parts[0]}{last_name}",
            f"{first_initial}.{last_name}",
            f"{name_parts[0]}.{last_name}",
            last_name,
        ]
    else:
        username_variants = [name_parts[0] if name_parts else ""]

    # Common URL patterns
    patterns = [
        "/~{username}",
        "/people/{username}",
        "/faculty/{username}",
        "/directory/{username}",
        "/faculty/{name}",
        "/people/{name}",
        "/~{name}",
    ]

    for username in username_variants:
        for pattern in patterns:
            if "{username}" in pattern:
                urls.append(urljoin(base_url, pattern.format(username=username)))
            elif "{name}" in pattern:
                # Use last name for name-based patterns
                if len(name_parts) >= 2:
                    urls.append(urljoin(base_url, pattern.format(name=name_parts[-1])))

    return urls


def search_page_for_author_name(
    page_url: str, author_name: str, timeout: int = 5
) -> bool:
    """
    Check if a page contains the author's name.
    """
    try:
        response = requests.get(page_url, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            return False

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()

        # Try exact match and variations
        name_variants = [
            author_name,
            author_name.lower(),
            author_name.upper(),
        ]
        # Also try first name + last name combinations
        name_parts = author_name.split()
        if len(name_parts) >= 2:
            name_variants.append(f"{name_parts[0]} {name_parts[-1]}")
            name_variants.append(f"{name_parts[0][0]}. {name_parts[-1]}")
            name_variants.append(f"{name_parts[-1]}, {name_parts[0]}")

        for variant in name_variants:
            if variant in text:
                return True
        return False
    except Exception:
        return False


def find_personal_homepage_from_openalex(author_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract personal homepage URL from OpenAlex author metadata.
    """
    if not author_data:
        return None

    # Check for homepage_url in author data
    homepage = author_data.get("homepage_url")
    if homepage:
        return homepage

    # Check for ORCID which might have profile page
    orcid = author_data.get("orcid")
    if orcid:
        return f"https://orcid.org/{orcid.replace('https://orcid.org/', '')}"

    return None


def discover_professor_urls(
    author_name: str, author_data: Dict[str, Any], institution_homepage: str
) -> Dict[str, Optional[str]]:
    """
    Discover professor's personal/university page URLs using multiple strategies.

    Returns a dictionary with:
    - 'personal_homepage': Personal homepage URL (if found)
    - 'university_page': University faculty directory page (if found)
    - 'best_match': Best URL to use for scraping (personal homepage preferred)
    """
    result = {"personal_homepage": None, "university_page": None, "best_match": None}

    # Strategy 1: Check OpenAlex author metadata for personal homepage
    personal_homepage = find_personal_homepage_from_openalex(author_data)
    if personal_homepage:
        result["personal_homepage"] = personal_homepage
        result["best_match"] = personal_homepage
        return result

    # Strategy 2: Try to find faculty directory
    faculty_dir_url = find_faculty_directory_url(institution_homepage)
    if faculty_dir_url:
        result["university_page"] = faculty_dir_url

    # Strategy 3: Try constructed URL patterns
    potential_urls = construct_personal_page_urls(author_name, institution_homepage)

    # Also add faculty directory if found
    if faculty_dir_url:
        potential_urls.append(faculty_dir_url)

    # Test each URL to see if it contains the author's name
    for url in potential_urls[:10]:  # Limit to first 10 to avoid too many requests
        if search_page_for_author_name(url, author_name):
            if url == faculty_dir_url:
                result["university_page"] = url
            else:
                result["personal_homepage"] = url
            if not result["best_match"]:
                result["best_match"] = url
            # Add small delay to be respectful
            time.sleep(0.5)

    # Set best_match if we found something
    if not result["best_match"]:
        result["best_match"] = (
            result["personal_homepage"]
            or result["university_page"]
            or institution_homepage
        )

    return result


def extract_research_description(page_url: str, author_name: str) -> Optional[str]:
    """
    Extract research description from a professor's page.
    Looks for sections like "Research", "Research Interests", "Research Overview"
    """
    try:
        response = requests.get(page_url, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Look for research-related headings
        research_keywords = ["research", "interests", "overview", "focus", "areas"]
        research_sections = []

        # Find headings containing research keywords
        for heading_tag in ["h1", "h2", "h3", "h4"]:
            for heading in soup.find_all(heading_tag):
                heading_text = heading.get_text().lower()
                if any(keyword in heading_text for keyword in research_keywords):
                    # Get text content after this heading
                    next_siblings = []
                    for sibling in heading.next_siblings:
                        if sibling.name and sibling.name in ["h1", "h2", "h3", "h4"]:
                            break
                        if hasattr(sibling, "get_text"):
                            text = sibling.get_text().strip()
                            if text:
                                next_siblings.append(text)
                    if next_siblings:
                        research_sections.append(
                            " ".join(next_siblings[:3])
                        )  # Take first 3 paragraphs

        # Also look for common class/id patterns
        for selector in [
            ".research",
            "#research",
            ".interests",
            "#interests",
            ".bio",
            "#bio",
        ]:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                if text and len(text) > 50:  # Meaningful content
                    research_sections.append(text)

        if research_sections:
            # Combine and clean up
            combined = " ".join(research_sections[:2])  # Take first 2 sections
            # Clean up whitespace
            combined = re.sub(r"\s+", " ", combined).strip()
            return combined[:500]  # Limit length

        return None
    except Exception:
        return None


def extract_lab_goals(page_url: str) -> Optional[str]:
    """
    Extract lab goals/current projects from a page.
    Looks for sections like "Lab", "Current Projects", "Research Goals"
    """
    try:
        response = requests.get(page_url, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Look for lab-related content
        lab_keywords = [
            "lab",
            "laboratory",
            "current projects",
            "research goals",
            "ongoing",
        ]
        lab_sections = []

        for heading_tag in ["h1", "h2", "h3"]:
            for heading in soup.find_all(heading_tag):
                heading_text = heading.get_text().lower()
                if any(keyword in heading_text for keyword in lab_keywords):
                    next_siblings = []
                    for sibling in heading.next_siblings:
                        if sibling.name and sibling.name in ["h1", "h2", "h3"]:
                            break
                        if hasattr(sibling, "get_text"):
                            text = sibling.get_text().strip()
                            if text:
                                next_siblings.append(text)
                    if next_siblings:
                        lab_sections.append(" ".join(next_siblings[:2]))

        # Look for lab-specific selectors
        for selector in [".lab", "#lab", ".projects", "#projects", ".current"]:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                if text and len(text) > 50:
                    lab_sections.append(text)

        if lab_sections:
            combined = " ".join(lab_sections[:2])
            combined = re.sub(r"\s+", " ", combined).strip()
            return combined[:500]

        return None
    except Exception:
        return None
