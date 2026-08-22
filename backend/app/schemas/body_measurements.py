from pydantic import BaseModel


class BodyMeasurementRequest(BaseModel):
    date: str
    weight_kg: float
