
from fastapi import FastAPI
import requests
from typing import Optional, List
from .helpers import display_field_ids, build_works_filter
from .pcsas_scraper import scrape_pcsas
from pydantic import BaseModel

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
    fields = display_field_ids()
    return {"fields": fields}

@app.post("/api/v1/search")
async def search_papers(request: SearchRequest):
    filter_string = build_works_filter(
        search_term=request.search_term,
        from_year=request.from_year,
        country_code=request.country_code,
        topic_ids=request.topic_ids
    )
    
    url = f'{BASE_URL}works?filter={filter_string}&sort=fwci:desc'
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        works = data.get('results', [])
    except requests.exceptions.RequestException as e:
        works = []
        print(f"Error fetching data: {e}")

    return {"works": works}

@app.get("/api/v1/pcsas")
async def get_pcsas_data():
    data = scrape_pcsas()
    return {"programs": data}
