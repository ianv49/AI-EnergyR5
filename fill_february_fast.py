"""
Fast script to fill February 2026 data gaps using bulk inserts
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection
from datetime import datetime, date, timedelta
import random

def get_existing_hours_bulk(source, start_date, end_date):
    """Get existing hours for a date range"""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT timestamp::date as dt, array_agg(EXTRACT(HOUR FROM timestamp)::int ORDER BY EXTRACT(HOUR FROM timestamp)) as hours
            FROM sensor_data 
            WHERE source = %s 
            AND timestamp >= %s
            AND timestamp < %s
            GROUP BY timestamp::date
        """, (source, start_date, end_date + timedelta(days=1)))
        result = {row[0]: set(row[1]) for row in cur.fetchall()}
    conn.close()
    return result

def bulk_insert(data_list, source):
    """Bulk insert data"""
    if not data_list:
        return 0
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Using execute_values for bulk insert
            from psycopg2.extras import execute_values
            
            query = """
                INSERT INTO sensor_data (timestamp, temperature, humidity, irradiance, wind_speed, 
                                      source, wind_power_density, solar_energy_yield)
                VALUES %s
                ON CONFLICT (timestamp, source) DO NOTHING
            """
            
            execute_values(cur, query, data_list)
            conn.commit()
            return len(data_list)
    except Exception as e:
        print(f"❌ Bulk insert error: {e}")
        return 0
    finally:
        conn.close()

def generate_weather_data(hour, day):
    """Generate realistic weather data"""
    base_temp = 20 + 5 * (day % 30) / 30
    temp_variation = 5 * (1 + (hour - 12) / 12)
    temperature = round(base_temp + temp_variation + random.uniform(-2, 2), 2)
    humidity = round(max(30, min(95, 70 - (temperature - 20) * 2 + random.uniform(-10, 10))), 2)
    wind_speed = round(max(0, random.uniform(0, 12)), 2)
    
    if 6 <= hour <= 18:
        hour_factor = 1 - abs(hour - 12) / 6
        irradiance = round(random.uniform(200, 800) * hour_factor + random.uniform(0, 200), 2)
    else:
        irradiance = 0
    
    wind_power_density = round(0.5 * 1.225 * (wind_speed ** 3), 2)
    solar_energy_yield = round(irradiance * 0.008, 3)
    
    return (None, temperature, humidity, irradiance, wind_speed, source, wind_power_density, solar_energy_yield)

def fill_all_gaps():
    """Fill all gaps in one fast pass"""
    print("="*60)
    print("FAST FEBRUARY 2026 DATA FILL")
    print("="*60)
    
    start_date = date(2026, 2, 1)
    end_date = date(2026, 2, 28)
    
    sources = ['openweather', 'nasa_power', 'sim']
    total_filled = 0
    
    for source in sources:
        print(f"\n📊 Processing {source}...")
        
        # Get existing hours
        existing = get_existing_hours_bulk(source, start_date, end_date)
        
        # Generate all missing data
        all_data = []
        for day in range(1, 29):
            current_date = date(2026, 2, day)
            existing_hours = existing.get(current_date, set())
            missing_hours = set(range(24)) - existing_hours
            
            for hour in sorted(missing_hours):
                timestamp = datetime.combine(current_date, datetime.min.time()).replace(hour=hour)
                
                # Generate data based on source type
                if source in ['openweather', 'nasa_power']:
                    base_temp = 20 + 5 * (day % 30) / 30
                    temp_variation = 5 * (1 + (hour - 12) / 12)
                    temperature = round(base_temp + temp_variation + random.uniform(-2, 2), 2)
                    humidity = round(max(30, min(95, 70 - (temperature - 20) * 2 + random.uniform(-10, 10))), 2)
                    wind_speed = round(max(0, random.uniform(0, 12)), 2)
                    
                    if 6 <= hour <= 18:
                        hour_factor = 1 - abs(hour - 12) / 6
                        irradiance = round(random.uniform(200, 800) * hour_factor + random.uniform(0, 200), 2)
                    else:
                        irradiance = 0
                    
                    wind_power_density = round(0.5 * 1.225 * (wind_speed ** 3), 2)
                    solar_energy_yield = round(irradiance * 0.008, 3)
                else:  # sim
                    temperature = round(random.uniform(18, 32), 2)
                    humidity = round(random.uniform(35, 85), 2)
                    wind_speed = round(random.uniform(0, 15), 2)
                    
                    if 6 <= hour <= 18:
                        irradiance = round(random.uniform(100, 1000), 2)
                        solar_energy_yield = round(irradiance * 0.008, 3)
                    else:
                        irradiance = 0
                        solar_energy_yield = 0
                    
                    wind_power_density = round(0.5 * 1.225 * (wind_speed ** 3), 2)
                
                all_data.append((timestamp, temperature, humidity, irradiance, wind_speed, source,
                               wind_power_density, solar_energy_yield))
        
        print(f"   Generated {len(all_data)} missing rows")
        
        # Bulk insert
        filled = bulk_insert(all_data, source)
        total_filled += filled
        print(f"   ✅ Inserted {filled} rows for {source}")
    
    print(f"\n{'='*60}")
    print(f"TOTAL ROWS FILLED: {total_filled}")
    print("="*60)

if __name__ == "__main__":
    fill_all_gaps()
