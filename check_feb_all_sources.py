from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT source, COUNT(*) 
    FROM sensor_data 
    WHERE timestamp >= '2026-02-01' AND timestamp < '2026-03-01' 
    GROUP BY source 
    ORDER BY source
""")
print("February 2026 data from all sources:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} rows")
conn.close()
