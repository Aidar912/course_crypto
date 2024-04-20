import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import CurrencyData, Model


async def load_model(session: Session, model_name: str):

    model_record = session.query(Model).filter(Model.name == model_name).first()
    if model_record is None:
        return None

    if model_record.type == 'pkl':
        return joblib.load(model_record.path)
    elif model_record.type == 'h5':
        from keras.models import load_model
        return load_model(model_record.path)
    else:
        return None


def prepare_single_input(data, features, target_date):
    # Преобразование target_date в формат datetime.date для сравнения
    if not isinstance(target_date, pd.Timestamp):
        target_date = pd.to_datetime(target_date).date()

    # Убедиться, что 'date' в data преобразован в datetime.date
    if pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = data['date'].dt.date
    else:
        data['date'] = pd.to_datetime(data['date']).dt.date

    # Фильтрация данных для получения 30 дней до включительно target_date
    filtered_data = data[data['date'] <= target_date]
    sorted_data = filtered_data.sort_values(by='date', ascending=True)
    if len(sorted_data) < 30:
        raise ValueError("Not enough data to prepare input. Required 30, given {}".format(len(sorted_data)))
    recent_data = sorted_data.tail(30)

    # Извлечение нужных столбцов
    feature_data = recent_data[features]

    # Изменение формы данных под нужды модели
    X_single = feature_data.to_numpy().reshape(1, 30, len(features))

    return X_single

def safe_convert_to_jsonable(data):
    if isinstance(data, np.ndarray):
        return data.tolist()  # Преобразуем массивы NumPy в список
    if isinstance(data, (np.float32, np.float64)):
        return float(data)  # Преобразуем NumPy float в Python float
    if isinstance(data, (np.int32, np.int64)):
        return int(data)  # Преобразуем NumPy int в Python int
    return data

async def make_prediction(request, db: Session):
    model = await load_model(db, request.model_name)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found or model type is unsupported")

    # Извлечение последних 30 записей до указанной даты
    data = db.query(CurrencyData).filter(
        CurrencyData.currency_id == request.currency,
        CurrencyData.date <= request.date
    ).order_by(CurrencyData.date.desc()).limit(30).all()

    # Проверка, достаточно ли данных
    if len(data) < 30:
        raise HTTPException(status_code=400, detail=f"Not enough data available for the given parameters. Only {len(data)} records found.")

    # Переворачиваем данные для правильного хронологического порядка
    data.reverse()

    # Создание DataFrame
    data_df = pd.DataFrame({
        'date': [d.date for d in data],
        'Open': [d.open for d in data],
        'High': [d.high for d in data],
        'Low': [d.low for d in data],
        'Close': [d.close for d in data]
    })

    # Подготовка данных для модели
    X_single = prepare_single_input(data_df, ['Open', 'High', 'Low', 'Close'], request.date)

    prediction = model.predict(X_single)
    predicted_value = safe_convert_to_jsonable(prediction[0][0])

    # Возврат предсказанного значения
    return {"predicted_price": predicted_value}