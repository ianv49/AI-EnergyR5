import psycopg2
conn = psycopg2.connect(dbname='energy_db', user='postgres', password='PdM', host='localhost', port='5432')
cur = conn.cursor()

# Check specific timestamps from the sample data
print('=== Checking 2026-03-01 06:30:00 ===')
cur.execute("SELECT source, temperature, humidity, irradiance, wind_speed FROM sensor_data WHERE timestamp = '2026-03-01 06:30:00' ORDER BY source")
for row in cur.fetchall():
    print(f'  {row}')

print('\n=== Checking 2026-02-28 23:00:00 ===')
cur.execute("SELECT source, temperature, humidity, irradiance, wind_speed FROM sensor_data WHERE timestamp = '2026-02-28 23:00:00' ORDER BY source")
for row in cur.fetchall():
    print(f'  {row}')

print('\n=== Checking 2026-02-28 22:00:00 ===')
cur.execute("SELECT source, temperature, humidity, irradiance, wind_speed FROM sensor_data WHERE timestamp = '2026-02-28 22:00:00' ORDER BY source")
for row in cur.fetchall():
    print(f'  {row}')

conn.close()
