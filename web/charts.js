// charts.js - Summary cards with real metrics from collect*.txt
// Loads 7 APIs automatically, creates cards dynamically

const sources = {
  1: { name: 'Sim Data', file: 'data/collect1.txt', color: '#3B82F6', api: 'sim' },
  2: { name: 'NASA POWER', file: 'data/collect2.txt', color: '#F59E0B', api: 'nasa_power' },
  3: { name: 'Open-Meteo', file: 'data/collect3.txt', color: '#10B981', api: 'open_meteo' },
  4: { name: 'Solcast', file: 'data/collect4.txt', color: '#8B5CF6', api: 'solcast' },
  5: { name: 'Meteostat', file: 'data/collect5.txt', color: '#EF4444', api: 'meteostat' },
  6: { name: 'Tomorrow', file: 'data/collect6.txt', color: '#06B6D4', api: 'tomorrow' },
  7: { name: 'Weatherbit', file: 'data/collect7.txt', color: '#F97316', api: 'weatherbit' }
};

function createSummaryCard(sourceId, metrics) {
  const source = sources[sourceId];
  const container = document.getElementById('summaryCards') || document.body;
  
  // Find max avgSEY across all for highlight
  const maxSEY = Math.max(...Object.values(allMetrics || {}).map(m => m.avgSEY));
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
        <span class="text-2xl font-bold text-gray-900 dark:text-white">${metrics.avgTemp}°C</span>
      </div>
      <div class="flex justify-between items-baseline">
        <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Irradiance</span>
        <span class="text-2xl font-bold text-orange-600 dark:text-orange-400">${metrics.avgIrr} W/m²</span>
      </div>
      <div class="flex justify-between items-baseline">
        <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Max Wind</span>
        <span class="text-2xl font-bold text-blue-600 dark:text-blue-400">${metrics.maxWind} m/s</span>
      </div>
      <div class="flex justify-between items-baseline ${isBest ? 'bg-emerald-50 dark:bg-emerald-900/50 p-3 rounded-xl' : ''}">
        <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Avg SEY</span>
        <span class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">${metrics.avgSEY.toFixed(2)} kWh</span>
      </div>
    </div>
  `;
  
  container.appendChild(card);
}

let allMetrics = {};

// Correct mapping with file paths
const sources = {
  1: { name: 'sim', color: '#3B82F6', file: 'data/collect1.txt' },
  2: { name: 'nasa_power', color: '#F59E0B', file: 'data/collect2.txt' },
  3: { name: 'open_meteo', color: '#10B981', file: 'data/collect3.txt' },
  4: { name: 'solcast', color: '#8B5CF6', file: 'data/collect4.txt' },
  5: { name: 'meteostat', color: '#EF4444', file: 'data/collect5.txt' },
  6: { name: 'tomorrow', color: '#06B6D4', file: 'data/collect6.txt' },
  7: { name: 'weatherbit', color: '#F97316', file: 'data/collect7.txt' }
};

async function parseDataFile(sourceId) {
  const src = sources[sourceId];
  try {
    const response = await fetch(src.file);
    const text = await response.text();
    const rows = text.trim().split('\n');

    let temps = [], irrads = [], winds = [], seys = [];

    rows.forEach(row => {
      const parts = row.split(',');
      // Adjust indices based on your file format
      const temp = parseFloat(parts[1]);
      const irrad = parseFloat(parts[2]);
      const wind = parseFloat(parts[3]);
      const sey = parseFloat(parts[4]);

      if (!isNaN(temp)) temps.push(temp);
      if (!isNaN(irrad)) irrads.push(irrad);
      if (!isNaN(wind)) winds.push(wind);
      if (!isNaN(sey)) seys.push(sey);
    });

    const metrics = {
      avgTemp: temps.reduce((a,b)=>a+b,0) / temps.length || 0,
      avgIrr: irrads.reduce((a,b)=>a+b,0) / irrads.length || 0,
      maxWind: winds.length ? Math.max(...winds) : 0,
      avgSEY: seys.reduce((a,b)=>a+b,0) / seys.length || 0,
      count: rows.length
    };

    const card = createSummaryCard(sourceId, metrics);
    document.getElementById('summaryCards').appendChild(card);
  } catch (err) {
    console.error(`Error loading ${src.file}:`, err);
  }
}

// Loop through all sources
Object.keys(sources).forEach(id => parseDataFile(parseInt(id)));


