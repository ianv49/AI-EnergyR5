# NOAA Climate Data API - Replicate NASA Routine

**Task:** Replicate NASA POWER routine for NOAA CDO API, fetch historical 2 days real sensor data (no sim), save to DB aligned format (source='noaa_gsod').

**Location:** Manila (lat=14.5995, lon=120.9842)
**Dates:** Historical 2 full days (e.g. yesterday & day before)
**Real-only:** Skip bad/missing flagged data

## Progress Steps (update [x] when complete)

- [ ] 1. Verify NOAA token, query /stations find best Manila GSOD stationid (active, recent maxdate)
- [ ] 2. Create `api_wrappers/noaa.py`:
  - get_gsod_data(stationid, start_date, end_date) → list[dict] {date, temp_avg C, humidity %, wind_mps, prcp; skip if mflag!=''; derive irradiance diurnal scaled}
- [ ] 3. Create `backfill_noaa_2days.py`:
  - Mirror backfill_nasa: delete source='noaa_gsod' range
  - Fetch 2 days via noaa.get_gsod_data()
  - Expand each day to 24 hourly (flat values or temp diurnal var ±5%, irradiance derive like NASA but scale ~temp)
  - Calc derived wind_power_density, solar_energy_yield (same formulas)
  - Batch insert to sensor_data
  - Dedup, verify ~48 rows, avg values realistic
- [ ] 4. Add to `.env`: `NOAA_TOKEN=upMIDPMAdLpTskzddVUHEMYlxbfeMHpA`
- [ ] 5. Test run: `python backfill_noaa_2days.py`
- [ ] 6. Verify: `python check_sources.py` shows noaa_gsod, check_feb_all_sources.py-like summary
- [ ] 7. Update README.md with NOAA section

## NOAA Notes
- API: https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GSOD&stationid=...&startDate=&endDate=&limit=100&datatypeid=TAVG,RHAVG,AWND
- Token: upMIDPMAdLpTskzddVUHEMYlxbfeMHpA (valid?)
- Station candidates: 482170-99999 (RIZAL MEMORIAL Manila), confirm recent data
- Fields map: temp=TAVG/10, hum=RHAVG, wind=AWND/10 m/s, irradiance=derive (1000*sin(hour)* (90-hum)/90 ), prcp ignore
- Dates format YYYY-MM-DD

**Next:** Step 1 - find stationid

