async function parseSimData() {
  try {
    const response = await fetch('data/collect1.txt');
    const text = await response.text();
    const rows = text.trim().split('\n');
    const dataRows = rows.slice(1); // skip header

    let temps = [], hums = [], irrads = [], winds = [], wpds = [], seys = [];

    dataRows.forEach(row => {
      const parts = row.trim().split(',');
      if (parts.length >= 9) {
        temps.push(parseFloat(parts[2]));
        hums.push(parseFloat(parts[3]));
        irrads.push(parseFloat(parts[4]));
        winds.push(parseFloat(parts[5]));
        wpds.push(parseFloat(parts[7]));
        seys.push(parseFloat(parts[8]));
      }
    });

    const metrics = {
      avgTemp: temps.reduce((a,b)=>a+b,0) / temps.length || 0,
      avgHum: hums.reduce((a,b)=>a+b,0) / hums.length || 0,
      avgIrr: irrads.reduce((a,b)=>a+b,0) / irrads.length || 0,
      maxWind: winds.length ? Math.max(...winds) : 0,
      avgWPD: wpds.reduce((a,b)=>a+b,0) / wpds.length || 0,
      avgSEY: seys.reduce((a,b)=>a+b,0) / seys.length || 0,
      count: dataRows.length
    };

    document.getElementById('simSummary').innerHTML = `
      <h1 class="text-2xl font-bold text-blue-600 mb-4">Sim Data Summary</h1>
      <div class="space-y-2 text-gray-700">
        <p><span class="font-semibold">Data points:</span> ${metrics.count}</p>
        <p><span class="font-semibold">Avg Temp:</span> ${metrics.avgTemp.toFixed(1)} °C</p>
        <p><span class="font-semibold">Avg Humidity:</span> ${metrics.avgHum.toFixed(1)} %</p>
        <p><span class="font-semibold">Avg Irradiance:</span> ${metrics.avgIrr.toFixed(1)} W/m²</p>
        <p><span class="font-semibold">Max Wind Speed:</span> ${metrics.maxWind.toFixed(1)} m/s</p>
        <p><span class="font-semibold">Avg WPD:</span> ${metrics.avgWPD.toFixed(2)}</p>
        <p><span class="font-semibold">Avg SEY:</span> ${metrics.avgSEY.toFixed(2)} kWh/m²/day</p>
      </div>
    `;
  } catch (err) {
    console.error('Error loading sim data:', err);
    document.getElementById('simSummary').innerHTML = `
      <h1 class="text-2xl font-bold text-blue-600 mb-4">Sim Data Summary</h1>
      <p class="text-red-500">Error loading sim data.</p>
    `;
  }
}

parseSimData();
