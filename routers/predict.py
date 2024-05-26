from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import get_db
from predictions.make_prediction.lstm_prediction import make_lstm_prediction
from predictions.predictor import make_prediction
from schemas.schemas import PredictionRequest
from utils.utils import verify_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@router.post("/predict/", summary="Сделать предсказание", description="Используйте этот маршрут для получения предсказания курса валюты", response_description="Предсказанное значение")
async def predict(request: PredictionRequest):
    try:
        date = request.date
        symbol = request.symbol
        interval = request.interval
        modelPath = request.modelPath

        prediction = make_lstm_prediction(date, symbol, interval, modelPath)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))