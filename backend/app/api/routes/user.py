import logging
from typing import Any

from fastapi import APIRouter, Cookie, HTTPException

from app.clients.hevy import HevyError
from app.core.config import settings
from app.core.security import get_hevy_client
from app.services.demo_data import load_sample_data


router = APIRouter()


@router.get("/user/account", tags=["User"])
def get_user_account(
    hevy_access_token: str | None = Cookie(None),
    hevy_api_key: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Get authenticated user's account information.

    Requires authentication cookie (OAuth2 token or Hevy PRO API key).
    """
    if settings.demo_mode:
        logging.info("Demo mode: Serving sample user account")
        return load_sample_data("user_account.json")

    try:
        client = get_hevy_client(access_token_cookie=hevy_access_token, api_key_cookie=hevy_api_key)
        account = client.get_user_account()

        return account

    except HevyError as e:
        logging.error(f"Error fetching account: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
