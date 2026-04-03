#!/usr/bin/env python3
import csv, math
from pathlib import Path
from collections import defaultdict
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
from datetime import datetime, timedelta

nasa_file      = Path("data/nasa-api.txt")
ml_output_file = Path("data/ml-nasa-output.txt")

def load_csv_skip_comments(file_path):
    with open(file_path, newline="") as f:
        lines = [line for line in f if not line.strip().startswith("#") and not line.strip().startswith("[")]
        reader = csv.DictReader(lines)
        rows = []
        for row in reader:
            clean = {k.strip(): v.strip() for k,v in row.items()}
            rows.append(clean)
        return rows, [h.strip() for h in reader.fieldnames]

def parse_date(ts):
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

def create_features(row):
    dt = parse_date(row["timestamp"])
    day_of_year = dt.timetuple().tm_yday
    hour = dt.hour
    day_of_week = dt.weekday()
    month = dt.month
    return [day_of_year, hour, day_of_week, month, float(row["temperature"]), float(row["humidity"])]

def train_ml_model(hourly_data):
    # Train data: Jan 1 2025 to Feb 20 2026
    train_data = [r for r in hourly_data if parse_date(r["timestamp"]).date() <= parse_date("2026-02-20 23:59:59").date()]
    
    X = []
    y_wind = []
    y_solar = []
    for row in train_data:
        features = create_features(row)
        X.append(features)
        y_wind.append(float(row["wind_speed"]))
        y_solar.append(float(row["irradiance"]))
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train models
    wind_model = RandomForestRegressor(n_estimators=100, random_state=42)
    solar_model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    wind_model.fit(X_scaled, y_wind)
    solar_model.fit(X_scaled, y_solar)
    
    return wind_model, solar_model, scaler

def predict_daily_avgs(model_wind, model_solar, scaler):
    # Predict for Feb 21-28 2026
    dates = ["2026-02-21", "2026-02-22", "2026-02-23", "2026-02-24", "2026-02-25", "2026-02-26", "2026-02-27", "2026-02-28"]
    predict_data = []
    
    for i, date in enumerate(dates, 1):
        # Generate 24 hourly timestamps for this date
        daily_hourly = []
        for hour in range(24):
            ts = f"{date} {hour:02d}:00:00"
            dummy_row = {"timestamp": ts, "temperature": "30.0", "humidity": "80.0", "wind_speed": "0", "irradiance": "0"}
            features = create_features(dummy_row)
            daily_hourly.append(features)
        
        X_daily = scaler.transform(daily_hourly)
        wind_preds = model_wind.predict(X_daily)
        solar_preds = model_solar.predict(X_daily)
        
        wind_min, wind_avg, wind_max = min(wind_preds), np.mean(wind_preds), max(wind_preds)
        solar_min, solar_avg, solar_max = min(solar_preds), np.mean(solar_preds), max(solar_preds)
        
        predict_data.append({
            "id": str(i),
            "timestamp": date,
            "wind-min": f"{wind_min:.2f}",
            "wind-avg": f"{wind_avg:.2f}",
            "wind-max": f"{wind_max:.2f}",
            "solar-min": f"{solar_min:.2f}",
            "solar-avg": f"{solar_avg:.2f}",
            "solar-max": f"{solar_max:.2f}",
            "source": "nasa-ML"
        })
    return predict_data

def aggregate_daily_actual(hourly_data):
    daily = defaultdict(list)
    for row in hourly_data:
        date = row["timestamp"].split()[0]
        if "2026-02-21" <= date <= "2026-02-28":
            daily[date].append(row)

    results = []
    for i, date in enumerate(sorted(daily.keys()), start=1):
        rows = daily[date]
        wind_vals = [float(r["wind_speed"]) for r in rows]
        solar_vals = [float(r["irradiance"]) for r in rows]
        wind_min = min(wind_vals)
        wind_avg = sum(wind_vals)/len(wind_vals)
        wind_max = max(wind_vals)
        solar_min = min(solar_vals)
        solar_avg = sum(solar_vals)/len(solar_vals)
        solar_max = max(solar_vals)
        results.append({
            "id": str(i),
            "timestamp": date,
            "wind-min": f"{wind_min:.2f}",
            "wind-avg": f"{wind_avg:.2f}",
            "wind-max": f"{wind_max:.2f}",
            "solar-min": f"{solar_min:.2f}",
            "solar-avg": f"{solar_avg:.2f}",
            "solar-max": f"{solar_max:.2f}",
            "source": "nasa-API"
        })
    return results

def main():
    nasa_data, _ = load_csv_skip_comments(nasa_file)
    
    print("Training ML model using Jan 1 2025 - Feb 20 2026 NASA data...")
    wind_model, solar_model, scaler = train_ml_model(nasa_data)
    
    ml_daily = predict_daily_avgs(wind_model, solar_model, scaler)
    nasa_daily = aggregate_daily_actual(nasa_data)
    
    # Write to ml-nasa-output.txt - FIXED SPACING
    with open(ml_output_file, "w") as f:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"# ML page output last updated: {now_str}\n")
        f.write(f"# Summary: nasa actual = {len(nasa_daily)} | nasa predict = {len(ml_daily)}\n")
        f.write("[nasa]\n\n")
        
        # Data-A Header
        f.write("# Data-A: ML Predictions (Feb 21–28 2026)\n")
        f.write("id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source\n")
        for row in ml_daily:
            f.write(f"{row['id']},{row['timestamp']},{row['wind-min']},{row['wind-avg']},{row['wind-max']},{row['solar-min']},{row['solar-avg']},{row['solar-max']},{row['source']}\n")
        f.write("\n")
        
        # Data-B Header
        f.write("# Data-B: NASA Power Daily Averages (Feb 21–28 2026)\n")
        f.write("id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source\n")
        for row in nasa_daily:
            f.write(f"{row['id']},{row['timestamp']},{row['wind-min']},{row['wind-avg']},{row['wind-max']},{row['solar-min']},{row['solar-avg']},{row['solar-max']},{row['source']}\n")
        f.write("\n")
        
        # Metrics
        f.write("# Metrics: Prediction vs NASA Actual (Feb 21–28 2026)\n")
        pred_map = {r["timestamp"]: r for r in ml_daily}
        actual_map = {r["timestamp"]: r for r in nasa_daily}
        common_dates = sorted(set(pred_map.keys()) & set(actual_map.keys()))

        if not common_dates:
            f.write("No overlapping dates between ML predictions and NASA data.\n")
        else:
            y_pred = [float(pred_map[d]["wind-avg"]) for d in common_dates]
            y_true = [float(actual_map[d]["wind-avg"]) for d in common_dates]
            mae = mean_absolute_error(y_true, y_pred)
            rmse = math.sqrt(mean_squared_error(y_true, y_pred))
            r2 = r2_score(y_true, y_pred)
            corr = np.corrcoef(y_true, y_pred)[0,1]
            f.write(f"MAE (wind-avg): {mae:.3f}\n")
            f.write(f"RMSE: {rmse:.3f}\n")
            f.write(f"R²: {r2:.3f}\n")
            f.write(f"Correlation: {corr:.3f}\n")

    print(f"✅ data/ml-nasa-output.txt generated with NASA ML (Data-A/B + metrics) - FIXED SPACING")

if __name__ == "__main__":
    main()
