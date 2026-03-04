from db.db_connector import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT source, COUNT(*) FROM sensor_data WHERE timestamp >= '2025-01-01' AND timestamp < '2026-01-01' GROUP BY source ORDER BY source")
print('2025 Data by Source:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')
conn.close()
