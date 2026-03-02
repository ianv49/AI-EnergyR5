"""
Fix remaining alignment issues in February 2026
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection
from datetime import datetime

def fix_remaining():
    """Fix remaining alignment issues"""
    conn = get_connection()
    
    print("="*70)
    print("FIXING REMAINING ALIGNMENT ISSUES")
    print("="*70)
    
    # Get the problematic timestamps
    with conn.cursor() as cur:
        # Find timestamps not aligned to the hour
        cur.execute("""
            SELECT timestamp, source
            FROM sensor_data
            WHERE timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
            AND (EXTRACT(MINUTE FROM timestamp) != 0 
                 OR EXTRACT(SECOND FROM timestamp) != 0)
            ORDER BY timestamp
        """)
        misaligned = cur.fetchall()
    
    print(f"\nFound {len(misaligned)} remaining misaligned timestamps:")
    for ts, src in misaligned:
        print(f"   {src}: {ts}")
    
    # Fix each
    for ts, source in misaligned:
        # Round to nearest hour
        hour = ts.hour
        minute = ts.minute
        
        # Round up if minute >= 30
        if minute >= 30:
            hour = (hour + 1) % 24
            if ts.day == 28 and hour == 0:
                # Skip wrap-around to next day
                hour = 23
                ts = ts.replace(hour=hour, minute=0, second=0, microsecond=0)
                # Just delete this one
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM sensor_data WHERE timestamp = %s AND source = %s", (ts, source))
                    conn.commit()
                    print(f"   🗑️  Deleted {source} @ {ts} (would wrap to next day)")
                continue
        
        aligned_ts = ts.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # Check if aligned version exists
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM sensor_data
                WHERE timestamp = %s AND source = %s
            """, (aligned_ts, source))
            exists = cur.fetchone()[0] > 0
            
            if exists:
                cur.execute("DELETE FROM sensor_data WHERE timestamp = %s AND source = %s", (ts, source))
                print(f"   🗑️  Deleted {source} @ {ts}")
            else:
                cur.execute("UPDATE sensor_data SET timestamp = %s WHERE timestamp = %s AND source = %s", 
                          (aligned_ts, ts, source))
                print(f"   ✅ Fixed {source} @ {ts} -> {aligned_ts}")
            
            conn.commit()
    
    conn.close()

if __name__ == "__main__":
    fix_remaining()
