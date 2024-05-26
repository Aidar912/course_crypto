import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Model as DBModel
from schemas.schemas import Model, ModelCreate, ModelUpdate
import os
import datetime

router = APIRouter()

UPLOAD_DIRECTORY = "./models"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

@router.post(
    "/",
    response_model=Model,
    status_code=status.HTTP_201_CREATED,
    summary="Создать модель",
    description="Создание новой модели с загрузкой файла модели и указанием типа (pkl или h5)."
)
async def create_model(
    name: str,
    type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if type not in ["pkl", "h5"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid type. Must be 'pkl' or 'h5'."
        )

    db_model = db.query(DBModel).filter(DBModel.name == name).first()
    if db_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model with this name already exists."
        )

    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_model = DBModel(name=name, path=file_path, type=type, last_update=datetime.datetime.now())
    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    return new_model

@router.get(
    "/",
    response_model=List[Model],
    summary="Получить список моделей",
    description="Получение списка всех моделей с возможностью пагинации."
)
async def read_models(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    models = db.query(DBModel).offset(skip).limit(limit).all()
    return models

@router.get(
    "/{model_id}",
    response_model=Model,
    summary="Получить модель",
    description="Получение информации о модели по её идентификатору."
)
async def read_model(model_id: int, db: Session = Depends(get_db)):
    db_model = db.query(DBModel).filter(DBModel.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return db_model

@router.put(
    "/{model_id}",
    response_model=Model,
    summary="Обновить модель",
    description="Обновление информации о модели по её идентификатору."
)
async def update_model(model_id: int, model: ModelUpdate, db: Session = Depends(get_db)):
    db_model = db.query(DBModel).filter(DBModel.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    if model.type not in ["pkl", "h5"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid type. Must be 'pkl' or 'h5'."
        )

    db_model.name = model.name
    db_model.type = model.type
    db_model.last_update = datetime.datetime.now()
    db.commit()
    db.refresh(db_model)
    return db_model

@router.delete(
    "/{model_id}",
    response_model=Model,
    summary="Удалить модель",
    description="Удаление модели по её идентификатору."
)
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    db_model = db.query(DBModel).filter(DBModel.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    db.delete(db_model)
    db.commit()
    return db_model
