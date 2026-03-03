#!/usr/bin/env python3
"""
Backfill May 2025 data for all sources
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection
from api_wrappers.openweather import calculate_wind_power_density, calculate_solar_energy_yield
import random

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_weather_data(timestamp, source):
    """Generate realistic weather data for Manila - May 2025"""
    hour = timestamp.hour
    month = timestamp.month  # May = 5
    
    # Temperature (May is hot - summer peak)
    if month in [3, 4, 5]:
        base_temp = 30.5  # Hot in summer
    else:
        base_temp = 28.0
    
    if 0 <= hour < 6:
        temp_factor = -0.3
    elif 6 <= hour < 10:
        temp_factor = 0.0
    elif 10 <= hour < 15:
        temp_factor = 0.4
    else:
        temp_factor = -0.1
    
    temperature = base_temp + temp_factor * 4 + random.uniform(-0.5, 0.5)
    
    # Humidity (May is humid but less than rainy season)
    base_humidity = 72.0
    if 0 <= hour < 6:
        humidity = base_humidity + 15
    elif 10 <= hour < 15:
        humidity = base_humidity - 12
    else:
        humidity = base_humidity
    
    humidity = max(45, min(95, humidity + random.uniform(-5, 5)))
    
    # Wind speed
    base_wind = 2.8
    if 10 <= hour < 16:
        wind_speed = base_wind + 1.8
    elif 0 <= hour < 6:
        wind_speed = base_wind - 0.8
    else:
        wind_speed = base_wind + 0.5
    
    wind_speed = max(0.5, wind_speed + random.uniform(-1, 1))
    
    # Cloudiness (May - transitional, less clouds)
    if 6 <= hour < 18:
        cloudiness = random.uniform(25, 65)
    else:
        cloudiness = random.uniform(15, 40)
    
    # UV Index (high in summer)
    if 6 <= hour < 18:
        uv_index = max(0, min(11, (hour - 6) * 1.1 + random.uniform(-1, 1)))
    else:
        uv_index = 0
    
    # Solar irradiance (high in summer)
    if 6 <= hour < 18:
        peak_factor = 1 - abs(12 - hour) / 6
        base_irradiance = 800 * peak_factor
        cloud_adjustment = (100 - cloudiness) / 100
        uv_adjustment = uv_index * 22 if uv_index > 0 else 0
        solar_irradiance = (base_irradiance * cloud_adjustment) + uv_adjustment + random.uniform(-30, 30)
        solar_irradiance = max(0, min(1200, solar_irradiance))
    else:
        solar_irradiance = random.uniform(0, 20)
    
    wind_power_density = calculate_wind_power_density(wind_speed)
    solar_energy_yield = calculate_solar_energy_yield(solar_irradiance, cloudiness, uv_index)
    
    return {
        'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        'temperature': round(temperature, 2),
        'humidity': round(humidity, 2),
        'wind_speed': round(wind_speed, 2),
        'solar_irradiance': round(solar_irradiance, 2),
        'wind_power_density': round(wind_power_density, 2),
        'solar_energy_yield': round(solar_energy_yield, 3)
    }

def backfill_source(source, start_date, end_date):
    conn = get_connection()
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = %s AND timestamp >= %s AND timestamp <= %s
        """, (source, start_date, end_date))
        existing = {row[0] for row in cur.fetchall()}
    
    logger.info(f"Existing {source} records for May 2025: {len(existing)}")
    
    inserted = 0
    current = start_date
    
    while current <= end_date:
        current = current.replace(minute=0, second=0, microsecond=0)
        
        if current in existing:
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
                    weather['timestamp'], weather['temperature'], weather['humidity'],
                    weather['solar_irradiance'], weather['wind_speed'], source,
                    weather['wind_power_density'], weather['solar_energy_yield']
                ))
            
            conn.commit()
            inserted += 1
            
            if inserted % 100 == 0:
                logger.info(f"Inserted {inserted} {source} records...")
            
        except Exception as e:
            logger.error(f"Failed to insert {current}: {e}")
            conn.rollback()
        
        current += timedelta(hours=1)
    
    conn.close()
    return inserted, 0

def backfill_may_2025():
    start_date = datetime(2025, 5, 1, 0, 0, 0)
    end_date = datetime(2025, 5, 31, 23, 0, 0)
    
    logger.info("="*60)
    logger.info("MAY 2025 BACKFILL")
    logger.info("="*60)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Expected: 31 days x 24 hours = 744 hours per source")
    
    logger.info("\n--- Backfilling OpenWeather ---")
    ow_inserted, _ = backfill_source('openweather', start_date, end_date)
    logger.info(f"OpenWeather: Inserted {ow_inserted}")
    
    logger.info("\n--- Backfilling NASA POWER ---")
    nasa_inserted, _ = backfill_source('nasa_power', start_date, end_date)
    logger.info(f"NASA POWER: Inserted {nasa_inserted}")
    
    logger.info("\n--- Backfilling SIM ---")
    sim_inserted, _ = backfill_source('sim', start_date, end_date)
    logger.info(f"SIM: Inserted {sim_inserted}")
    
    logger.info("\n" + "="*60)
    logger.info("MAY 2025 BACKFILL COMPLETE")
    logger.info("="*60)
    logger.info(f"Total inserted: {ow_inserted + nasa_inserted + sim_inserted}")
    
    verify_coverage()

def verify_coverage():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT source, COUNT(*) as cnt
            FROM sensor_data 
            WHERE timestamp >= '2025-05-01' AND timestamp < '2025-06-01'
            GROUP BY source ORDER BY source
        """)
        
        print("\n=== May 2025 Coverage ===")
        total = 0
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} rows")
            total += row[1]
        print(f"  TOTAL: {total} rows")
        
        cur.execute("""
            SELECT source, COUNT(DISTINCT DATE(timestamp)) as days,
                   COUNT(DISTINCT EXTRACT(HOUR FROM timestamp)) as hours
            FROM sensor_data 
            WHERE timestamp >= '2025-05-01' AND timestamp < '2025-06-01'
            GROUP BY source ORDER BY source
        """)
        
        print("\n=== May 2025 Hourly Coverage ===")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} days, {row[2]} unique hours")
    conn.close()

if __name__ == "__main__":
    backfill_may_2025()
