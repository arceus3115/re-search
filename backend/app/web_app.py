
import logging
from fastapi import FastAPI
import requests
from typing import Optional, List
from .helpers import display_field_ids, build_works_filter
from .pcsas_scraper import scrape_pcsas
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BASE_URL = 'https://api.openalex.org/'
HEADERS = {
    'User-Agent': 'ResearchNetwork/0.1 (mailto:kennedy.b.ho@gmail.com)',
    'Accept': 'application/json'
}

class SearchRequest(BaseModel):
    search_term: str
    from_year: Optional[int] = 1980
    country_code: Optional[str] = "US"
    topic_ids: List[str] = []

@app.get("/api/v1/fields")
async def get_fields():
    """Retrieves a list of available academic fields.

    Returns:
        dict: A dictionary containing a list of academic fields.
    """
    logger.info("GET /api/v1/fields request received.")
    fields = display_field_ids()
    logger.info("Returning fields data.")
    return {"fields": fields}

@app.get("/api/v1/search")
async def search_papers(
    search_term: str,
    from_year: Optional[int] = 1980,
    country_code: Optional[str] = "US",
    topic_ids: List[str] = [],
    page: int = 1,
    per_page: int = 25
):
    """Searches for academic papers based on the provided criteria.

    Args:
        request (SearchRequest): The search request containing search term, year, country code, and topic IDs.

    Returns:
        dict: A dictionary containing a list of academic works.
    """
    logger.info(f"GET /api/v1/search request received with search_term: {search_term}, from_year: {from_year}, country_code: {country_code}, topic_ids: {topic_ids}, page: {page}, per_page: {per_page}")
    filter_string = build_works_filter(
        search_term=search_term,
        from_year=from_year,
        country_code=country_code,
        topic_ids=topic_ids
    )
    
    url = f'{BASE_URL}works?filter={filter_string}&sort=fwci:desc&per-page={per_page}&page={page}'
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        works = data.get('results', [])
        logger.info(f"Successfully fetched {len(works)} works for search term: {search_term}")
    except requests.exceptions.RequestException as e:
        works = []
        logger.error(f"Error fetching data for search term {request.search_term}: {e}")

    return {"works": works}

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
