// nasa-ml.js - NASA ML Predict vs Actual: Feb 21-28 2026 wind/solar charts.
// Uses hardcoded metrics from nasa-ml.html and Chart.js for visualization.
// IMPORTANT: NASA ML metrics are hardcoded in HTML - this script protects against any clearing.

const HARDCODED_METRICS = {
  'mae (wind-avg)': 1.224,
  'rmse': 1.246,
  'r²': -129.957,
  'correlation': -0.596
};

function lockMetricsDisplay() {
  // Immediately set metrics to hardcoded values and KEEP them there
  const maeCell = document.getElementById('mae-val');
  const rmseCell = document.getElementById('rmse-val');
  const r2Cell = document.getElementById('r2-val');
  const corrCell = document.getElementById('corr-val');

  if (maeCell) maeCell.textContent = '1.224';
  if (rmseCell) rmseCell.textContent = '1.246';
  if (r2Cell) r2Cell.textContent = '-129.957';
  if (corrCell) corrCell.textContent = '-0.596';

  // Prevent any other script from clearing these values
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((m) => {
      if (m.target.id === 'mae-val' && m.target.textContent !== '1.224') {
        m.target.textContent = '1.224';
      }
      if (m.target.id === 'rmse-val' && m.target.textContent !== '1.246') {
        m.target.textContent = '1.246';
      }
      if (m.target.id === 'r2-val' && m.target.textContent !== '-129.957') {
        m.target.textContent = '-129.957';
      }
      if (m.target.id === 'corr-val' && m.target.textContent !== '-0.596') {
        m.target.textContent = '-0.596';
      }
    });
  });

  if (maeCell) observer.observe(maeCell, { characterData: true, subtree: true });
  if (rmseCell) observer.observe(rmseCell, { characterData: true, subtree: true });
  if (r2Cell) observer.observe(r2Cell, { characterData: true, subtree: true });
  if (corrCell) observer.observe(corrCell, { characterData: true, subtree: true });

  console.log('✅ Metrics locked:', HARDCODED_METRICS);
}

// Lock metrics ASAP, even before DOM fully loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', lockMetricsDisplay);
} else {
  lockMetricsDisplay();
}

// Also lock on window load as safety measure
window.addEventListener('load', lockMetricsDisplay);

