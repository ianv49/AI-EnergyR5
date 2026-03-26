// ml.js
// LSTM Forecast for AI-EnergyR5 Phase10 - Wind/Solar 7-day April 2025 from Jan-Mar data

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

function filterQuarterData(rows) {
  return rows.filter(r => {
    const year = r.timestamp.getFullYear();
    const month = r.timestamp.getMonth() + 1;
    return year === 2025 && month >= 1 && month <= 3;
  });
}

// LSTM utils
function normalize(values) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  return {
    min,
    max,
    scaled: values.map(v => (v - min) / (max - min || 1))
  };
}

function createSequences(data, seqLen = 10) {
  const xs = [];
  const ys = [];
  for (let i = 0; i < data.length - seqLen; i++) {
    xs.push(data.slice(i, i + seqLen));
    ys.push(data[i + seqLen]);
  }
  return { xs, ys };
}

function buildModel(seqLen) {
  const model = tf.sequential({
    layers: [
      tf.layers.lstm({units: 50, inputShape: [seqLen, 1], returnSequences: false}),
      tf.layers.dense({units: 1})
    ]
  });
  model.compile({
    optimizer: 'adam',
    loss: 'meanSquaredError'
  });
  return model;
}

function renderPredictions(windStats, solarStats) {
  ['min', 'avg', 'max'].forEach(stat => {
    document.getElementById(`wind-${stat}`).textContent = windStats[stat].toFixed(2);
    document.getElementById(`solar-${stat}`).textContent = solarStats[stat].toFixed(2);
  });
  console.log('LSTM forecast stats:', { windStats, solarStats });
}

function renderChart(windForecast, solarForecast) {
  const ctx = document.getElementById('predictionChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
      datasets: [{
        label: '🌪️ Wind Yield',
        data: windForecast,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }, {
        label: '☀️ Solar Yield',
        data: solarForecast,
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'April 2025 7-Day LSTM Forecast'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: v => v.toFixed(2) }
        }
      }
    }
  });
  console.log('LSTM forecast chart rendered');
}

async function runML() {
  console.log('Phase10 LSTM: Jan-Mar 2025 → April 7-day forecast');
  
  const rows = await loadSimData();
  const quarterData = filterQuarterData(rows);
  console.log(`${quarterData.length} training points (Jan-Mar 2025)`);
  
  if (quarterData.length < 20) {
    console.error('Insufficient training data');
    return;
  }
  
  const windValues = quarterData.map(r => r.wind).filter(v => !isNaN(v));
  const solarValues = quarterData.map(r => r.solar).filter(v => !isNaN(v));
  
  const windNorm = normalize(windValues);
  const solarNorm = normalize(solarValues);
  
  const seqLen = 10;
  const windSeq = createSequences(windNorm.scaled, seqLen);
  const solarSeq = createSequences(solarNorm.scaled, seqLen);
  
  console.log(`Wind sequences: ${windSeq.xs.length}, Solar: ${solarSeq.xs.length}`);
  
  const windModel = buildModel(seqLen);
  const solarModel = buildModel(seqLen);
  
  // Train
  await windModel.fit(
    tf.tensor3d(windSeq.xs.map(seq => [seq]), [windSeq.xs.length, seqLen, 1]),
    tf.tensor2d(windSeq.ys.map(y => [y]), [windSeq.ys.length, 1]),
    { epochs: 30, validationSplit: 0.2, verbose: 1 }
  );
  
  await solarModel.fit(
    tf.tensor3d(solarSeq.xs.map(seq => [seq]), [solarSeq.xs.length, seqLen, 1]),
    tf.tensor2d(solarSeq.ys.map(y => [y]), [solarSeq.ys.length, 1]),
    { epochs: 30, validationSplit: 0.2, verbose: 1 }
  );
  
  // Forecast 7 days
  const windForecast = [];
  const solarForecast = [];
  let windInput = windNorm.scaled.slice(-seqLen);
  let solarInput = solarNorm.scaled.slice(-seqLen);
  
  for (let day = 0; day < 7; day++) {
    const windPredScaled = windModel.predict(tf.tensor3d([windInput], [1, seqLen, 1]), { batchSize: 1 }).dataSync()[0];
    const solarPredScaled = solarModel.predict(tf.tensor3d([solarInput], [1, seqLen, 1]), { batchSize: 1 }).dataSync()[0];
    
    const windPred = windPredScaled * (windNorm.max - windNorm.min) + windNorm.min;
    const solarPred = solarPredScaled * (solarNorm.max - solarNorm.min) + solarNorm.min;
    
    windForecast.push(windPred);
    solarForecast.push(solarPred);
    
    windInput = windInput.slice(1).concat(windPredScaled);
    solarInput = solarInput.slice(1).concat(solarPredScaled);
  }
  
  const windStats = {
    min: Math.min(...windForecast),
    avg: windForecast.reduce((a, b) => a + b) / 7,
    max: Math.max(...windForecast)
  };
  
  const solarStats = {
    min: Math.min(...solarForecast),
    avg: solarForecast.reduce((a, b) => a + b) / 7,
    max: Math.max(...solarForecast)
  };
  
  renderPredictions(windStats, solarStats);
  renderChart(windForecast, solarForecast);
  
  console.log('✅ LSTM Phase10 complete: Real 7-day forecasts ready');
}

// Run on load
document.addEventListener('DOMContentLoaded', runML);

