"""
Routes for PCSAS scraper.
"""

from fastapi import APIRouter, HTTPException

from ..scrapers import pcsas_scraper
from ..utils.exceptions import ScrapingError

router = APIRouter()


@router.get("/pcsas")
async def get_pcsas_data():
    """Retrieves PCSAS accredited programs data."""
    try:
        data = pcsas_scraper.scrape_pcsas()
        return {"programs": data}
    except ScrapingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Failed to scrape PCSAS data: {exc}"
        ) from exc
