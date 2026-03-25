// charts.js - Summary cards with real metrics from collect*.txt
// Loads 7 APIs automatically

const sources = {
  1: { name: 'sim', color: '#3B82F6', file: 'data/collect1.txt' },
  2: { name: 'nasa_power', color: '#F59E0B', file: 'data/collect2.txt' },
  3: { name: 'open_meteo', color: '#10B981', file: 'data/collect3.txt' },
  4: { name: 'solcast', color: '#8B5CF6', file: 'data/collect4.txt' },
  5: { name: 'meteostat', color: '#EF4444', file: 'data/collect5.txt' },
  6: { name: 'tomorrow', color: '#06B6D4', file: 'data/collect6.txt' },
  7: { name: 'weatherbit', color: '#F97316', file: 'data/collect7.txt' }
};

let allMetrics = {};

function createSummaryCard(sourceId, metrics) {
  const source = sources[sourceId];
  const container = document.getElementById('summaryCards') || document.body;
  
  // Find best performer
  const maxSEY = Math.max(...Object.values(allMetrics).map(m => m.avgSEY));
  const isBest = metrics.avgSEY === maxSEY;
  
  const card = document.createElement('div');
  card.className = `bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 border border-gray-200 dark:border-gray-700 hover:shadow-2xl transition-all duration-300 ${isBest ? 'ring-4 ring-emerald-200 dark:ring-emerald-900' : ''}`;
  card.style.maxWidth = '300px';
  
  card.innerHTML = `
    <div class="flex items-center mb-4">
      <div class="w-12 h-12 bg-gradient-to-br from-[${source.color}] to-[${source.color}] rounded-2xl p-3 flex-shrink-0 shadow-lg">
        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
      </div>
      <div class="ml-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">${source.name}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">${metrics.count.toLocaleString()} rows</p>
      </div>
    </div>
    <div class="space-y-3">
      <div class="flex justify-between items-baseline">
        <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Temp</span>
        <span class="text-2xl font-bold text-gray-900 dark:text-white">${metrics.avgTemp.toFixed(1)}°C</span>
      </div>
      <div class="flex justify-between items-baseline">
        <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Irradiance</span>
        <span class="text-2xl font-bold text-orange-600 dark:text-orange-400">${metrics.avgIrr.toFixed(1)} W/m²</span>
      </div>
      <div class="flex justify-between items-baseline">
        <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Max Wind</span>
        <span class="text-2xl font-bold text-blue-600 dark:text-blue-400">${metrics.maxWind.toFixed(1)} m/s</span>
      </div>
      <div class="flex justify-between items-baseline ${isBest ? 'bg-emerald-50 dark:bg-emerald-900/50 p-3 rounded-xl' : ''}">
        <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Avg SEY</span>
        <span class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">${metrics.avgSEY.toFixed(2)} kWh</span>
      </div>
    </div>
  `;
  
  container.appendChild(card);
}

async function parseDataFile(sourceId) {
  const source = sources[sourceId];
  try {
    const response = await fetch(source.file);
    const text = await response.text();
    const lines = text.split('\n').slice(1); // Skip first header line
    
    let tempSum = 0, irrSum = 0, windMax = 0, seySum = 0, count = 0;
    
    for (let line of lines) {
      if (!line.trim()) continue;
      const cols = line.split('\t');
      if (cols.length < 9) continue;
      
      const temp = parseFloat(cols[2]);
      const irr = parseFloat(cols[4]);
      const wind = parseFloat(cols[5]);
      const sey = parseFloat(cols[8]);
      
      if (!isNaN(temp) && !isNaN(irr) && !isNaN(wind) && !isNaN(sey)) {
        tempSum += temp;
        irrSum += irr;
        windMax = Math.max(windMax, wind);
        seySum += sey;
        count++;
      }
    }
    
    const metrics = {
      avgTemp: count ? tempSum / count : 0,
      avgIrr: count ? irrSum / count : 0,
      maxWind: windMax,
      avgSEY: count ? seySum / count : 0,
      count
    };
    
    allMetrics[sourceId] = metrics;
    createSummaryCard(sourceId, metrics);
    
  } catch (e) {
    console.error(`Error parsing ${source.file}:`, e);
    createSummaryCard(sourceId, {count: 0, avgTemp:0, avgIrr:0, maxWind:0, avgSEY:0});
  }
}

// Load all
for (let sourceId = 1; sourceId <= 7; sourceId++) {
  parseDataFile(sourceId);
}

