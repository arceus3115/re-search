from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .routes import (
    scraper_routes,
    pi_routes,
    profile_routes,
    pi_research_routes,
    draft_routes,
    clinicaltrials_routes,
    program_discovery_routes,
)
from .utils.logger import setup_logger

setup_logger()

app = FastAPI(title="re-search API", version="1.0.0")

_default_origins = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]
_env_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
_allowed_origins = _default_origins + _env_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# PCSAS scraper endpoint
app.include_router(scraper_routes.router, prefix="/api/v1")
# PI Finder Agent endpoint
app.include_router(pi_routes.router, prefix="/api/v1")
# Profile routes
app.include_router(profile_routes.router, prefix="/api/v1")
# PI Research routes
app.include_router(pi_research_routes.router, prefix="/api/v1")
# Draft generation routes
app.include_router(draft_routes.router, prefix="/api/v1")
# ClinicalTrials.gov routes
app.include_router(clinicaltrials_routes.router, prefix="/api/v1")
# Program Discovery routes
app.include_router(program_discovery_routes.router, prefix="/api/v1")
