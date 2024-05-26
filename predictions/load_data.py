from datetime import datetime, timedelta

import yfinance as yf

from predictions.lstm_learn import learn_model


def load_data(currency_name, interval="1h"):
    current_date = datetime.now()

    # Преобразовать дату в строку в нужном формате
    formatted_date = current_date.strftime('%Y-%m-%d')

    # Получить дату 100 дней назад
    date_100_days_ago = current_date - timedelta(days=120)

    # Преобразовать дату 100 дней назад в строку в нужном формате
    formatted_date_100_days_ago = date_100_days_ago.strftime('%Y-%m-%d')
    try:
        data = yf.download(tickers=currency_name, start=formatted_date_100_days_ago, end=formatted_date,
                           interval=interval)
        if data.empty:
            raise ValueError(f"No price data found for pepe in the specified period.")
        print(data.info())
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
        print(data.info())
        return data
    except ValueError as ve:
        try:
            data = yf.download(tickers=currency_name, end=formatted_date,
                               interval=interval)

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
            print(data.head())
            return data
        except:
            return None

    except Exception as e:
        print(e)
        return None


data_set = load_data('ETH-USD', '1h')
learn_model(data_set, 'ETH-USD', '1h')
