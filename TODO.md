# AI-EnergyR5 ML Validation Enhancement Plan - Approved
Progress tracked here. Steps completed will be marked ✅.

## Approved Plan Steps (User confirmed: ok)

1. **✅ Create TODO.md** - Track progress (this file)

2. **Fix ml_validation.py parsing + expand validation** 
   - Parse MLoutput.txt correctly (skip header properly)
   - Expand to full overlapping period (Mar25-Apr7 or recent 14/30 days)
   - Add accuracy metrics (MAE, RMSE)
   - Output JSON (ml_stats.json) + PNG charts
   - ~~CLI: --full --forecast~~

3. **Dynamic ml.html** - Load from validation JSON (no hardcoded data)

4. **Dynamic Chart HTMLs** (ml-chart.html, ml-solar-chart.html, ml-dual-chart.html)
   - Chart.js from JSON API/validation output
   - Overlay actual vs predicted lines

5. **index.html update** - Add ML validation stats tab

6. **New ml/ml_forecast.py** 
   - Train RandomForestRegressor on collect1.txt historical
   - Predict next 14 days wind/solar min/avg/max
   - Append to MLoutput.txt as 'sim-ML-new'

7. **Install deps + Test** 
   - pip install scikit-learn (for RandomForest)
   - python ml_validation.py --full
   - python ml/ml_forecast.py
   - Verify charts/data in browser

8. **Follow-up Integration**
   - DB queries for full API data validation
   - Update TODO.md with Phase 10 ML progress

## Pending User Input (if any)
- Date range: Default recent 30 days from collect1.txt/MLoutput.txt overlap
- ML model: RandomForestRegressor (simple start, per plan)

## Next Action
Run `python ml_validation.py` to test current state → Report results → Proceed to Step 2 edits.

**Status: Ready for implementation**
