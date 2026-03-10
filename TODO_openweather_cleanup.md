# OpenWeather Cleanup - TODO

## Status: IN PROGRESS

### Task Summary
Remove all OpenWeather data from the system:
1. ✅ Database cleanup script created (db/cleanup_openweather.py)
2. ✅ collect2.txt cleared (old openweather data removed)
3. ⏳ Web tool modifications needed (manual)
4. ⏳ Database cleanup execution (requires database to be running)

---

## Completed Steps

### 1. Database Cleanup Script ✅
- Location: `db/cleanup_openweather.py`
- Script deletes all rows where source = 'openweather'
- Includes verification function to confirm cleanup

### 2. Data File Cleanup ✅  
- File: `data/collect2.txt`
- Cleared all OpenWeather data from the file
- File now contains only header row

---

## Remaining Steps

### 3. Execute Database Cleanup
**Prerequisite**: PostgreSQL database must be running

**To start database**:
```
# Start PostgreSQL service
net start postgresql-x64-16
```

**To run cleanup**:
```
cd d:\My Documents\ee\1_Tester_cee\AI\AI-EnergyR5
python db\cleanup_openweather.py
```

Expected output:
```
==================================================
OpenWeather Data Cleanup
==================================================
Found XXXX OpenWeather rows to delete.
Successfully deleted XXXX OpenWeather rows from database.

=== Verification ===
Remaining OpenWeather rows: 0
...
```

---

### 4. Web Tool Modifications

#### Option A: Comment out routes (Recommended)
Edit `web/ingestion_trigger.py` and comment out these functions/routes:
- `from api_wrappers.openweather import get_weather_data` 
- `from scripts.capture_weather_data import insert_weather_data`
- `/fetch_weather_data_from_db` route
- `/fetch_openweather` route
- `get_weather_summary()` function

#### Option B: Simple restart (easiest)
The web tool will gracefully fail when OpenWeather data is deleted from database.

---

### 5. Verify Cleanup
Run this to verify:
```
python db\test_connection.py
```

Should show:
- OpenWeather data: 0 rows
- Only 'sim' and 'nasa_power' sources remain

---

## Files Modified
- `data/collect2.txt` - Cleared
- `db/cleanup_openweather.py` - Created
- `db/cleanup_openweather_web.py` - Helper script created

## Files That Need Manual Edit
- `web/ingestion_trigger.py` - Comment out weather routes (optional)

