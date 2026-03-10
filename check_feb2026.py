from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'")
print('Open-Meteo Feb 2026:', cur.fetchone()[0])
cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'open_meteo' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'")
print('Date range:', cur.fetchone())
conn.close()
