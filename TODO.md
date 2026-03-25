# Fix Web Tool Loading Issue

✅ 1. Created this TODO.md

⏳ 2. Edit index_summary.html - Replace broken GitHub fetches with local data/collect*.txt parsing matching web/charts.js logic (fetch local, skip header, cols[2]=temp,[4]=irr,[5]=wind,[8]=sey, compute avgs/count/maxWind). Ensure hideLoading(), render summary cards/charts/legend even with partial data.

⏳ 3. Test: Run `start index_summary.html` in terminal to open dashboard. Verify:
   - Loading spinner hides
   - 7 summary cards appear with metrics (avg temp/irr/SEY, max wind, row count)
   - Best SEY source highlighted with green ring
   - Irradiance line chart and yield bar chart render
   - Legend shows sources

⏳ 4. Update README.md if needed for web usage.

⏳ 5. attempt_completion

