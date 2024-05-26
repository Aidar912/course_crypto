import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import CurrencyData
from utils.utils import load_model, prepare_single_input, safe_convert_to_jsonable

async def make_prediction(request, db: Session):
    model = await load_model(db, request.model_name)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found or model type is unsupported")

    data = db.query(CurrencyData).filter(
        CurrencyData.currency_id == request.currency,
        CurrencyData.date <= request.date
    ).order_by(CurrencyData.date.desc()).limit(30).all()

    if len(data) < 30:
        raise HTTPException(status_code=400, detail=f"Not enough data available for the given parameters. Only {len(data)} records found.")

    data.reverse()

    data_df = pd.DataFrame({
        'date': [d.date for d in data],
        'Open': [d.open for d in data],
        'High': [d.high for d in data],
        'Low': [d.low for d in data],
        'Close': [d.close for d in data]
    })

    X_single = prepare_single_input(data_df, ['Open', 'High', 'Low', 'Close'], request.date)

    prediction = model.predict(X_single)
    predicted_value = safe_convert_to_jsonable(prediction[0][0])

    return {"predicted_price": predicted_value}
