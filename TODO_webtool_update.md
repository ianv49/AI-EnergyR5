# Webtool Update TODO (Static GitHub Pages, collect*.txt only, No DB)

## 1. ✅ Gather Info (Done)
- List HTML: dashboard.html (multi-table JS), latest_weather_data.html (static old)
- Features analyzed
- Plan confirmed: Static, txt-only, GH Pages

## 2. ✅ Restructure for GitHub Pages
- ✅ Created `index.html` (new static dashboard with Chart.js, all sources)
- [ ] Copy `data/collect*.txt` to GH Pages dir
- [ ] Delete old: `web/dashboard.html`, `web/latest_weather_data.html`, `web/ingestion_trigger.py`, `web/generate*.py`, `db/` dir

## 3. Update index.html
- [ ] Remove DB fetch buttons/endpoints
- [ ] Add tables for all collect1-7.txt + NOAA/PVOutput.txt
- [ ] Add Chart.js charts tab
- [ ] Add stats/export/filter

## 4. Data Prep
- [ ] Generate/update all collect*.txt via backfills
- [ ] Create NOAA.txt, PVOutput.txt

## 5. ✅ Test & Deploy
- ✅ Local: http://localhost:8080
- ✅ GH Pages: Deployed via npx gh-pages (check https://username.github.io/AI-EnergyR5)

## 6. Enhancements
- [ ] Source tabs
- [ ] Auto-refresh
- [ ] ML forecast embed

