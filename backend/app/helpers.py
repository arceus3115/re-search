from typing import List
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org/"
HEADERS = {
    "User-Agent": "ResearchNetwork/0.1 (mailto:kennedy.b.ho@gmail.com)",
    "Accept": "application/json",
}

TOPIC_FIELDS_CACHE = {}


def display_field_ids():
    """Retrieves a list of academic fields/topics from OpenAlex.

    Returns:
        dict: A dictionary containing a mapping of topic IDs to their display names.
    """
    logger.info("Fetching topic fields from OpenAlex.")
    if TOPIC_FIELDS_CACHE:
        logger.info("Returning topic fields from cache.")
        return TOPIC_FIELDS_CACHE

    url = f"{BASE_URL}fields?per-page=200"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        fields = {
            result["id"].split("/")[-1]: result["display_name"]
            for result in data.get("results", [])
        }
        TOPIC_FIELDS_CACHE.update(fields)
        logger.info(f"Successfully fetched {len(fields)} topic fields from OpenAlex.")
        return fields
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching topic fields: {e}")
        return {}


def build_works_filter(
    search_term: str,
    from_year: int = 1980,
    country_code: str = "US",
    topic_ids: List[str] = None,
) -> str:
    """Constructs a filter string for the OpenAlex API's /works endpoint.

    This function takes various search parameters and formats them into a query
    string suitable for filtering academic works in the OpenAlex API.

    Args:
        search_term (str): The primary term to search within the titles and abstracts of works.
        from_year (int): The minimum publication year for the works. Defaults to 1980.
        country_code (str): The two-letter country code (ISO 3166-1 alpha-2)
                                      to filter works by the institution's country. Defaults to 'US'.
        topic_ids (List[str], optional): A list of topic IDs to filter works by specific academic fields.
                                         If provided, works will match any of the given topic IDs.
                                         Defaults to None.

    Returns:
        str: A comma-separated string of filters, URL-encoded where necessary,
             ready to be appended to the OpenAlex API /works endpoint URL.
    """
    filters = [
        f"title_and_abstract.search:{quote(search_term)}",
        f"publication_year:>{from_year}",
        f"institutions.country_code:{country_code}",
    ]

    if topic_ids:
        filters.append(f"topics.field.id:{'|'.join(topic_ids)}")

    return ",".join(filters)


def scrape_pcsas():
    """Scrapes the PCSAS accredited programs page to extract program information.

    This function sends an HTTP GET request to the PCSAS website, parses the HTML
    content to find the table of accredited programs, and extracts relevant details
    such as program name, website, and student outcomes link.

    Returns:
        list: A list of dictionaries, where each dictionary represents a program
              and contains the keys 'program_name', 'website', and 'student_outcomes_link'.
              Returns an empty list if the table is not found or no programs are extracted.
    """
    URL = "https://pcsas.org/pcsas-accredited-programs/"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")[1:]  # Skip header row

    programs_data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:  # Ensure there are enough columns
            continue

        # Program/University column
        uni_cell = cols[0]
        uni_link_element = uni_cell.find("a")
        program_name = uni_link_element.text.strip() if uni_link_element else "N/A"
        program_website = uni_link_element["href"] if uni_link_element else "N/A"

        # Student Outcomes Link column
        outcomes_cell = cols[3]
        outcomes_link_element = outcomes_cell.find("a")
        student_outcomes_link = (
            outcomes_link_element["href"] if outcomes_link_element else "N/A"
        )

        programs_data.append(
            {
                "program_name": program_name,
                "website": program_website,
                "student_outcomes_link": student_outcomes_link,
            }
        )

    return programs_data


async def crawl_universities():
    scorer = KeywordRelevanceScorer(
        keywords=[
            "accepting students",
            "faculty",
            "student admissions",
            "prospective students",
        ],
        weight=0.5,
    )

    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        include_external=False,
        url_scorer=scorer,
        max_pages=25,
    )
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        exclude_social_media_domains=True,
        pdf=True,
        verbose=True,
    )
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(
            "https://psychology.northwestern.edu/graduate/program-areas/clinical/",
            config=config,
        )
        crawled_data = []
        for result in results:
            crawled_data.append(
                {"url": result.url, "depth": result.metadata.get("depth", 0)}
            )
        return crawled_data


def normalize_university_name(name: str) -> str:
    """Normalizes university names by removing content in parentheses and converting to lowercase."""
    name = re.sub(r"\s*\([^)]*\)", "", name)  # Remove content in parentheses
    return name.lower().strip()
