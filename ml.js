// ml.js - Simple ML Baseline for AI-EnergyR5 (Mar 2025 historical + Apr preds)
// Updated per task: parse collect1.txt (parts[5]=wind, [8]=solar), Jan-Mar filter, daily stats, baseline pred, table + MLoutput.txt

async function loadSimData() {
  console.log('loadSimData START'); // DEBUG
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
    
  console.log(`Loaded ${rows.length} valid data points from collect1.txt (Q1: ${quarterData.length} after filter)`);
    return rows;
  } catch (error) {
    console.error('Error loading data:', error);
    return [];
  }
}

function filterQuarterData(rows) {
  console.log(`filterQuarterData: input ${rows.length}, Q1 dates:`, rows.map(r=>r.timestamp.toISOString().slice(0,10)).slice(-10)); // DEBUG
  return rows.filter(r => {
    const year = r.timestamp.getFullYear();
    const month = r.timestamp.getMonth() + 1;
    return year === 2025 && month >= 1 && month <= 3;
  });
}

function getDateKey(timestamp) {
  return timestamp.toISOString().split('T')[0]; // YYYY-MM-DD
}

function getDailyStats(rows, targetDays) {
  const dayData = {};
  rows.forEach(r => {
    const key = getDateKey(r.timestamp);
    if (!dayData[key]) dayData[key] = {winds: [], solars: []};
    dayData[key].winds.push(r.wind);
    dayData[key].solars.push(r.solar);
  });

  const stats = {};
  targetDays.forEach(day => {
    const data = dayData[day];
    if (data && data.winds.length > 0) {
      stats[day] = {
        wind: {
          min: Math.min(...data.winds).toFixed(2),
          avg: (data.winds.reduce((a,b)=>a+b,0)/data.winds.length).toFixed(2),
          max: Math.max(...data.winds).toFixed(2)
        },
        solar: {
          min: Math.min(...data.solars).toFixed(2),
          avg: (data.solars.reduce((a,b)=>a+b,0)/data.solars.length).toFixed(2),
          max: Math.max(...data.solars).toFixed(2)
        }
      };
    } else {
      stats[day] = {wind: {min:'--', avg:'--', max:'--'}, solar: {min:'--', avg:'--', max:'--'}};
    }
  });
  return stats;
}

function generatePredictions(marchStats) {
  // Compute March avgs/stddev from Mar 25-31
  const marchWind = [], marchSolar = [];
  ['2025-03-25','2025-03-26','2025-03-27','2025-03-28','2025-03-29','2025-03-30','2025-03-31'].forEach(day => {
    const s = marchStats[day];
    if (s.wind.avg !== '--') {
      marchWind.push(parseFloat(s.wind.avg));
      marchSolar.push(parseFloat(s.solar.avg));
    }
  });

  if (marchWind.length === 0) {
    console.error('No March data for predictions');
    return {};
  }

  const windAvg = marchWind.reduce((a,b)=>a+b,0)/marchWind.length;
  const windStd = Math.sqrt(marchWind.reduce((a,b)=>(a += Math.pow(b-windAvg,2)),0)/marchWind.length);
  const solarAvg = marchSolar.reduce((a,b)=>a+b,0)/marchSolar.length;
  const solarStd = Math.sqrt(marchSolar.reduce((a,b)=>(a += Math.pow(b-solarAvg,2)),0)/marchSolar.length);

  console.log('March baselines:', {windAvg: windAvg.toFixed(2), windStd: windStd.toFixed(2), solarAvg: solarAvg.toFixed(2), solarStd: solarStd.toFixed(2)});

  // Baseline preds: avg ± std * rand(0.8-1.2)
  const predDays = ['2025-04-01','2025-04-02','2025-04-03','2025-04-04','2025-04-05','2025-04-06','2025-04-07'];
  const predStats = {};
  predDays.forEach(day => {
    const windVar = (Math.random() * 0.4 + 0.8) * windStd; // 0.8-1.2 * std
    const solarVar = (Math.random() * 0.4 + 0.8) * solarStd;
    const windAvgDay = (windAvg + (Math.random() < 0.5 ? -windVar : windVar)).toFixed(2);
    const solarAvgDay = (solarAvg + (Math.random() < 0.5 ? -solarVar : solarVar)).toFixed(2);
    predStats[day] = {
      wind: {min: (parseFloat(windAvgDay) * 0.7).toFixed(2), avg: windAvgDay, max: (parseFloat(windAvgDay) * 1.3).toFixed(2)},
      solar: {min: (parseFloat(solarAvgDay) * 0.7).toFixed(2), avg: solarAvgDay, max: (parseFloat(solarAvgDay) * 1.3).toFixed(2)}
    };
  });
  return predStats;
}

async function writeMLOutput(allStats) {
  const now = new Date().toISOString().slice(0,19).replace('T', ' ');
  let csv = `# ML page output last updated: ${now}\n`;
  csv += `# Summary: sim-ML = 14\n`;
  csv += `[sim]\n`;
  csv += `id,timestamp,wind-min,wind-avg,wind-max,solar-min,solar-avg,solar-max,source\n`;

  const days = ['2025-03-25','2025-03-26','2025-03-27','2025-03-28','2025-03-29','2025-03-30','2025-03-31','2025-04-01','2025-04-02','2025-04-03','2025-04-04','2025-04-05','2025-04-06','2025-04-07'];
  days.forEach((day, id) => {
    const s = allStats[day];
    csv += `${id+1},${day},${s.wind.min},${s.wind.avg},${s.wind.max},${s.solar.min},${s.solar.avg},${s.solar.max},sim-ML\n`;
  });

  try {
    await fetch('data/MLoutput.txt', {
      method: 'PUT',
      headers: {'Content-Type': 'text/plain'},
      body: csv
    });
    console.log('✅ MLoutput.txt written successfully');
  } catch (error) {
    console.error('Error writing MLoutput.txt:', error);
  }
}

function populateTable(allStats) {
  const dayMap = {
    '2025-03-25': 'mar25', '2025-03-26': 'mar26', '2025-03-27': 'mar27', '2025-03-28': 'mar28',
    '2025-03-29': 'mar29', '2025-03-30': 'mar30', '2025-03-31': 'mar31',
    '2025-04-01': 'apr01', '2025-04-02': 'apr02', '2025-04-03': 'apr03', '2025-04-04': 'apr04',
    '2025-04-05': 'apr05', '2025-04-06': 'apr06', '2025-04-07': 'apr07'
  };

  Object.keys(dayMap).forEach(day => {
    const prefix = dayMap[day];
    const s = allStats[day];
    document.getElementById(`${prefix}-wind-min`).textContent = s.wind.min;
    document.getElementById(`${prefix}-wind-avg`).textContent = s.wind.avg;
    document.getElementById(`${prefix}-wind-max`).textContent = s.wind.max;
    document.getElementById(`${prefix}-solar-min`).textContent = s.solar.min;
    document.getElementById(`${prefix}-solar-avg`).textContent = s.solar.avg;
    document.getElementById(`${prefix}-solar-max`).textContent = s.solar.max;
  });
  console.log('✅ Table populated with 14 days data');
}

async function runMLBaseline() {
  console.log('AI-EnergyR5 Simple ML Baseline - Mar 25-31 stats + Apr 01-07 predictions');
  
  const rows = await loadSimData();
  const quarterData = filterQuarterData(rows);
  console.log(`Q1 2025 data: ${quarterData.length} points`);

  const histDays = ['2025-03-25','2025-03-26','2025-03-27','2025-03-28','2025-03-29','2025-03-30','2025-03-31'];
  const histStats = getDailyStats(quarterData, histDays);
  console.log('Historical Mar stats:', histStats);

  const predStats = generatePredictions(histStats);
  console.log('Predicted Apr stats:', predStats);

  const allStats = {...histStats, ...predStats};
  populateTable(allStats);
  await writeMLOutput(allStats);

  console.log('✅ ML Baseline complete - table + MLoutput.txt ready!');
}

// Run on load
document.addEventListener('DOMContentLoaded', runMLBaseline);
