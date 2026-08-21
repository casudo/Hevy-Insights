import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Cookie, HTTPException, Request, Response

from app.clients.hevy import HevyClient, HevyError
from app.clients.recaptcha import get_recaptcha_token, invalidate_recaptcha_cache
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import clear_auth_cookies, set_auth_cookies
from app.schemas.auth import AuthStatusResponse, LoginRequest, LoginResponse, ValidateApiKeyRequest, ValidateApiKeyResponse


router = APIRouter()


@router.post("/login", response_model=LoginResponse, tags=["Authentication"])
@limiter.limit("5/minute")
async def login(credentials: LoginRequest, request: Request, response: Response) -> LoginResponse:
    """
    Login with Hevy credentials using OAuth2 authentication.

    - **emailOrUsername**: Your Hevy username or email
    - **password**: Your Hevy password

    Returns OAuth2 access token with refresh token. Rate limited to 5 attempts per minute.
    Sets HttpOnly cookies for secure token storage.
    """
    if settings.demo_mode:
        logging.info("Demo mode: Login successful (any credentials accepted)")
        login_response = LoginResponse(
            access_token="demo-access-token",
            refresh_token="demo-refresh-token",
            user_id="demo-user-id",
            username="demo_user",
            email="demo_user@demo.local",
            expires_at=int((datetime.now() + timedelta(days=30)).timestamp()),
        )
        set_auth_cookies(
            response,
            access_token=login_response.access_token,
            refresh_token=login_response.refresh_token,
            expires_at=login_response.expires_at,
        )
        return login_response

    try:
        recaptcha_token = await get_recaptcha_token()

        client = HevyClient()
        user = client.login(credentials.emailOrUsername, credentials.password, recaptcha_token)

        login_response = LoginResponse(
            access_token=user.access_token,
            refresh_token=user.refresh_token,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            expires_at=user.expires_at,
        )

        set_auth_cookies(
            response,
            access_token=user.access_token,
            refresh_token=user.refresh_token,
            expires_at=user.expires_at,
        )

        return login_response

    except HevyError as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected login error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        invalidate_recaptcha_cache()


@router.post("/refresh_token", response_model=LoginResponse, tags=["Authentication"])
@limiter.limit("10/minute")
def refresh_token(
    request: Request,
    response: Response,
    hevy_refresh_token: str | None = Cookie(None),
    hevy_access_token: str | None = Cookie(None),
) -> LoginResponse:
    """
    Refresh an expired or expiring OAuth2 access token.

    Returns new OAuth2 access token with updated expiration.
    Rate limited to 10 attempts per minute.
    """
    if settings.demo_mode:
        logging.info("Demo mode: Token refresh successful")
        refresh_response = LoginResponse(
            access_token="demo-access-token-refreshed",
            refresh_token="demo-refresh-token-refreshed",
            user_id="demo-user-id",
            username="demo_user",
            email="demo_user@demo.local",
            expires_at=int((datetime.now() + timedelta(days=30)).timestamp()),
        )
        set_auth_cookies(
            response,
            access_token=refresh_response.access_token,
            refresh_token=refresh_response.refresh_token,
            expires_at=refresh_response.expires_at,
        )
        return refresh_response

    if not hevy_refresh_token:
        raise HTTPException(status_code=401, detail="No refresh credentials found. Please login again.")

    try:
        client = HevyClient()
        user = client.refresh_access_token(
            refresh_token=hevy_refresh_token,
        )

        refresh_token_value = user.refresh_token or hevy_refresh_token

        refresh_response = LoginResponse(
            access_token=user.access_token,
            refresh_token=refresh_token_value,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            expires_at=user.expires_at,
        )

        set_auth_cookies(
            response,
            access_token=user.access_token,
            refresh_token=refresh_token_value,
            expires_at=user.expires_at,
        )

        return refresh_response

    except HevyError as e:
        logging.error(f"Token refresh error: {e}")
        clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected token refresh error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/validate_api_key", response_model=ValidateApiKeyResponse, tags=["Authentication"])
def validate_api_key(key_data: ValidateApiKeyRequest, response: Response) -> ValidateApiKeyResponse:
    """
    Validate a Hevy PRO API key.

    - **api_key**: The API key to validate

    Returns validation status and sets HttpOnly cookie if valid.
    """
    if settings.demo_mode:
        logging.info("Demo mode: API key validation bypassed (always valid)")
        set_auth_cookies(response, api_key="demo-api-key")
        return ValidateApiKeyResponse(valid=True)

    try:
        client = HevyClient(api_key=key_data.api_key)
        is_valid = client.validate_api_key()

        if is_valid:
            set_auth_cookies(response, api_key=key_data.api_key)
            set_auth_cookies(response, access_token="api_key_mode")

        return ValidateApiKeyResponse(valid=is_valid)

    except HevyError as e:
        logging.error(f"API key validation error: {e}")
        return ValidateApiKeyResponse(valid=False, error=str(e))


@router.post("/logout", tags=["Authentication"])
def logout(response: Response):
    """
    Logout the current user by clearing authentication cookies.

    Returns success message.
    """
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@router.get("/auth/status", response_model=AuthStatusResponse, tags=["Authentication"])
def auth_status(
    hevy_access_token: str | None = Cookie(None),
    hevy_api_key: str | None = Cookie(None),
):
    """
    Check current authentication status.

    Returns whether user is authenticated and the auth mode.
    Useful for frontend route guards.
    """
    if hevy_access_token == "csv_mode":
        return AuthStatusResponse(
            authenticated=True,
            auth_mode="csv",
        )

    if hevy_api_key or hevy_access_token == "api_key_mode":
        return AuthStatusResponse(
            authenticated=True,
            auth_mode="api_key",
        )

    if hevy_access_token and hevy_access_token not in ["csv_mode", "api_key_mode"]:
        return AuthStatusResponse(
            authenticated=True,
            auth_mode="oauth2",
        )

    return AuthStatusResponse(
        authenticated=False,
        auth_mode=None,
    )
