// nasa-ml.js - Static NASA ML Data Injection
// Fetches data/nasa-ml.txt, extracts Data-A (predict) & Data-B (actual), injects into nasa-ml.html variables.
// Hardcodes chart data and metrics at page load (one-time, fully static).

async function fetchAndParseMeteorMLData() {
  console.log('NASA-ML: Fetching data/nasa-ml.txt...');
  
  try {
    const response = await fetch('data/nasa-ml.txt');
    if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
    
    const text = await response.text();
    const lines = text.split('\n');
    
    // Parse Data-A (Predict) section
    let dataALines = [];
    let dataBLines = [];
    let metricsText = '';
    let inSection = '';
    
    for (let line of lines) {
      line = line.trim();
      
      // Skip comments and empty
      if (line.startsWith('#') || !line) continue;
      
      if (line.includes('Data-A') || line.includes('Predict')) {
        inSection = 'A';
        continue;
      }
      if (line.includes('Data-B') || line.includes('Actual')) {
        inSection = 'B';
        continue;
      }
      if (line.includes('Metric')) {
        inSection = 'metrics';
        continue;
      }
      
      // Record lines by section
      if (inSection === 'A' && !line.startsWith('id')) {
        if (line.match(/^\d/)) dataALines.push(line);
      } else if (inSection === 'B' && !line.startsWith('id')) {
        if (line.match(/^\d/)) dataBLines.push(line);
      } else if (inSection === 'metrics') {
        metricsText += line + '\n';
      }
    }
    
    console.log(`Parsed: ${dataALines.length} Data-A, ${dataBLines.length} Data-B records`);
    
    // Extract arrays from data
    const predict_wind_min = [];
    const predict_wind_avg = [];
    const predict_wind_max = [];
    const predict_solar_min = [];
    const predict_solar_avg = [];
    const predict_solar_max = [];
    
    for (const line of dataALines) {
      const cols = line.split(',');
      if (cols.length >= 9) {  // Ensure all 9 columns: id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source
        predict_wind_min.push(parseFloat(cols[2]));
        predict_wind_avg.push(parseFloat(cols[3]));
        predict_wind_max.push(parseFloat(cols[4]));
        predict_solar_min.push(parseFloat(cols[5]));
        predict_solar_avg.push(parseFloat(cols[6]));
        predict_solar_max.push(parseFloat(cols[7]));
      }
    }
    
    const actual_wind_min = [];
    const actual_wind_avg = [];
    const actual_wind_max = [];
    const actual_solar_min = [];
    const actual_solar_avg = [];
    const actual_solar_max = [];
    
    for (const line of dataBLines) {
      const cols = line.split(',');
      if (cols.length >= 9) {  // Ensure all 9 columns: id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source
        actual_wind_min.push(parseFloat(cols[2]));
        actual_wind_avg.push(parseFloat(cols[3]));
        actual_wind_max.push(parseFloat(cols[4]));
        actual_solar_min.push(parseFloat(cols[5]));
        actual_solar_avg.push(parseFloat(cols[6]));
        actual_solar_max.push(parseFloat(cols[7]));
      }
    }
    
    // Inject into window globals for Chart.js to use
    window.predict_wind_min = predict_wind_min;
    window.predict_wind_avg = predict_wind_avg;
    window.predict_wind_max = predict_wind_max;
    window.predict_solar_min = predict_solar_min;
    window.predict_solar_avg = predict_solar_avg;
    window.predict_solar_max = predict_solar_max;
    
    window.actual_wind_min = actual_wind_min;
    window.actual_wind_avg = actual_wind_avg;
    window.actual_wind_max = actual_wind_max;
    window.actual_solar_min = actual_solar_min;
    window.actual_solar_avg = actual_solar_avg;
    window.actual_solar_max = actual_solar_max;
    
    // Parse metrics
    const maeMatch = metricsText.match(/MAE.*?wind.*?:\s*([\d.-]+)/i);
    const rmseMatch = metricsText.match(/RMSE.*?:\s*([\d.-]+)/i);
    const r2Match = metricsText.match(/R[²2].*?:\s*([\d.-]+)/i);
    const corrMatch = metricsText.match(/Correlation.*?:\s*([\d.-]+)/i);
    
    const mae = maeMatch ? parseFloat(maeMatch[1]) : 1.224;
    const rmse = rmseMatch ? parseFloat(rmseMatch[1]) : 1.246;
    const r2 = r2Match ? parseFloat(r2Match[1]) : -129.957;
    const corr = corrMatch ? parseFloat(corrMatch[1]) : -0.596;
    
    // Inject metrics into HTML elements
    const maeEl = document.getElementById('mae-val');
    const rmseEl = document.getElementById('rmse-val');
    const r2El = document.getElementById('r2-val');
    const corrEl = document.getElementById('corr-val');
    
    if (maeEl) maeEl.textContent = mae.toFixed(3);
    if (rmseEl) rmseEl.textContent = rmse.toFixed(3);
    if (r2El) r2El.textContent = r2.toFixed(3);
    if (corrEl) corrEl.textContent = corr.toFixed(3);
    
    // Validate data before update
    if (predict_wind_avg.length !== 8 || actual_wind_avg.length !== 8) {
      throw new Error(`Invalid data lengths: predict=${predict_wind_avg.length}, actual=${actual_wind_avg.length}`);
    }
    
    console.log('✅ NASA-ML data validated & metrics displayed');
    
    // Wait for charts to be fully initialized, then update
    setTimeout(() => {
      updateChartsWithData();
    }, 500);
    
  } catch (error) {
    console.error('NASA-ML ERROR:', error.message);
    console.warn('Keeping HTML default hardcoded values for charts');
  }
}

function updateChartsWithData() {
  console.log('updateChartsWithData() called - checking charts...');
  
  // Verify data exists
  if (!window.predict_wind_avg || window.predict_wind_avg.length === 0) {
    console.warn('⚠️ No wind prediction data - using defaults');
    return;
  }
  
  // Update wind chart
  const windChart = Chart.getChart('combined_wind');
  if (windChart) {
    console.log('Updating wind chart with', window.predict_wind_avg.length, 'points');
    windChart.data.datasets[0].data = window.predict_wind_avg;
    windChart.data.datasets[1].data = window.predict_wind_min;
    windChart.data.datasets[2].data = window.predict_wind_max;
    windChart.data.datasets[3].data = window.actual_wind_avg;
    windChart.data.datasets[4].data = window.actual_wind_min;
    windChart.data.datasets[5].data = window.actual_wind_max;
    windChart.update();
    console.log('✅ Wind chart updated');
  } else {
    console.warn('⚠️ Wind chart not found (Chart.getChart returned null)');
  }
  
  // Update solar chart
  const solarChart = Chart.getChart('combined_solar');
  if (solarChart) {
    if (!window.predict_solar_avg || window.predict_solar_avg.length === 0) {
      console.warn('⚠️ No solar prediction data - using defaults');
      return;
    }
    console.log('Updating solar chart with', window.predict_solar_avg.length, 'points');
    solarChart.data.datasets[0].data = window.predict_solar_avg;
    solarChart.data.datasets[1].data = window.predict_solar_min;
    solarChart.data.datasets[2].data = window.predict_solar_max;
    solarChart.data.datasets[3].data = window.actual_solar_avg;
    solarChart.data.datasets[4].data = window.actual_solar_min;
    solarChart.data.datasets[5].data = window.actual_solar_max;
    solarChart.update();
    console.log('✅ Solar chart updated');
  } else {
    console.warn('⚠️ Solar chart not found (Chart.getChart returned null)');
  }
}

// Run on page load - wait for DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded: scheduling fetch...');
    setTimeout(fetchAndParseMeteorMLData, 100);
  });
} else {
  console.log('DOM already loaded: scheduling fetch...');
  setTimeout(fetchAndParseMeteorMLData, 100);
}

