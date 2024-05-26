from datetime import datetime

from statsmodels.tsa.arima.model import ARIMA

from predictions.load_data import load_data


def learn_model(data_set, currency_name, interval):
    try:
        # Extract the target variable 'Adj Close'
        target_data = data_set['Adj Close']

        # Fit ARIMA model
        model = ARIMA(target_data, order=(1, 1, 1))  # Example order, adjust as needed
        fitted_model = model.fit()

        # Save the model
        current_date = datetime.now()
        formatted_date = current_date.strftime('%Y-%m-%d')
        fitted_model.save(f"../models/arima_{currency_name}_{interval}_{formatted_date}.pkl")

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


data_set = load_data("NEAR-USD")
print(learn_model(data_set, "NEAR-USD", "1h"))