from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

# Check Jan 2026 data by source
cur.execute("SELECT source, COUNT(*) FROM sensor_data WHERE timestamp >= '2026-01-01' AND timestamp < '2026-02-01' GROUP BY source")
print('Jan 2026 data by source:')
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} rows")

# Check what data exists for each source
print("\n--- Details by source ---")

# Sim data
cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'sim' AND timestamp >= '2026-01-01' AND timestamp < '2026-02-01'")
r = cur.fetchone()
print(f"Sim: {r[0]} to {r[1]}")

# OpenWeather
cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'openweather' AND timestamp >= '2026-01-01' AND timestamp < '2026-02-01'")
r = cur.fetchone()
print(f"OpenWeather: {r[0]} to {r[1]}")

# NASA Power
cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'nasa_power' AND timestamp >= '2026-01-01' AND timestamp < '2026-02-01'")
r = cur.fetchone()
print(f"NASA POWER: {r[0]} to {r[1]}")

# Open-Meteo
cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-01-01' AND timestamp < '2026-02-01'")
r = cur.fetchone()
print(f"Open-Meteo: {r[0]} to {r[1]}")

conn.close()
