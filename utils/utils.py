from datetime import datetime, timedelta
from typing import Optional
import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, HTTPException , status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt , JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import csv
from datetime import datetime
from db import models
from db.models import Model
from db.models import User as DBUser
from schemas import schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "courseWork21"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, role="user")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def update_user_role(db: Session, user_id: int, role: str):
    user = get_user(db, user_id)
    if user:
        user.role = role
        db.commit()
        db.refresh(user)
        return user
    return None

def get_model_path_by_name(db: Session, name: str):
    model = db.query(Model).filter(Model.name == name).first()
    if model:
        return model.path
    return None


async def load_model(session: Session, model_name: str):
    model_record = session.query(Model).filter(Model.name == model_name).first()
    if model_record is None:
        return None

    if model_record.type == 'pkl':
        return joblib.load(model_record.path)
    elif model_record.type == 'h5' or model_record.type == 'keras':
        from keras.src.saving import load_model
        return load_model(model_record.path)
    else:
        return None

def prepare_single_input(data, features, target_date):
    if not isinstance(target_date, pd.Timestamp):
        target_date = pd.to_datetime(target_date).date()

    if pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = data['date'].dt.date
    else:
        data['date'] = pd.to_datetime(data['date']).dt.date

    filtered_data = data[data['date'] <= target_date]
    sorted_data = filtered_data.sort_values(by='date', ascending=True)
    if len(sorted_data) < 30:
        raise ValueError("Not enough data to prepare input. Required 30, given {}".format(len(sorted_data)))
    recent_data = sorted_data.tail(30)

    feature_data = recent_data[features]
    X_single = feature_data.to_numpy().reshape(1, 30, len(features))

    return X_single

def safe_convert_to_jsonable(data):
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, (np.float32, np.float64)):
        return float(data)
    if isinstance(data, (np.int32, np.int64)):
        return int(data)
    return data


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def process_csv(file):
    data_list = []
    csv_reader = csv.DictReader(file, fieldnames=["Timestamp", "Open", "High", "Low", "Close", "Volume (BTC)", "Volume (Currency)", "Weighted Price"])
    next(csv_reader)  # Skip the header row
    for row in csv_reader:
        data = {
            "date": datetime.utcfromtimestamp(int(row["Timestamp"])).date(),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume_btc": float(row["Volume (BTC)"]),
            "volume_currency": float(row["Volume (Currency)"]),
            "weighted_price": float(row["Weighted Price"]),
        }
        data_list.append(data)
    return data_list


def get_currency(db: Session, currency_id: int):
    return db.query(models.Currency).filter(models.Currency.id == currency_id).first()

def get_currency_by_name(db: Session, name: str):
    return db.query(models.Currency).filter(models.Currency.name == name).first()

def create_currency(db: Session, currency: models.Currency):
    db.add(currency)
    db.commit()
    db.refresh(currency)
    return currency

def get_all_currency_names(db: Session):
    return db.query(models.Currency.name).all()
