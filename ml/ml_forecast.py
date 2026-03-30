#!/usr/bin/env python3
"""
ML Forecast Script - Train RandomForest on collect1.txt history, predict next 14 days
Appends predictions to data/MLoutput.txt as 'sim-ML-new'
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
from datetime import datetime, timedelta
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_historical_data(file='data/collect1.txt'):
    """Load hourly sim data for training"""
    try:
        df = pd.read_csv(file, skiprows=3)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.dropna()
        logger.info(f"Loaded {len(df)} historical records for training")
        return df
    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        return pd.DataFrame()

def prepare_features_target(df, target_horizon_days=14):
    """Prepare features (temp, humidity, irradiance, hour, dayofyear) for wind/solar prediction"""
    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour
    df['dayofyear'] = df['timestamp'].dt.dayofyear
    df['wind_energy'] = np.power(df['wind_speed'], 3) * 0.5  # Scaling factor from validation.py
    
    features = ['temperature', 'humidity', 'irradiance', 'hour', 'dayofyear']
    targets = ['wind_speed', 'solar_energy_yield', 'wind_energy']
    
    X = df[features].values
    y_wind = df['wind_speed'].values
    y_solar = df['solar_energy_yield'].values
    y_wind_energy = df['wind_energy'].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    logger.info(f"Features shape: {X_scaled.shape}, Targets: wind={len(y_wind)}, solar={len(y_solar)}")
    return X_scaled, y_wind, y_solar, y_wind_energy, scaler, features

def train_models(X, y_wind, y_solar, y_wind_energy):
    """Train separate RF models for wind_speed, solar_yield, wind_energy"""
    rf_wind = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_solar = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_wind_energy = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    rf_wind.fit(X, y_wind)
    rf_solar.fit(X, y_solar)
    rf_wind_energy.fit(X, y_wind_energy)
    
    logger.info("Models trained successfully")
    return rf_wind, rf_solar, rf_wind_energy

def predict_next_14_days(scaler, rf_wind, rf_solar, rf_wind_energy, features, last_date):
    """Generate synthetic features for next 14 days, predict min/avg/max"""
    predictions = []
    current_date = last_date
    
    for day_offset in range(14):
        current_date += timedelta(days=1)
        for hour in range(24):
            # Synthetic features based on historical patterns + noise
            temp = 26 + np.sin(2*np.pi*current_date.timetuple().tm_yday/365)*3 + np.random.normal(0, 1)
            humidity = 75 + np.random.normal(0, 10)
            irradiance = max(0, 400 * np.sin(np.pi * hour / 12) * np.sin(np.pi * hour / 24) + np.random.normal(0, 50))
            hour_feat = hour
            dayofyear = current_date.timetuple().tm_yday
            
            feat_row = np.array([[temp, humidity, irradiance, hour_feat, dayofyear]])
            feat_scaled = scaler.transform(feat_row)
            
            wind_pred = rf_wind.predict(feat_scaled)[0]
            solar_pred = rf_solar.predict(feat_scaled)[0]
            wind_energy_pred = rf_wind_energy.predict(feat_scaled)[0]
            
            predictions.append({
                'timestamp': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'wind_speed': wind_pred,
                'solar_yield': solar_pred,
                'wind_energy': wind_energy_pred
            })
    
    return predictions

def daily_aggregates(predictions):
    """Compute daily min/avg/max from hourly predictions"""
    df_pred = pd.DataFrame(predictions)
    df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])
    df_daily = df_pred.groupby(df_pred['timestamp'].dt.date).agg({
        'wind_speed': ['min', 'mean', 'max'],
        'solar_yield': ['min', 'mean', 'max']
    }).round(2)
    
    df_daily.columns = ['wind-min', 'wind-avg', 'wind-max', 'solar-min', 'solar-avg', 'solar-max']
    df_daily['id'] = range(1, len(df_daily)+1)
    df_daily['timestamp'] = [d.strftime('%Y-%m-%d') for d in df_daily.index]
    df_daily['source'] = 'sim-ML-new'
    
    # Reorder columns to match MLoutput.txt
    cols = ['id', 'timestamp', 'wind-min', 'wind-avg', 'wind-max', 'solar-min', 'solar-avg', 'solar-max', 'source']
    df_daily = df_daily[cols]
    
    logger.info(f"Generated {len(df_daily)} daily predictions")
    return df_daily

def append_to_mloutput(df_new):
    """Append new predictions to data/MLoutput.txt"""
    ml_file = 'data/MLoutput.txt'
    if not os.path.exists(ml_file):
        logger.warning(f"{ml_file} not found - creating")
        df_new.to_csv(ml_file, index=False)
    else:
        # Append without header
        df_new.to_csv(ml_file, mode='a', header=False, index=False)
    
    logger.info(f"Appended {len(df_new)} new predictions to {ml_file}")

def main():
    df_hist = load_historical_data()
    if df_hist.empty:
        return
    
    X, y_wind, y_solar, y_wind_energy, scaler, features = prepare_features_target(df_hist)
    
    rf_wind, rf_solar, rf_wind_energy = train_models(X, y_wind, y_solar, y_wind_energy)
    
    # Predict from last date in data
    last_date = df_hist['timestamp'].max().date()
    hourly_preds = predict_next_14_days(scaler, rf_wind, rf_solar, rf_wind_energy, features, last_date)
    
    df_daily_new = daily_aggregates(hourly_preds)
    append_to_mloutput(df_daily_new)
    
    logger.info("✅ Forecasting complete - New predictions appended to MLoutput.txt")
    print("\nSample new predictions:")
    print(df_daily_new.head())

if __name__ == "__main__":
    main()
