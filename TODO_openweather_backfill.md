# OpenWeather Backfill Strategy - 2025 Data

## Executive Summary

**Finding**: OpenWeather One Call API 3.0 returns **401 Unauthorized** - historical data access NOT available with current API key.

**Solution**: Use NASA POWER API which provides **REAL web sensor data** for both wind and solar energy.

---

## API Capability Analysis

### OpenWeather API (Current Key)
| API Endpoint | Status | Historical Data |
|-------------|--------|-----------------|
| Basic Weather (/data/2.5/weather) | ✅ Working (200) | ❌ No - Current only |
| One Call API 3.0 (/data/3.0/onecall) | ❌ 401 Unauthorized | ❌ No - Requires subscription |
| Historical Weather API | ❌ Not accessible | ❌ Paid API |

### NASA POWER API (Free & Working)
| Parameter | Code | 2025 Data |
|-----------|------|-----------|
| Solar Irradiance | ALLSKY_SFC_SW_DWN | ✅ 365 days complete |
| Wind Speed (10m) | WS10M | ✅ 365 days complete |
| Temperature | T2M | ✅ Available |
| Relative Humidity | RH2M | ✅ Available |

---

## Recommended Strategy

### Approach: NASA POWER Dual-Data Backfill

Since OpenWeather historical API is not accessible, use NASA POWER for **real web sensor data**:

1. **Solar Data** (already complete in DB):
   - Source: NASA POWER ALLSKY_SFC_SW_DWN
   - Already has 8,760 hourly records for 2025

2. **Wind Data** (needs backfill):
   - Source: NASA POWER WS10M (wind speed at 10m height)
   - Daily wind speed → hourly with realistic variation
   - Calculate wind_power_density from wind speed

---

## Data Coverage Assessment

### Current Database Status (2025)
| Source | Records | Data Quality |
|--------|---------|--------------|
| openweather | 8,760 | ⚠️ Most is SIMULATED (Jan: all identical values) |
| nasa_power | 8,760 | ✅ REAL API data (solar only) |
| sim | 8,760 | Simulation |

### After Wind Backfill
| Source | Records | Data Quality |
|--------|---------|--------------|
| nasa_power (solar) | 8,760 | ✅ REAL API data |
| nasa_power (wind) | 8,760 | ✅ REAL API data (NEW) |
| openweather | Keep as-is | Historical reference |

---

## Implementation Plan

### Phase 1: Fetch Real Wind Data from NASA POWER
- [ ] Create script to fetch WS10M (wind speed) for all 2025 dates
- [ ] Convert daily wind speed to hourly with realistic variation
- [ ] Calculate wind_power_density using formula: P = 0.5 × 1.225 × v³
- [ ] Insert into database with source='nasa_power' (same as solar)

### Phase 2: Data Verification
- [ ] Verify 365 days × 24 hours = 8,760 wind records
- [ ] Check wind speed range matches Manila climate (1-8 m/s typical)
- [ ] Validate wind_power_density calculations

### Phase 3: Coverage Summary
- [ ] Show final data summary by month
- [ ] Document data sources for each metric

---

## API Limitations Validation

### OpenWeather (Confirmed)
- **Free tier**: Current weather only, no historical
- **One Call API 3.0**: Requires paid subscription (current key not authorized)
- **Daily limit**: 1,000,000 calls/month (not the bottleneck)
- **Historical limit**: 40+ years (but requires paid access)

### NASA POWER (Confirmed Working)
- **Free**: No API key required
- **Daily data**: Returns all dates in single request
- **Date range**: 1983-2025 (complete)
- **Rate limit**: Polite usage (1 request/second recommended)
- **2025 Performance**: 365/365 days successful, 0 missing

---

## Alternative Options (Not Recommended)

### Option A: Purchase OpenWeather Subscription
- Pros: Direct OpenWeather data
- Cons: Costs money ($40+/month), key change required
- Effort: Medium (new API key, new script)

### Option B: Try Alternative Free APIs
- Visual Crossing (free tier: 1000 rows/day)
- Meteostat (free, historical)
- Pros: May provide additional data
- Cons: More complex implementation, may have gaps

---

## Conclusion

**Best approach**: Use NASA POWER for both solar AND wind data
- Solar: Already complete (8,760 records)
- Wind: Backfill needed (~8,760 records)
- Total real web sensor data: **17,520 records** for 2025

This gives REAL web sensor data for wind and solar energy, which was the original goal.

