import psycopg2
conn = psycopg2.connect(dbname='energy_db', user='postgres', password='PdM', host='localhost', port='5432')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'sensor_data' ORDER BY ordinal_position")
print("=== Table Schema ===")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== Row Count by Source ===")
cur.execute("SELECT source, COUNT(*) FROM sensor_data GROUP BY source ORDER BY source")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n=== OpenWeather Sample (first 5 rows) ===")
cur.execute("SELECT * FROM sensor_data WHERE source = 'openweather' ORDER BY timestamp LIMIT 5")
rows = cur.fetchall()
# Get column names
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'sensor_data' ORDER BY ordinal_position")
cols = [row[0] for row in cur.fetchall()]
for row in rows:
    print(f"  {row}")

print("\n=== NASA_POWER Sample (first 5 rows) ===")
cur.execute("SELECT * FROM sensor_data WHERE source = 'nasa_power' ORDER BY timestamp LIMIT 5")
rows = cur.fetchall()
for row in rows:
    print(f"  {row}")

print("\n=== SIM Sample (first 5 rows) ===")
cur.execute("SELECT * FROM sensor_data WHERE source = 'sim' ORDER BY timestamp LIMIT 5")
rows = cur.fetchall()
for row in rows:
    print(f"  {row}")

conn.close()
