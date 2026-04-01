# ML Sim API Scope Adjustment (2026-04-02)

**Goal**: Train 2025-01-01 to 2026-02-20 data from sim-api.txt. Predict 2026-02-21 to 28 (8 days) daily min/avg/max wind/solar to ml-sim-output.txt.

**Status**: [ ] Plan approved → [ ] Fix syntax → [ ] Filter dates → [ ] Predict Feb21-28 → [ ] Update ml.js dates/table → [ ] Test → [ ] Done

1. Fix ml/ml-sim-forecast.py syntax (load_historical_data def/indent, ml_file in append_to_mloutput)
2. In load_historical_data: df = df[(df['timestamp'] >= '2025-01-01') & (df['timestamp'] < '2026-02-21')]
3. Change predict_next_14_days → predict_feb21_28, range(8), start_date = datetime(2026,2,21)
4. daily_aggregates source='sim-api-ML-feb26'
5. ml.js: histDays Feb11-20 2026, predDays ['2026-02-21'..'28'], filter data year=2026 month=2 day<=20
6. Test `py ml/ml-sim-forecast.py`, open ml.html (table), ml-sim.html (charts if updated)
7. Log myNotes.txt

Approve plan → proceed step-by-step.
