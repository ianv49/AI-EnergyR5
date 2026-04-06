#!/usr/bin/env python3
"""
all-ml.py - Unified ML Pipeline for All Weather Data Sources
Trains RandomForest models on combined NASA, Open-Meteo, Meteostat, Tomorrow.io, WeatherBit data.
Predicts wind & solar for Feb 21-28 2026. Outputs to data/all-ml.txt.
"""

import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

def load_csv_skip_comments(filename):
    """Load CSV, skip lines starting with #."""
    data = []
    if not os.path.exists(filename):
        print(f"⚠️ {filename} not found, skipping...")
        return data
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    data.append(line)
        print(f"✅ Loaded {len(data)} records from {filename}")
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
    return data

def parse_timestamp(ts_str):
    """Parse timestamp string (YYYY-MM-DD HH:MM:SS or YYYY-MM-DD)."""
    try:
        if ' ' in ts_str:
            return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.strptime(ts_str, '%Y-%m-%d')
    except:
        return None

def load_all_sources():
    """Load data from all 5 API sources, merge into single dataset."""
    all_records = []
    
    sources = [
        ('data/nasa-api.txt', 'nasa-API'),
        ('data/opmet-api.txt', 'open-meteo'),
        ('data/metstat-api.txt', 'meteostat'),
        ('data/tomr-api.txt', 'tomorrow-io'),
        ('data/wethbit-api.txt', 'weatherbit'),
    ]
    
    for filepath, source_name in sources:
        lines = load_csv_skip_comments(filepath)
        if not lines:
            continue
            
        for line in lines:
            cols = line.split(',')
            if len(cols) < 7:  # Minimum columns: timestamp, temp, humidity, wind-speed, irradiance, etc.
                continue
            try:
                ts = parse_timestamp(cols[0])
                if not ts:
                    continue
                
                # Extract numeric fields (be flexible with column order)
                temp = float(cols[1]) if len(cols) > 1 else 30.0
                humidity = float(cols[2]) if len(cols) > 2 else 80.0
                wind = float(cols[3]) if len(cols) > 3 else 0.0
                irradiance = float(cols[4]) if len(cols) > 4 else 0.0
                
                all_records.append({
                    'timestamp': ts,
                    'temp': temp,
                    'humidity': humidity,
                    'wind': wind,
                    'irradiance': irradiance,
                    'source': source_name
                })
            except (ValueError, IndexError):
                continue
    
    print(f"\n📊 Loaded {len(all_records)} total records from all sources")
    return all_records

def create_features(timestamp):
    """Create temporal features from timestamp."""
    return {
        'day_of_year': timestamp.timetuple().tm_yday,
        'hour': timestamp.hour,
        'day_of_week': timestamp.weekday(),
        'month': timestamp.month,
    }

def train_ml_model(records):
    """Train RandomForest models on combined data."""
    if len(records) < 100:
        print("❌ Not enough training data")
        return None, None
    
    # Build feature matrix and targets
    X = []
    y_wind = []
    y_solar = []
    
    for rec in records:
        ts = rec['timestamp']
        
        # Only use data up to Feb 20, 2026 for training
        if ts > datetime(2026, 2, 20, 23, 59, 59):
            continue
        
        feat = create_features(ts)
        X.append([
            feat['day_of_year'],
            feat['hour'],
            feat['day_of_week'],
            feat['month'],
            rec['temp'],
            rec['humidity'],
        ])
        y_wind.append(rec['wind'])
        y_solar.append(rec['irradiance'])
    
    if len(X) < 50:
        print(f"❌ Only {len(X)} training records available")
        return None, None
    
    print(f"🤖 Training on {len(X)} records...")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train wind model
    wind_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    wind_model.fit(X_scaled, y_wind)
    
    # Train solar model
    solar_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    solar_model.fit(X_scaled, y_solar)
    
    print("✅ Models trained successfully")
    return (wind_model, solar_model, scaler), records

def predict_daily_avgs(models, scaler):
    """Generate 8 daily predictions for Feb 21-28 2026."""
    wind_model, solar_model, _ = models
    predictions = []
    
    for day_offset in range(8):
        start_date = datetime(2026, 2, 21) + timedelta(days=day_offset)
        day_winds = []
        day_solars = []
        
        # Generate 24 hourly predictions for this day
        for hour in range(24):
            ts = start_date.replace(hour=hour)
            feat = create_features(ts)
            
            X = np.array([[
                feat['day_of_year'],
                feat['hour'],
                feat['day_of_week'],
                feat['month'],
                30.0,  # Dummy temp
                80.0,  # Dummy humidity
            ]])
            X_scaled = scaler.transform(X)
            
            wind_pred = max(0, wind_model.predict(X_scaled)[0])
            solar_pred = max(0, solar_model.predict(X_scaled)[0])
            
            day_winds.append(wind_pred)
            day_solars.append(solar_pred)
        
        wind_min, wind_avg, wind_max = min(day_winds), np.mean(day_winds), max(day_winds)
        solar_min, solar_avg, solar_max = min(day_solars), np.mean(day_solars), max(day_solars)
        
        predictions.append({
            'id': day_offset + 1,
            'date': start_date.strftime('%Y-%m-%d'),
            'wind_min': wind_min,
            'wind_avg': wind_avg,
            'wind_max': wind_max,
            'solar_min': solar_min,
            'solar_avg': solar_avg,
            'solar_max': solar_max,
        })
    
    return predictions

def aggregate_daily_actual(records):
    """Group hourly data into daily min/avg/max for Feb 21-28."""
    daily = {}
    
    for rec in records:
        ts = rec['timestamp']
        if not (datetime(2026, 2, 21) <= ts <= datetime(2026, 2, 28, 23, 59, 59)):
            continue
        
        day_key = ts.strftime('%Y-%m-%d')
        if day_key not in daily:
            daily[day_key] = {'winds': [], 'solars': []}
        
        daily[day_key]['winds'].append(rec['wind'])
        daily[day_key]['solars'].append(rec['irradiance'])
    
    actuals = []
    for day_id, date_str in enumerate(
        [(datetime(2026, 2, 21) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)],
        start=1
    ):
        if date_str in daily:
            winds = daily[date_str]['winds']
            solars = daily[date_str]['solars']
            actuals.append({
                'id': day_id,
                'date': date_str,
                'wind_min': min(winds) if winds else 0,
                'wind_avg': np.mean(winds) if winds else 0,
                'wind_max': max(winds) if winds else 0,
                'solar_min': min(solars) if solars else 0,
                'solar_avg': np.mean(solars) if solars else 0,
                'solar_max': max(solars) if solars else 0,
            })
        else:
            actuals.append({
                'id': day_id,
                'date': date_str,
                'wind_min': 0,
                'wind_avg': 0,
                'wind_max': 0,
                'solar_min': 0,
                'solar_avg': 0,
                'solar_max': 0,
            })
    
    return actuals

def compute_metrics(predictions, actuals):
    """Compute MAE, RMSE, R², correlation for wind-avg."""
    pred_avgs = [p['wind_avg'] for p in predictions]
    actual_avgs = [a['wind_avg'] for a in actuals]
    
    mae = np.mean(np.abs(np.array(pred_avgs) - np.array(actual_avgs)))
    rmse = np.sqrt(np.mean((np.array(pred_avgs) - np.array(actual_avgs)) ** 2))
    
    pred_mean = np.mean(pred_avgs)
    actual_mean = np.mean(actual_avgs)
    ss_res = np.sum((np.array(actual_avgs) - np.array(pred_avgs)) ** 2)
    ss_tot = np.sum((np.array(actual_avgs) - actual_mean) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    cov = np.cov(pred_avgs, actual_avgs)[0, 1]
    corr = cov / (np.std(pred_avgs) * np.std(actual_avgs)) if np.std(pred_avgs) * np.std(actual_avgs) != 0 else 0
    
    return {'MAE': mae, 'RMSE': rmse, 'R²': r2, 'Correlation': corr}

def main():
    print("=" * 70)
    print("ALL-ML: Unified ML Pipeline (All Sources)")
    print("=" * 70)
    
    # Load data
    all_records = load_all_sources()
    if not all_records:
        print("❌ No data loaded")
        return
    
    # Train models
    result = train_ml_model(all_records)
    if not result[0]:
        print("❌ Training failed")
        return
    
    models, records = result
    
    # Generate predictions
    predictions = predict_daily_avgs(models, models[2])
    print(f"\n📈 Generated {len(predictions)} daily predictions")
    
    # Aggregate actuals
    actuals = aggregate_daily_actual(records)
    print(f"📊 Aggregated {len(actuals)} daily actuals")
    
    # Compute metrics
    metrics = compute_metrics(predictions, actuals)
    
    # Write output
    output_lines = [
        f"# ML page output last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Summary: all sources predict = {len(predictions)} | all sources actual = {len(actuals)}",
        "[all-ml]",
        "# Data-A: ML Predictions (Feb 21-28 2026) - Trained on all sources",
        "id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source",
    ]
    
    for p in predictions:
        output_lines.append(f"{p['id']},{p['date']},{p['wind_min']:.2f},{p['wind_avg']:.2f},{p['wind_max']:.2f},{p['solar_min']:.2f},{p['solar_avg']:.2f},{p['solar_max']:.2f},all-ML")
    
    output_lines.append("# Data-B: Actual Observations (Feb 21-28 2026) - Merged from all sources")
    output_lines.append("id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source")
    
    for a in actuals:
        output_lines.append(f"{a['id']},{a['date']},{a['wind_min']:.2f},{a['wind_avg']:.2f},{a['wind_max']:.2f},{a['solar_min']:.2f},{a['solar_avg']:.2f},{a['solar_max']:.2f},multi-source")
    
    output_lines.extend([
        "",
        "[Metrics]",
        f"MAE (wind-avg): {metrics['MAE']:.3f}",
        f"RMSE: {metrics['RMSE']:.3f}",
        f"R² Score: {metrics['R²']:.3f}",
        f"Correlation: {metrics['Correlation']:.3f}",
        "Sources Used: NASA POWER, Open-Meteo, Meteostat, Tomorrow.io, WeatherBit",
    ])
    
    with open('data/all-ml.txt', 'w') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n✅ Output written to data/all-ml.txt")
    print(f"\n📊 METRICS (wind-avg):")
    print(f"   MAE:         {metrics['MAE']:.3f}")
    print(f"   RMSE:        {metrics['RMSE']:.3f}")
    print(f"   R² Score:    {metrics['R²']:.3f}")
    print(f"   Correlation: {metrics['Correlation']:.3f}")

if __name__ == '__main__':
    main()
