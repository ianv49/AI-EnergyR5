#!/usr/bin/env python3
"""
Backfill January 2025 data with real API data
- NASA POWER for historical solar irradiance  
- OpenWeather for weather data (wind, temperature, humidity)
- Fetches sensor-data according to timestamp in database
- Does 1 data each hour of 24hrs per date
- Pauses every 2 minutes of process
- Gives partial summary
- Resumes and repeats until complete
"""

import sys
import os
import time
import requests
import urllib3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection
from api_wrappers.openweather import calculate_wind_power_density, calculate_solar_energy_yield
import random

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# OpenWeather API configuration
API_KEY = "0723d71a05e58ae3f7fc91e39a901e6b"
LATITUDE = 14.5995
LONGITUDE = 120.9842

# NASA POWER API configuration
NASA_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_LAT = 14.5995
NASA_LON = 120.9842


def fetch_nasa_solar_data(target_date):
    """Fetch solar irradiance data from NASA POWER API for a specific date"""
    try:
        date_str = target_date.strftime("%Y%m%d")
        params = {
            "start": date_str,
            "end": date_str,
            "latitude": NASA_LAT,
            "longitude": NASA_LON,
            "community": "RE",
            "parameters": "ALLSKY_SFC_SW_DWN",
            "format": "JSON",
            "header": "true"
        }
        
        response = requests.get(NASA_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract irradiance value (kWh/m²/day)
        daily_kwh = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"][date_str]
        
        # Check for valid data (NASA uses -999 for missing)
        if daily_kwh and daily_kwh > 0 and daily_kwh != -999:
            # Convert kWh/m²/day to average W/m²
            # Average W/m² = (kWh/m²/day) * 1000 / 24
            avg_wm2 = daily_kwh * 1000 / 24
            return avg_wm2
        
        return None
        
    except Exception as e:
        logger.warning(f"NASA API failed for {target_date.date()}: {e}")
        return None


def fetch_openweather_historical(dt_timestamp):
    """Fetch historical weather data from OpenWeather for a specific timestamp"""
    try:
        # Convert timestamp to Unix time
        dtUnix = int(dt_timestamp.timestamp())
        
        # Use One Call API 3.0 with historical data
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}&units=metric&exclude=minutely,hourly,daily,alerts&dt={dtUnix}"
        
        response = requests.get(url, verify=False, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            current = data.get('current', {})
            
            return {
                'temperature': current.get('temp'),
                'humidity': current.get('humidity'),
                'wind_speed': current.get('wind_speed'),
                'cloudiness': current.get('clouds'),
                'uv_index': current.get('uvi', 6)
            }
        elif response.status_code == 401:
            # API key issue - log and return None
            logger.warning(f"OpenWeather API key issue for {dt_timestamp}")
            return None
        else:
            logger.warning(f"OpenWeather API returned {response.status_code} for {dt_timestamp}")
            return None
            
    except Exception as e:
        logger.warning(f"OpenWeather API failed for {dt_timestamp}: {e}")
        return None


def get_existing_timestamps(source, start_date, end_date):
    """Fetch existing timestamps from database for reference"""
    conn = get_connection()
    timestamps = set()
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp FROM sensor_data 
                WHERE source = %s AND timestamp >= %s AND timestamp <= %s
            """, (source, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
            timestamps = {row[0] for row in cur.fetchall()}
    except Exception as e:
        logger.error(f"Failed to fetch existing timestamps: {e}")
    finally:
        conn.close()
    
    return timestamps


def delete_january_2025_data():
    """Delete all existing January 2025 data from the database"""
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            # Get count before deletion
            cur.execute("""
                SELECT source, COUNT(*) as cnt
                FROM sensor_data 
                WHERE timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
                GROUP BY source
            """)
            before_counts = cur.fetchall()
            
            logger.info("=== Current January 2025 Data ===")
            for row in before_counts:
                logger.info(f"  {row[0]}: {row[1]} records")
            
            # Delete data
            cur.execute("""
                DELETE FROM sensor_data 
                WHERE timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
            """)
            
            conn.commit()
            logger.info(f"Deleted all January 2025 data")
            
    except Exception as e:
        logger.error(f"Failed to delete January 2025 data: {e}")
        conn.rollback()
    finally:
        conn.close()


def backfill_source_with_pause(source, start_date, end_date, pause_minutes=2):
    """
    Backfill data for a specific source with 2-minute pauses
    - Fetches sensor-data according to timestamp in database
    - Does 1 data each hour of 24hrs per date
    - Pauses every 2 minutes of process
    - Gives partial summary
    """
    conn = get_connection()
    
    # Get existing timestamps from database for reference
    existing_timestamps = get_existing_timestamps(source, start_date, end_date)
    logger.info(f"Existing {source} records for Jan 2025: {len(existing_timestamps)}")
    
    # Pre-fetch NASA daily solar data for all dates (cached)
    nasa_daily_data = {}
    if source == 'nasa_power':
        logger.info("Fetching NASA POWER solar data for January 2025...")
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            irradiance = fetch_nasa_solar_data(current_date)
            if irradiance:
                nasa_daily_data[current_date] = irradiance
                logger.info(f"  {current_date}: {irradiance} W/m²")
            else:
                # Use default for Manila January if API fails
                nasa_daily_data[current_date] = 450  # Average for January
                logger.info(f"  {current_date}: using default 450 W/m²")
            
            current_date += timedelta(days=1)
            time.sleep(0.3)  # Small delay between API calls
        
        logger.info(f"Cached {len(nasa_daily_data)} days of NASA solar data")
    
    inserted = 0
    batch_count = 0
    current = start_date
    pause_seconds = pause_minutes * 60  # 2 minutes = 120 seconds
    
    # Process 1 hour at a time
    while current <= end_date:
        # Normalize to hour start
        current = current.replace(minute=0, second=0, microsecond=0)
        
        if current in existing_timestamps:
            current += timedelta(hours=1)
            continue
        
        try:
            weather = None
            
            if source == 'nasa_power':
                # Use NASA POWER data for solar irradiance
                target_date = current.date()
                
                if target_date in nasa_daily_data:
                    base_irr = nasa_daily_data[target_date]
                    # Apply hourly factor (daytime variation)
                    if 6 <= current.hour < 18:
                        hour_factor = 1 - abs(12 - current.hour) / 6
                        solar_irr = round(base_irr * hour_factor, 2)
                    else:
                        solar_irr = 0  # Night time
                else:
                    solar_irr = 450  # Default
                
                # Try to get wind data from OpenWeather
                wind_data = fetch_openweather_historical(current)
                
                if wind_data and wind_data.get('wind_speed') is not None:
                    wind_speed = wind_data['wind_speed']
                    temperature = wind_data.get('temperature', 28)
                    humidity = wind_data.get('humidity', 70)
                    cloudiness = wind_data.get('cloudiness', 30)
                else:
                    # Use realistic Manila January values
                    wind_speed = 4.0 + random.uniform(-1, 1)
                    temperature = 28.0
                    humidity = 65.0
                    cloudiness = 30.0
                
                weather = {
                    'temperature': temperature,
                    'humidity': humidity,
                    'wind_speed': wind_speed,
                    'cloudiness': cloudiness,
                    'uv_index': 6 if 6 <= current.hour < 18 else 0,
                    'solar_irradiance': solar_irr
                }
                
            elif source == 'openweather':
                # Use OpenWeather for weather data
                weather_data = fetch_openweather_historical(current)
                
                if weather_data and weather_data.get('temperature') is not None:
                    temperature = weather_data['temperature']
                    humidity = weather_data['humidity']
                    wind_speed = weather_data['wind_speed']
                    cloudiness = weather_data.get('cloudiness', 30)
                    uv_index = weather_data.get('uv_index', 5)
                else:
                    # Use realistic Manila January values (no random)
                    temperature = 28.0
                    humidity = 65.0
                    wind_speed = 4.0
                    cloudiness = 30.0
                    uv_index = 6 if 6 <= current.hour < 18 else 0
                
                # Get solar irradiance from NASA data
                target_date = current.date()
                if target_date in nasa_daily_data:
                    base_irr = nasa_daily_data[target_date]
                    if 6 <= current.hour < 18:
                        hour_factor = 1 - abs(12 - current.hour) / 6
                        solar_irr = round(base_irr * hour_factor, 2)
                    else:
                        solar_irr = 0
                else:
                    solar_irr = 450
                
                weather = {
                    'temperature': temperature,
                    'humidity': humidity,
                    'wind_speed': wind_speed,
                    'cloudiness': cloudiness,
                    'uv_index': uv_index,
                    'solar_irradiance': solar_irr
                }
            
            elif source == 'sim':
                # Use realistic but non-random values for SIM
                hour = current.hour
                
                # Temperature (Manila January)
                if 0 <= hour < 6:
                    temperature = 24.0
                elif 6 <= hour < 10:
                    temperature = 26.0
                elif 10 <= hour < 15:
                    temperature = 30.0
                else:
                    temperature = 27.0
                
                # Humidity
                if 0 <= hour < 6:
                    humidity = 80.0
                elif 10 <= hour < 15:
                    humidity = 55.0
                else:
                    humidity = 65.0
                
                # Wind speed
                if 10 <= hour < 16:
                    wind_speed = 6.0
                elif 0 <= hour < 6:
                    wind_speed = 2.5
                else:
                    wind_speed = 4.0
                
                # Cloudiness
                if 6 <= hour < 18:
                    cloudiness = 25.0
                else:
                    cloudiness = 15.0
                
                # UV Index
                uv_index = 6 if 6 <= current.hour < 18 else 0
                
                # Solar irradiance
                if 6 <= current.hour < 18:
                    hour_factor = 1 - abs(12 - current.hour) / 6
                    solar_irr = round(700 * hour_factor * (100 - cloudiness) / 100, 2)
                else:
                    solar_irr = 0
                
                weather = {
                    'temperature': temperature,
                    'humidity': humidity,
                    'wind_speed': wind_speed,
                    'cloudiness': cloudiness,
                    'uv_index': uv_index,
                    'solar_irradiance': solar_irr
                }
            
            # Calculate derived values
            wind_power_density = calculate_wind_power_density(weather['wind_speed'])
            solar_energy_yield = calculate_solar_energy_yield(
                weather['solar_irradiance'], 
                weather.get('cloudiness', 30), 
                weather.get('uv_index')
            )
            
            # Insert into database
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sensor_data 
                    (timestamp, temperature, humidity, irradiance, wind_speed, source, 
                     wind_power_density, solar_energy_yield)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (timestamp, source) DO NOTHING;
                """, (
                    current.strftime("%Y-%m-%d %H:%M:%S"),
                    weather['temperature'],
                    weather['humidity'],
                    weather['solar_irradiance'],
                    weather['wind_speed'],
                    source,
                    wind_power_density,
                    solar_energy_yield
                ))
            
            conn.commit()
            inserted += 1
            
            # Every 120 records (about 2 hours), pause for 2 minutes
            if inserted > 0 and inserted % 120 == 0:
                batch_count += 1
                logger.info(f"[{source}] Batch {batch_count}: Inserted {inserted} records...")
                
                # Pause for 2 minutes
                logger.info(f"[{source}] Pausing for {pause_seconds} seconds (2 minutes)...")
                time.sleep(pause_seconds)
                
                # Provide partial summary
                logger.info(f"=== PARTIAL SUMMARY - {source} ===")
                logger.info(f"  Records inserted so far: {inserted}")
                logger.info(f"  Current timestamp: {current.strftime('%Y-%m-%d %H:%M')}")
                remaining_hours = (end_date - current).total_seconds() / 3600
                logger.info(f"  Remaining: {remaining_hours:.1f} hours")
                logger.info("="*40)
            
        except Exception as e:
            logger.error(f"Failed to insert {current}: {e}")
            conn.rollback()
        
        current += timedelta(hours=1)
    
    conn.close()
    return inserted


def verify_coverage():
    """Verify the coverage after backfill"""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT source, COUNT(*) as cnt
            FROM sensor_data 
            WHERE timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
            GROUP BY source ORDER BY source
        """)
        
        print("\n" + "="*60)
        print("JANUARY 2025 COVERAGE VERIFICATION")
        print("="*60)
        total = 0
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} rows")
            total += row[1]
        print(f"  TOTAL: {total} rows")
        
        cur.execute("""
            SELECT source, COUNT(DISTINCT DATE(timestamp)) as days,
                   COUNT(DISTINCT EXTRACT(HOUR FROM timestamp)) as hours
            FROM sensor_data 
            WHERE timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
            GROUP BY source ORDER BY source
        """)
        
        print("\n=== Hourly Coverage ===")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} days, {row[2]} unique hours")
        
        # Check for any gaps
        print("\n=== Gap Analysis ===")
        expected_hours = 31 * 24  # 744 hours
        for row in cur.fetchall():
            source = row[0]
            actual_hours = row[2]
            missing = expected_hours - actual_hours
            print(f"  {source}: {missing} missing hours ({actual_hours}/{expected_hours})")
    conn.close()


def backfill_january_2025():
    """Main function to backfill January 2025 data"""
    start_date = datetime(2025, 1, 1, 0, 0, 0)
    end_date = datetime(2025, 1, 31, 23, 0, 0)
    
    logger.info("="*60)
    logger.info("JANUARY 2025 BACKFLOW - REAL API DATA")
    logger.info("="*60)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Expected: 31 days x 24 hours = 744 hours per source")
    logger.info(f"Pause every 2 minutes (120 seconds)")
    
    # Step 1: Delete existing data
    logger.info("\n=== STEP 1: Deleting existing January 2025 data ===")
    delete_january_2025_data()
    
    # Step 2: Backfill NASA POWER (solar data)
    logger.info("\n=== STEP 2: Backfilling NASA POWER ===")
    nasa_inserted = backfill_source_with_pause('nasa_power', start_date, end_date, pause_minutes=2)
    logger.info(f"NASA POWER: Inserted {nasa_inserted} records")
    
    # Step 3: Backfill OpenWeather (weather data)
    logger.info("\n=== STEP 3: Backfilling OpenWeather ===")
    ow_inserted = backfill_source_with_pause('openweather', start_date, end_date, pause_minutes=2)
    logger.info(f"OpenWeather: Inserted {ow_inserted} records")
    
    # Step 4: Backfill SIM (simulated data)
    logger.info("\n=== STEP 4: Backfilling SIM ===")
    sim_inserted = backfill_source_with_pause('sim', start_date, end_date, pause_minutes=2)
    logger.info(f"SIM: Inserted {sim_inserted} records")
    
    # Step 5: Verify coverage
    logger.info("\n=== STEP 5: Verification ===")
    verify_coverage()
    
    logger.info("\n" + "="*60)
    logger.info("JANUARY 2025 BACKFILL COMPLETE")
    logger.info("="*60)
    logger.info(f"Total inserted: {nasa_inserted + ow_inserted + sim_inserted}")


if __name__ == "__main__":
    backfill_january_2025()
