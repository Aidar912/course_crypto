from datetime import datetime

import numpy as np
from keras import Input, Model, Sequential
from keras.api import optimizers
from keras.src.layers import LSTM, Dense, Activation
from keras.src.saving import load_model
from sklearn.metrics import explained_variance_score
from sklearn.preprocessing import MinMaxScaler



# def learn_model(data_set, currency_name, interval):
#     try:
#         print(data_set.info())
#         sc = MinMaxScaler(feature_range=(0, 1))
#         data_set_scaled = sc.fit_transform(data_set)
#         print(data_set_scaled)
#
#         X = []
#         print(data_set_scaled[0].size)
#         # data_set_scaled=data_set.values
#         backcandles = 30
#         print(data_set_scaled.shape[0])
#         for j in range(7):  # data_set_scaled[0].size):#2 columns are target not X
#             X.append([])
#             for i in range(backcandles, data_set_scaled.shape[0]):  # backcandles+2
#                 X[j].append(data_set_scaled[i - backcandles:i, j])
#
#         # move axis from 0 to position 2
#         X = np.moveaxis(X, [0], [2])
#
#         # Erase first elements of y because of backcandles to match X length
#         # del(yi[0:backcandles])
#         # X, yi = np.array(X), np.array(yi)
#         # Choose -1 for last column, classification else -2...
#         X, yi = np.array(X), np.array(data_set_scaled[backcandles:, -1])
#         y = np.reshape(yi, (len(yi), 1))
#
#         # split data into train test sets
#         splitlimit = int(len(X) * 0.8)
#         print(splitlimit)
#         X_train, X_test = X[:splitlimit], X[splitlimit:]
#         y_train, y_test = y[:splitlimit], y[splitlimit:]
#
#         lstm_input = Input(shape=(backcandles, 7), name='lstm_input')
#         inputs = LSTM(150, name='first_layer')(lstm_input)
#         inputs = Dense(1, name='dense_layer')(inputs)
#         output = Activation('linear', name='output')(inputs)
#         model = Model(inputs=lstm_input, outputs=output)
#         adam = optimizers.Adam()
#         model.compile(optimizer=adam, loss='mse')
#         model.fit(x=X_train, y=y_train, batch_size=15, epochs=15, shuffle=False, validation_split=0.1)
#         current_date = datetime.now()
#
#         # Преобразовать дату в строку в нужном формате
#         formatted_date = current_date.strftime('%Y-%m-%d')
#         model.save(f"../models/lstm_{currency_name}_{interval}_{formatted_date}.keras")
#         return True
#     except Exception as e:
#         print(e)
#         return False
def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0]   ###i=0, 0,1,2,3-----99   100
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)

def learn_model(data_set, currency_name, interval):
    try:
        scaler = MinMaxScaler(feature_range=(0, 1))
        data_set = scaler.fit_transform(np.array(data_set).reshape(-1, 1))

        training_size = int(len(data_set) * 0.60)
        test_size = len(data_set) - training_size
        train_data, test_data = data_set[0:training_size, :], data_set[training_size:len(data_set), :1]
        print("train_data: ", train_data.shape)
        print("test_data: ", test_data.shape)

        time_step = 15
        X_train, y_train = create_dataset(train_data, time_step)
        X_test, y_test = create_dataset(test_data, time_step)

        print("X_train: ", X_train.shape)
        print("y_train: ", y_train.shape)
        print("X_test: ", X_test.shape)
        print("y_test", y_test.shape)

        # reshape input to be [samples, time steps, features] which is required for LSTM
        X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

        print("X_train: ", X_train.shape)
        print("X_test: ", X_test.shape)

        model = Sequential()

        model.add(LSTM(10, input_shape=(None, 1), activation="relu"))

        model.add(Dense(1))

        model.compile(loss="mean_squared_error", optimizer="adam")

        history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=200, batch_size=32, verbose=1)

        current_date = datetime.now()
        # model = load_model("../models/lstm_BTC-USD_1h_2024-05-26.keras")

        train_predict = model.predict(X_train)
        test_predict = model.predict(X_test)

        train_predict = scaler.inverse_transform(train_predict)
        test_predict = scaler.inverse_transform(test_predict)
        original_ytrain = scaler.inverse_transform(y_train.reshape(-1, 1))
        original_ytest = scaler.inverse_transform(y_test.reshape(-1, 1))

        print("Train data explained variance regression score:",
              explained_variance_score(original_ytrain, train_predict))
        print("Test data explained variance regression score:",
              explained_variance_score(original_ytest, test_predict))


        # Преобразовать дату в строку в нужном формате
        formatted_date = current_date.strftime('%Y-%m-%d')
        model.save(f"../models/lstm_{currency_name}_{interval}_{formatted_date}.keras")
        return True
    except Exception as e:
        print(e)
        return False

