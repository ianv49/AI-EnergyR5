"""
Fix the 2 mismatched SIM timestamps to align with other sources
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection
from datetime import datetime

def fix_sim_timestamps():
    """Fix SIM timestamps to match other sources"""
    conn = get_connection()
    
    # The mismatched timestamps
    bad_timestamps = [
        datetime(2026, 2, 26, 12, 0),
        datetime(2026, 2, 27, 18, 0)
    ]
    
    # Get the correct timestamps from OpenWeather (or NASA_POWER)
    print("Finding correct timestamps from OpenWeather...")
    with conn.cursor() as cur:
        # Get timestamps that should exist in SIM but don't
        cur.execute("""
            SELECT o.timestamp 
            FROM sensor_data o
            LEFT JOIN sensor_data s ON s.timestamp = o.timestamp AND s.source = 'sim'
            WHERE o.source = 'openweather'
            AND o.timestamp >= '2026-02-25'
            AND o.timestamp < '2026-03-01'
            AND s.timestamp IS NULL
            ORDER BY o.timestamp
        """)
        missing_timestamps = [row[0] for row in cur.fetchall()]
    
    print(f"Found {len(missing_timestamps)} missing SIM timestamps")
    
    if len(missing_timestamps) >= 2:
        # Get data to copy for the missing timestamps
        with conn.cursor() as cur:
            cur.execute("""
                SELECT temperature, humidity, wind_speed, irradiance, wind_power_density, solar_energy_yield
                FROM sensor_data
                WHERE source = 'sim'
                AND timestamp IN (%s, %s)
            """, (bad_timestamps[0], bad_timestamps[1]))
            bad_data = cur.fetchall()
        
        print(f"Data from bad timestamps: {bad_data}")
        
        # Delete the bad SIM rows
        print(f"Deleting bad SIM rows...")
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM sensor_data
                WHERE source = 'sim' AND timestamp IN (%s, %s)
            """, (bad_timestamps[0], bad_timestamps[1]))
            conn.commit()
            print(f"Deleted {cur.rowcount} rows")
        
        # Insert correct rows using OpenWeather data
        print(f"Inserting correct SIM rows...")
        with conn.cursor() as cur:
            for ts in missing_timestamps[:2]:
                # Get corresponding OpenWeather data
                cur.execute("""
                    SELECT temperature, humidity, wind_speed, irradiance, wind_power_density, solar_energy_yield
                    FROM sensor_data
                    WHERE source = 'openweather' AND timestamp = %s
                """, (ts,))
                ow_data = cur.fetchone()
                
                if ow_data:
                    cur.execute("""
                        INSERT INTO sensor_data (timestamp, temperature, humidity, irradiance, wind_speed, 
                                          source, wind_power_density, solar_energy_yield)
                        VALUES (%s, %s, %s, %s, %s, 'sim', %s, %s)
                        ON CONFLICT (timestamp, source) DO NOTHING
                    """, (ts, ow_data[0], ow_data[1], ow_data[3], ow_data[2], ow_data[4], ow_data[5]))
                    print(f"  Inserted SIM row for {ts}")
            
            conn.commit()
    
    conn.close()
    print("\n✅ SIM timestamps fixed!")
    
    # Verify the fix
    print("\nVerifying fix...")
    os.system('py check_feb25_28.py')

if __name__ == "__main__":
    fix_sim_timestamps()
