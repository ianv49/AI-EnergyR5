#!/usr/bin/env python3
import pandas as pd
from datetime import datetime

SCALING_FACTOR = 0.5
PANEL_AREA = 1.6
EFFICIENCY = 0.20

def daily_aggregate_sim(sim_file='data/collect1.txt'):
    """Aggregate hourly sim data to daily for Apr 1-7"""
    df = pd.read_csv(sim_file, skiprows=3)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.date
    apr_df = df[(df['timestamp'] >= datetime(2025, 4, 1).date()) & 
                (df['timestamp'] <= datetime(2025, 4, 7).date())]
    
    daily = apr_df.groupby('timestamp').agg({
        'wind_speed': ['min', 'mean', 'max'],
        'solar_energy_yield': ['min', 'mean', 'max']
    }).round(2)
    
    daily.columns = ['wind-min', 'wind-avg', 'wind-max', 'solar-min', 'solar-avg', 'solar-max']
    daily['wind-energy'] = (daily['wind-avg'] ** 3 * SCALING_FACTOR).round(2)
    daily['solar-energy'] = (daily['solar-avg'] * PANEL_AREA * EFFICIENCY).round(2)
    daily['source'] = 'sim-daily'
    daily = daily.reset_index()
    daily['timestamp'] = pd.to_datetime(daily['timestamp']).dt.strftime('%Y-%m-%d')
    daily['id'] = range(8, 15)  # Match MLoutput ids
    return daily[['id', 'timestamp', 'wind-min', 'wind-avg', 'wind-max', 
                  'solar-min', 'solar-avg', 'solar-max', 'wind-energy', 
                  'solar-energy', 'source']]

def revise_mlres1(mlres_file='data/MLres1.txt'):
    """Revise rows 1-7 with sim daily aggregates + energy"""
    daily_sim = daily_aggregate_sim()
    
    # Overwrite first 7 rows with daily sim data
    daily_sim.to_csv(mlres_file, index=False, mode='w')
    print("✅ Rows 1-7 revised with daily sim Apr 1-7 + energy")
    print(daily_sim)
    
    # Append original hourly Data-B (skip first 7 lines to avoid double header)
    with open(mlres_file, 'r') as f:
        lines = f.readlines()
    
    hourly_lines = lines[8:]  # Skip header + 7 daily rows
    with open(mlres_file, 'a') as f:
        f.writelines(hourly_lines)
    
    print(f"✅ Full MLres1.txt: 7 daily (revised) + original hourly Data-B")

if __name__ == '__main__':
    revise_mlres1()

