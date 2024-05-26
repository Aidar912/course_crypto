from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import engine
from db.models import Base
from routers import auth, users, predict, model, currency

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = FastAPI(
    title="Currency Prediction API",
    description="API для предсказания курса валют с использованием моделей машинного обучения",
    version="1.0.0",
    docs_url="/docs",  # URL для документации Swagger
    redoc_url="/redoc"  # URL для документации ReDoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_root():
    return {"message": "Добро пожаловать в Model API!"}

app.include_router(model.router, prefix="/api/models", tags=["Models"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(predict.router, prefix="/api", tags=["predict"])
app.include_router(currency.router,prefix="/api/currency",tags=["currency"])






