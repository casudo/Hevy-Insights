from dataclasses import dataclass
from os import getenv
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    demo_mode: bool = getenv("DEMO_MODE", "false").lower() == "true"
    sample_data_dir: Path = Path(__file__).resolve().parents[2] / "sample_data"
    log_level: str = getenv("LOG_LEVEL", "INFO")

    current_version: str = "1.8.6"
    github_repo: str = "casudo/Hevy-Insights"

    cookie_secure: bool = getenv("COOKIE_SECURE", "false").lower() == "true"
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_max_age: int = 60 * 60

    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://localhost:80",
    )


settings = Settings()
