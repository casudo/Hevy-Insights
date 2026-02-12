from fastapi import FastAPI, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from hevy_api import HevyClient, HevyError
from hevy_recaptcha import get_recaptcha_token, invalidate_recaptcha_cache
from dotenv import load_dotenv
from os import getenv
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
from datetime import datetime, timedelta
from packaging import version
import json
from pathlib import Path

### ===============================================================================

### Load environment variables from .env file
load_dotenv()

### Demo Mode Configuration
DEMO_MODE = getenv("DEMO_MODE", "false").lower() == "true"
SAMPLE_DATA_DIR = Path(__file__).parent / "sample_data"

### Configure logging
logging.basicConfig(
    level=getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] - %(message)s", datefmt="%d.%m.%Y %H:%M:%S"
)

if DEMO_MODE:
    logging.warning("=" * 80)
    logging.warning("DEMO MODE ENABLED - Using sample data instead of real API calls")
    logging.warning("=" * 80)

### Version check configuration
CURRENT_VERSION = "1.8.2"
GITHUB_REPO = "casudo/Hevy-Insights"
version_cache = {"latest_version": None, "checked_at": None}

app = FastAPI(
    title="Hevy Insights API",
    description="Backend API for Hevy Insights",
    version="1.4.0",
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
    access_token: str  # OAuth2 access token
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    refresh_token: Optional[str] = None  # OAuth2 refresh token for token renewal
    expires_at: Optional[str] = None  # Token expiration timestamp


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="OAuth2 refresh token")


class ValidateApiKeyRequest(BaseModel):
    api_key: str


class ValidateApiKeyResponse(BaseModel):
    valid: bool
    error: Optional[str] = None


class BodyMeasurementRequest(BaseModel):
    date: str
    weight_kg: float


class HealthResponse(BaseModel):
    status: str


### Helper function to get client with OAuth2 Bearer token or PRO API key
def get_hevy_client(authorization: Optional[str] = None, api_key: Optional[str] = None) -> HevyClient:
    """Creates a HevyClient with OAuth2 Bearer token or API key.

    Args:
        authorization (Optional[str]): The Authorization header value (e.g., "Bearer <token>").
        api_key (Optional[str]): The api-key header value for PRO users.

    Raises:
        HTTPException: If neither authorization nor api_key header is provided.

    Returns:
        HevyClient: Configured Hevy client.
    """
    ### Extract Bearer token from Authorization header
    access_token = None
    if authorization:
        if authorization.startswith("Bearer "):
            access_token = authorization[7:]  # Remove "Bearer " prefix
        else:
            access_token = authorization  # Fallback for direct token

    if not access_token and not api_key:
        raise HTTPException(
            status_code=401, detail="Missing authentication: provide either Authorization Bearer token or api-key header"
        )

    return HevyClient(access_token=access_token, api_key=api_key)


### Helper function to load sample data for demo mode
def load_sample_data(filename: str) -> dict:
    """Load sample data from JSON file in sample_data directory.

    Args:
        filename: Name of the JSON file (e.g., "user_account.json")

    Returns:
        dict: Loaded JSON data

    Raises:
        HTTPException: If file not found or invalid JSON
    """
    file_path = SAMPLE_DATA_DIR / filename

    if not file_path.exists():
        logging.error(f"Sample data file not found: {file_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Demo mode enabled but sample data file '{filename}' not found. Please create it in backend/sample_data/",
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in sample data file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON in sample data file '{filename}'")
    except Exception as e:
        logging.error(f"Error loading sample data file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading sample data file '{filename}'")


### ===============================================================================
### Hevy Insights Backend API Endpoints


@app.post("/api/login", response_model=LoginResponse, tags=["Authentication"])
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
async def login(credentials: LoginRequest, request: Request) -> LoginResponse:
    """
    Login with Hevy credentials using OAuth2 authentication.

    - **emailOrUsername**: Your Hevy username or email
    - **password**: Your Hevy password

    Returns OAuth2 access token with refresh token. Rate limited to 5 attempts per minute.
    """
    ### Demo mode: accept any credentials
    if DEMO_MODE:
        logging.info("Demo mode: Login successful (any credentials accepted)")
        return LoginResponse(
            access_token="demo-access-token",
            refresh_token="demo-refresh-token",
            user_id="demo-user-id",
            username="demo_user",
            email="demo_user@demo.local",
            expires_at=int((datetime.now() + timedelta(days=30)).timestamp()),
        )

    try:
        ### Step 1: Get reCAPTCHA token automatically
        recaptcha_token = await get_recaptcha_token()

        ### Step 2: Login using OAuth2 with reCAPTCHA token
        client = HevyClient()
        user = client.login(credentials.emailOrUsername, credentials.password, recaptcha_token)

        return LoginResponse(
            access_token=user.access_token,
            refresh_token=user.refresh_token,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            expires_at=user.expires_at,
        )

    except HevyError as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected login error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        ### Always invalidate cache after login attempt to prevent token reuse
        invalidate_recaptcha_cache()


@app.post("/api/refresh_token", response_model=LoginResponse, tags=["Authentication"])
@limiter.limit("10/minute")  # Max 10 refresh attempts per minute per IP
def refresh_token(token_request: RefreshTokenRequest, request: Request) -> LoginResponse:
    """
    Refresh an expired or expiring OAuth2 access token.

    - **refresh_token**: The refresh token received during login

    Returns new OAuth2 access token with updated expiration.
    Rate limited to 10 attempts per minute.
    """
    ### Demo mode: return demo tokens
    if DEMO_MODE:
        logging.info("Demo mode: Token refresh successful")
        return LoginResponse(
            access_token="demo-access-token-refreshed",
            refresh_token="demo-refresh-token-refreshed",
            user_id="demo-user-id",
            username="demo_user",
            email="demo_user@demo.local",
            expires_at=int((datetime.now() + timedelta(days=30)).timestamp()),
        )

    try:
        ### Refresh the access token using the refresh token
        client = HevyClient()
        user = client.refresh_access_token(
            refresh_token=token_request.refresh_token, current_access_token=token_request.access_token
        )

        ### TODO: Add same response checks as in hevy_api.login()

        return LoginResponse(
            access_token=user.access_token,
            refresh_token=user.refresh_token,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            expires_at=user.expires_at,
        )

    except HevyError as e:
        logging.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected token refresh error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/validate_api_key", response_model=ValidateApiKeyResponse, tags=["Authentication"])
def validate_api_key(key_data: ValidateApiKeyRequest) -> ValidateApiKeyResponse:
    """
    Validate a Hevy PRO API key.

    - **api_key**: The API key to validate

    Returns validation status.
    """
    ### Demo mode: always return valid
    if DEMO_MODE:
        logging.info("Demo mode: API key validation bypassed (always valid)")
        return ValidateApiKeyResponse(valid=True)

    try:
        client = HevyClient(api_key=key_data.api_key)
        is_valid = client.validate_api_key()

        return ValidateApiKeyResponse(valid=is_valid)

    except HevyError as e:
        logging.error(f"API key validation error: {e}")
        return ValidateApiKeyResponse(valid=False, error=str(e))


@app.get("/api/user/account", tags=["User"])
def get_user_account(
    authorization: Optional[str] = Header(None, alias="Authorization"), api_key: Optional[str] = Header(None, alias="api-key")
) -> dict:
    """
    Get authenticated user's account information.

    Requires either Authorization Bearer token or api-key header.
    """
    ### Demo mode: return sample data
    if DEMO_MODE:
        logging.info("Demo mode: Serving sample user account")
        return load_sample_data("user_account.json")

    try:
        client = get_hevy_client(authorization=authorization, api_key=api_key)
        account = client.get_user_account()

        return account

    except HevyError as e:
        logging.error(f"Error fetching account: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@app.get("/api/workouts", tags=["Workouts"])
def get_workouts(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    api_key: Optional[str] = Header(None, alias="api-key"),
    offset: int = Query(0, ge=0, description="Pagination offset (increments of 5) - for OAuth2 mode"),
    username: Optional[str] = Query(None, description="Filter by username - for OAuth2 mode"),
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

    Requires either Authorization Bearer token or api-key header.
    """
    ### Demo mode: return complete sample data only on first request, empty afterwards
    if DEMO_MODE:
        if offset == 0 and page == 1:
            return load_sample_data("user_workouts_paged.json")
        else:
            return {"workouts": []}

    try:
        client = get_hevy_client(authorization=authorization, api_key=api_key)

        ### Use PRO API if API key is provided
        if api_key:
            workouts = client.get_pro_workouts(page=page, page_size=page_size)
        else:
            ### Use OAuth2 API with Bearer token
            if not username:
                raise HTTPException(status_code=400, detail="username parameter is required for OAuth2 mode")
            workouts = client.get_workouts(username=username, offset=offset)

        return workouts

    except HevyError as e:
        logging.error(f"Error fetching workouts: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@app.get("/api/body_measurements", tags=["Body Measurements"])
def get_body_measurements(
    authorization: str = Header(..., alias="Authorization"),
):
    """
    Get body measurements (weight tracking).

    Returns list of measurements with id, weight_kg, date, and created_at.

    Requires Authorization Bearer token header. PRO API does not support body measurements.
    """
    ### Demo mode: return sample data
    if DEMO_MODE:
        logging.info("Demo mode: Serving sample body measurements")
        return load_sample_data("body_measurements.json")

    try:
        ### Extract Bearer token
        access_token = authorization[7:] if authorization.startswith("Bearer ") else authorization
        client = HevyClient(access_token=access_token)
        measurements = client.get_body_measurements()
        return measurements

    except HevyError as e:
        logging.error(f"Error fetching body measurements: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@app.post("/api/body_measurements_batch", tags=["Body Measurements"])
def post_body_measurements(
    measurement: BodyMeasurementRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    """
    Post a new body measurement (weight tracking).

    Requires Authorization Bearer token header. PRO API does not support body measurements.

    Args:
        measurement: Body measurement data (date and weight_kg)
    """
    ### Demo mode: simulate success without posting
    if DEMO_MODE:
        logging.info("Demo mode: Simulating body measurement post")
        return {"message": "Body measurement posted successfully (demo mode)"}

    try:
        ### Extract Bearer token
        access_token = authorization[7:] if authorization.startswith("Bearer ") else authorization
        client = HevyClient(access_token=access_token)
        client.post_body_measurements(measurement.date, measurement.weight_kg)
        return {"message": "Body measurement posted successfully"}

    except HevyError as e:
        logging.error(f"Error posting body measurement: {e}")
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


### Check for available updates from GitHub releases
@app.get("/api/version/check", tags=["FastAPI System"])
async def check_version():
    """
    Check for available updates from GitHub releases.

    Compares current version with latest GitHub release.
    Results are cached for 6 hours to avoid hitting rate limits.

    Returns current version, latest version, and whether an update is available.
    """
    ### Cache for 6 hours to avoid GitHub API rate limits
    if version_cache["checked_at"] and datetime.now() - version_cache["checked_at"] < timedelta(hours=6):
        logging.info("Returning cached version check result")
        return version_cache["latest_version"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                latest = data["tag_name"].lstrip("v")  # Strip "v" prefix if present

                result = {
                    "current_version": CURRENT_VERSION,
                    "latest_version": latest,
                    "update_available": version.parse(latest) > version.parse(CURRENT_VERSION),
                    "release_url": data["html_url"],
                    "release_notes": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                }

                version_cache["latest_version"] = result
                version_cache["checked_at"] = datetime.now()
                logging.info(
                    f"Version check: current={CURRENT_VERSION}, latest={latest}, update_available={result['update_available']}"
                )
                return result
            else:
                logging.warning(f"GitHub API returned status {response.status_code}")
                return {
                    "current_version": CURRENT_VERSION,
                    "latest_version": None,
                    "update_available": False,
                    "error": f"GitHub API returned status {response.status_code}",
                }
    except Exception as e:
        logging.error(f"Error checking version: {e}")
        return {
            "current_version": CURRENT_VERSION,
            "latest_version": None,
            "update_available": False,
            "error": "Failed to check for updates from GitHub.",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
