"""
Routes for PCSAS scraper.
"""

from fastapi import APIRouter
from ..scrapers import pcsas_scraper

router = APIRouter()


@router.get("/pcsas")
async def get_pcsas_data():
    """Retrieves PCSAS accredited programs data."""
    try:
        data = pcsas_scraper.scrape_pcsas()
        return {"programs": data}
    except Exception as e:
        return {"error": str(e)}
