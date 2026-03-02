"""
Delete SIM-only timestamps that don't exist in other sources
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection
from datetime import datetime

def delete_sim_only():
    """Delete SIM timestamps that don't exist in OpenWeather or NASA_POWER"""
    conn = get_connection()
    
    print("="*70)
    print("DELETING SIM-ONLY TIMESTAMPS")
    print("="*70)
    
    with conn.cursor() as cur:
        # Get all timestamps for each source
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = 'openweather'
            AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
        """)
        ow_timestamps = {row[0] for row in cur.fetchall()}
        
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = 'nasa_power'
            AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
        """)
        nasa_timestamps = {row[0] for row in cur.fetchall()}
        
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = 'sim'
            AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
        """)
        sim_timestamps = {row[0] for row in cur.fetchall()}
    
    # Find SIM-only timestamps
    other_sources = ow_timestamps | nasa_timestamps
    sim_only = sim_timestamps - other_sources
    
    print(f"\nSIM-only timestamps to delete: {len(sim_only)}")
    for ts in sorted(sim_only):
        print(f"   {ts}")
    
    # Delete SIM-only timestamps
    for ts in sim_only:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sensor_data WHERE timestamp = %s AND source = 'sim'", (ts,))
            conn.commit()
            print(f"   🗑️  Deleted SIM @ {ts}")
    
    conn.close()
    print(f"\n✅ Deleted {len(sim_only)} SIM-only timestamps")

if __name__ == "__main__":
    delete_sim_only()
