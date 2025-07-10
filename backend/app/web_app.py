import logging
from fastapi import FastAPI
import requests
from typing import Optional, List

from .pcsas_scraper import scrape_pcsas
from .academic_network import AcademicNetwork


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BASE_URL = "https://api.openalex.org/"
HEADERS = {
    "User-Agent": "ResearchNetwork/0.1 (mailto:kennedy.b.ho@gmail.com)",
    "Accept": "application/json",
}


@app.get("/api/v1/pcsas")
async def get_pcsas_data():
    """Retrieves PCSAS data.

    Returns:
        dict: A dictionary containing a list of PCSAS programs.
    """
    logger.info("GET /api/v1/pcsas request received.")
    try:
        data = scrape_pcsas()
        logger.info("Successfully scraped PCSAS data.")
    except Exception as e:
        data = []
        logger.error(f"Error scraping PCSAS data: {e}")
    return {"programs": data}


@app.get("/api/v1/author_works/{author_id}")
async def get_author_works(author_id: str, page: int = 1, per_page: int = 25):
    """Retrieves works by a specific author.

    Args:
        author_id (str): The OpenAlex ID of the author.
        page (int): The page number for pagination.
        per_page (int): The number of results per page.

    Returns:
        dict: A dictionary containing a list of academic works by the author.
    """
    logger.info(
        f"GET /api/v1/author_works request received for author_id: {author_id}, page: {page}, per_page: {per_page}"
    )
    url = f"{BASE_URL}works?filter=author.id:{author_id}&sort=cited_by_count:desc&per-page={per_page}&page={page}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        works = data.get("results", [])
        logger.info(
            f"Successfully fetched {len(works)} works for author_id: {author_id}"
        )
    except requests.exceptions.RequestException as e:
        works = []
        logger.error(f"Error fetching data for author_id {author_id}: {e}")

    return {"works": works}


@app.get("/api/v1/author_details/{author_id}")
async def get_author_details(author_id: str):
    """Retrieves details for a specific author.

    Args:
        author_id (str): The OpenAlex ID of the author.

    Returns:
        dict: A dictionary containing the author's details.
    """
    logger.info(
        f"GET /api/v1/author_details request received for author_id: {author_id}"
    )
    url = f"{BASE_URL}authors/{author_id}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        author_details = response.json()
        logger.info(f"Successfully fetched details for author_id: {author_id}")
    except requests.exceptions.RequestException as e:
        author_details = {}
        logger.error(f"Error fetching author details for {author_id}: {e}")

    return {"author": author_details}


def normalize_university_name(name: str) -> str:
    """Normalizes university names by removing content in parentheses and converting to lowercase."""
    import re

    name = re.sub(r"\s*\([^)]*\)", "", name)  # Remove content in parentheses
    return name.lower().strip()


@app.get("/api/v1/cross_search_universities")
async def cross_search_universities(search_term: str, top_x_works: int = 10):
    """
    Cross-searches affiliated universities of top research works with PCSAS accredited universities.

    Args:
        search_term (str): The search term for academic papers.
        top_x_works (int): The number of top works to consider for affiliation extraction.

    Returns:
        dict: A dictionary containing a list of common universities.
    """
    logger.info(
        f"GET /api/v1/cross_search_universities request received for search_term: {search_term}, top_x_works: {top_x_works}"
    )

    # 1. Get top X works
    works_url = f"{BASE_URL}works?filter=default.search:{search_term}&sort=cited_by_count:desc&per-page={top_x_works}"
    try:
        works_response = requests.get(works_url, headers=HEADERS)
        works_response.raise_for_status()
        works_data = works_response.json().get("results", [])
        logger.info(
            f"Successfully fetched {len(works_data)} top works for search term: {search_term}"
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching top works for search term {search_term}: {e}")
        return {"common_universities": []}

    # 2. Extract affiliations from top works and normalize names
    academic_network = AcademicNetwork()
    affiliated_universities_raw = academic_network.get_affiliations_from_works(
        works_data
    )
    affiliated_universities_normalized = {
        normalize_university_name(name) for name in affiliated_universities_raw
    }
    logger.info(
        f"Extracted {len(affiliated_universities_normalized)} normalized affiliated universities from top works."
    )

    # 3. Get PCSAS accredited universities and normalize names
    try:
        pcsas_universities_raw = scrape_pcsas()
        pcsas_university_map = {
            normalize_university_name(program["program_name"]): {
                "name": program["program_name"],
                "website": program["website"],
            }
            for program in pcsas_universities_raw
        }
        logger.info(
            f"Successfully scraped {len(pcsas_university_map)} PCSAS accredited universities."
        )
    except Exception as e:
        logger.error(f"Error scraping PCSAS data: {e}")
        return {"common_universities": []}

    # 4. Find common universities and their websites
    common_universities_with_links = []
    for normalized_uni_name in affiliated_universities_normalized:
        if normalized_uni_name in pcsas_university_map:
            common_universities_with_links.append(
                pcsas_university_map[normalized_uni_name]
            )

    logger.info(f"Found {len(common_universities_with_links)} common universities.")

    return {"common_universities": common_universities_with_links}
