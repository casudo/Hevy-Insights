from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from hevy_api import HevyClient, HevyError
from dotenv import load_dotenv
from os import getenv
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

### ===============================================================================

### Load environment variables from .env file
load_dotenv()

### Configure logging
logging.basicConfig(level=getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] - %(message)s", datefmt="%d.%m.%Y %H:%M:%S")

app = FastAPI(
    title="Hevy Insights API",
    description="Backend API for Hevy Insights",
    version="1.2.0",
    docs_url="/api/docs",  # Swagger
)
### Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vue dev server
        "http://localhost:80",  # Production (Nginx proxy)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow necessary methods
    allow_headers=["*"],
)


### Pydantic models for request/response validation
class LoginRequest(BaseModel):
    emailOrUsername: str = Field(..., description="User's email or username")
    password: str = Field(..., description="User's password")


class LoginResponse(BaseModel):
    auth_token: str
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None


class ValidateTokenRequest(BaseModel):
    auth_token: str


class ValidateTokenResponse(BaseModel):
    valid: bool
    error: Optional[str] = None


class ValidateApiKeyRequest(BaseModel):
    api_key: str


class ValidateApiKeyResponse(BaseModel):
    valid: bool
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str


### Helper function to get client with either auth token or PRO API key
def get_hevy_client(auth_token: Optional[str] = None, api_key: Optional[str] = None) -> HevyClient:
    """Creates a HevyClient with either auth token or API key.

    Args:
        auth_token (Optional[str]): The auth-token header value.
        api_key (Optional[str]): The pro-api-key header value.

    Raises:
        HTTPException: If neither auth_token nor api_key header is provided.

    Returns:
        HevyClient: Configured Hevy client.
    """
    if not auth_token and not api_key:
        raise HTTPException(status_code=401, detail="Missing authentication: provide either auth-token or pro-api-key header")

    return HevyClient(auth_token=auth_token, api_key=api_key)


### ===============================================================================
### Hevy Insights Backend API Endpoints


@app.post("/api/login", response_model=LoginResponse, tags=["Authentication"])
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
def login(credentials: LoginRequest, request: Request) -> LoginResponse:
    """
    Login with Hevy credentials to obtain an authentication token.

    - **emailOrUsername**: Your Hevy username or email
    - **password**: Your Hevy password

    Returns auth token. Rate limited to 5 attempts per minute.
    """
    try:
        client = HevyClient()
        user = client.login(credentials.emailOrUsername, credentials.password)

        return LoginResponse(auth_token=user.auth_token, user_id=user.user_id, username=user.username, email=user.email)

    except HevyError as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/validate-auth-token", response_model=ValidateTokenResponse, tags=["Authentication"])
def validate_token(token_data: ValidateTokenRequest) -> ValidateTokenResponse:
    """
    Validate an authentication token.

    - **auth_token**: The token to validate

    Returns validation status.
    """
    try:
        client = HevyClient(token_data.auth_token)
        is_valid = client.validate_auth_token()

        return ValidateTokenResponse(valid=is_valid)

    except HevyError as e:
        logging.error(f"Token validation error: {e}")
        return ValidateTokenResponse(valid=False, error=str(e))


@app.post("/api/validate-api-key", response_model=ValidateApiKeyResponse, tags=["Authentication"])
def validate_api_key(key_data: ValidateApiKeyRequest) -> ValidateApiKeyResponse:
    """
    Validate a Hevy PRO API key.

    - **api_key**: The API key to validate

    Returns validation status.
    """
    try:
        client = HevyClient(api_key=key_data.api_key)
        is_valid = client.validate_api_key()

        return ValidateApiKeyResponse(valid=is_valid)

    except HevyError as e:
        logging.error(f"API key validation error: {e}")
        return ValidateApiKeyResponse(valid=False, error=str(e))


@app.get("/api/user/account", tags=["User"])
def get_user_account(
    auth_token: Optional[str] = Header(None, alias="auth-token"),
    api_key: Optional[str] = Header(None, alias="api-key")
) -> dict:
    """
    Get authenticated user's account information.

    Requires either auth-token or api-key header.
    """
    try:
        client = get_hevy_client(auth_token=auth_token, api_key=api_key)
        account = client.get_user_account()

        return account

    except HevyError as e:
        logging.error(f"Error fetching account: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@app.get("/api/workouts", tags=["Workouts"])
def get_workouts(
    auth_token: Optional[str] = Header(None, alias="auth-token"),
    api_key: Optional[str] = Header(None, alias="api-key"),
    offset: int = Query(0, ge=0, description="Pagination offset (increments of 5) - for auth-token mode"),
    username: Optional[str] = Query(None, description="Filter by username - for auth-token mode"),
    page: int = Query(1, ge=1, description="Page number - for api-key mode"),
    page_size: int = Query(10, ge=1, le=50, description="Page size - for api-key mode"),
):
    """
    Get paginated workout history.

    **Auth-token mode:**
    - **offset**: Pagination offset (0, 5, 10, 15, ...)
    - **username**: Username filter (required)

    **API-key mode:**
    - **page**: Page number (default: 1)
    - **page_size**: Number of workouts per page (default: 10)

    Requires either auth-token or api-key header.
    """
    try:
        client = get_hevy_client(auth_token=auth_token, api_key=api_key)

        ### Use PRO API if API key is provided
        if api_key:
            workouts = client.get_pro_workouts(page=page, page_size=page_size)
        else:
            ### Use free API with auth token
            if not username:
                raise HTTPException(status_code=400, detail="username parameter is required for auth-token mode")
            workouts = client.get_workouts(username=username, offset=offset)

        return workouts

    except HevyError as e:
        logging.error(f"Error fetching workouts: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


### Check Hevy Insights API Backend Health
@app.get("/api/health", response_model=HealthResponse, tags=["FastAPI System"])
async def health():
    """
    Health check endpoint.

    Returns API status.
    """
    return HealthResponse(status="healthy")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
