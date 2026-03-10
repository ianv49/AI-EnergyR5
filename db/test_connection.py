from db_connector import get_connection
from tabulate import tabulate   # for pretty tables

def main():
    # Step 1: Connect to DB
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            # Step 2: Count total rows
            cur.execute("SELECT COUNT(*) FROM sensor_data;")
            result = cur.fetchone()
            print("✅ Database connection test successful!")
            print(f"📊 sensor_data table has {result[0]} total rows.")
            
            # Step 3: Count rows by source
            cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'sim';")
            sim_count = cur.fetchone()[0]
            
            # OpenWeather data: source = 'openweather' OR source = 'Database' OR source IS NULL
            # Exclude nasa_power source explicitly
            cur.execute("""
                SELECT COUNT(*) FROM sensor_data 
                WHERE (source = 'openweather' OR source = 'Database' OR source IS NULL)
                AND source != 'nasa_power';
            """)
            openweather_count = cur.fetchone()[0]
            
            # NASA POWER data: source = 'nasa_power'
            cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'nasa_power';")
            nasa_count = cur.fetchone()[0]
            
            # Open-Meteo data: source = 'open_meteo'
            cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo';")
            open_meteo_count = cur.fetchone()[0]
            
            # Calculate other rows (unknown sources)
            other_count = result[0] - sim_count - openweather_count - nasa_count - open_meteo_count
            
            print(f"   - Sim data: {sim_count} rows")
            print(f"   - OpenWeather data: {openweather_count} rows")
            print(f"   - NASA POWER data: {nasa_count} rows")
            print(f"   - Open-Meteo data: {open_meteo_count} rows")
            if other_count > 0:
                print(f"   - Other/Unknown sources: {other_count} rows")

            # Step 4: Show latest row for each source
            headers = None
            
            # Latest sim row
            cur.execute("SELECT * FROM sensor_data WHERE source = 'sim' ORDER BY timestamp DESC LIMIT 1;")
            sim_row = cur.fetchall()
            if sim_row:
                if headers is None:
                    headers = [desc[0] for desc in cur.description]
                print("\n🔎 Latest sim row:")
                print(tabulate(sim_row, headers=headers, tablefmt="psql"))
            
            # Latest openweather row (include Database and NULL sources, exclude nasa_power)
            cur.execute("""
                SELECT * FROM sensor_data 
                WHERE (source = 'openweather' OR source = 'Database' OR source IS NULL)
                AND source != 'nasa_power'
                ORDER BY timestamp DESC LIMIT 1;
            """)
            openweather_row = cur.fetchall()
            if openweather_row:
                if headers is None:
                    headers = [desc[0] for desc in cur.description]
                print("\n🔎 Latest OpenWeather row:")
                print(tabulate(openweather_row, headers=headers, tablefmt="psql"))
            
            # Latest nasa_power row
            cur.execute("SELECT * FROM sensor_data WHERE source = 'nasa_power' ORDER BY timestamp DESC LIMIT 1;")
            nasa_row = cur.fetchall()
            if nasa_row:
                if headers is None:
                    headers = [desc[0] for desc in cur.description]
                print("\n🔎 Latest NASA POWER row:")
                print(tabulate(nasa_row, headers=headers, tablefmt="psql"))
            
            # Latest open_meteo row
            cur.execute("SELECT * FROM sensor_data WHERE source = 'open_meteo' ORDER BY timestamp DESC LIMIT 1;")
            open_meteo_row = cur.fetchall()
            if open_meteo_row:
                if headers is None:
                    headers = [desc[0] for desc in cur.description]
                print("\n🔎 Latest Open-Meteo row:")
                print(tabulate(open_meteo_row, headers=headers, tablefmt="psql"))



    except Exception as e:
        print(f"❌ Query failed: {e}")

    # Step 5: Close connection
    conn.close()

if __name__ == "__main__":
    main()
