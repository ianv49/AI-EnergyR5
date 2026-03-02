"""
Check full February 2026 timestamp alignment across all sources
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import get_connection

def check_full_february_alignment():
    """Check timestamp alignment for entire February 2026"""
    conn = get_connection()
    
    print("="*70)
    print("FULL FEBRUARY 2026 TIMESTAMP ALIGNMENT CHECK")
    print("="*70)
    
    with conn.cursor() as cur:
        # Get all timestamps for each source
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = 'openweather'
            AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
            ORDER BY timestamp
        """)
        ow_timestamps = {row[0] for row in cur.fetchall()}
        
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = 'nasa_power'
            AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
            ORDER BY timestamp
        """)
        nasa_timestamps = {row[0] for row in cur.fetchall()}
        
        cur.execute("""
            SELECT timestamp FROM sensor_data 
            WHERE source = 'sim'
            AND timestamp >= '2026-02-01' AND timestamp < '2026-03-01'
            ORDER BY timestamp
        """)
        sim_timestamps = {row[0] for row in cur.fetchall()}
    
    conn.close()
    
    # Calculate alignment
    common_all = ow_timestamps & nasa_timestamps & sim_timestamps
    total_unique = ow_timestamps | nasa_timestamps | sim_timestamps
    
    print(f"\n📊 TIMESTAMP ANALYSIS:")
    print(f"   OpenWeather unique timestamps: {len(ow_timestamps)}")
    print(f"   NASA_POWER unique timestamps: {len(nasa_timestamps)}")
    print(f"   SIM unique timestamps: {len(sim_timestamps)}")
    print(f"   Common across all 3 sources: {len(common_all)}")
    print(f"   Total unique timestamps: {len(total_unique)}")
    
    # Find issues
    ow_only = ow_timestamps - nasa_timestamps - sim_timestamps
    nasa_only = nasa_timestamps - ow_timestamps - sim_timestamps
    sim_only = sim_timestamps - ow_timestamps - nasa_timestamps
    
    print(f"\n⚠️  ALIGNMENT ISSUES:")
    print(f"   OpenWeather-only: {len(ow_only)}")
    print(f"   NASA_POWER-only: {len(nasa_only)}")
    print(f"   SIM-only: {len(sim_only)}")
    
    if ow_only:
        print(f"\n   OpenWeather unique times: {sorted(ow_only)[:10]}")
    if nasa_only:
        print(f"   NASA_POWER unique times: {sorted(nasa_only)[:10]}")
    if sim_only:
        print(f"   SIM unique times: {sorted(sim_only)[:10]}")
    
    # Overall status
    alignment_pct = (len(common_all) / len(total_unique) * 100) if total_unique else 0
    
    print(f"\n{'='*70}")
    if alignment_pct == 100:
        print("✅ PERFECT ALIGNMENT! All timestamps match across all sources!")
    else:
        print(f"⚠️  ALIGNMENT: {alignment_pct:.1f}% ({len(common_all)}/{len(total_unique)} timestamps)")
    print("="*70)

if __name__ == "__main__":
    check_full_february_alignment()
