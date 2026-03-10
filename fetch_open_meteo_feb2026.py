"""
Script to fetch February 2026 data from Open-Meteo API and store in database.
"""
import sys
import os
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_wrappers.open_meteo import get_historical_data, calculate_wind_power_density, calculate_solar_energy_yield
from db.db_connector import get_connection
from scripts.capture_weather_data import insert_weather_data

def fetch_february_2026_data():
    """Fetch all February 2026 data from Open-Meteo API and store in database."""
    print("Starting February 2026 Open-Meteo data fetch...")
    
    # Define February 2026 date range
    start_date = date(2026, 2, 1)
    end_date = date(2026, 2, 28)  # 2026 is not a leap year
    
    print(f"Fetching data from {start_date} to {end_date}")
    
    # Fetch historical data from Open-Meteo API
    weather_data_list = get_historical_data(start_date, end_date)
    
    if not weather_data_list:
        print("No data returned from Open-Meteo API")
        return 0
    
    print(f"Fetched {len(weather_data_list)} hourly records from Open-Meteo API")
    
    # Insert data into database
    conn = get_connection()
    if not conn:
        print("Failed to connect to database")
        return 0
    
    rows_inserted = 0
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
            
            # Insert with source='open_meteo' to distinguish from other sources
            insert_weather_data(
                conn, 
                weather_tuple, 
                source='open_meteo',
                wind_power_density=wind_power_density,
                solar_energy_yield=solar_energy_yield
            )
            rows_inserted += 1
            
        except Exception as e:
            print(f"Error inserting data for {weather_data.get('timestamp')}: {e}")
            continue
    
    conn.close()
    print(f"Successfully inserted {rows_inserted} rows into database")
    
    return rows_inserted

if __name__ == "__main__":
    fetch_february_2026_data()
