from db.db_connector import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM sensor_data WHERE source = 'nasa_power' AND timestamp >= '2025-03-01' AND timestamp < '2025-04-01'")
row = cur.fetchone()
print(f'March 2025: {row[0]} records ({row[1]} to {row[2]})')
conn.close()
