import logging
from datetime import datetime, timedelta
from typing import Any, cast

import httpx
from packaging import version

from app.core.config import settings


VersionCheck = dict[str, Any]
_latest_version_cache: VersionCheck | None = None
_version_checked_at: datetime | None = None


async def check_latest_version() -> VersionCheck:
    global _latest_version_cache, _version_checked_at

    if _latest_version_cache and _version_checked_at and datetime.now() - _version_checked_at < timedelta(hours=6):
        logging.info("Returning cached version check result")
        return _latest_version_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{settings.github_repo}/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = cast(VersionCheck, response.json())
                latest = str(data["tag_name"]).lstrip("v")

                result: VersionCheck = {
                    "current_version": settings.current_version,
                    "latest_version": latest,
                    "update_available": version.parse(latest) > version.parse(settings.current_version),
                    "release_url": data["html_url"],
                    "release_notes": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                }

                _latest_version_cache = result
                _version_checked_at = datetime.now()
                logging.info(
                    f"Version check: current={settings.current_version}, latest={latest}, "
                    f"update_available={result['update_available']}"
                )
                return result

            logging.warning(f"GitHub API returned status {response.status_code}")
            return {
                "current_version": settings.current_version,
                "latest_version": None,
                "update_available": False,
                "error": f"GitHub API returned status {response.status_code}",
            }
    except Exception as e:
        logging.error(f"Error checking version: {e}")
        return {
            "current_version": settings.current_version,
            "latest_version": None,
            "update_available": False,
            "error": "Failed to check for updates from GitHub.",
        }
