from fastapi import HTTPException, Response

from app.clients.hevy import HevyClient
from app.core.config import settings


def set_auth_cookies(
    response: Response,
    access_token: str | None = None,
    refresh_token: str | None = None,
    api_key: str | None = None,
    expires_at: str | int | None = None,
) -> None:
    if access_token:
        response.set_cookie(
            key="hevy_access_token",
            value=access_token,
            max_age=settings.cookie_max_age,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            path="/",
        )

    if refresh_token:
        response.set_cookie(
            key="hevy_refresh_token",
            value=refresh_token,
            max_age=settings.cookie_max_age,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            path="/",
        )

    if expires_at:
        response.set_cookie(
            key="hevy_token_expires_at",
            value=str(expires_at),
            max_age=settings.cookie_max_age,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            path="/",
        )

    if api_key:
        response.set_cookie(
            key="hevy_api_key",
            value=api_key,
            max_age=settings.cookie_max_age,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            path="/",
        )


def clear_auth_cookies(response: Response) -> None:
    cookie_names = [
        "hevy_access_token",
        "hevy_refresh_token",
        "hevy_api_key",
        "hevy_token_expires_at",
    ]
    for cookie_name in cookie_names:
        response.delete_cookie(
            key=cookie_name,
            path="/",
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )


def get_hevy_client(
    access_token_cookie: str | None = None,
    api_key_cookie: str | None = None,
) -> HevyClient:
    if access_token_cookie == "csv_mode":
        raise HTTPException(
            status_code=400,
            detail="CSV mode does not support backend API calls. Data is stored client-side only.",
        )

    if api_key_cookie:
        return HevyClient(api_key=api_key_cookie)

    if access_token_cookie and access_token_cookie != "api_key_mode":
        return HevyClient(access_token=access_token_cookie)

    raise HTTPException(
        status_code=401,
        detail="Missing authentication: please login again",
    )
