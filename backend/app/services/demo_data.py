import json
import logging
from typing import Any, cast

from fastapi import HTTPException

from app.core.config import settings


def load_sample_data(filename: str) -> dict[str, Any]:
    file_path = settings.sample_data_dir / filename

    if not file_path.exists():
        logging.error(f"Sample data file not found: {file_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Demo mode enabled but sample data file '{filename}' not found. Please create it in backend/sample_data/",
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return cast(dict[str, Any], json.load(f))
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in sample data file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON in sample data file '{filename}'")
    except Exception as e:
        logging.error(f"Error loading sample data file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading sample data file '{filename}'")
