# AI-EnergyR5 Dashboard Summary Cards Implementation TODO

**Status: In Progress**

## Approved Plan Summary
- **Files**: index.html (main dashboard)
- **Issues Fixed**: 
  - TSV parsing (split(',') → split('\\t'))
  - Source mapping (1=NASA → 1=sim for collect1.txt; extend to 2-7)
  - Summary cards with stats (avg temp/irr, max wind, avg yield)
  - Charts with recent 168h data
  - Highlight best yield source
- **Approach**: Parse all data/collect*.txt, compute stats, render cards/charts, limit perf.

## Steps:
- [x] 1. Read index.html and sample data/collect1.txt
- [ ] 2. Create TODO.md with plan tracking
- [ ] 3. Fix parsing in JS: change to tab delimiter, update source mapping (1='sim')
- [ ] 4. Update summaryCards rendering with accurate stats from all 7 files
- [ ] 5. Fix charts for irradiance (col4), yield (col8)
- [ ] 6. Add legend with correct source names
- [ ] 7. Test by running open index.html
- [ ] 8. Mark complete with attempt_completion
