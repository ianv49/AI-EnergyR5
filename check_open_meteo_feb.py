from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()

# Check Open-Meteo February 2026 data
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'")
print('Open-Meteo Feb 2026 rows:', cur.fetchone()[0])

cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'")
r = cur.fetchone()
print('Date range:', r[0], 'to', r[1])

# Show sample data
cur.execute("SELECT timestamp, temperature, humidity, wind_speed, irradiance, wind_power_density, solar_energy_yield FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-02-01' AND timestamp < '2026-02-02' ORDER BY timestamp LIMIT 5")
print('\nSample data (Feb 1, 2026):')
for row in cur.fetchall():
    print(row)

conn.close()
