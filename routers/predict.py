from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import get_db
from predictions.make_prediction.lstm_prediction import make_lstm_prediction
from predictions.predictor import make_prediction
from schemas.schemas import PredictionRequest
from utils.utils import verify_token, get_model_path_by_name

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/predict/", summary="Сделать предсказание",
             description="Используйте этот маршрут для получения предсказания курса валюты",
             response_description="Предсказанное значение")
async def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    try:
        date = request.date
        symbol = request.symbol
        interval = request.interval
        model_name = request.model_name

        path = get_model_path_by_name(db, model_name)
        if path is None:
            raise HTTPException(status_code=404, detail="Model not found")

        # Использование пути модели для предсказания
        prediction = make_lstm_prediction(date, symbol, interval, path)
        return {"prediction":  round(float(prediction), 2)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))