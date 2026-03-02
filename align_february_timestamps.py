"""
Align all February 2026 timestamps to hour precision
Remove seconds from timestamps to ensure alignment
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection
from datetime import datetime, timedelta

def align_timestamps():
    """Align timestamps to hour precision (remove seconds)"""
    conn = get_connection()
    
    print("="*70)
    print("ALIGNING FEBRUARY 2026 TIMESTAMPS")
    print("="*70)
    
    # Find timestamps with seconds (not aligned to hour)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT timestamp, source
            FROM sensor_data
            WHERE timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
            AND EXTRACT(SECOND FROM timestamp) != 0
            ORDER BY timestamp
        """)
        misaligned = cur.fetchall()
    
    print(f"\nFound {len(misaligned)} misaligned timestamps")
    
    # Group by source
    sources = {}
    for ts, src in misaligned:
        if src not in sources:
            sources[src] = []
        sources[src].append(ts)
    
    for src, timestamps in sources.items():
        print(f"   {src}: {len(timestamps)} timestamps")
    
    # Fix each timestamp
    fixed_count = 0
    for ts, source in misaligned:
        # Round down to the hour
        aligned_ts = ts.replace(minute=0, second=0, microsecond=0)
        
        # Check if aligned timestamp already exists
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM sensor_data
                WHERE timestamp = %s AND source = %s
            """, (aligned_ts, source))
            exists = cur.fetchone()[0] > 0
            
            if exists:
                # Delete the misaligned row
                cur.execute("""
                    DELETE FROM sensor_data
                    WHERE timestamp = %s AND source = %s
                """, (ts, source))
                print(f"   🗑️  Deleted {source} @ {ts} (aligned version exists)")
            else:
                # Update the timestamp
                cur.execute("""
                    UPDATE sensor_data
                    SET timestamp = %s
                    WHERE timestamp = %s AND source = %s
                """, (aligned_ts, ts, source))
                print(f"   ✅ Fixed {source} @ {ts} -> {aligned_ts}")
            
            fixed_count += 1
            conn.commit()
    
    conn.close()
    print(f"\n✅ Fixed {fixed_count} misaligned timestamps")

if __name__ == "__main__":
    align_timestamps()
