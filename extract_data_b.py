#!/usr/bin/env python3
import pandas as pd
from datetime import datetime

# Constants (matching ml_validation.py)
SCALING_FACTOR = 0.5
PANEL_AREA = 1.6
EFFICIENCY = 0.20

def load_sim_data(file='data/collect1.txt'):
    df = pd.read_csv(file, skiprows=3)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def filter_apr_1_7(df):
    target_start = datetime(2025, 4, 1).date()
    target_end = datetime(2025, 4, 7).date()
    return df[(df['timestamp'].dt.date >= target_start) & 
              (df['timestamp'].dt.date <= target_end)].copy()

def calculate_energy(df):
    df['wind-energy'] = (df['wind_speed'] ** 3) * SCALING_FACTOR
    df['solar-energy'] = df['solar_energy_yield'] * PANEL_AREA * EFFICIENCY
    return df

def prepare_data_b(df):
    # Select/rename columns to match spec (use wind_speed as wind-avg proxy, etc.)
    data_b = df[['id', 'timestamp', 'wind_speed', 'wind_speed', 'wind_speed', 
                 'solar_energy_yield', 'solar_energy_yield', 'solar_energy_yield',
                 'wind-energy', 'solar-energy', 'source']].copy()
    data_b.columns = ['id', 'timestamp', 'wind-min', 'wind-avg', 'wind-max', 
                      'solar-min', 'solar-avg', 'solar-max', 'wind-energy', 
                      'solar-energy', 'source']
    return data_b.round(2)

def append_data_b(filename='data/MLres1.txt'):
    df = load_sim_data()
    df_apr = filter_apr_1_7(df)
    df_energy = calculate_energy(df_apr)
    data_b = prepare_data_b(df_energy)
    
    # Append without header
    data_b.to_csv(filename, mode='a', header=False, index=False)
    print(f"✅ Data-B appended: {len(data_b)} rows (Apr 1-7 sim data)")
    print(data_b.head())

if __name__ == '__main__':
    append_data_b()

