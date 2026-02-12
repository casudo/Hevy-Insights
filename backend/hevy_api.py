"""Single Module File for Hevy API"""

import requests
import logging
from dataclasses import dataclass
from typing import Optional
from os import getenv
from dotenv import load_dotenv

### ============================================================================

load_dotenv()  # Load environment variables from .env file

### Data classes to replace passing many parameters around


@dataclass
class HevyUser:
    """User data returned from Hevy API login (OAuth2)"""
    access_token: str  # OAuth2 access token
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    refresh_token: Optional[str] = None  # OAuth2 refresh token
    expires_at: Optional[str] = None  # Token expiration timestamp


### Configuration class
## This is the default configuration for the Hevy API client. The user can create a custom configuration by subclassing this class or by passing a custom instance.
class HevyConfig:
    """Default configuration for Hevy API client."""

    def __init__(self):
        self.base_url = "https://api.hevyapp.com"
        self.x_api_key = getenv("X_API_KEY")  # Static for all users (free API)
        if not self.x_api_key:
            raise ValueError("X_API_KEY environment variable is required")

    @property
    def login_url(self) -> str:
        return f"{self.base_url}/login"

    @property
    def refresh_token_url(self) -> str:
        """OAuth2 token refresh endpoint"""
        return f"{self.base_url}/refresh_token"

    @property
    def user_account_url(self) -> str:
        return f"{self.base_url}/user/account"

    @property
    def user_workouts_paged_url(self) -> str:
        return f"{self.base_url}/user_workouts_paged"

    @property
    def pro_workouts_url(self) -> str:
        return f"{self.base_url}/v1/workouts"

    @property
    def body_measurements_url(self) -> str:
        return f"{self.base_url}/body_measurements"


### Main API client class
class HevyClient:
    """
    Main API client to interact with Hevy services.
    
    Seperated into two authentication methods:
    1. OAuth2 Bearer token (for username/password login)
    2. Hevy PRO API key (for PRO subscribers)
    """

    def __init__(self, access_token: Optional[str] = None, api_key: Optional[str] = None, config: Optional[HevyConfig] = None):
        self.access_token = access_token  # OAuth2 access token
        self.api_key = api_key  # Hevy PRO API key
        self.config = config or HevyConfig()
        self.session = requests.Session()

        if access_token or api_key:
            self._update_headers()

    def _update_headers(self) -> None:
        """
        Update session headers with current OAuth2 Bearer token or PRO API key.
        """
        headers = {
            "Content-Type": "application/json",
        }

        ### Use PRO API key if available, otherwise use OAuth2 Bearer token
        if self.api_key:
            headers["api-key"] = self.api_key
        elif self.access_token:
            headers["x-api-key"] = self.config.x_api_key
            headers["Authorization"] = f"Bearer {self.access_token}"

        self.session.headers.update(headers)

    ### ========== Free Hevy API Methods ==========

    def login(self, email_or_username: str, password: str, recaptcha_token: str) -> HevyUser:
        """
        Login with OAuth2 and reCAPTCHA token.
        
        Args:
            email_or_username: User's email or username
            password: User's password
            recaptcha_token: reCAPTCHA v3 Enterprise token 

        Returns:
            HevyUser: User data with OAuth2 tokens

        Raises:
            HevyError: If login fails or returns unexpected response
        """
        logging.debug(f"Attempting OAuth2 login for user: {email_or_username}")

        headers = {
            "x-api-key": self.config.x_api_key,
            "Content-Type": "application/json",
            "Hevy-Platform": "web"
        }

        body = {
            "emailOrUsername": email_or_username,
            "password": password,
            "recaptchaToken": recaptcha_token,
            "useAuth2_0": True 
        }

        try:
            response = self.session.post(self.config.login_url, headers=headers, json=body, timeout=30)
            response.raise_for_status()

            data = response.json()
            
            ### Extract response and validate
            access_token = data.get("access_token") or data.get("auth_token") # fallback
            refresh_token = data.get("refresh_token")
            
            ### Validate response
            if not access_token or not refresh_token:
                logging.error(f"Missing access/refresh token in response. Keys: {list(data.keys())}")
                raise HevyError("Login response missing access/refresh token")

            ### Update client's access token and headers after successful login
            self.access_token = access_token
            self._update_headers()
            
            return HevyUser(
                access_token=access_token,
                user_id=data.get("user_id"),
                username=email_or_username if "@" not in email_or_username else None,
                email=email_or_username if "@" in email_or_username else None,
                refresh_token=refresh_token,
                expires_at=data.get("expires_at")
            )

        except requests.JSONDecodeError as e:
            logging.error(f"JSON decode error during login: {e}")
            raise HevyError(f"JSON decode error occurred: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error during login: {e}")
            if e.response.status_code == 401:
                raise HevyError("Invalid credentials")
            elif e.response.status_code == 400:
                raise HevyError(f"Bad request: {e.response.text[:200]}")
            raise HevyError(f"HTTP error occurred: {e}")
        except requests.ConnectionError as e:
            logging.error(f"Connection error during login: {e}")
            raise HevyError(f"Connection error occurred: {e}")
        except requests.Timeout as e:
            logging.error(f"Timeout error during login: {e}")
            raise HevyError(f"Request timed out: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during login: {e}")
            raise HevyError(f"Unexpected error occurred: {e}")

    def refresh_access_token(self, refresh_token: str) -> HevyUser:
        """
        Refresh OAuth2 access token using refresh token.
        
        Args:
            refresh_token: The refresh token from previous login

        Returns:
            HevyUser: User data with new OAuth2 tokens

        Raises:
            HevyError: If refresh fails
        """
        logging.debug("Refreshing OAuth2 access token...")

        headers = {
            "x-api-key": self.config.x_api_key,
            "Content-Type": "application/json",
            "Hevy-Platform": "web"
        }
    
        body = {
            "refresh_token": refresh_token
        }
    
        try:
            response = self.session.post(self.config.refresh_token_url, headers=headers, json=body, timeout=30)
            response.raise_for_status()

            data = response.json()
            
            ### Extract response and validate
            access_token = data.get("access_token") or data.get("auth_token") # fallback
            new_refresh_token = data.get("refresh_token")
            
            ### Validate response
            if not access_token or not new_refresh_token:
                logging.error(f"Missing access/refresh token in response. Keys: {list(data.keys())}")
                raise HevyError("Login response missing access/refresh token")

            ### Update client's access token and headers after successful login
            self.access_token = access_token
            self._update_headers()
            
            return HevyUser(
                access_token=access_token,
                user_id=data.get("user_id"),
                refresh_token=new_refresh_token,
                expires_at=data.get("expires_at")
            )

        except requests.HTTPError as e:
            logging.error(f"HTTP error during token refresh: {e}")
            logging.error(f"Response status: {e.response.status_code}")
            if e.response.status_code == 401:
                raise HevyError("Invalid or expired refresh token")
            raise HevyError(f"Token refresh failed: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during token refresh: {e}")
            raise HevyError(f"Unexpected error occurred: {e}")

    def get_user_account(self) -> Optional[dict]:
        """
        Fetch user account information.

        Returns:
            Optional[dict]: User account data if successful, None otherwise

        Raises:
            HevyError: If API request fails
        """
        logging.debug("Fetching user account information...")

        if not self.access_token:
            raise HevyError("No access token available. Please login first.")

        try:
            response = self.session.get(self.config.user_account_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            logging.debug(f"Successfully fetched account for user: {data.get('username')}")
            return data

        except requests.JSONDecodeError as e:
            logging.error(f"JSON decode error fetching user account: {e}")
            raise HevyError(f"JSON decode error occurred: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error fetching user account: {e}")
            if e.response.status_code == 401:
                raise HevyError("Unauthorized - Invalid or expired access token")
            raise HevyError(f"HTTP error occurred: {e}")
        except requests.ConnectionError as e:
            logging.error(f"Connection error fetching user account: {e}")
            raise HevyError(f"Connection error occurred: {e}")
        except requests.Timeout as e:
            logging.error(f"Timeout error fetching user account: {e}")
            raise HevyError(f"Request timed out: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching user account: {e}")
            raise HevyError(f"Unexpected error occurred: {e}")

    def get_workouts(self, username: str, offset: int = 0) -> dict:
        """
        Fetch paginated workouts from Hevy API.

        Args:
            username: Username to filter workouts
            offset: Pagination offset (increments by 5: 0, 5, 10, 15, ...)

        Returns:
            dict: Workouts data containing 'workouts' key with list of workout objects

        Raises:
            HevyError: If API request fails
        """
        logging.debug(f"Fetching workouts ({username=}, {offset=})")

        if not self.access_token:
            raise HevyError("No access token available. Please login first.")

        params = {"offset": offset, "username": username}

        try:
            response = self.session.get(self.config.user_workouts_paged_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            workout_count = len(data.get("workouts", []))
            logging.debug(f"Successfully fetched {workout_count} workouts")
            return data

        except requests.JSONDecodeError as e:
            logging.error(f"JSON decode error fetching workouts: {e}")
            raise HevyError(f"JSON decode error occurred: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error fetching workouts: {e}")
            if e.response.status_code == 401:
                raise HevyError("Unauthorized - Invalid or expired access token")
            raise HevyError(f"HTTP error occurred: {e}")
        except requests.ConnectionError as e:
            logging.error(f"Connection error fetching workouts: {e}")
            raise HevyError(f"Connection error occurred: {e}")
        except requests.Timeout as e:
            logging.error(f"Timeout error fetching workouts: {e}")
            raise HevyError(f"Request timed out: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching workouts: {e}")
            raise HevyError(f"Unexpected error occurred: {e}")

    def get_body_measurements(self) -> list:
        """
        Fetch body measurements from Hevy API.

        Returns:
            list: Body measurements data (list of dicts with id, weight_kg, date, created_at)

        Raises:
            HevyError: If API request fails
        """
        logging.debug("Fetching body measurements")

        if not self.access_token:
            raise HevyError("No access token available. Please login first.")

        try:
            response = self.session.get(self.config.body_measurements_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            logging.debug(f"Successfully fetched {len(data)} body measurements")
            return data

        except requests.JSONDecodeError as e:
            logging.error(f"JSON decode error fetching body measurements: {e}")
            raise HevyError(f"JSON decode error occurred: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error fetching body measurements: {e}")
            if e.response.status_code == 401:
                raise HevyError("Unauthorized - Invalid or expired access token")
            raise HevyError(f"HTTP error occurred: {e}")
        except requests.ConnectionError as e:
            logging.error(f"Connection error fetching body measurements: {e}")
            raise HevyError(f"Connection error occurred: {e}")
        except requests.Timeout as e:
            logging.error(f"Timeout error fetching body measurements: {e}")
            raise HevyError(f"Request timed out: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching body measurements: {e}")
            raise HevyError(f"Unexpected error occurred: {e}")

    def post_body_measurements(self, date: str, weight_kg: float) -> None:
        """
        Post body measurements to Hevy API.

        Args:
            date: Date of the measurement in ISO 8601 format (YYYY-MM-DD)
            weight_kg: Weight in kilograms

        Raises:
            HevyError: If API request fails
        """
        logging.debug(f"Posting body measurement: {date=}, {weight_kg=}")

        if not self.access_token:
            raise HevyError("No access token available. Please login first.")

        try:
            body = {"measurementsBatch": [{"date": date, "weight_kg": weight_kg, "_unsyncedObjectId": "zitronenkuchen"}]}

            response = self.session.post(f"{self.config.body_measurements_url}_batch", json=body, timeout=30)
            response.raise_for_status()

            ### Hevy API returns 200 OK with empty body on successful POST
            if response.status_code == 200:
                logging.debug("Successfully posted body measurement")
                return {"success": True}

        except requests.JSONDecodeError as e:
            logging.error(f"JSON decode error posting body measurements: {e}")
            logging.error(f"Response status: {response.status_code}, Content: {response.text[:200]}")
            raise HevyError(f"JSON decode error occurred: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error posting body measurements: {e}")
            if e.response.status_code == 401:
                raise HevyError("Unauthorized - Invalid or expired access token")
            raise HevyError(f"HTTP error occurred: {e}")
        except requests.ConnectionError as e:
            logging.error(f"Connection error posting body measurements: {e}")
            raise HevyError(f"Connection error occurred: {e}")
        except requests.Timeout as e:
            logging.error(f"Timeout error posting body measurements: {e}")
            raise HevyError(f"Request timed out: {e}")
        except Exception as e:
            logging.error(f"Unexpected error posting body measurements: {e}")
            raise HevyError(f"Unexpected error occurred: {e}")

    ### ========== Hevy PRO API Methods ==========

    def get_pro_workouts(self, page: int = 1, page_size: int = 10) -> dict:
        """
        Fetch paginated workouts from Hevy PRO API.

        Args:
            page: Page number (default: 1)
            page_size: Number of workouts per page (default: 10)

        Returns:
            dict: Workouts data containing 'workouts', 'page', 'page_count' keys

        Raises:
            HevyError: If API request fails
        """
        logging.debug(f"Fetching PRO workouts ({page=}, {page_size=})")

        if not self.api_key:
            raise HevyError("No PRO API key available. Please use a Hevy PRO API key.")

        params = {"page": page, "pageSize": page_size}

        try:
            response = self.session.get(self.config.pro_workouts_url, params=params)
            response.raise_for_status()

            data = response.json()
            workouts = data.get("workouts", [])

            ### Transform PRO API format to match free API format
            from datetime import datetime

            for workout in workouts:
                ### Convert ISO 8601 timestamps to Unix timestamps (seconds)
                ## NOTE: Frontend expects timestamps in Unix format (just like free API)
                if "start_time" in workout and isinstance(workout["start_time"], str):
                    workout["start_time"] = int(datetime.fromisoformat(workout["start_time"].replace("Z", "+00:00")).timestamp())
                if "end_time" in workout and isinstance(workout["end_time"], str):
                    workout["end_time"] = int(datetime.fromisoformat(workout["end_time"].replace("Z", "+00:00")).timestamp())
                if "updated_at" in workout and isinstance(workout["updated_at"], str):
                    workout["updated_at"] = int(datetime.fromisoformat(workout["updated_at"].replace("Z", "+00:00")).timestamp())
                if "created_at" in workout and isinstance(workout["created_at"], str):
                    workout["created_at"] = int(datetime.fromisoformat(workout["created_at"].replace("Z", "+00:00")).timestamp())

                ### Calculate estimated_volume_kg from exercises/sets (PRO API doesn't include this)
                ## NOTE: Frontend relies on this field for various calculations and displays
                estimated_volume = 0
                for exercise in workout.get("exercises", []):
                    ### Add unique ID for exercise if missing (for frontend state management)
                    if "id" not in exercise:
                        exercise["id"] = f"{workout['id']}-ex-{exercise['index']}"

                    for set_data in exercise.get("sets", []):
                        ### Add unique ID for set if missing
                        if "id" not in set_data:
                            set_data["id"] = f"{exercise['id']}-set-{set_data['index']}"

                        ### Include all set types in volume calculation
                        weight = set_data.get("weight_kg") or 0
                        reps = set_data.get("reps") or 0
                        estimated_volume += weight * reps

                workout["estimated_volume_kg"] = estimated_volume

            workout_count = len(workouts)
            logging.debug(f"Successfully fetched {workout_count} PRO workouts")
            return {"workouts": workouts, "page": page, "page_size": page_size, "workout_count": workout_count}

        except requests.JSONDecodeError as e:
            logging.error(f"JSON decode error fetching PRO workouts: {e}")
            raise HevyError(f"JSON decode error occurred: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error fetching PRO workouts: {e}")
            if e.response.status_code == 401:
                raise HevyError("Unauthorized - Invalid API key")
            ### Handle 404 when no more workouts are available
            if e.response.status_code == 404:
                logging.debug(f"No workouts found on page {page} (404)")
                return {"workouts": [], "page": page, "page_size": page_size, "workout_count": 0}
            raise HevyError(f"HTTP error occurred: {e}")
        except requests.ConnectionError as e:
            logging.error(f"Connection error fetching PRO workouts: {e}")
            raise HevyError(f"Connection error occurred: {e}")
        except requests.Timeout as e:
            logging.error(f"Timeout error fetching PRO workouts: {e}")
            raise HevyError(f"Request timed out: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching PRO workouts: {e}")
            raise HevyError(f"Unexpected error occurred: {e}")

    def validate_api_key(self) -> bool:
        """
        Validate the Hevy PRO API key by attempting to fetch a single workout.

        Returns:
            bool: True if valid, False otherwise
        """
        logging.debug("Validating PRO API key...")

        if not self.api_key:
            logging.warning("No API key to validate")
            return False

        try:
            ### Try to fetch a single workout to validate the key
            response = self.session.get(self.config.pro_workouts_url, params={"page": 1, "pageSize": 1})

            is_valid = response.status_code == 200
            logging.debug(f"PRO API key validation result: {is_valid}")
            return is_valid

        except requests.RequestException as e:
            logging.error(f"Error validating PRO API key: {e}")
            raise HevyError(f"PRO API key validation failed: {e}")


### ============================================================================


class HevyError(Exception):
    """Custom error for Hevy API operations."""

    pass
