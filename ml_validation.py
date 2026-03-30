#!/usr/bin/env python3
"""
ML Validation Script - Compare predictions vs actual data
Production-ready modular code with error handling
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
from pathlib import Path
import logging

# Constants
SCALING_FACTOR = 0.5  # Wind power density scaling
PANEL_AREA = 1.6      # m² per panel
EFFICIENCY = 0.20     # 20% panel efficiency

# Date range for comparison
TARGET_DATES = pd.date_range('2025-03-25', '2025-04-07', freq='D').strftime('%Y-%m-%d')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create required directories"""
    Path('charts').mkdir(exist_ok=True)
    Path('data').mkdir(exist_ok=True)
    logger.info("Directories ready")

def load_ml_predictions(ml_file='data/MLoutput.txt'):
    """
    Load ML predictions (Data-A) for Apr 1-7
    Returns DataFrame with columns: id, timestamp, wind-min, wind-avg, wind-max, solar-min, solar-avg, solar-max, source
    """
    try:
        if not os.path.exists(ml_file):
            raise FileNotFoundError(f"{ml_file} not found")
        
        df = pd.read_csv(ml_file, skiprows=11, names=['id', 'timestamp', 'wind-min', 'wind-avg', 'wind-max', 'solar-min', 'solar-avg', 'solar-max', 'source'])  # Skip 11 lines + explicit names
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_ml = df[df['timestamp'].dt.strftime('%Y-%m-%d').isin(TARGET_DATES)]
        
        if df_ml.empty:
            logger.warning("No ML predictions found for target dates")
            return pd.DataFrame()
            
        logger.info(f"Loaded {len(df_ml)} ML predictions")
        return df_ml[['id', 'timestamp', 'wind-min', 'wind-avg', 'wind-max', 
                     'solar-min', 'solar-avg', 'solar-max', 'source']]
    except Exception as e:
        logger.error(f"Error loading ML predictions: {e}")
        return pd.DataFrame()

def load_api_data(api_file='data/collect1.txt'):
    """
    Load actual sim API data for Apr 1-7 from collect1.txt
    Returns DataFrame with raw columns
    """
    try:
        if not os.path.exists(api_file):
            raise FileNotFoundError(f"{api_file} not found")
        
        # Skip 3 lines: #header + #Summary + [sim]\n        df = pd.read_csv(api_file, skiprows=3, names=['id', 'timestamp', 'temperature', 'humidity', 'irradiance', 'wind_speed', 'source', 'wind_power_density', 'solar_energy_yield'])  # Skip + names
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_api = df[df['timestamp'].dt.strftime('%Y-%m-%d').isin(TARGET_DATES)]
        
        if df_api.empty:
            logger.warning("No API data found for target dates")
            return pd.DataFrame()
            
        logger.info(f"Loaded {len(df_api)} API data points")
        return df_api
    except Exception as e:
        logger.error(f"Error loading API data: {e}")
        return pd.DataFrame()

def calculate_energy(df):
    """
    Calculate wind-energy and solar-energy
    wind-energy = wind-avg^3 * scaling_factor
    solar-energy = solar-avg * panel_area * efficiency
    """
    if df.empty:
        return df
        
    df = df.copy()
    df['wind-energy'] = np.power(df['wind_speed'], 3) * SCALING_FACTOR
    df['solar-energy'] = df['solar_energy_yield'] * PANEL_AREA * EFFICIENCY
    
    logger.info("Energy calculations complete")
    return df

def save_results(df_ml, df_api):
    """
    Save Data-A (ML predictions) + Data-B (API + energy) to MLres1.txt
    """
    try:
        ml_res_file = 'data/MLres1.txt'
        
        # Data-A: ML predictions
        if not df_ml.empty:
            df_ml.to_csv(ml_res_file, index=False, mode='w')
            logger.info(f"Saved Data-A ({len(df_ml)} rows) to {ml_res_file}")
        
        # Data-B: API + energy (append)
        if not df_api.empty:
            df_api.to_csv(ml_res_file, index=False, mode='a', header=False)
            logger.info(f"Appended Data-B ({len(df_api)} rows) to {ml_res_file}")
        
        logger.info(f"Results saved: {ml_res_file}")
        return ml_res_file
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return None

def build_charts(df_ml, df_api):
    """
    Create 3 comparison charts and save as PNG
    """
    if df_ml.empty or df_api.empty:
        logger.warning("Skipping charts - missing data")
        return
    
    try:
        # Prepare daily aggregates for comparison
        df_ml_daily = df_ml.groupby(df_ml['timestamp'].dt.date)['wind-avg', 'solar-avg'].mean().reset_index()
        df_ml_daily['type'] = 'Prediction'
        df_ml_daily['date_str'] = df_ml_daily['timestamp'].dt.strftime('%Y-%m-%d')
        
        df_api_daily = df_api.groupby(df_api['timestamp'].dt.date)['wind_speed', 'solar_energy_yield'].mean().reset_index()
        df_api_daily.columns = ['timestamp', 'wind-avg', 'solar-avg']
        df_api_daily['type'] = 'Actual'
        df_api_daily['date_str'] = df_api_daily['timestamp'].dt.strftime('%Y-%m-%d')
        
        comparison = pd.concat([df_ml_daily, df_api_daily])
        
        # Chart 1: Wind Avg comparison
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 3, 1)
        for t in comparison['type'].unique():
            subset = comparison[comparison['type'] == t]
            plt.plot(subset['date_str'], subset['wind-avg'], marker='o', label=t, linewidth=2.5)
        plt.title('Wind Avg: Prediction vs Actual', fontsize=14, fontweight='bold')
        plt.ylabel('Wind Avg (m/s)')
        plt.xlabel('Date')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Chart 2: Solar Avg comparison
        plt.subplot(1, 3, 2)
        for t in comparison['type'].unique():
            subset = comparison[comparison['type'] == t]
            plt.plot(subset['date_str'], subset['solar-avg'], marker='s', label=t, linewidth=2.5)
        plt.title('Solar Avg: Prediction vs Actual', fontsize=14, fontweight='bold')
        plt.ylabel('Solar Avg (kWh/m²)')
        plt.xlabel('Date')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # Chart 3: Wind vs Solar Energy (actual only)
        plt.subplot(1, 3, 3)
        actual_energy = df_api_daily[['wind-avg', 'solar-avg']].mean()
        plt.bar(['Wind Energy', 'Solar Energy'], 
                [actual_energy['wind-avg'], actual_energy['solar-avg']], 
                color=['#36a2eb', '#f59e0b'], alpha=0.8)
        plt.title('Actual Energy Comparison', fontsize=14, fontweight='bold')
        plt.ylabel('Average Energy')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('charts/ml_validation.png', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        logger.info("Charts saved to charts/ml_validation.png")
        
    except Exception as e:
        logger.error(f"Error building charts: {e}")

def main():
    """Main workflow orchestration"""
    logger.info("ML Validation Script Started")
    
    # Ensure directories
    ensure_directories()
    
    # Load data
    logger.info("Loading ML predictions...")
    df_ml = load_ml_predictions()
    
    logger.info("Loading API data...")
    df_api = load_api_data()
    
    if df_ml.empty and df_api.empty:
        logger.error("No data found - exiting")
        return
    
    # Calculate energy for API data
    logger.info("Calculating energy...")
    df_api_energy = calculate_energy(df_api)
    
    # Save results
    logger.info("Saving results...")
    result_file = save_results(df_ml, df_api_energy)
    
    # Build charts
    logger.info("Building charts...")
    build_charts(df_ml, df_api_energy)
    
    logger.info(f"✅ Complete! Results: {result_file}")
    logger.info(f"Charts saved in /charts/")

if __name__ == "__main__":
    main()
