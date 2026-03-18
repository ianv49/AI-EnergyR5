import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
import sys
sys.path.append('..')
sys.path.append('../db')
import db_connector
get_connection = db_connector.get_connection
import os
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

def fetch_data(conn, start_date='2025-01-01', end_date='2025-04-01'):
    """Fetch hourly data Jan-Mar 2025 from nasa_power/open_meteo for training."""
    query = """
    SELECT timestamp, solar_energy_yield, temperature, irradiance, wind_speed, hour(timestamp) as hour_of_day, 
           EXTRACT(dow FROM timestamp) as day_of_week
    FROM sensor_data 
    WHERE timestamp >= %s AND timestamp < %s 
    AND source IN ('nasa_power', 'open_meteo')
    AND solar_energy_yield IS NOT NULL
    ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn, params=[start_date, end_date])
    return df

def create_features(df):
    """Add lag features and seasonality."""
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['lag_1'] = df['solar_energy_yield'].shift(1)
    df['lag_24'] = df['solar_energy_yield'].shift(24)  # daily lag
    df['temp_irr_mean'] = (df['temperature'] + df['irradiance']) / 2
    df = df.dropna()
    return df[['solar_energy_yield', 'lag_1', 'lag_24', 'temp_irr_mean', 'hour_of_day', 'day_of_week']]

def generate_apr_timestamps():
    """Generate 720 hourly timestamps for Apr 2025."""
    start = pd.to_datetime('2025-04-01 00:00:00')
    end = pd.to_datetime('2025-04-30 23:00:00')
    timestamps = pd.date_range(start, end, freq='H')
    apr_df = pd.DataFrame({'hour_of_day': timestamps.hour, 'day_of_week': timestamps.dayofweek})
    return apr_df

def main():
    conn = get_connection()
    try:
        print("Fetching Jan-Mar 2025 data...")
        df = fetch_data(conn)
        print(f"Loaded {len(df)} rows")

        print("Creating features...")
        features_df = create_features(df)
        X = features_df.drop('solar_energy_yield', axis=1)
        y = features_df['solar_energy_yield']

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)
        
        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        print(f"Test MAE: {mae:.3f}, RMSE: {rmse:.3f}")

        # Predict Apr 2025 (use mean lags from train for simplicity)
        apr_df = generate_apr_timestamps()
        apr_df['lag_1'] = features_df['solar_energy_yield'].mean()
        apr_df['lag_24'] = features_df['solar_energy_yield'].mean()
        apr_df['temp_irr_mean'] = (25 + 200) / 2  # avg from data
        apr_X = scaler.transform(apr_df[['lag_1', 'lag_24', 'temp_irr_mean', 'hour_of_day', 'day_of_week']])
        apr_forecast = model.predict(apr_X)

        # Save Eforecast.txt
        os.makedirs('ml', exist_ok=True)
        results = pd.DataFrame({
            'timestamp': pd.date_range('2025-04-01', periods=720, freq='H'),
            'predicted_solar_yield_kwh_m2_day': np.clip(apr_forecast, 0, None)
        })
        results.to_csv('ml/Eforecast.txt', sep='\\t', index=False)
        print("✅ Forecasts saved to ml/Eforecast.txt")
        print(results.head(10).to_string(index=False))
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()

