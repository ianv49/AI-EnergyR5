#!/usr/bin/env python3
"""
Cleanup script to remove all OpenWeather data from the database.
This script deletes all rows where source = 'openweather' from the sensor_data table.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db_connector import get_connection


def cleanup_openweather_data():
    """Delete all OpenWeather data from the database."""
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            # First, count how many rows will be deleted
            cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'openweather'")
            count = cur.fetchone()[0]
            print(f"Found {count} OpenWeather rows to delete.")
            
            if count == 0:
                print("No OpenWeather data found in database.")
                return 0
            
            # Delete all OpenWeather data
            cur.execute("DELETE FROM sensor_data WHERE source = 'openweather'")
            deleted_count = cur.rowcount
            conn.commit()
            
            print(f"Successfully deleted {deleted_count} OpenWeather rows from database.")
            return deleted_count
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_cleanup():
    """Verify that OpenWeather data has been removed."""
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sensor_data WHERE source = 'openweather'")
            remaining = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM sensor_data")
            total = cur.fetchone()[0]
            
            print(f"\n=== Verification ===")
            print(f"Remaining OpenWeather rows: {remaining}")
            print(f"Total rows in database: {total}")
            
            # Show breakdown by source
            print("\nRows by source:")
            cur.execute("""
                SELECT source, COUNT(*) 
                FROM sensor_data 
                GROUP BY source 
                ORDER BY COUNT(*) DESC
            """)
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")
                
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 50)
    print("OpenWeather Data Cleanup")
    print("=" * 50)
    
    deleted = cleanup_openweather_data()
    
    if deleted > 0:
        verify_cleanup()
    
    print("\nCleanup complete!")

