from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import get_db
from predictions.predictor import make_prediction
from schemas.schemas import PredictionRequest
from utils.utils import verify_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@router.post("/predict/", summary="Сделать предсказание", description="Используйте этот маршрут для получения предсказания курса валюты", response_description="Предсказанное значение")
async def predict(request: PredictionRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    verify_token(token)  # Проверка токена
    result = await make_prediction(request, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result