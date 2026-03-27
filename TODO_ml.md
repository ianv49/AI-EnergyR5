# ML Page Implementation TODO (User-Approved)

## Confirmed Requirements Coverage
- Do NOT touch index.html/style.css/script.js ✓
- ml.html: \"Machine Learning Workspace\", \"14-Day Yield Table (March–April 2025)\" section, table columns Day|Wind Min|Ave|Max|Solar Min|Ave|Max, 14 rows (Mar25-31 hist + Apr1-7 pred), nav to index ✓
- ml.js: Load data/collect1.txt, CSV parse col5=wind_speed col8=solar_yield, filter Jan-Mar2025 training, Mar25-31 daily stats (24h/day), LSTM TF.js train, Apr1-7 forecast daily stats, populate table ✓
- Data validated: 2025 Q1 timestamps present ✓

## Breakdown Steps
1. [x] **Step 1**: Edit ml.html ✓ - Full table structure/14 rows with IDs created and confirmed.
2. [x] **Step 2**: Edit ml.js ✓ - Added getDateKey(), getDailyStats(), ready for historical computation.
3. [ ] **Step 3**: Edit ml.js - Prepare Jan-Mar hourly data, train separate LSTM models for wind/solar (seq_len suitable e.g. 24-168).
4. [ ] **Step 4**: Edit ml.js - Forecast 168 hours (7 days) from Mar31 end, group to daily min/avg/max Apr1-7.
5. [ ] **Step 5**: Edit ml.js - Populate all 14 rows table cells on DOMContentLoaded.
6. [ ] **Step 6**: Test - Provide `start ml.html` or browser open command, verify table shows numbers (not '--').
7. [ ] **Step 7**: Validate - Check console no errors, historical ~recent data, predictions plausible, update TODO complete.

**Current: Step 2 complete. Step 3 - LSTM hourly data prep + train wind/solar on Jan-Mar 2025**

