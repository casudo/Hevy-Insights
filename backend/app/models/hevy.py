from dataclasses import dataclass


@dataclass
class HevyUser:
    """User data returned from Hevy API login (OAuth2)."""

    access_token: str
    user_id: str
    username: str | None = None
    email: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None
