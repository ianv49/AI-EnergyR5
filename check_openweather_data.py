#!/usr/bin/env python3
"""Quick check of OpenWeather data quality"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

# Check sample data
print("=== OpenWeather Sample (Jan 1-2, 2025) ===")
cur.execute("""
    SELECT timestamp, wind_speed, irradiance, wind_power_density, solar_energy_yield
    FROM sensor_data 
    WHERE source = 'openweather' 
    AND timestamp >= '2025-01-01' 
    AND timestamp < '2025-01-02'
    ORDER BY timestamp 
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]} | wind_speed={row[1]} | irradiance={row[2]} | wind_pd={row[3]} | solar_yield={row[4]}")

# Check total by month
print("\n=== OpenWeather 2025 Monthly Breakdown ===")
cur.execute("""
    SELECT 
        TO_CHAR(timestamp, 'YYYY-MM') as month,
        COUNT(*) as cnt,
        AVG(wind_speed) as avg_wind,
        AVG(irradiance) as avg_irr
    FROM sensor_data 
    WHERE source = 'openweather' 
    AND timestamp >= '2025-01-01' 
    AND timestamp < '2026-01-01'
    GROUP BY month
    ORDER BY month
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} rows | avg_wind={row[2]:.2f} | avg_irr={row[3]:.2f}")

# Check if there's realistic variation (not all same values)
print("\n=== OpenWeather Data Variation Check ===")
cur.execute("""
    SELECT 
        MIN(wind_speed) as min_wind,
        MAX(wind_speed) as max_wind,
        MIN(irradiance) as min_irr,
        MAX(irradiance) as max_irr,
        COUNT(DISTINCT wind_speed) as unique_wind,
        COUNT(DISTINCT irradiance) as unique_irr
    FROM sensor_data 
    WHERE source = 'openweather' 
    AND timestamp >= '2025-01-01' 
    AND timestamp < '2026-01-01'
""")
row = cur.fetchone()
print(f"  Wind speed range: {row[0]} - {row[1]} m/s ({row[4]} unique values)")
print(f"  Irradiance range: {row[2]} - {row[3]} W/m² ({row[5]} unique values)")

conn.close()

