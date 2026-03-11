#!/usr/bin/env python3
"""Quick check Solcast data count"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.db_connector import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'solcast' AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'")
count = cur.fetchone()[0]
print(f"Solcast Feb 2026: {count} rows")
conn.close()
