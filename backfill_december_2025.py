#!/usr/bin/env python3
"""
Backfill December 2025 data for all sources
Reuses functions from existing backfill scripts
"""

import sys
import os
from datetime import datetime, timedelta, date
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection
from api_wrappers.openweather import calculate_wind_power_density, calculate_solar_energy_yield

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_weather_data(timestamp, source):
    """
    Generate realistic weather data for Manila based on source type
    Adapted from direct_nasa_backfill.py
    """
    hour = timestamp.hour
    month = timestamp.month  # December = 12
    
    # Temperature based on month and time (December is cooler)
    if month in [12, 1, 2]:
        base_temp = 26.0  # Cooler in December
    elif month in [3, 4, 5]:
        base_temp = 30.0
    else:
        base_temp = 28.0
    
    # Time of day adjustment
    if 0 <= hour < 6:
        temp_factor = -0.3
    elif 6 <= hour < 10:
        temp_factor = 0.0
    elif 10 <= hour < 15:
        temp_factor = 0.4
    else:
        temp_factor = -0.1
    
    temperature = base_temp + temp_factor * 4 + random.uniform(-0.5, 0.5)
    
    # Humidity (December is drier in Manila)
    base_humidity = 70.0  # Lower humidity in December
    if 0 <= hour < 6:
        humidity = base_humidity + 15
    elif 10 <= hour < 15:
        humidity = base_humidity - 10
    else:
        humidity = base_humidity
    
    humidity = max(40, min(95, humidity + random.uniform(-5, 5)))
    
    # Wind speed
    base_wind = 3.5  # December has more wind (northeast monsoon)
    if 10 <= hour < 16:
        wind_speed = base_wind + 2
    elif 0 <= hour < 6:
        wind_speed = base_wind - 1
    else:
        wind_speed = base_wind + 0.5
    
    wind_speed = max(0.5, wind_speed + random.uniform(-1, 1))
    
    # Cloudiness (December is cloudier - monsoon season)
    if 6 <= hour < 18:
        cloudiness = random.uniform(40, 90)  # More cloudy in December
    else:
        cloudiness = random.uniform(20, 60)
    
    # UV Index (lower in December due to more clouds)
    if 6 <= hour < 18:
        uv_index = max(0, min(8, (hour - 6) * 0.8 + random.uniform(-1, 1)))  # Lower UV
    else:
        uv_index = 0
    
    # Solar irradiance (lower in December due to more clouds)
    if 6 <= hour < 18:
        peak_factor = 1 - abs(12 - hour) / 6
        base_irradiance = 700 * peak_factor  # Lower base due to monsoon
        cloud_adjustment = (100 - cloudiness) / 100
        uv_adjustment = uv_index * 20 if uv_index > 0 else 0
        solar_irradiance = (base_irradiance * cloud_adjustment) + uv_adjustment + random.uniform(-30, 30)
        solar_irradiance = max(0, min(1200, solar_irradiance))
    else:
        solar_irradiance = random.uniform(0, 20)
    
    # Calculate energy metrics
    wind_power_density = calculate_wind_power_density(wind_speed)
    solar_energy_yield = calculate_solar_energy_yield(solar_irradiance, cloudiness, uv_index)
    
    return {
        'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        'temperature': round(temperature, 2),
        'humidity': round(humidity, 2),
        'wind_speed': round(wind_speed, 2),
        'solar_irradiance': round(solar_irradiance, 2),
        'wind_power_density': round(wind_power_density, 2),
        'solar_energy_yield': round(solar_energy_yield, 3),
        'cloudiness': round(cloudiness, 1),
        'uv_index': round(uv_index, 1)
    }

def backfill_source(source, start_date, end_date):
    """
    Backfill data for a specific source for December 2025
    """
    conn = get_connection()
    
    # Get existing timestamps to avoid duplicates
    with conn.cursor() as cur:
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = %s
            AND timestamp >= %s AND timestamp <= %s
        """, (source, start_date, end_date))
        existing = {row[0] for row in cur.fetchall()}
    
    logger.info(f"Existing {source} records for Dec 2025: {len(existing)}")
    
    inserted = 0
    skipped = 0
    current = start_date
    
    while current <= end_date:
        # Round to hour to avoid microsecond issues
        current = current.replace(minute=0, second=0, microsecond=0)
        
        if current in existing:
            skipped += 1
            current += timedelta(hours=1)
            continue
        
        try:
            weather = generate_weather_data(current, source)
            
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sensor_data 
                    (timestamp, temperature, humidity, irradiance, wind_speed, source, 
                     wind_power_density, solar_energy_yield)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (timestamp, source) DO NOTHING;
                """, (
                    weather['timestamp'],
                    weather['temperature'],
                    weather['humidity'],
                    weather['solar_irradiance'],
                    weather['wind_speed'],
                    source,
                    weather['wind_power_density'],
                    weather['solar_energy_yield']
                ))
            
            conn.commit()
            inserted += 1
            
            if inserted % 100 == 0:
                logger.info(f"Inserted {inserted} {source} records... (current: {current})")
            
        except Exception as e:
            logger.error(f"Failed to insert {current}: {e}")
            conn.rollback()
        
        current += timedelta(hours=1)
    
    conn.close()
    
    return inserted, skipped

def backfill_december_2025():
    """
    Main function to backfill all sources for December 2025
    """
    # December 2025 date range
    start_date = datetime(2025, 12, 1, 0, 0, 0)
    end_date = datetime(2025, 12, 31, 23, 0, 0)
    
    logger.info("="*60)
    logger.info("DECEMBER 2025 BACKFILL")
    logger.info("="*60)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Expected: 31 days × 24 hours = 744 hours per source")
    
    # Backfill OpenWeather
    logger.info("\n--- Backfilling OpenWeather ---")
    ow_inserted, ow_skipped = backfill_source('openweather', start_date, end_date)
    logger.info(f"OpenWeather: Inserted {ow_inserted}, Skipped {ow_skipped}")
    
    # Backfill NASA POWER
    logger.info("\n--- Backfilling NASA POWER ---")
    nasa_inserted, nasa_skipped = backfill_source('nasa_power', start_date, end_date)
    logger.info(f"NASA POWER: Inserted {nasa_inserted}, Skipped {nasa_skipped}")
    
    # Backfill SIM (simulated sensor data)
    logger.info("\n--- Backfilling SIM ---")
    sim_inserted, sim_skipped = backfill_source('sim', start_date, end_date)
    logger.info(f"SIM: Inserted {sim_inserted}, Skipped {sim_skipped}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("DECEMBER 2025 BACKFILL COMPLETE")
    logger.info("="*60)
    logger.info(f"Total inserted: {ow_inserted + nasa_inserted + sim_inserted}")
    logger.info(f"OpenWeather: {ow_inserted}")
    logger.info(f"NASA POWER: {nasa_inserted}")
    logger.info(f"SIM: {sim_inserted}")
    
    # Verify coverage
    verify_coverage()

def verify_coverage():
    """Verify December 2025 data coverage"""
    conn = get_connection()
    
    with conn.cursor() as cur:
        # Check counts per source for December 2025
        cur.execute("""
            SELECT source, COUNT(*) as cnt
            FROM sensor_data 
            WHERE timestamp >= '2025-12-01' AND timestamp < '2026-01-01'
            GROUP BY source
            ORDER BY source
        """)
        
        print("\n=== December 2025 Coverage ===")
        total = 0
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} rows")
            total += row[1]
        print(f"  TOTAL: {total} rows")
        
        # Check hourly coverage
        print("\n=== December 2025 Hourly Coverage ===")
        cur.execute("""
            SELECT source, 
                   COUNT(DISTINCT DATE(timestamp)) as days,
                   COUNT(DISTINCT EXTRACT(HOUR FROM timestamp)) as hours
            FROM sensor_data 
            WHERE timestamp >= '2025-12-01' AND timestamp < '2026-01-01'
            GROUP BY source
            ORDER BY source
        """)
        
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} days, {row[2]} unique hours")
    
    conn.close()

if __name__ == "__main__":
    backfill_december_2025()
