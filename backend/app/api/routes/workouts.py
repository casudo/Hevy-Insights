import logging

from fastapi import APIRouter, Cookie, HTTPException, Query

from app.clients.hevy import HevyError
from app.core.config import settings
from app.core.security import get_hevy_client
from app.services.demo_data import load_sample_data


router = APIRouter()


@router.get("/workouts", tags=["Workouts"])
def get_workouts(
    hevy_access_token: str | None = Cookie(None),
    hevy_api_key: str | None = Cookie(None),
    offset: int = Query(0, ge=0, description="Pagination offset (increments of 5) - for OAuth2 mode"),
    username: str | None = Query(None, description="Filter by username - for OAuth2 mode"),
    page: int = Query(1, ge=1, description="Page number - for api-key mode"),
    page_size: int = Query(10, ge=1, le=50, description="Page size - for api-key mode"),
):
    """
    Get paginated workout history.

    **OAuth2 mode (Bearer token):**
    - **offset**: Pagination offset (0, 5, 10, 15, ...)
    - **username**: Username filter (required)

    **API-key mode:**
    - **page**: Page number (default: 1)
    - **page_size**: Number of workouts per page (default: 10)

    Requires authentication cookie (OAuth2 token or API key).
    """
    if settings.demo_mode:
        if offset == 0 and page == 1:
            return load_sample_data("user_workouts_paged.json")
        return {"workouts": []}

    try:
        client = get_hevy_client(access_token_cookie=hevy_access_token, api_key_cookie=hevy_api_key)

        if hevy_api_key:
            workouts = client.get_pro_workouts(page=page, page_size=page_size)
        else:
            if not username:
                raise HTTPException(status_code=400, detail="username parameter is required for OAuth2 mode")
            workouts = client.get_workouts(username=username, offset=offset)

        return workouts

    except HevyError as e:
        logging.error(f"Error fetching workouts: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
