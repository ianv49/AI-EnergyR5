import psycopg2
from tabulate import tabulate

conn = psycopg2.connect(dbname='energy_db', user='postgres', password='PdM', host='localhost', port='5432')
cur = conn.cursor()

print("=== Source Value Analysis ===\n")

# Check exact source values
print("1. All distinct source values:")
cur.execute("SELECT DISTINCT source, COUNT(*) FROM sensor_data GROUP BY source ORDER BY source")
for row in cur.fetchall():
    print(f"   '{row[0]}' - {row[1]} rows")

# Check for whitespace issues
print("\n2. Check for whitespace in source:")
cur.execute("SELECT DISTINCT source, LENGTH(source) as len FROM sensor_data")
for row in cur.fetchall():
    print(f"   '{row[0]}' (length: {row[1]})")

# Check OpenWeather data - what's in irradiance column?
print("\n3. OpenWeather - irradiance values (should be NULL if only weather data):")
cur.execute("SELECT COUNT(*) as total, COUNT(irradiance) as has_irradiance, AVG(irradiance) as avg_irr FROM sensor_data WHERE source = 'openweather'")
row = cur.fetchall()[0]
print(f"   Total rows: {row[0]}, With irradiance: {row[1]}, Avg irradiance: {row[2]}")

# Check NASA_POWER data - what's in temperature/humidity columns?
print("\n4. NASA_POWER - temperature/humidity values (should be NULL if only solar data):")
cur.execute("SELECT COUNT(*) as total, COUNT(temperature) as has_temp, AVG(temperature) as avg_temp FROM sensor_data WHERE source = 'nasa_power'")
row = cur.fetchall()[0]
print(f"   Total rows: {row[0]}, With temperature: {row[1]}, Avg temperature: {row[2]}")

# Check data range for each source
print("\n5. Data Range by Source:")
cur.execute("""
    SELECT 
        source,
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        COUNT(*) as count
    FROM sensor_data 
    GROUP BY source 
    ORDER BY source
""")
for row in cur.fetchall():
    print(f"   {row[0]}: {row[1]} to {row[2]} ({row[3]} rows)")

# Check for any potential data mixing issues
print("\n6. Sample data comparison (same timestamp for all sources):")
cur.execute("""
    SELECT timestamp 
    FROM sensor_data 
    WHERE source = 'openweather' 
    ORDER BY timestamp 
    LIMIT 1
""")
sample_ts = cur.fetchone()[0]

cur.execute("""
    SELECT source, temperature, humidity, irradiance, wind_speed 
    FROM sensor_data 
    WHERE timestamp = %s
""", (sample_ts,))
print(f"   At timestamp {sample_ts}:")
for row in cur.fetchall():
    print(f"     {row[0]}: temp={row[1]}, hum={row[2]}, irr={row[3]}, wind={row[4]}")

conn.close()
