import logging

from fastapi import APIRouter, Cookie, HTTPException

from app.clients.hevy import HevyClient, HevyError
from app.core.config import settings
from app.schemas.body_measurements import BodyMeasurementRequest
from app.services.demo_data import load_sample_data


router = APIRouter()


@router.get("/body_measurements", tags=["Body Measurements"])
def get_body_measurements(
    hevy_access_token: str | None = Cookie(None),
):
    """
    Get body measurements (weight tracking).

    Returns list of measurements with id, weight_kg, date, and created_at.

    Requires OAuth2 authentication cookie. PRO API does not support body measurements.
    """
    if settings.demo_mode:
        logging.info("Demo mode: Serving sample body measurements")
        return load_sample_data("body_measurements.json")

    if not hevy_access_token or hevy_access_token in ["csv_mode", "api_key_mode"]:
        raise HTTPException(
            status_code=400,
            detail="Body measurements require OAuth2 authentication. Not available for Hevy PRO API key or CSV mode.",
        )

    try:
        client = HevyClient(access_token=hevy_access_token)
        measurements = client.get_body_measurements()
        return measurements

    except HevyError as e:
        logging.error(f"Error fetching body measurements: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/body_measurements_batch", tags=["Body Measurements"])
def post_body_measurements(
    measurement: BodyMeasurementRequest,
    hevy_access_token: str | None = Cookie(None),
):
    """
    Post a new body measurement (weight tracking).

    Requires OAuth2 authentication cookie. PRO API does not support body measurements.

    Args:
        measurement: Body measurement data (date and weight_kg)
    """
    if settings.demo_mode:
        logging.info("Demo mode: Simulating body measurement post")
        return {"message": "Body measurement posted successfully (demo mode)"}

    if not hevy_access_token or hevy_access_token in ["csv_mode", "api_key_mode"]:
        raise HTTPException(
            status_code=400,
            detail="Body measurements require OAuth2 authentication. Not available for Hevy PRO API key or CSV mode.",
        )

    try:
        client = HevyClient(access_token=hevy_access_token)
        client.post_body_measurements(measurement.date, measurement.weight_kg)
        return {"message": "Body measurement posted successfully"}

    except HevyError as e:
        logging.error(f"Error posting body measurement: {e}")
        status_code = 401 if "Unauthorized" in str(e) else 500
        raise HTTPException(status_code=status_code, detail=str(e))
