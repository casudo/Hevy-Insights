from fastapi import APIRouter

from app.schemas.system import HealthResponse
from app.services.version import check_latest_version


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["FastAPI System"])
async def health():
    """
    Health check endpoint.

    Returns API status.
    """
    return HealthResponse(status="healthy")


@router.get("/version/check", tags=["FastAPI System"])
async def check_version():
    """
    Check for available updates from GitHub releases.

    Compares current version with latest GitHub release.
    Results are cached for 6 hours to avoid hitting rate limits.

    Returns current version, latest version, and whether an update is available.
    """
    return await check_latest_version()
