import pandas as pd
import os
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from datetime import datetime, timedelta
import numpy as np

def get_future_data(today_date=None):
    try:
        if today_date is None:
            today_date = datetime.now().date()

        # Load the weather data
        csv_path = os.path.join(os.path.dirname(__file__), "dataset.csv")
        weather = pd.read_csv(csv_path, index_col="DATE")
        weather.index = pd.to_datetime(weather.index)

        # Prepare the data
        core_weather = weather[["PRCP", "TMAX", "TMIN"]].copy()
        core_weather.columns = ["precip", "temp_max", "temp_min"]

        # Handle missing values
        imputer = SimpleImputer(strategy='mean')
        core_weather = pd.DataFrame(imputer.fit_transform(core_weather), columns=core_weather.columns, index=core_weather.index)

        # Calculate additional features
        core_weather["month_max"] = core_weather["temp_max"].rolling(30, min_periods=1).mean()
        core_weather["month_day_max"] = core_weather["month_max"].div(core_weather["temp_max"].replace(0, np.nan), fill_value=1)
        core_weather["max_min"] = core_weather["temp_max"].div(core_weather["temp_min"].replace(0, np.nan), fill_value=1)

        # Replace any remaining inf or NaN values with finite numbers
        core_weather.replace([np.inf, -np.inf], np.nan, inplace=True)
        core_weather.fillna(core_weather.mean(), inplace=True)

        # Prepare predictors and target, ensuring equal lengths
        predictors = ["precip", "temp_max", "temp_min", "month_day_max", "max_min"]
        X = core_weather[predictors][:-1]  # Exclude the last row from predictors
        y = core_weather["temp_max"].shift(-1).dropna()  # Target variable with NaN removed

        # Train the model
        reg = make_pipeline(Ridge(alpha=0.1))
        reg.fit(X, y)

        # Make the prediction for tomorrow
        tomorrow = today_date + timedelta(days=1)

        # Use historical data from the same date in previous years
        historical_data = core_weather[core_weather.index.month == tomorrow.month]
        historical_data = historical_data[historical_data.index.day == tomorrow.day]

        # Calculate averages for predictors from historical data
        if not historical_data.empty:
            avg_precip = historical_data["precip"].mean()
            avg_temp_max = historical_data["temp_max"].mean()
            avg_temp_min = historical_data["temp_min"].mean()
            avg_month_day_max = historical_data["month_day_max"].mean()
            avg_max_min = historical_data["max_min"].mean()

            pred_data = pd.DataFrame([[
                avg_precip, avg_temp_max, avg_temp_min, avg_month_day_max, avg_max_min
            ]], columns=predictors)

            prediction = reg.predict(pred_data)[0]

            # Return a dictionary with all relevant data
            return {
                "precip": avg_precip,
                "temp_max": avg_temp_max,
                "temp_min": avg_temp_min,
                "predicted_temp_max": prediction
            }
        else:
            print(f"No historical data available for the date: {tomorrow}")
            return None

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None
