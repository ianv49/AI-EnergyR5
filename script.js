// Tab Switching and Data Loading Functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    let apiStats = null;
    let weatherbitData = null;  // Dedicated storage for WeatherBit data

    // Default fallback data in case JSON fails to load
    const fallbackData = {
        sim: {
            temperature: { min: 18.02, max: 36.93, mean: 28.02, count: 9478 },
            humidity: { min: 35.05, max: 96.99, mean: 73.63, count: 9478 },
            irradiance: { min: 0.0, max: 1182.25, mean: 140.16, count: 9478 },
            wind_speed: { min: 0.02, max: 15.0, mean: 3.69, count: 9478 },
            wind_power_density: { min: 0.0, max: 2065.2, mean: 67.37, count: 9478 },
            solar_energy_yield: { min: 0.0, max: 7.97, mean: 0.42, count: 9478 }
        },
        nasa_power: {
            temperature: { min: 27.0, max: 34.8, mean: 30.2, count: 10177 },
            humidity: { min: 55.83, max: 97.0, mean: 74.53, count: 10177 },
            irradiance: { min: 0.0, max: 358.18, mean: 6.84, count: 10177 },
            wind_speed: { min: 1.0, max: 4.47, mean: 2.79, count: 10177 },
            wind_power_density: { min: 0.62, max: 54.81, mean: 16.12, count: 10177 },
            solar_energy_yield: { min: 0.0, max: 2.56, mean: 0.01, count: 10177 }
        },
        open_meteo: {
            temperature: { min: 22.4, max: 36.9, mean: 27.64, count: 10176 },
            humidity: { min: 25.0, max: 99.0, mean: 75.06, count: 10176 },
            irradiance: { min: 0.0, max: 1001.0, mean: 208.26, count: 10176 },
            wind_speed: { min: 0.0, max: 40.7, mean: 7.22, count: 10176 },
            wind_power_density: { min: 0.0, max: 41294.23, mean: 803.6, count: 10176 },
            solar_energy_yield: { min: 0.0, max: 1.0, mean: 0.21, count: 10176 }
        },
        meteostat: {
            temperature: { min: 23.7, max: 37.0, mean: 28.69, count: 9438 },
            humidity: { min: 36.0, max: 100.0, mean: 75.04, count: 9438 },
            irradiance: { min: 0.0, max: 0.0, mean: 0.0, count: 9438 },
            wind_speed: { min: 0.0, max: 11.31, mean: 2.58, count: 9438 },
            wind_power_density: { min: 0.0, max: 885.08, mean: 22.36, count: 9438 },
            solar_energy_yield: { min: 0.0, max: 0.0, mean: 0.0, count: 9438 }
        },
        weatherbit: {
            temperature: { min: 24.0, max: 37.0, mean: 29.5, count: 10905 },
            humidity: { min: 35.0, max: 100.0, mean: 75.0, count: 10905 },
            irradiance: { min: 0.0, max: 1182.25, mean: 300.0, count: 10905 },
            wind_speed: { min: 0.0, max: 15.0, mean: 3.0, count: 10905 },
            wind_power_density: { min: 0.0, max: 2065.2, mean: 50.0, count: 10905 },
            solar_energy_yield: { min: 0.0, max: 7.97, mean: 1.0, count: 10905 }
        }
    };

    // Dedicated function to load WeatherBit stats from weatherbit_stats.json
    async function loadWeatherbitData() {
        try {
            const response = await fetch('weatherbit_stats.json');
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            const data = await response.json();
            weatherbitData = data.weatherbit;
            console.log('✓ Successfully loaded weatherbit_stats.json', weatherbitData.temperature.count, 'records');
            return weatherbitData;
        } catch (error) {
            console.error('⚠ Error loading weatherbit_stats.json:', error);
            weatherbitData = fallbackData.weatherbit;
            return weatherbitData;
        }
    }

    // Load stats from JSON file (existing logic)
    fetch('api_stats.json')
        .then(response => {
            if (!response.ok) throw new Error('JSON response not OK');
            return response.json();
        })
        .then(data => {
            console.log('✓ Successfully loaded api_stats.json');
            apiStats = data;
            // Always load WeatherBit data independently
            loadWeatherbitData().then(() => {
                // Override/merge WeatherBit data
                apiStats.weatherbit = weatherbitData;
                updateSummaryCounts(apiStats);
                populateMetricsForAllAPIs(apiStats);
            });
        })
        .catch(error => {
            console.error('⚠ Error loading api_stats.json, using fallback data:', error);
            apiStats = { ...fallbackData };
            // Still load real WeatherBit data
            loadWeatherbitData().then(() => {
                apiStats.weatherbit = weatherbitData;
                updateSummaryCounts(apiStats);
                populateMetricsForAllAPIs(apiStats);
            });
        });

    // Update main summary counts
    function updateSummaryCounts(data) {
        const simCount = data.sim?.temperature?.count || 9478;
        const nasaCount = data.nasa_power?.temperature?.count || 10177;
        const openmeteoCount = data.open_meteo?.temperature?.count || 10176;
        const meteostatCount = data.meteostat?.temperature?.count || 9438;
        const weatherbitCount = data.weatherbit?.temperature?.count || 10905;
        document.getElementById('weatherbit-count').textContent = weatherbitCount.toLocaleString();
        const totalRealCount = nasaCount + openmeteoCount + meteostatCount + weatherbitCount;

        document.getElementById('sim-count').textContent = simCount.toLocaleString();
        document.getElementById('nasa-count').textContent = nasaCount.toLocaleString();
        document.getElementById('openmeteo-count').textContent = openmeteoCount.toLocaleString();
        document.getElementById('meteostat-count').textContent = meteostatCount.toLocaleString();
        document.getElementById('total-count').textContent = totalRealCount.toLocaleString();
    }

    // Populate metrics for all APIs
    function populateMetricsForAllAPIs(data) {
        console.log('📊 Populating metrics for all APIs');
        populateMetricsTab('sim-stats-metrics', data.sim, 'Sim');
        populateMetricsTab('nasa-stats-metrics', data.nasa_power, 'NASA Power');
        populateMetricsTab('openmeteo-stats-metrics', data.open_meteo, 'OpenMeteo');
        populateMetricsTab('meteostat-stats-metrics', data.meteostat, 'Meteostat');
        populateMetricsTab('weatherbit-stats-metrics', data.weatherbit, 'WeatherBit');
    }

    // Populate metrics tab with organized rows (unchanged)
    function populateMetricsTab(containerId, apiData, apiName) {
        const container = document.getElementById(containerId);
        console.log(`📍 Processing container: ${containerId}, exists: ${!!container}`);
        
        if (!container) {
            console.error(`❌ Container not found: ${containerId}`);
            return;
        }
        
        if (!apiData) {
            console.error(`❌ No data for: ${apiName}`);
            return;
        }

        // Clear existing content
        container.innerHTML = '';

        const fields = [
            { key: 'temperature', label: 'Temperature (°C)' },
            { key: 'humidity', label: 'Humidity (%)' },
            { key: 'irradiance', label: 'Irradiance (W/m²)' },
            { key: 'wind_speed', label: 'Wind Speed (m/s)' },
            { key: 'wind_power_density', label: 'Wind Power Density (W/m²)' },
            { key: 'solar_energy_yield', label: 'Solar Energy Yield (kWh)' }
        ];

        let createdCount = 0;
        fields.forEach(field => {
            const fieldData = apiData[field.key];
            if (!fieldData) {
                console.warn(`⚠ Missing data for field: ${field.key}`);
                return;
            }

            const metricItem = document.createElement('div');
            metricItem.className = 'metric-item';
            metricItem.innerHTML = `
                <div class="metric-label">${field.label}</div>
                <div class="metric-values">
                    <div class="metric-value">
                        <div class="metric-value-label">Min</div>
                        <div class="metric-value-number">${fieldData.min.toFixed(2)}</div>
                    </div>
                    <div class="metric-value">
                        <div class="metric-value-label">Ave</div>
                        <div class="metric-value-number">${fieldData.mean.toFixed(2)}</div>
                    </div>
                    <div class="metric-value">
                        <div class="metric-value-label">Max</div>
                        <div class="metric-value-number">${fieldData.max.toFixed(2)}</div>
                    </div>
                </div>
            `;
            container.appendChild(metricItem);
            createdCount++;
        });

        console.log(`✓ Created ${createdCount} metrics for ${apiName}`);
    }

    // Tab click handler
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        });
    });

    // Log script initialization
    console.log('✓ Script initialized successfully');
});
