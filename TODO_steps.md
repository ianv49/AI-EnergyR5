# Task: Fix summary cards to show real metrics from collect*.txt

## Approved Plan Summary
- **Status**: Already implemented in index.html parseData/renderSummary().
- **Issue**: Zeros on GitHub Pages https://ianv49.github.io/AI-EnergyR5/ (likely data/ fetch fails).
- **Files**: index.html (main), data/collect*.txt (confirmed data present).

## Steps Completed ✓
### 1. Analyzed files [DONE]
- Read index.html: Parser already perfect (tab-split, cols[2,4,5,8], real avgs).
- Sampled collect1.txt: Valid tab-delimited data (~9500 rows, non-zero values).

### 2. Test locally [PENDING]
- Open index.html in browser to verify metrics load.

### 3. Diagnose GH Pages issue [PENDING]
- Check if data/*.txt accessible via fetch on live site.

### 4. Fix deployment [PENDING]
- Ensure GitHub Pages serves data/ files (add to repo, commit/push).
- Alternative: Base64 embed or API endpoint.

### 5. Verify & complete [PENDING]

**Next: Test local browser open.**

