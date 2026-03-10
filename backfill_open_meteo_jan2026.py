"""
Backfill Open-Meteo data for January 2026.
Fetches real historical weather data from Open-Meteo Archive API.
"""
import sys
import os
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_wrappers.open_meteo import get_historical_data, calculate_wind_power_density, calculate_solar_energy_yield
from db.db_connector import get_connection
from scripts.capture_weather_data import insert_weather_data

def backfill_january_2026():
    """Fetch all January 2026 data from Open-Meteo API and store in database."""
    print("Starting January 2026 Open-Meteo data backfill...")
    print("=" * 60)
    
    # Define January 2026 date range
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 31)
    
    print(f"Fetching data from {start_date} to {end_date}")
    print(f"Expected rows: 31 days × 24 hours = 744 rows")
    print()
    
    # Connect to database
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return 0
    
    # Check existing data first
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-01-01' AND timestamp < '2026-02-01'")
    existing = cur.fetchone()[0]
    print(f"Existing Open-Meteo Jan 2026 rows: {existing}")
    
    if existing > 0:
        print(f"⚠️  Warning: {existing} rows already exist. Will skip duplicates.")
    print()
    
    # Fetch historical data from Open-Meteo API
    print("Fetching data from Open-Meteo Archive API...")
    weather_data_list = get_historical_data(start_date, end_date)
    
    if not weather_data_list:
        print("❌ No data returned from Open-Meteo API")
        conn.close()
        return 0
    
    print(f"✅ Fetched {len(weather_data_list)} hourly records from Open-Meteo API")
    print()
    
    # Insert data into database
    print("Inserting data into database...")
    rows_inserted = 0
    rows_skipped = 0
    
    for weather_data in weather_data_list:
        try:
            timestamp = weather_data['timestamp']
            temperature = weather_data['temperature']
            humidity = weather_data['humidity']
            wind_speed = weather_data['wind_speed']
            irradiance = weather_data['irradiance']
            
            # Calculate derived values
            wind_power_density = calculate_wind_power_density(wind_speed)
            solar_energy_yield = calculate_solar_energy_yield(irradiance)
            
            # Create tuple for insertion
            weather_tuple = (timestamp, temperature, humidity, irradiance, wind_speed)
            
            # Insert with source='open_meteo'
            insert_weather_data(
                conn, 
                weather_tuple, 
                source='open_meteo',
                wind_power_density=wind_power_density,
                solar_energy_yield=solar_energy_yield
            )
            rows_inserted += 1
            
            # Progress indicator every 100 rows
            if rows_inserted % 100 == 0:
                print(f"  Progress: {rows_inserted}/{len(weather_data_list)} rows inserted")
            
        except Exception as e:
            print(f"❌ Error inserting data for {weather_data.get('timestamp')}: {e}")
            continue
    
    conn.close()
    
    print()
    print("=" * 60)
    print(f"✅ Backfill complete!")
    print(f"   Rows inserted: {rows_inserted}")
    print(f"   Date range: {start_date} to {end_date}")
    
    # Verify final count
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-01-01' AND timestamp < '2026-02-01'")
    total = cur.fetchone()[0]
    print(f"   Total Open-Meteo Jan 2026 rows in DB: {total}")
    conn.close()
    
    return rows_inserted

if __name__ == "__main__":
    backfill_january_2026()
