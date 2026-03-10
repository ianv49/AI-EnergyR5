"""
Script to run February 2026 Open-Meteo backfill.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the backfill function
from backfill_open_meteo import backfill_month

# Run the backfill for February 2026
if __name__ == "__main__":
    result = backfill_month(2026, 2)
    print(f"\nFinal result: {result} rows inserted for February 2026")
