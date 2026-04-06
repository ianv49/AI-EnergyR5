// nasa-ml.js - NASA ML Predict vs Actual: Feb 21-28 2026 wind/solar charts.
// Uses hardcoded metrics from nasa-ml.html and Chart.js for visualization.
// Charts load from inline HTML data; metrics are retained from HTML defaults.

// Hardcoded metrics matching nasa-ml.html values
const HARDCODED_METRICS = {
  'mae (wind-avg)': 1.224,
  'rmse': 1.246,
  'r²': -129.957,
  'correlation': -0.596
};

function ensureMetricsDisplay() {
  const maeCell = document.getElementById('mae-val');
  const rmseCell = document.getElementById('rmse-val');
  const r2Cell = document.getElementById('r2-val');
  const corrCell = document.getElementById('corr-val');

  // Only update if the element is empty or shows "--"
  if (maeCell && (maeCell.textContent === '--' || !maeCell.textContent)) {
    maeCell.textContent = HARDCODED_METRICS['mae (wind-avg)'].toFixed(3);
  }
  if (rmseCell && (rmseCell.textContent === '--' || !rmseCell.textContent)) {
    rmseCell.textContent = HARDCODED_METRICS['rmse'].toFixed(3);
  }
  if (r2Cell && (r2Cell.textContent === '--' || !r2Cell.textContent)) {
    r2Cell.textContent = HARDCODED_METRICS['r²'].toFixed(3);
  }
  if (corrCell && (corrCell.textContent === '--' || !corrCell.textContent)) {
    corrCell.textContent = HARDCODED_METRICS['correlation'].toFixed(3);
  }

  console.log('✅ Metrics ensured displayed:', HARDCODED_METRICS);
}

async function initNasaML() {
  console.log('AI-EnergyR5 NASA-ML: Initializing charts and metrics...');
  
  // Ensure metrics are visible (they have hardcoded HTML defaults)
  ensureMetricsDisplay();
  
  // Charts are already initialized by inline Chart.js code in HTML
  console.log('✅ nasa-ml.js ready - charts and metrics displayed!');
}

// Run after DOM loads
window.addEventListener('load', initNasaML);

