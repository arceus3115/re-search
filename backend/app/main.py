from fastapi import FastAPI
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

app = FastAPI()

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
