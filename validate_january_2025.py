#!/usr/bin/env python3
"""
Validate OpenWeather web sensor data against database data for January 2025.
Compares actual API data with database records and calculates offset percentages.
Produces CSV file: 2025_jan_compare.csv
"""

import sys
import os
import csv
import requests
import urllib3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection
from api_wrappers.openweather import (
    calculate_wind_power_density, 
    calculate_solar_energy_yield,
    API_KEY,
    LATITUDE,
    LONGITUDE
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# OpenWeather One Call API 3.0 for historical data
HISTORICAL_URL = f"https://api.openweathermap.org/data/3.0/onecall?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}&units=metric"


def fetch_openweather_current() -> Optional[Dict]:
    """Fetch current weather data from OpenWeather API."""
    try:
        BASIC_URL = f"https://api.openweathermap.org/data/2.5/weather?q=Manila&appid={API_KEY}&units=metric"
        response = requests.get(BASIC_URL, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temperature = data.get('main', {}).get('temp')
        humidity = data.get('main', {}).get('humidity')
        wind_speed = data.get('wind', {}).get('speed')
        cloudiness = data.get('clouds', {}).get('all', 50)
        
        # Get UV index from One Call API if available
        uv_index = 6
        try:
            one_call_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}&units=metric&exclude=minutely,hourly,daily,alerts"
            oc_response = requests.get(one_call_url, timeout=10, verify=False)
            if oc_response.status_code == 200:
                oc_data = oc_response.json()
                uv_index = oc_data.get('current', {}).get('uvi', 6)
        except:
            pass
        
        # Calculate derived values
        solar_irradiance = (100 - cloudiness) * 10 + (uv_index * 25)
        wind_power_density = calculate_wind_power_density(wind_speed)
        solar_energy_yield = calculate_solar_energy_yield(solar_irradiance, cloudiness, uv_index)
        
        return {
            'timestamp': timestamp,
            'temperature': temperature,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'cloudiness': cloudiness,
            'uv_index': uv_index,
            'irradiance': round(solar_irradiance, 2),
            'wind_power_density': wind_power_density,
            'solar_energy_yield': solar_energy_yield
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch current weather: {e}")
        return None


def get_db_data_for_january_2025() -> List[Dict]:
    """Fetch OpenWeather data from database for January 2025"""
    conn = get_connection()
    data = []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, temperature, humidity, wind_speed, irradiance,
                       wind_power_density, solar_energy_yield
                FROM sensor_data
                WHERE source = 'openweather'
                  AND timestamp >= '2025-01-01 00:00:00'
                  AND timestamp < '2025-02-01 00:00:00'
                ORDER BY timestamp
            """)
            
            for row in cur.fetchall():
                data.append({
                    'timestamp': row[0],
                    'temperature': row[1],
                    'humidity': row[2],
                    'wind_speed': row[3],
                    'irradiance': row[4],
                    'wind_power_density': row[5],
                    'solar_energy_yield': row[6]
                })
                
    except Exception as e:
        logger.error(f"Failed to fetch database data: {e}")
    finally:
        conn.close()
    
    return data


def calculate_percentage_offset(value1, value2) -> Optional[float]:
    """Calculate percentage offset between two values"""
    try:
        value1 = float(value1) if value1 is not None else None
        value2 = float(value2) if value2 is not None else None
    except (ValueError, TypeError):
        return None
    
    if value1 is None or value2 is None:
        return None
    if value1 == 0:
        return None if value2 == 0 else 100.0
    
    offset = ((value2 - value1) / value1) * 100
    return round(offset, 2)


def compare_data():
    """Main comparison function"""
    logger.info("="*60)
    logger.info("VALIDATING JANUARY 2025 DATA")
    logger.info("="*60)
    
    # Get database data
    logger.info("Fetching OpenWeather data from database for January 2025...")
    db_data = get_db_data_for_january_2025()
    logger.info(f"Found {len(db_data)} records in database")
    
    if not db_data:
        logger.warning("No OpenWeather data found in database for January 2025")
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT source, COUNT(*) 
                FROM sensor_data 
                WHERE timestamp >= '2025-01-01' AND timestamp < '2025-02-01'
                GROUP BY source
            """)
            logger.info("Data sources available for January 2025:")
            for row in cur.fetchall():
                logger.info(f"  {row[0]}: {row[1]} records")
        conn.close()
        return
    
    # Fetch current API data for comparison
    logger.info("Fetching current weather data from OpenWeather API...")
    api_data = fetch_openweather_current()
    
    if api_data:
        logger.info(f"API data fetched: wind_speed={api_data['wind_speed']}, "
                   f"wind_power_density={api_data['wind_power_density']}, "
                   f"irradiance={api_data['irradiance']}, "
                   f"solar_energy_yield={api_data['solar_energy_yield']}")
    else:
        logger.warning("Could not fetch API data - comparison will use available data")
    
    # Prepare comparison records
    comparison_results = []
    
    for db_record in db_data:
        db_ts = db_record['timestamp']
        
        if api_data:
            api_ts = datetime.now()
            
            # Calculate offsets
            wind_speed_offset = calculate_percentage_offset(db_record['wind_speed'], api_data['wind_speed'])
            wind_power_density_offset = calculate_percentage_offset(db_record['wind_power_density'], api_data['wind_power_density'])
            irradiance_offset = calculate_percentage_offset(db_record['irradiance'], api_data['irradiance'])
            solar_energy_yield_offset = calculate_percentage_offset(db_record['solar_energy_yield'], api_data['solar_energy_yield'])
            
            comparison_results.append({
                'db_timestamp': db_ts.strftime("%Y-%m-%d %H:%M:%S") if db_ts else '',
                'api_timestamp': api_ts.strftime("%Y-%m-%d %H:%M:%S"),
                'db_wind_speed': db_record['wind_speed'],
                'api_wind_speed': api_data['wind_speed'],
                'wind_speed_offset_pct': wind_speed_offset,
                'db_wind_power_density': db_record['wind_power_density'],
                'api_wind_power_density': api_data['wind_power_density'],
                'wind_power_density_offset_pct': wind_power_density_offset,
                'db_irradiance': db_record['irradiance'],
                'api_irradiance': api_data['irradiance'],
                'irradiance_offset_pct': irradiance_offset,
                'db_solar_energy_yield': db_record['solar_energy_yield'],
                'api_solar_energy_yield': api_data['solar_energy_yield'],
                'solar_energy_yield_offset_pct': solar_energy_yield_offset,
                'db_temperature': db_record['temperature'],
                'api_temperature': api_data['temperature'],
                'db_humidity': db_record['humidity'],
                'api_humidity': api_data['humidity']
            })
    
    # Write to CSV
    output_file = "2025_jan_compare.csv"
    logger.info(f"Writing comparison results to {output_file}...")
    
    with open(output_file, 'w', newline='') as f:
        if comparison_results:
            fieldnames = [
                'db_timestamp', 'api_timestamp',
                'db_wind_speed', 'api_wind_speed', 'wind_speed_offset_pct',
                'db_wind_power_density', 'api_wind_power_density', 'wind_power_density_offset_pct',
                'db_irradiance', 'api_irradiance', 'irradiance_offset_pct',
                'db_solar_energy_yield', 'api_solar_energy_yield', 'solar_energy_yield_offset_pct',
                'db_temperature', 'api_temperature',
                'db_humidity', 'api_humidity'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comparison_results)
    
    logger.info(f"Comparison complete! {len(comparison_results)} records written to {output_file}")
    
    # Print summary statistics
    if comparison_results:
        logger.info("\n=== COMPARISON SUMMARY ===")
        
        wind_offsets = [r['wind_speed_offset_pct'] for r in comparison_results if r['wind_speed_offset_pct'] is not None]
        wind_power_offsets = [r['wind_power_density_offset_pct'] for r in comparison_results if r['wind_power_density_offset_pct'] is not None]
        irradiance_offsets = [r['irradiance_offset_pct'] for r in comparison_results if r['irradiance_offset_pct'] is not None]
        solar_offsets = [r['solar_energy_yield_offset_pct'] for r in comparison_results if r['solar_energy_yield_offset_pct'] is not None]
        
        if wind_offsets:
            avg_wind = sum(wind_offsets) / len(wind_offsets)
            logger.info(f"Wind Speed Offset: avg={avg_wind:.2f}%, min={min(wind_offsets):.2f}%, max={max(wind_offsets):.2f}%")
        
        if wind_power_offsets:
            avg_wind_power = sum(wind_power_offsets) / len(wind_power_offsets)
            logger.info(f"Wind Power Density Offset: avg={avg_wind_power:.2f}%, min={min(wind_power_offsets):.2f}%, max={max(wind_power_offsets):.2f}%")
        
        if irradiance_offsets:
            avg_irr = sum(irradiance_offsets) / len(irradiance_offsets)
            logger.info(f"Irradiance Offset: avg={avg_irr:.2f}%, min={min(irradiance_offsets):.2f}%, max={max(irradiance_offsets):.2f}%")
        
        if solar_offsets:
            avg_solar = sum(solar_offsets) / len(solar_offsets)
            logger.info(f"Solar Energy Yield Offset: avg={avg_solar:.2f}%, min={min(solar_offsets):.2f}%, max={max(solar_offsets):.2f}%")
    
    return comparison_results


if __name__ == "__main__":
    compare_data()
