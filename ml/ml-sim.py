#!/usr/bin/env python3
"""
Consolidated ML-Sim API Pipeline
Combines forecasting, validation, data prep, energy calcs from:
- ml/ml-sim-forecast.py (core ML)
- ml_validation.py (validation/charts)
- scripts/build_mlres1.py (metrics)
- extract_data_b.py / revise_mlres1.py (Data-B)
- prepare_data.py (training data)
Apr1 focus: Train on historical sim-api.txt, predict/validate Apr1-7
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import logging
from datetime import datetime, timedelta
import csv
from collections import defaultdict
import math

# Constants (unified)
SCALING_FACTOR = 0.5      # Wind power ~ v^3
PANEL_AREA = 1.6          # m²
EFFICIENCY = 0.20         # Panel efficiency
TARGET_DATES = pd.date_range('2025-04-01', '2025-04-07', freq='D').strftime('%Y-%m-%d')

# Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Path('charts').mkdir(exist_ok=True)
Path('data').mkdir(exist_ok=True)
Path('ml').mkdir(exist_ok=True)

def prepare_training_set():
    """Merge collect*.txt -> ml/training_set.csv with ML features (from prepare_data.py)"""
    all_data = []
    files = ['data/collect1.txt', 'data/collect2.txt', 'data/collect3.txt', 'data/collect4.txt', 
             'data/collect5.txt', 'data/collect6.txt', 'data/collect7.txt']
    
    for f in files:
        if os.path.exists(f):
            df = pd.read_csv(f, comment='#', skip_blank_lines=True)
            df = df[~df['id'].astype(str).str.contains(r'\[', na=False)]
            all_data.append(df)
    
    if not all_data:
        logger.warning("No collect data found")
        return
    
    master_df = pd.concat(all_data, ignore_index=True)
    master_df['timestamp'] = pd.to_datetime(master_df['timestamp'])
    master_df['hour'] = master_df['timestamp'].dt.hour
    master_df['hour_sin'] = np.sin(2 * np.pi * master_df['hour']/24.0)
    master_df['hour_cos'] = np.cos(2 * np.pi * master_df['hour']/24.0)
    master_df = master_df.dropna()
    
    output_path = 'ml/training_set.csv'
    master_df.to_csv(output_path, index=False)
    logger.info(f"Training set created: {output_path} ({len(master_df)} rows)")
    return master_df

def load_historical_sim_data(file='data/sim-api.txt'):
    """Load historical sim data for training (from ml-sim-forecast.py)"""
    try:
        df = pd.read_csv(file, skiprows=3)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[(df['timestamp'] >= '2025-01-01') & (df['timestamp'] < '2026-02-21')]
        df = df.dropna()
        logger.info(f"Loaded {len(df)} historical sim records")
        return df
    except Exception as e:
        logger.error(f"Error loading sim data: {e}")
        return pd.DataFrame()

def prepare_features(df):
    """ML features/targets (unified from forecast)"""
    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour
    df['dayofyear'] = df['timestamp'].dt.dayofyear
    df['wind_energy'] = np.power(df['wind_speed'], 3) * SCALING_FACTOR
    
    features = ['temperature', 'humidity', 'irradiance', 'hour', 'dayofyear']
    targets = ['wind_speed', 'solar_energy_yield', 'wind_energy']
    
    X = df[features].fillna(0).values
    y_wind = df['wind_speed'].fillna(0).values
    y_solar = df['solar_energy_yield'].fillna(0).values
    y_wind_energy = df['wind_energy'].fillna(0).values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y_wind, y_solar, y_wind_energy, scaler, features

def train_ml_models(X, y_wind, y_solar, y_wind_energy):
    """Train 3 RF models"""
    rf_wind = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_solar = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_wind_energy = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    rf_wind.fit(X, y_wind)
    rf_solar.fit(X, y_solar)
    rf_wind_energy.fit(X, y_wind_energy)
    
    logger.info("✅ Models trained")
    return rf_wind, rf_solar, rf_wind_energy

def generate_predictions(scaler, models, n_days=7, start_date='2025-04-01'):
    """Predict daily for Apr1-7 using synthetic features"""
    rf_wind, rf_solar, rf_wind_energy = models
    predictions = []
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    for day_offset in range(n_days):
        current_date = start_dt + timedelta(days=day_offset)
        for hour in range(24):
            # Synthetic features (historical patterns + noise)
            temp = 26 + np.sin(2*np.pi*current_date.timetuple().tm_yday/365)*3 + np.random.normal(0, 1)
            humidity = 75 + np.random.normal(0, 10)
            irradiance = max(0, 400 * np.sin(np.pi * hour / 12) * np.sin(np.pi * hour / 24) + np.random.normal(0, 50))
            feat_row = np.array([[temp, humidity, irradiance, hour, current_date.timetuple().tm_yday]])
            feat_scaled = scaler.transform(feat_row)
            
            wind_pred = rf_wind.predict(feat_scaled)[0]
            solar_pred = rf_solar.predict(feat_scaled)[0]
            predictions.append({
                'timestamp': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'wind_speed': round(wind_pred, 2),
                'solar_energy_yield': round(solar_pred, 2)
            })
    
    # Daily aggregates
    df_pred = pd.DataFrame(predictions)
    df_pred['timestamp'] = pd.to_datetime(df_pred['timestamp'])
    df_daily = df_pred.groupby(df_pred['timestamp'].dt.date).agg({
        'wind_speed': ['min', 'mean', 'max'],
        'solar_energy_yield': ['min', 'mean', 'max']
    }).round(2)
    
    df_daily.columns = ['wind-min', 'wind-avg', 'wind-max', 'solar-min', 'solar-avg', 'solar-max']
    df_daily['id'] = range(1, len(df_daily)+1)
    df_daily['timestamp'] = [d.strftime('%Y-%m-%d') for d in df_daily.index]
    df_daily['source'] = 'sim-api-ML-apr1'
    cols = ['id', 'timestamp', 'wind-min', 'wind-avg', 'wind-max', 'solar-min', 'solar-avg', 'solar-max', 'source']
    df_daily = df_daily[cols]
    
    logger.info(f"Generated {len(df_daily)} Apr predictions")
    return df_daily

def append_predictions(df_daily, output_file='data/ml-sim-output.txt'):
    """Append predictions (unified output)"""
    if not os.path.exists(output_file):
        df_daily.to_csv(output_file, index=False)
    else:
        df_daily.to_csv(output_file, mode='a', header=False, index=False)
    logger.info(f"Appended to {output_file}")

def load_ml_predictions(ml_file='data/ml-sim-output.txt'):
    """Load predictions for validation"""
    try:
        if not os.path.exists(ml_file):
            return pd.DataFrame()
        df = pd.read_csv(ml_file, skiprows=11, names=['id', 'timestamp', 'wind-min', 'wind-avg', 'wind-max', 'solar-min', 'solar-avg', 'solar-max', 'source'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_ml = df[df['timestamp'].dt.strftime('%Y-%m-%d').isin(TARGET_DATES)]
        return df_ml
    except:
        return pd.DataFrame()

def load_actual_api(api_file='data/collect1.txt'):
    """Load sim API actuals"""
    try:
        if not os.path.exists(api_file):
            return pd.DataFrame()
        df = pd.read_csv(api_file, skiprows=3, names=['id', 'timestamp', 'temperature', 'humidity', 'irradiance', 'wind_speed', 'source', 'wind_power_density', 'solar_energy_yield'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_api = df[df['timestamp'].dt.strftime('%Y-%m-%d').isin(TARGET_DATES)]
        return df_api
    except:
        return pd.DataFrame()

def calculate_energy(df):
    """Energy calcs"""
    df = df.copy()
    df['wind-energy'] = np.power(df['wind_speed'], 3) * SCALING_FACTOR
    df['solar-energy'] = df['solar_energy_yield'] * PANEL_AREA * EFFICIENCY
    return df

def aggregate_daily_api(df_api):
    """Daily aggs for API (from build_mlres1.py)"""
    daily = defaultdict(list)
    for _, row in df_api.iterrows():
        date = row['timestamp'].strftime('%Y-%m-%d')
        daily[date].append(row)
    
    results = []
    schema = ["id","timestamp","wind-min","wind-avg","wind-max","solar-min","solar-avg","solar-max","source"]
    for i, date in enumerate(sorted(daily), 1):
        rows = daily[date]
        wind_vals = [row['wind_speed'] for row in rows]
        solar_vals = [row['solar_energy_yield'] for row in rows]
        results.append({
            "id": i, "timestamp": date,
            "wind-min": min(wind_vals), "wind-avg": np.mean(wind_vals), "wind-max": max(wind_vals),
            "solar-min": min(solar_vals), "solar-avg": np.mean(solar_vals), "solar-max": max(solar_vals),
            "source": "sim-API"
        })
    return pd.DataFrame(results)

def save_mlres1(df_ml, df_api_daily, mlres_file='data/MLres1.txt'):
    """Unified save with metrics"""
    with open(mlres_file, "w") as f:
        f.write("# ML-Sim Consolidated Results (Apr 1-7)\n")
        f.write(f"# Predictions: {len(df_ml)} | Actuals: {len(df_api_daily)}\n")
        f.write("[sim]\n")
        
        writer = csv.writer(f)
        schema = ["id","timestamp","wind-min","wind-avg","wind-max","solar-min","solar-avg","solar-max","source"]
        writer.writerow(schema)
        
        # Data-A ML
        for _, row in df_ml.iterrows():
            writer.writerow([row[col] for col in schema])
        
        # Data-B API
        for _, row in df_api_daily.iterrows():
            writer.writerow([row[col] for col in schema])
        
        # Metrics
        f.write("\n# Metrics\n")
        if len(df_ml) > 0 and len(df_api_daily) > 0:
            y_pred = df_ml['wind-avg'].values
            y_true = df_api_daily['wind-avg'].values[:len(y_pred)]
            mae = mean_absolute_error(y_true, y_pred)
            rmse = math.sqrt(mean_squared_error(y_true, y_pred))
            r2 = r2_score(y_true, y_pred)
            f.write(f"Wind MAE: {mae:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}\n")
    
    logger.info(f"Saved {mlres_file}")

def build_validation_charts(df_ml, df_api):
    """Charts from ml_validation.py"""
    if df_ml.empty or df_api.empty:
        return
    
    df_ml_daily = df_ml.groupby(df_ml['timestamp'].dt.date)[['wind-avg', 'solar-avg']].mean().reset_index()
    df_ml_daily['type'] = 'ML Predict'
    df_ml_daily['date_str'] = df_ml_daily['timestamp'].dt.strftime('%Y-%m-%d')
    
    df_api_daily = df_api.groupby(df_api['timestamp'].dt.date)[['wind_speed', 'solar_energy_yield']].mean().reset_index()
    df_api_daily.columns = ['timestamp', 'wind-avg', 'solar-avg']
    df_api_daily['type'] = 'Sim API Actual'
    df_api_daily['date_str'] = df_api_daily['timestamp'].dt.strftime('%Y-%m-%d')
    
    comparison = pd.concat([df_ml_daily, df_api_daily])
    
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    
    # Wind
    for t in comparison['type'].unique():
        subset = comparison[comparison['type'] == t]
        axs[0].plot(subset['date_str'], subset['wind-avg'], marker='o', label=t, linewidth=2)
    axs[0].set_title('Wind: Predict vs Actual')
    axs[0].legend()
    axs[0].grid(True, alpha=0.3)
    
    # Solar
    for t in comparison['type'].unique():
        subset = comparison[comparison['type'] == t]
        axs[1].plot(subset['date_str'], subset['solar-avg'], marker='s', label=t, linewidth=2)
    axs[1].set_title('Solar: Predict vs Actual')
    axs[1].legend()
    axs[1].grid(True, alpha=0.3)
    
    # Energy bar
    energy_means = df_api_daily[['wind-avg', 'solar-avg']].mean()
    axs[2].bar(['Wind', 'Solar'], [energy_means['wind-avg'], energy_means['solar-avg']], color=['blue', 'orange'])
    axs[2].set_title('Actual Energy')
    
    for ax in axs:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('charts/ml_sim_validation.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info("Charts saved: charts/ml_sim_validation.png")

def ml_forecast_pipeline():
    """Full ML forecast"""
    df_hist = load_historical_sim_data()
    if df_hist.empty:
        return
    
    # Train
    X, y_wind, y_solar, y_wind_energy, scaler, features = prepare_features(df_hist)
    models = train_ml_models(X, y_wind, y_solar, y_wind_energy)
    
    # Predict
    df_preds = generate_predictions(scaler, models)
    append_predictions(df_preds)
    logger.info("✅ Forecast complete")

def ml_validation_pipeline():
    """Full validation"""
    df_ml = load_ml_predictions()
    df_api = load_actual_api()
    
    if df_ml.empty or df_api.empty:
        logger.warning("Missing data for validation")
        return
    
    df_api = calculate_energy(df_api)
    df_api_daily = aggregate_daily_api(df_api)
    
    save_mlres1(df_ml, df_api_daily)
    build_validation_charts(df_ml, df_api)
    logger.info("✅ Validation complete")

def full_pipeline():
    """End-to-end: prep -> train -> predict -> validate"""
    logger.info("=== ML-Sim Full Pipeline ===")
    prepare_training_set()
    ml_forecast_pipeline()
    ml_validation_pipeline()
    logger.info("=== Pipeline Complete ===")

if __name__ == "__main__":
    # Run specific parts or full
    full_pipeline()

