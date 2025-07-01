from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
from typing import Optional
from helpers import display_field_ids, build_works_filter

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_URL = 'https://api.openalex.org/'
HEADERS = {
    'User-Agent': 'ResearchNetwork/0.1 (mailto:kennedy.b.ho@gmail.com)',
    'Accept': 'application/json'
}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    fields = display_field_ids()
    return templates.TemplateResponse("index.html", {"request": request, "fields": fields})

@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, search_term: str = Form(...), from_year: Optional[str] = Form(None), country_code: Optional[str] = Form(None), topic_ids: list[str] = Form([])):
    if not from_year:
        from_year = "1980"
    if not country_code:
        country_code = "US"

    filter_string = build_works_filter(
        search_term=search_term,
        from_year=int(from_year),
        country_code=country_code,
        topic_ids=topic_ids
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

    return templates.TemplateResponse("results.html", {"request": request, "works": works})