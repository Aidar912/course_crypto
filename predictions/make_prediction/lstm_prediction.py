from datetime import timedelta, datetime

import numpy as np
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0]   ###i=0, 0,1,2,3-----99   100
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)

def make_lstm_prediction(date_curr, currency_name, interval , modelPath):
    import numpy as np
    from keras.src.saving import load_model
    current_date = datetime.now()
    if modelPath.endswith('.h5'):
        model = load_model(modelPath)
    elif modelPath.endswith('.keras'):
        model = load_model(modelPath)
    else:
        raise ValueError("Unsupported model file format. Please use '.keras' or '.h5' format.")

    # Преобразовать дату в строку в нужном формате
    formatted_date = current_date.strftime('%Y-%m-%d')

    # Получить дату 100 дней назад
    date_100_days_ago = current_date - timedelta(days=120)

    # Преобразовать дату 100 дней назад в строку в нужном формате
    formatted_date_100_days_ago = date_100_days_ago.strftime('%Y-%m-%d')
    data = yf.download(tickers=currency_name, start=formatted_date_100_days_ago, end=date_curr,
                       interval=interval)
    if data.empty:
        raise ValueError(f"No price data found for pepe in the specified period.")
    data['Target'] = data['Adj Close'] - data['Open']
    data['Target'] = data['Target'].shift(-1)

    # Use .iloc to access elements by position
    data['TargetClass'] = [1 if data['Target'].iloc[i] > 0 else 0 for i in range(len(data))]

    data['TargetNextClose'] = data['Adj Close'].shift(-1)

    data.dropna(inplace=True)
    data.reset_index(inplace=True)
    if interval == "1d":
        data.drop(['Volume', 'Close', 'Date'], axis=1, inplace=True)
    else:
        data.drop(['Volume', 'Close', 'Datetime'], axis=1, inplace=True)
    # Загрузка модели из файла
    model = load_model(modelPath)
    # Прогноз на следующий день
    scaler = MinMaxScaler(feature_range=(0, 1))
    data_set = scaler.fit_transform(np.array(data).reshape(-1, 1))




    # Подготовка данных для подачи в модель
    time_step = 15  # Установите time_step, который был использован при тренировке
    X_data = []
    for i in range(len(data_set) - time_step):
        X_data.append(data_set[i:(i + time_step), 0])
    X_data = np.array(X_data)
    X_data = X_data.reshape(X_data.shape[0], X_data.shape[1], 1)  # Reshape для LSTM

    predictions = model.predict(X_data)
    predictions = scaler.inverse_transform(
        predictions)  # Обратное преобразование для получения исходного масштаба значений

    predictions_response = predictions[-1]
    print(predictions_response[0])
    return float(predictions_response[0])



