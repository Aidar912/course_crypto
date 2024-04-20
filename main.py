from fastapi import FastAPI, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from db.models import Base
from predictions.predictor import make_prediction
from schemas.schemas import PredictionRequest


app = FastAPI(debug=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/predict/")
async def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    result = await make_prediction(request, db)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result



