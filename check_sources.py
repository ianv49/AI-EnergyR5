import psycopg2
from tabulate import tabulate

conn = psycopg2.connect(
    dbname='energy_db',
    user='postgres',
    password='PdM',
    host='localhost',
    port='5432'
)
cur = conn.cursor()

# Check unique source values
print('=== Unique Source Values ===')
cur.execute('SELECT DISTINCT source FROM sensor_data ORDER BY source')
sources = cur.fetchall()
for s in sources:
    print(f'  "{s[0]}"')

# Check OpenWeather data sample
print('\n=== OpenWeather Sample (first 10 rows) ===')
cur.execute('''SELECT timestamp, temperature, humidity, wind_speed, cloudiness, uv_index, source 
               FROM sensor_data 
               WHERE source = 'openweather' 
               ORDER BY timestamp 
               LIMIT 10''')
rows = cur.fetchall()
headers = ['timestamp', 'temperature', 'humidity', 'wind_speed', 'cloudiness', 'uv_index', 'source']
print(tabulate(rows, headers=headers, tablefmt='psql'))

# Count rows by source
print('\n=== Row Count by Source ===')
cur.execute('SELECT source, COUNT(*) FROM sensor_data GROUP BY source ORDER BY source')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check for any null/empty source values
print('\n=== Null/Empty Source Check ===')
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source IS NULL OR source = ''")
null_count = cur.fetchone()[0]
print(f'  Null/empty source count: {null_count}')

# Check for potential source name variations
print('\n=== Check for source variations ===')
cur.execute("SELECT DISTINCT LOWER(source) FROM sensor_data ORDER BY LOWER(source)")
for row in cur.fetchall():
    print(f'  "{row[0]}"')

conn.close()
