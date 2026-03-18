from db_connector import get_connection
from tabulate import tabulate
import logging

logging.basicConfig(level=logging.INFO)

def main():
    conn = get_connection()
    cur = conn.cursor()
    try:
        print("✅ Database connection test successful!")
        
        # Total rows
        cur.execute("SELECT COUNT(*) FROM sensor_data")
        total = cur.fetchone()[0]
        print(f"📊 sensor_data table has {total} total rows.")
        
        # Counts by source
        cur.execute("SELECT source, COUNT(*) FROM sensor_data GROUP BY source ORDER BY COUNT(*) DESC")
        print("\n📈 Data breakdown by source:")
        headers = ['source', 'rows']
        data = cur.fetchall()
        print(tabulate(data, headers=headers, tablefmt='grid'))
        
# Latest rows by source (added meteostat)
        sources = ['sim', 'nasa_power', 'open_meteo', 'meteostat', 'solcast', 'pvoutput', 'noaa']
        for src in sources:
            print(f"\n🔎 Latest '{src}' row:")
            cur.execute("""
                SELECT timestamp, temperature, humidity, irradiance, wind_speed, source 
                FROM sensor_data 
                WHERE source ILIKE %s 
                ORDER BY timestamp DESC LIMIT 1
            """, (src,))
            row = cur.fetchone()
            if row:
                headers = ['timestamp', 'temperature', 'humidity', 'irradiance', 'wind_speed', 'source']
                print(tabulate([row], headers=headers, tablefmt='grid'))
            else:
                print("No data")
                
        print("\n✅ Test complete - connection and data verified!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()

