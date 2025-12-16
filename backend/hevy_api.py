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


### Main API client class
class HevyClient:
    """Main API client class for interacting with Hevy services."""

    def __init__(self, auth_token: Optional[str] = None, config: Optional[HevyConfig] = None):
        self.auth_token = auth_token
        self.config = config or HevyConfig()
        self.session = requests.Session()

        if auth_token:
            self._update_headers()

    def _update_headers(self) -> None:
        """Update session headers with current auth token."""
        self.session.headers.update({
            "x-api-key": self.config.x_api_key,
            "auth-token": self.auth_token,
            "Content-Type": "application/json",
        })

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


### ============================================================================


class HevyError(Exception):
    """Custom error for Hevy API operations."""

    pass
