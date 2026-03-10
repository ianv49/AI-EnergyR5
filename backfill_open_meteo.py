"""
Backfill Open-Meteo data for any month.
Fetches real historical weather data from Open-Meteo Archive API.
Usage: python backfill_open_meteo.py [year] [month]
Example: python backfill_open_meteo.py 2025 10
"""
import sys
import os
from datetime import date, timedelta
import calendar

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_wrappers.open_meteo import get_historical_data, calculate_wind_power_density, calculate_solar_energy_yield
from db.db_connector import get_connection
from scripts.capture_weather_data import insert_weather_data

def backfill_month(year, month):
    """Fetch all data for a specific month from Open-Meteo API and store in database."""
    print(f"Starting Open-Meteo data backfill for {year}-{month:02d}...")
    print("=" * 60)
    
    # Calculate date range for the month
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    print(f"Fetching data from {start_date} to {end_date}")
    print(f"Expected rows: {last_day} days × 24 hours = {last_day * 24} rows")
    print()
    
    # Connect to database
    conn = get_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return 0
    
    # Check existing data first
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= %s AND timestamp < %s", 
                (f"{year}-{month:02d}-01", f"{year}-{month:02d}-28" if month == 12 else f"{year}-{month+1:02d}-01"))
    existing = cur.fetchone()[0]
    print(f"Existing Open-Meteo {year}-{month:02d} rows: {existing}")
    
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
    if month == 12:
        next_month = f"{year+1}-01-01"
    else:
        next_month = f"{year}-{month+1:02d}-01"
    cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= %s AND timestamp < %s", 
                (f"{year}-{month:02d}-01", next_month))
    total = cur.fetchone()[0]
    print(f"   Total Open-Meteo {year}-{month:02d} rows in DB: {total}")
    conn.close()
    
    return rows_inserted

if __name__ == "__main__":
    # Default to October 2025 if no arguments provided
    if len(sys.argv) >= 3:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        year = 2025
        month = 10
        print(f"No arguments provided, using default: {year}-{month:02d}")
    
    print(f"Backfilling Open-Meteo data for {year}-{month:02d}")
    backfill_month(year, month)
