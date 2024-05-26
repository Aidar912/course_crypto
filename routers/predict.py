from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from predictions.predictor import make_prediction
from schemas.schemas import PredictionRequest

router = APIRouter()

@router.post("/predict/", summary="Сделать предсказание", description="Используйте этот маршрут для получения предсказания курса валюты", response_description="Предсказанное значение")
async def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    result = await make_prediction(request, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result