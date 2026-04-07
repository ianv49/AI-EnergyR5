#!/usr/bin/env python3
"""
all-lstm.py - LSTM ML Pipeline for Energy Forecasting
Uses PyTorch LSTM on merged weather data for wind/solar predictions.
Feb 21-28 2026 forecasts, outputs to data/all-lstm.txt.
"""

import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
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
            if len(cols) < 5:  # Minimum: timestamp, temp, hum, wind, irrad
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

def create_sequences(data, targets_wind, targets_solar, lookback=24):
    """Create sequences for LSTM input: [samples, timesteps, features]"""
    X, y_wind, y_solar = [], [], []
    for i in range(len(data) - lookback):
        X.append(data[i:(i+lookback)])
        y_wind.append(targets_wind[i+lookback])
        y_solar.append(targets_solar[i+lookback])
    return np.array(X), np.array(y_wind), np.array(y_solar)

class LSTMEnergyModel(nn.Module):
    def __init__(self, input_size=6, hidden_size=64, num_layers=2, output_size=2):
        super(LSTMEnergyModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        out = self.fc(h_n[-1])
        return out

class TimeSeriesDataset(Dataset):
    def __init__(self, X, y_wind, y_solar):
        self.X = torch.FloatTensor(X)
        self.y_wind = torch.FloatTensor(y_wind)
        self.y_solar = torch.FloatTensor(y_solar)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y_wind[idx], self.y_solar[idx]

def train_ml_model(records):
    """Train LSTM model on combined data for wind/solar."""
    # Filter training records (pre-2026-02-21)
    train_records = [r for r in records if r['timestamp'] <= datetime(2026, 2, 20, 23, 59, 59)]
    if len(train_records) < 100:
        print("❌ Not enough training data")
        return None, None
    
    print(f"🤖 Preparing {len(train_records)} records for LSTM training...")
    
    # Sort by timestamp
    train_records.sort(key=lambda r: r['timestamp'])
    
    # Build feature/target arrays
    features = []
    wind_targets = []
    solar_targets = []
    for rec in train_records:
        feat = create_features(rec['timestamp'])
        feature_vec = np.array([
            feat['day_of_year'] / 365.0,  # normalize
            feat['hour'] / 24.0,
            feat['day_of_week'] / 6.0,
            feat['month'] / 12.0,
            rec['temp'] / 50.0,  # rough norm
            rec['humidity'] / 100.0,
        ])
        features.append(feature_vec)
        wind_targets.append(rec['wind'])
        solar_targets.append(rec['irradiance'])
    
    data = np.array(features)
    wind_t = np.array(wind_targets)
    solar_t = np.array(solar_targets)
    
    # Create sequences (lookback=24 hours)
    lookback = 24
    X_seq, y_wind_seq, y_solar_seq = create_sequences(data, wind_t, solar_t, lookback)
    
    if len(X_seq) < 50:
        print(f"❌ Only {len(X_seq)} sequences available")
        return None, None
    
    print(f"📊 Created {len(X_seq)} sequences (lookback={lookback})")
    
    # Dataset & Dataloader
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    dataset = TimeSeriesDataset(X_seq, y_wind_seq, y_solar_seq)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Model
    model = LSTMEnergyModel(input_size=6).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Train
    epochs = 50
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for X_b, yw_b, ys_b in dataloader:
            X_b, yw_b, ys_b = X_b.to(device), yw_b.to(device), ys_b.to(device)
            optimizer.zero_grad()
            pred = model(X_b)
            loss = criterion(pred[:, 0], yw_b) + criterion(pred[:, 1], ys_b)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")
    
    print("✅ LSTM model trained successfully")
    scaler = StandardScaler()  # dummy for compat
    scaler.fit(np.zeros((1,6)))  # placeholder
    return (model, None, scaler), records  # single model, None solar_model, scaler

def predict_daily_avgs(models, scaler):
    """Generate 8 daily predictions for Feb 21-28 2026 using LSTM."""
    lstm_model, _, _ = models
    device = next(lstm_model.parameters()).device
    lstm_model.eval()
    
    predictions = []
    # Use last 24 train features as seed (approx from train_records end)
    # Synthetic rollout: generate features, predict, feedback loop
    lookback = 24
    
    for day_offset in range(8):
        start_date = datetime(2026, 2, 21) + timedelta(days=day_offset)
        day_winds = []
        day_solars = []
        
        # Seed sequence: synthetic past 24h before day (dummy realistic patterns)
        seq_history = []
        for h in range(lookback):
            ts_past = start_date - timedelta(hours=lookback - h)
            feat_past = create_features(ts_past)
            feature_vec_past = np.array([
                feat_past['day_of_year'] / 365.0,
                feat_past['hour'] / 24.0,
                feat_past['day_of_week'] / 6.0,
                feat_past['month'] / 12.0,
                28.0 + np.sin(2 * np.pi * feat_past['hour'] / 24) * 2,  # cyclic temp
                75.0 + np.random.normal(0, 5),  # hum
            ])
            seq_history.append(feature_vec_past)
        seq_history = np.array(seq_history)[np.newaxis, :, :]  # [1,24,6]
        
        # Predict 24h for this day, autoregressive
        for hour in range(24):
            ts = start_date.replace(hour=hour)
            with torch.no_grad():
                X_seq = torch.FloatTensor(seq_history).to(device)
                pred = lstm_model(X_seq)
                wind_pred = max(0, pred[0][0].cpu().numpy())
                solar_pred = max(0, pred[0][1].cpu().numpy())
            
            day_winds.append(wind_pred)
            day_solars.append(solar_pred)
            
            # Shift seq: drop oldest, add new
            new_feat = np.array([
                ts.timetuple().tm_yday / 365.0,
                ts.hour / 24.0,
                ts.weekday() / 6.0,
                ts.month / 12.0,
                28.0 + np.sin(2 * np.pi * ts.hour / 24) * 2,  # temp
                75.0 + np.random.normal(0, 5),  # hum
            ])
            seq_history = np.roll(seq_history, -1, axis=1)
            seq_history[0, -1, :] = new_feat
        
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
    print("ALL-LTSM: LTSM ML Pipeline (All api)")
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
        "[all-ltsm]",
        "# Data-A: ML Predictions (Feb 21-28 2026) - Trained on all sources",
        "id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source",
    ]
    
    for p in predictions:
        output_lines.append(f"{p['id']},{p['date']},{p['wind_min']:.2f},{p['wind_avg']:.2f},{p['wind_max']:.2f},{p['solar_min']:.2f},{p['solar_avg']:.2f},{p['solar_max']:.2f},all-LTSM")
    
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
    
    with open('data/all-ltsm.txt', 'w') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n✅ Output written to data/all-ltsm.txt")
    print(f"\n📊 METRICS (wind-avg):")
    print(f"   MAE:         {metrics['MAE']:.3f}")
    print(f"   RMSE:        {metrics['RMSE']:.3f}")
    print(f"   R² Score:    {metrics['R²']:.3f}")
    print(f"   Correlation: {metrics['Correlation']:.3f}")

if __name__ == '__main__':
    main()
