from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from hevy_api import HevyClient, HevyError
from dotenv import load_dotenv
import logging

### ===============================================================================

### Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

### Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Hevy Insights API",
    description="Backend API for Hevy Insights",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
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

class HealthResponse(BaseModel):
    status: str

### Helper function to extract auth token from header
def get_auth_token(auth_token: Optional[str]) -> str:
    """Extracts the auth token from the auth-token header.

    Args:
        auth_token (Optional[str]): The auth-token header value.

    Raises:
        HTTPException: If the auth-token header is missing.

    Returns:
        str: The auth token.
    """
    if not auth_token:
        raise HTTPException(status_code=401, detail="Missing auth-token header")
    
    return auth_token

### ===============================================================================
### Hevy Insights Backend API Endpoints

@app.post("/api/login", response_model=LoginResponse, tags=["Authentication"])
async def login(credentials: LoginRequest):
    """
    Login with Hevy credentials to obtain an authentication token.
    
    - **emailOrUsername**: Your Hevy username or email
    - **password**: Your Hevy password
    
    Returns auth token.
    """
    try:
        client = HevyClient()
        user = client.login(credentials.emailOrUsername, credentials.password)
        
        return LoginResponse(
            auth_token = user.auth_token,
            user_id = user.user_id,
            username = user.username,
            email = user.email
        )
        
    except HevyError as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/validate", response_model=ValidateTokenResponse, tags=["Authentication"])
async def validate_token(token_data: ValidateTokenRequest) -> ValidateTokenResponse:
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


@app.get("/api/user/account", tags=["User"])
async def get_user_account(auth_token: str = Header(..., alias="auth-token")) -> dict:
    """
    Get authenticated user's account information.
    
    Requires auth-token header.
    """
    token = auth_token
    
    try:
        client = HevyClient(token)
        account = client.get_user_account()
        
        return account
        
    except HevyError as e:
        logging.error(f"Error fetching account: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@app.get("/api/workouts", tags=["Workouts"])
async def get_workouts(
    auth_token: str = Header(..., alias="auth-token"),
    offset: int = Query(0, ge=0, description="Pagination offset (increments of 5)"),
    username: str = Query(..., description="Filter by username")
):
    """
    Get paginated workout history.
    
    - **offset**: Pagination offset (0, 5, 10, 15, ...)
    - **username**: Username filter
    
    Requires auth-token header.
    """
    token = auth_token
    
    try:
        client = HevyClient(token)
        workouts = client.get_workouts(username=username, offset=offset)
        
        return workouts
        
    except HevyError as e:
        logging.error(f"Error fetching workouts: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


### Check Hevy Insights API Backend Health
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health():
    """
    Health check endpoint.
    
    Returns API status.
    """
    return HealthResponse(status="healthy")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
