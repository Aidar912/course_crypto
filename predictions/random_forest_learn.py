import joblib
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime

import numpy as np
from sklearn.preprocessing import MinMaxScaler

def learn_model_random_forest(data_set, currency_name, interval):
    try:
        # Scaling the data
        sc = MinMaxScaler(feature_range=(0, 1))
        data_set_scaled = sc.fit_transform(data_set)

        # Prepare X and y
        X = []
        backcandles = 30
        for j in range(7):
            X.append([])
            for i in range(backcandles, data_set_scaled.shape[0]):
                X[j].append(data_set_scaled[i - backcandles:i, j])
        X = np.moveaxis(X, [0], [2])
        X, yi = np.array(X), np.array(data_set_scaled[backcandles:, -1])
        y = np.reshape(yi, (len(yi), 1))

        # Split data into train and test sets
        splitlimit = int(len(X) * 0.8)
        X_train, X_test = X[:splitlimit], X[splitlimit:]
        y_train, y_test = y[:splitlimit], y[splitlimit:]

        # Initialize and train the RandomForestRegressor model
        model = RandomForestRegressor(n_estimators=100, random_state=0)
        model.fit(X_train.reshape(X_train.shape[0], -1), y_train.ravel())

        # Save the model
        current_date = datetime.now()
        formatted_date = current_date.strftime('%Y-%m-%d')
        joblib.dump(model, f"/models/random_forest_{currency_name}_{interval}_{formatted_date}.joblib")

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
