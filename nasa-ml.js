// nasa-ml.js - NASA ML Predict vs Actual: Feb 21-28 2026 wind/solar charts.
// Fetches/parses data/nasa-ml.txt daily stats CSV, updates nasa-ml.html Chart.js wind/solar charts dynamically.
// Only nasa-ml.js touched per instructions.

async function loadNasaMLData() {
  console.log('NASA ML: Loading data/nasa-ml.txt...');
  try {
    const response = await fetch('data/nasa-ml.txt');
    if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
    const text = await response.text();
    const lines = text.split('\n');

    const predictions = [], actuals = [];
    let section = '';

    for (let line of lines) {
      line = line.trim();
      if (line.startsWith('#') || !line) continue;
      if (line === '[nasa]') {
        section = 'data';
        continue;
      }
      if (section === 'data' && line) {
        const cols = line.split(',');
        if (cols.length >= 9) {
          const [, timestamp, wMin, wAvg, wMax, sMin, sAvg, sMax, src] = cols.map(c => c.trim());
          const nums = [wMin, wAvg, wMax, sMin, sAvg, sMax].map(Number);
          if (nums.every(n => !isNaN(n))) {
            const data = { timestamp, wMin: +wMin, wAvg: +wAvg, wMax: +wMax, sMin: +sMin, sAvg: +sAvg, sMax: +sMax, src };
            if (src.includes('nasa-ML') || src.includes('Data-A')) predictions.push(data);
            if (src.includes('nasa-API') || src.includes('Data-B')) actuals.push(data);
          }
        }
      }
    }

    console.log(`Loaded: ${predictions.length} preds, ${actuals.length} actuals`);

    // Parse metrics from end of file
    const metrics = {};
    const metricRegex = /MAE \(wind-avg\): ([\d.-]+)/i;
    const maeMatch = text.match(metricRegex);
    if (maeMatch) metrics['mae (wind-avg)'] = parseFloat(maeMatch[1]);

    const rmseRegex = /RMSE:\s*([\d.-]+)/i;
    const rmseMatch = text.match(rmseRegex);
    if (rmseMatch) metrics.rmse = parseFloat(rmseMatch[1]);

    const r2Regex = /R²:\s*([\d.-]+)/i;
    const r2Match = text.match(r2Regex);
    if (r2Match) metrics['r²'] = parseFloat(r2Match[1]);

    const corrRegex = /Correlation:\s*([\d.-]+)/i;
    const corrMatch = text.match(corrRegex);
    if (corrMatch) metrics.correlation = parseFloat(corrMatch[1]);
    
    console.log('Parsed metrics:', metrics);

    return { 
      predictions: predictions.sort((a,b)=>a.timestamp.localeCompare(b.timestamp)), 
      actuals: actuals.sort((a,b)=>a.timestamp.localeCompare(b.timestamp)),
      metrics 
    };
  } catch (err) {
    console.error('Load error:', err);
    return { predictions: [], actuals: [], metrics: {} };
  }
}

function updateCharts({ predictions, actuals }) {
  if (predictions.length < 8 || actuals.length < 8) {
    console.warn('Insufficient data for 8 days');
    return;
  }

  // Extract arrays for Feb21-28 (slice first 8)
  const pWAvg = predictions.slice(0,8).map(d => d.wAvg);
  const pWMin = predictions.slice(0,8).map(d => d.wMin);
  const pWMax = predictions.slice(0,8).map(d => d.wMax);
  const pSAvg = predictions.slice(0,8).map(d => d.sAvg);
  const pSMin = predictions.slice(0,8).map(d => d.sMin);
  const pSMax = predictions.slice(0,8).map(d => d.sMax);

  const aWAvg = actuals.slice(0,8).map(d => d.wAvg);
  const aWMin = actuals.slice(0,8).map(d => d.wMin);
  const aWMax = actuals.slice(0,8).map(d => d.wMax);
  const aSAvg = actuals.slice(0,8).map(d => d.sAvg);
  const aSMin = actuals.slice(0,8).map(d => d.sMin);
  const aSMax = actuals.slice(0,8).map(d => d.sMax);

  const labels = ['Feb21','Feb22','Feb23','Feb24','Feb25','Feb26','Feb27','Feb28'];

  // Update wind chart
  const windCtx = document.getElementById('combined_wind')?.getContext('2d');
  if (windCtx && Chart.getChart('combined_wind')) {
    const chart = Chart.getChart('combined_wind');
    chart.data.labels = labels;
    chart.data.datasets[0].data = pWAvg; // Predict Avg
    chart.data.datasets[1].data = pWMin;
    chart.data.datasets[2].data = pWMax;
    chart.data.datasets[3].data = aWAvg; // Actual Avg
    chart.data.datasets[4].data = aWMin;
    chart.data.datasets[5].data = aWMax;
    chart.update('active');
    console.log('Wind chart updated');
  }

  // Update solar chart
  const solarCtx = document.getElementById('combined_solar')?.getContext('2d');
  if (solarCtx && Chart.getChart('combined_solar')) {
    const chart = Chart.getChart('combined_solar');
    chart.data.labels = labels;
    chart.data.datasets[0].data = pSAvg;
    chart.data.datasets[1].data = pSMin;
    chart.data.datasets[2].data = pSMax;
    chart.data.datasets[3].data = aSAvg;
    chart.data.datasets[4].data = aSMin;
    chart.data.datasets[5].data = aSMax;
    chart.update('active');
    console.log('Solar chart updated');
  }
}

async function updateMetrics(metrics) {
  const maeCell = document.getElementById('mae-val');
  const rmseCell = document.getElementById('rmse-val');
  const r2Cell = document.getElementById('r2-val');
  const corrCell = document.getElementById('corr-val');

  if (maeCell) maeCell.textContent = metrics['mae (wind-avg)']?.toFixed(3) || '--';
  if (rmseCell) rmseCell.textContent = metrics.rmse?.toFixed(3) || '--';
  if (r2Cell) r2Cell.textContent = metrics['r²']?.toFixed(3) || '--';
  if (corrCell) corrCell.textContent = metrics.correlation?.toFixed(3) || '--';

  console.log('Metrics table updated:', metrics);
}

async function initNasaML() {
  console.log('AI-EnergyR5 NASA-ML: Aligning with data/nasa-ml.txt');
  const data = await loadNasaMLData();
  updateCharts(data);
  updateMetrics(data.metrics);
  console.log('✅ nasa-ml.js aligned - charts + metrics ready!');
}

// Run after DOM + charts load (delay for inline script)
window.addEventListener('load', initNasaML);

