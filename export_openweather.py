import psycopg2
from datetime import datetime

# Connect to database
conn = psycopg2.connect(dbname='energy_db', user='postgres', password='PdM', host='localhost', port='5432')
cur = conn.cursor()

# Fetch only openweather data, ordered by timestamp descending
cur.execute("""
    SELECT id, timestamp, temperature, humidity, irradiance, wind_speed, source, wind_power_density, solar_energy_yield
    FROM sensor_data 
    WHERE source = 'openweather'
    ORDER BY timestamp DESC
""")

rows = cur.fetchall()
print(f"Found {len(rows)} openweather rows in database")

# Generate the file content
lines = []
lines.append("# Data collection last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
lines.append(f"# Summary: weather={len(rows)}")
lines.append("[OpenWeather]")
lines.append("id,timestamp,temperature,humidity,irradiance,wind_speed,source,wind_power_density,solar_energy_yield")

for i, row in enumerate(rows, 1):
    row_id, timestamp, temp, hum, irr, wind, source, wpd, sey = row
    # Format the line - handle None values
    if temp is None: temp = 0.0
    if hum is None: hum = 0.0
    if irr is None: irr = 0.0
    if wind is None: wind = 0.0
    if wpd is None: wpd = ''
    if sey is None: sey = ''
    
    line = f"{i},{timestamp},{temp},{hum},{irr},{wind},{source},{wpd},{sey}"
    lines.append(line)

# Write to file
with open('data/collect2.txt', 'w') as f:
    f.write('\n'.join(lines))

print(f"Written {len(lines)} lines to data/collect2.txt")
print("\nFirst 10 lines:")
for line in lines[:10]:
    print(line)

conn.close()
