from pydantic import BaseModel, constr
from datetime import date


class PredictionRequest(BaseModel):
    currency: int
    date: date
    model_name: str