from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    emailOrUsername: str = Field(..., description="User's email or username")
    password: str = Field(..., description="User's password")


class LoginResponse(BaseModel):
    access_token: str
    user_id: str
    username: str | None = None
    email: str | None = None
    refresh_token: str | None = None
    expires_at: str | int | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="OAuth2 refresh token")


class ValidateApiKeyRequest(BaseModel):
    api_key: str


class ValidateApiKeyResponse(BaseModel):
    valid: bool
    error: str | None = None


class AuthStatusResponse(BaseModel):
    authenticated: bool
    auth_mode: str | None = None
