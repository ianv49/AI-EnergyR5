#!/usr/bin/env python3
"""Verify Solcast data in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

# Get sample data
cur.execute("""
    SELECT timestamp, temperature, humidity, wind_speed, irradiance, 
           wind_power_density, solar_energy_yield, source 
    FROM sensor_data 
    WHERE source = 'solcast' 
    AND timestamp >= '2026-02-01' 
    AND timestamp < '2026-02-02' 
    ORDER BY timestamp 
    LIMIT 5
""")

print('Sample Solcast Feb 2026 data (first 5 hours):')
print('timestamp, temperature, humidity, wind_speed, irradiance, wind_power_density, solar_energy_yield, source')
for row in cur.fetchall():
    print(f'{row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}, {row[7]}')

# Get summary
cur.execute("""
    SELECT 
        COUNT(*) as total_rows,
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        AVG(irradiance) as avg_irradiance,
        MIN(irradiance) as min_irr,
        MAX(irradiance) as max_irr
    FROM sensor_data 
    WHERE source = 'solcast' 
    AND timestamp >= '2026-02-01' 
    AND timestamp < '2026-03-01'
""")
row = cur.fetchone()
print(f'\nSummary:')
print(f'  Total rows: {row[0]}')
print(f'  Date range: {row[1]} to {row[2]}')
print(f'  Avg irradiance: {round(row[3], 2) if row[3] else "N/A"} W/m²')
print(f'  Min irradiance: {row[4] if row[4] else "N/A"} W/m²')
print(f'  Max irradiance: {row[5] if row[5] else "N/A"} W/m²')

conn.close()
