# PVOutput API Feb 2026 Backfill
## Status: Files Created ✓ [Next: Update SYSTEM_ID in config.py, Run backfill, Verify]

**Goal:** Replicate NASA POWER routine for PVOutput API:
- Create wrapper
- Backfill Feb 2026 (2026-02-01 to 2026-03-01, 28d x 24h = 672 rows)
- Real data from pvoutput.org/getsystem.jsp using key `a140f2a7fef02cfee5a7ade39b530667ff9525d9`
- source='pvoutput'
- Align to DB format (hourly, derive temp/hum/ws/irr from API status/temp/energy)

**Provided:** API Key: a140f2a7fef02cfee5a7ade39b530667ff9525d9
**Missing:** System ID (required for /getsystem.jsp?id=XXX). Use placeholder `YOUR_SYSTEM_ID` - update before run.

**File-Level Plan:**
1. `api_wrappers/pvoutput.py` - NASA-style wrapper, fetch daily XML, parse status/temp -> hourly.
2. `backfill_pvoutput_feb2026.py` - Mirror `backfill_nasa_december_2025.py`: delete range, loop days fetch_daily, hourly dist, insert.
3. Add to README/TODO.md refs.

**Detailed Steps:**
- [ ] 1. Create api_wrappers/pvoutput.py
- [ ] 2. Create backfill_pvoutput_feb2026.py  
- [ ] 3. Add PVOutput key/SID to config.py or env
- [ ] 4. Run `python backfill_pvoutput_feb2026.py`
- [ ] 5. Verify: `python check_feb_all_sources.py` expect 672 pvoutput rows
- [ ] 6. Update TODOs done.

**DB Alignment:** timestamp hourly Manila TZ, temp from API v5 or synth tropical, irr from status (Status*75W/m2 avg), ws synth 2-4m/s, hum 75-90%, derive wpd/sey.

Progress update here after each step.

