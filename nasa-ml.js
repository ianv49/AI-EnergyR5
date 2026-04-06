// nasa-ml.js - Static NASA ML Metrics Display
// Fetches data/nasa-api.txt, computes metrics ONCE, displays statically in HTML.
// No dynamic updates. Full static after page load.

async function fetchAndDisplayMetrics() {
  console.log('NASA-ML: Fetching data/nasa-api.txt for metrics...');
  
  try {
    const response = await fetch('data/nasa-api.txt');
    if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
    
    const text = await response.text();
    const lines = text.split('\n');
    
    // Parse hourly data for Feb 21-28 2026
    const feb21to28Data = [];
    
    for (const line of lines) {
      if (line.startsWith('#') || !line.trim()) continue;
      if (line === '[nasa_power]') continue;
      
      const cols = line.split(',');
      if (cols.length < 9) continue;
      
      const timestamp = cols[1].trim();
      const [dateStr] = timestamp.split(' ');
      const [year, month, day] = dateStr.split('-').map(Number);
      
      // Filter Feb 21-28 2026 only
      if (year === 2026 && month === 2 && day >= 21 && day <= 28) {
        const wind_speed = parseFloat(cols[5].trim());
        const solar_yield = parseFloat(cols[8].trim());
        
        if (!isNaN(wind_speed) && !isNaN(solar_yield)) {
          feb21to28Data.push({ timestamp, wind_speed, solar_yield });
        }
      }
    }
    
    console.log(`Parsed ${feb21to28Data.length} hourly records for Feb 21-28`);
    
    // Group by day and compute daily min/avg/max
    const dailyStats = {};
    for (const record of feb21to28Data) {
      const [dateStr] = record.timestamp.split(' ');
      if (!dailyStats[dateStr]) {
        dailyStats[dateStr] = { winds: [], solars: [] };
      }
      dailyStats[dateStr].winds.push(record.wind_speed);
      dailyStats[dateStr].solars.push(record.solar_yield);
    }
    
    // Convert to arrays
    const predictData = []; // Feb 21-28 predict (Data-A) - hardcoded in HTML
    const actualData = [];  // Feb 21-28 actual from nasa_power (Data-B)
    
    for (const dateStr in dailyStats) {
      const stats = dailyStats[dateStr];
      const wMin = Math.min(...stats.winds);
      const wAvg = stats.winds.reduce((a,b)=>a+b)/stats.winds.length;
      const wMax = Math.max(...stats.winds);
      const sMin = Math.min(...stats.solars);
      const sAvg = stats.solars.reduce((a,b)=>a+b)/stats.solars.length;
      const sMax = Math.max(...stats.solars);
      
      actualData.push({ dateStr, wMin, wAvg, wMax, sMin, sAvg, sMax });
    }
    
    // Sort by date
    actualData.sort((a, b) => a.dateStr.localeCompare(b.dateStr));
    
    // Hardcoded predict data (from ML model) - Feb 21-28 2026
    const predictFeb21to28 = [
      { dateStr: '2026-02-21', wMin: 3.23, wAvg: 3.39, wMax: 3.81, sMin: 0.00, sAvg: 0.24, sMax: 0.67 },
      { dateStr: '2026-02-22', wMin: 3.55, wAvg: 3.64, wMax: 3.84, sMin: 0.00, sAvg: 0.24, sMax: 0.68 },
      { dateStr: '2026-02-23', wMin: 3.35, wAvg: 3.43, wMax: 3.60, sMin: 0.00, sAvg: 0.23, sMax: 0.66 },
      { dateStr: '2026-02-24', wMin: 3.46, wAvg: 3.54, wMax: 3.65, sMin: 0.00, sAvg: 0.23, sMax: 0.66 },
      { dateStr: '2026-02-25', wMin: 3.42, wAvg: 3.52, wMax: 3.67, sMin: 0.00, sAvg: 0.24, sMax: 0.67 },
      { dateStr: '2026-02-26', wMin: 3.58, wAvg: 3.69, wMax: 3.84, sMin: 0.00, sAvg: 0.24, sMax: 0.67 },
      { dateStr: '2026-02-27', wMin: 3.64, wAvg: 3.78, wMax: 3.94, sMin: 0.00, sAvg: 0.24, sMax: 0.69 },
      { dateStr: '2026-02-28', wMin: 3.71, wAvg: 3.84, wMax: 4.01, sMin: 0.00, sAvg: 0.24, sMax: 0.68 }
    ];
    
    // Compute metrics: MAE, RMSE, R², Correlation for Feb 21-28
    if (actualData.length === 8 && predictFeb21to28.length === 8) {
      let sumAbsError = 0, sumSqError = 0;
      let actualMean = 0, predictMean = 0;
      
      // Calculate wind metrics (MAE, RMSE based on avg)
      for (let i = 0; i < 8; i++) {
        const pred = predictFeb21to28[i].wAvg;
        const actual = actualData[i].wAvg;
        sumAbsError += Math.abs(pred - actual);
        sumSqError += (pred - actual) ** 2;
        actualMean += actual;
        predictMean += pred;
      }
      
      actualMean /= 8;
      predictMean /= 8;
      
      const MAE = sumAbsError / 8;
      const RMSE = Math.sqrt(sumSqError / 8);
      
      // Calculate R² and Correlation
      let ssRes = 0, ssTot = 0, cov = 0, varActual = 0, varPredict = 0;
      for (let i = 0; i < 8; i++) {
        const pred = predictFeb21to28[i].wAvg;
        const actual = actualData[i].wAvg;
        ssRes += (actual - pred) ** 2;
        ssTot += (actual - actualMean) ** 2;
        cov += (actual - actualMean) * (pred - predictMean);
        varActual += (actual - actualMean) ** 2;
        varPredict += (pred - predictMean) ** 2;
      }
      
      const R2 = 1 - (ssRes / ssTot);
      const correlation = cov / Math.sqrt(varActual * varPredict);
      
      // DISPLAY METRICS STATICALLY (ONE TIME ONLY)
      document.getElementById('mae-val').textContent = MAE.toFixed(3);
      document.getElementById('rmse-val').textContent = RMSE.toFixed(3);
      document.getElementById('r2-val').textContent = R2.toFixed(3);
      document.getElementById('corr-val').textContent = correlation.toFixed(3);
      
      console.log('✅ Static metrics computed & displayed:');
      console.log(`  MAE: ${MAE.toFixed(3)}`);
      console.log(`  RMSE: ${RMSE.toFixed(3)}`);
      console.log(`  R²: ${R2.toFixed(3)}`);
      console.log(`  Correlation: ${correlation.toFixed(3)}`);
    }
  } catch (error) {
    console.error('Error fetching metrics:', error);
    // Keep hardcoded defaults if fetch fails
    document.getElementById('mae-val').textContent = '1.224';
    document.getElementById('rmse-val').textContent = '1.246';
    document.getElementById('r2-val').textContent = '-129.957';
    document.getElementById('corr-val').textContent = '-0.596';
  }
}

// Load metrics ONCE on page load
window.addEventListener('load', fetchAndDisplayMetrics);

