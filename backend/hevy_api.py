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
    auth_token: str
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None


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
    def validate_token_url(self) -> str:
        return f"{self.base_url}/validate_auth_token"

    @property
    def user_account_url(self) -> str:
        return f"{self.base_url}/user/account"

    @property
    def user_workouts_paged_url(self) -> str:
        return f"{self.base_url}/user_workouts_paged"

    @property
    def pro_workouts_url(self) -> str:
        return f"{self.base_url}/v1/workouts"


### Main API client class
class HevyClient:
    """Main API client class for interacting with Hevy services."""

    def __init__(self, auth_token: Optional[str] = None, pro_api_key: Optional[str] = None, config: Optional[HevyConfig] = None):
        self.auth_token = auth_token # Username/Password auth token
        self.pro_api_key = pro_api_key  # Hevy PRO API key
        self.config = config or HevyConfig()
        self.session = requests.Session()

        if auth_token or pro_api_key:
            self._update_headers()

    def _update_headers(self) -> None:
        """Update session headers with current auth token or PRO API key."""
        headers = {
            "Content-Type": "application/json",
        }
        
        ### Use PRO API key if available, otherwise use auth token
        if self.pro_api_key:
            headers["api-key"] = self.pro_api_key
        elif self.auth_token:
            headers["x-api-key"] = self.config.x_api_key
            headers["auth-token"] = self.auth_token
            
        self.session.headers.update(headers)

    ### ========== Free Hevy API Methods ==========

    def login(self, email_or_username: str, password: str) -> HevyUser:
        """
        Login with username/email and password to get auth token.

        Args:
            email_or_username: User's email or username
            password: User's password

        Returns:
            HevyUser: User data with auth token

        Raises:
            HevyError: If login fails or returns unexpected response
        """
        logging.debug(f"Attempting login for user: {email_or_username}")

        headers = {"x-api-key": self.config.x_api_key, "Content-Type": "application/json"}

        body = {"emailOrUsername": email_or_username, "password": password, "useAuth2_0": True}

        try:
            response = self.session.post(self.config.login_url, headers=headers, json=body)
            response.raise_for_status()

            data = response.json()

            ### Update client's auth token and headers after successful login
            self.auth_token = data.get("auth_token")
            self._update_headers()

            return HevyUser(
                auth_token=data.get("auth_token"),
                user_id=data.get("user_id"),
                username=email_or_username if "@" not in email_or_username else None,
                email=email_or_username if "@" in email_or_username else None,
            )

        except requests.JSONDecodeError as e:
            logging.error(f"JSON decode error during login: {e}")
            raise HevyError(f"JSON decode error occurred: {e}")
        except requests.HTTPError as e:
            logging.error(f"HTTP error during login: {e}")
            if e.response.status_code == 401:
                raise HevyError("Invalid credentials")
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

    def validate_auth_token(self) -> bool:
        """
        Validate the authentication token.

        Returns:
            bool: True if valid, False otherwise

        Raises:
            HevyError: If validation request fails
        """
        logging.debug("Validating auth token...")

        if not self.auth_token:
            logging.warning("No auth token to validate")
            return False

        try:
            response = self.session.post(self.config.validate_token_url, json={"authToken": self.auth_token})

            is_valid = response.status_code == 200
            logging.debug(f"Token validation result: {is_valid}")
            return is_valid

        except requests.RequestException as e:
            logging.error(f"Error validating auth token: {e}")
            raise HevyError(f"Token validation failed: {e}")

    def get_user_account(self) -> Optional[dict]:
        """
        Fetch user account information.

        Returns:
            Optional[dict]: User account data if successful, None otherwise

        Raises:
            HevyError: If API request fails
        """
        logging.debug("Fetching user account information...")

        if not self.auth_token:
            raise HevyError("No auth token available. Please login first.")

        try:
            response = self.session.get(self.config.user_account_url)
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
                raise HevyError("Unauthorized - Invalid or expired auth token")
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

        if not self.auth_token:
            raise HevyError("No auth token available. Please login first.")

        params = {"offset": offset, "username": username}

        try:
            response = self.session.get(self.config.user_workouts_paged_url, params=params)
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
                raise HevyError("Unauthorized - Invalid or expired auth token")
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

        if not self.pro_api_key:
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


### ============================================================================


class HevyError(Exception):
    """Custom error for Hevy API operations."""

    pass
