// ml.js
// LSTM Forecast for AI-EnergyR5 Phase10 - Wind & Solar 7-day April 2025

async function loadSimData() {
  try {
    const response = await fetch('data/collect1.txt');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const text = await response.text();
    const lines = text.trim().split('\n');
    
    const rows = lines.map(line => {
      if (line.startsWith('#') || line.trim() === '') return null;
      
      const parts = line.split(',');
      if (parts.length < 9) return null;
      
      const timestampStr = parts[1].trim();
      const timestamp = new Date(timestampStr);
      if (isNaN(timestamp)) return null;
      
      const wind = parseFloat(parts[5]); // wind_speed
      const solar = parseFloat(parts[8]); // solar_energy_yield
      
      if (isNaN(wind) || isNaN(solar)) return null;
      
      return { timestamp, wind, solar };
    }).filter(row => row !== null);
    
    console.log(`Loaded ${rows.length} valid data points from collect1.txt`);
    return rows;
  } catch (error) {
    console.error('Error loading data:', error);
    return [];
  }
}

function filterQuarterData(rows) {\n  return rows.filter(r => {\n    const year = r.timestamp.getFullYear();\n    const month = r.timestamp.getMonth() + 1;\n    return year === 2025 && month >= 1 && month <= 3;\n  });\n}\n\nfunction getDateKey(timestamp) {\n  return timestamp.toISOString().split('T')[0]; // YYYY-MM-DD\n}\n\nfunction getDailyStats(rows, targetDays) {\n  const dayData = {};\n  rows.forEach(r => {\n    const key = getDateKey(r.timestamp);\n    if (!dayData[key]) dayData[key] = {winds: [], solars: []};\n    dayData[key].winds.push(r.wind);\n    dayData[key].solars.push(r.solar);\n  });\n\n  const stats = {};\n  targetDays.forEach(day => {\n    const data = dayData[day];\n    if (data && data.winds.length > 0) {\n      stats[day] = {\n        wind: {\n          min: Math.min(...data.winds).toFixed(2),\n          avg: (data.winds.reduce((a,b)=>a+b,0)/data.winds.length).toFixed(2),\n          max: Math.max(...data.winds).toFixed(2)\n        },\n        solar: {\n          min: Math.min(...data.solars).toFixed(2),\n          avg: (data.solars.reduce((a,b)=>a+b,0)/data.solars.length).toFixed(2),\n          max: Math.max(...data.solars).toFixed(2)\n        }\n      };\n    } else {\n      stats[day] = {wind: {min:'--', avg:'--', max:'--'}, solar: {min:'--', avg:'--', max:'--'}};\n    }\n  });\n  return stats;\n}

function getLast7DaysStats(rows) {
  if (rows.length === 0) return { wind: {min:0, avg:0, max:0}, solar: {min:0, avg:0, max:0} };
  
  const last7Days = rows.slice(-168); // ~7*24 hours
  
  const windValues = last7Days.map(r => r.wind).filter(v => !isNaN(v));
  const solarValues = last7Days.map(r => r.solar).filter(v => !isNaN(v));
  
  const windStats = {
    min: Math.min(...windValues).toFixed(2),
    avg: (windValues.reduce((a,b)=>a+b,0)/windValues.length).toFixed(2),
    max: Math.max(...windValues).toFixed(2)
  };
  const solarStats = {
    min: Math.min(...solarValues).toFixed(2),
    avg: (solarValues.reduce((a,b)=>a+b,0)/solarValues.length).toFixed(2),
    max: Math.max(...solarValues).toFixed(2)
  };
  
  return { wind: windStats, solar: solarStats };
}

function normalize(values) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;
  if (range === 0) return { scaled: values, min, max, range: 0 };
  const scaled = values.map(v => (v - min) / range);
  return { scaled, min, max, range };
}

function createSequences(values, seqLen = 10) {
  const xs = [];
  const ys = [];
  for (let i = 0; i < values.length - seqLen; i++) {
    xs.push(values.slice(i, i + seqLen));
    ys.push(values[i + seqLen]);
  }
  return { xs, ys };
}

function buildModel(seqLen) {
  const model = tf.sequential();
  model.add(tf.layers.lstm({ 
    units: 50, 
    inputShape: [seqLen, 1],
    returnSequences: false 
  }));
  model.add(tf.layers.dropout({rate: 0.2}));
  model.add(tf.layers.dense({ units: 1 }));
  model.compile({ 
    optimizer: 'adam', 
    loss: 'meanSquaredError' 
  });
  return model;
}

function renderPredictions(windPred, solarPred) {
  document.getElementById('wind-min').textContent = windPred.min.toFixed(2);
  document.getElementById('wind-avg').textContent = windPred.avg.toFixed(2);
  document.getElementById('wind-max').textContent = windPred.max.toFixed(2);

  document.getElementById('solar-min').textContent = solarPred.min.toFixed(2);
  document.getElementById('solar-avg').textContent = solarPred.avg.toFixed(2);
  document.getElementById('solar-max').textContent = solarPred.max.toFixed(2);
  
  console.log('LSTM Forecast rendered:', { windPred, solarPred });
}

function renderChart(windForecast, solarForecast) {
  const ctx = document.getElementById('predictionChart').getContext('2d');
  
  const labels = ['Day1','Day2','Day3','Day4','Day5','Day6','Day7'];
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        { 
          label: 'Wind', 
          data: windForecast, 
          borderColor: 'blue', 
          fill: false 
        },
        { 
          label: 'Solar', 
          data: solarForecast, 
          borderColor: 'orange', 
          fill: false 
        }
      ]
    },
    options: {
      responsive: true,
      plugins: { 
        title: { 
          display: true, 
          text: '7-Day Predicted Yield (April 2025)' 
        } 
      }
    }
  });
  
  console.log('LSTM Chart rendered:', { windForecast, solarForecast });
}

function renderHistoricalStats(histStats) {
  document.getElementById('hist-wind-min').textContent = histStats.wind.min;
  document.getElementById('hist-wind-avg').textContent = histStats.wind.avg;
  document.getElementById('hist-wind-max').textContent = histStats.wind.max;
  
  document.getElementById('hist-solar-min').textContent = histStats.solar.min;
  document.getElementById('hist-solar-avg').textContent = histStats.solar.avg;
  document.getElementById('hist-solar-max').textContent = histStats.solar.max;
  
  console.log('Historical stats rendered:', histStats);
}

async function runML() {
  console.log('Phase10 LSTM - Training on Jan-Mar 2025 for Apr forecast...');
  
  const rows = await loadSimData();
  const quarterData = filterQuarterData(rows);
  
  // Historical Mar 25-31 daily stats
  console.log(`Q1 2025 training data: ${quarterData.length} hourly points`);
  
  // Historical Mar 25-31 daily stats from full Q1 data
  const histDays = ['2025-03-25','2025-03-26','2025-03-27','2025-03-28','2025-03-29','2025-03-30','2025-03-31'];
  const histStats = getDailyStats(quarterData, histDays);
  
  // Populate historical table rows (IDs like mar25windmin)
  histDays.forEach((day, index) => {
    const rowId = `mar${25 + index}`;
    const fullId = day.replace(/-/g, '').toLowerCase();
    const s = histStats[day];
    if (s.wind && s.wind.min !== '--') {
      document.getElementById(`${fullId}-wind-min`).textContent = s.wind.min;
      document.getElementById(`${fullId}-wind-avg`).textContent = s.wind.avg;
      document.getElementById(`${fullId}-wind-max`).textContent = s.wind.max;
      document.getElementById(`${fullId}-solar-min`).textContent = s.solar.min;
      document.getElementById(`${fullId}-solar-avg`).textContent = s.solar.avg;
      document.getElementById(`${fullId}-solar-max`).textContent = s.solar.max;
    }
  });
  console.log('Historical Mar 25-31 populated:', histStats);
  
  // LSTM training data
  const windValues = quarterData.map(r => r.wind).filter(v => !isNaN(v));
  const solarValues = quarterData.map(r => r.solar).filter(v => !isNaN(v));
  
  if (windValues.length < 50 || solarValues.length < 50) {
    console.error('Insufficient data for LSTM');
    return;
  }
  
  const windNorm = normalize(windValues);
  const solarNorm = normalize(solarValues);
  
const seqLen = 24; // hourly daily patterns
  const windSeq = createSequences(windNorm.scaled, seqLen);
  const solarSeq = createSequences(solarNorm.scaled, seqLen);
  
  console.log(`Wind sequences: ${windSeq.xs.length}, Solar: ${solarSeq.xs.length}`);
  
  // Build & train models
  const windModel = buildModel(seqLen);
  const solarModel = buildModel(seqLen);
  
  console.log('Training Wind LSTM...');
  await windModel.fit(
    tf.tensor3d(windSeq.xs.map(seq => [seq]), [windSeq.xs.length, seqLen, 1]),
    tf.tensor2d(windSeq.ys.map(y => [y]), [windSeq.ys.length, 1]),
    { epochs: 20, verbose: 1, callbacks: { onEpochEnd: (epoch, logs) => console.log(`Wind Epoch ${epoch}: loss=${logs.loss.toFixed(4)}`) } }
  );
  
  console.log('Training Solar LSTM...');
  await solarModel.fit(
    tf.tensor3d(solarSeq.xs.map(seq => [seq]), [solarSeq.xs.length, seqLen, 1]),
    tf.tensor2d(solarSeq.ys.map(y => [y]), [solarSeq.ys.length, 1]),
    { epochs: 20, verbose: 1, callbacks: { onEpochEnd: (epoch, logs) => console.log(`Solar Epoch ${epoch}: loss=${logs.loss.toFixed(4)}`) } }
  );
  
// 168-hour (7-day hourly) forecast from last Q1 timestamp
  console.log('Generating 168-hour forecast...');
  let windForecast = [];
  let solarForecast = [];
  let windInput = windNorm.scaled.slice(-seqLen);
  let solarInput = solarNorm.scaled.slice(-seqLen);
  
  for (let i = 0; i < 168; i++) {
    const wt = tf.tensor3d([windInput], [1, seqLen, 1]);
    const st = tf.tensor3d([solarInput], [1, seqLen, 1]);
    
    const windPredScaled = windModel.predict(wt).dataSync()[0];
    const solarPredScaled = solarModel.predict(st).dataSync()[0];
    
    wt.dispose();
    st.dispose();
    
    const windPred = windPredScaled * windNorm.range + windNorm.min;
    const solarPred = solarPredScaled * solarNorm.range + solarNorm.min;
    
    windForecast.push(windPred);
    solarForecast.push(solarPred);
    
    windInput = windInput.slice(1).concat(windPredScaled);
    solarInput = solarInput.slice(1).concat(solarPredScaled);
  }
  
  // Create predicted rows for daily grouping
  const lastTimestamp = quarterData[quarterData.length - 1].timestamp;
  const predRows = [];
  for (let h = 0; h < 168; h++) {
    const predTime = new Date(lastTimestamp.getTime() + (h + 1) * 60 * 60 * 1000);
    predRows.push({ timestamp: predTime, wind: windForecast[h], solar: solarForecast[h] });
  }
  
// Group predicted daily stats
  const predDays = ['2025-04-01','2025-04-02','2025-04-03','2025-04-04','2025-04-05','2025-04-06','2025-04-07'];
  const predStats = getDailyStats(predRows, predDays);
  
console.log('✅ Phase10 LSTM complete - Apr 2025 forecasts ready!');
console.log('=== VALIDATION OUTPUT ===');
console.log('Wind Forecast (7 days):', windForecast.map(v => v.toFixed(2)));
console.log('Solar Forecast (7 days):', solarForecast.map(v => v.toFixed(2)));
console.log('Wind min/avg/max:', windStats.min.toFixed(2), windStats.avg.toFixed(2), windStats.max.toFixed(2));
console.log('Solar min/avg/max:', solarStats.min.toFixed(2), solarStats.avg.toFixed(2), solarStats.max.toFixed(2));
console.log('========================');
}

// Run when page loads
document.addEventListener('DOMContentLoaded', runML);

