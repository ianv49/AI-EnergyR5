import React from 'react';
import Sidebar from './Sidebar';
import { ChartBarIcon } from '@heroicons/react/24/outline';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-gray-900 dark:to-gray-800">
      <Sidebar />
      
      {/* Main Content */}
      <main className="md:ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          <header className="mb-8">
            <div className="flex items-center space-x-4 mb-4">
              <ChartBarIcon className="h-12 w-12 text-indigo-600 dark:text-indigo-400" />
              <div>
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white">EnergyR5 Dashboard</h1>
                <p className="text-xl text-gray-600 dark:text-gray-400 mt-1">Monitor sensors, weather, and analytics</p>
              </div>
            </div>
          </header>

          {/* Content Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Sensors</h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="font-semibold text-gray-900 dark:text-white">Temperature</span>
                  <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">28.5°C</span>
                </div>
                <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="font-semibold text-gray-900 dark:text-white">Humidity</span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">65%</span>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Weather</h2>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Wind Speed</span>
                  <span className="font-bold text-green-600 dark:text-green-400">12.3 m/s</span>
                </div>
                <div className="flex justify-between">
                  <span>Irradiance</span>
                  <span className="font-bold text-orange-600 dark:text-orange-400">856 W/m²</span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl p-8 text-white shadow-2xl lg:col-span-1">
              <h2 className="text-2xl font-bold mb-4">System Status</h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Online Sensors</span>
                  <span className="font-bold">24/25</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Energy</span>
                  <span className="font-bold">1.24 MWh</span>
                </div>
                <div className="flex justify-between">
                  <span>Uptime</span>
                  <span className="font-bold">99.8%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Section */}
          <div className="mt-12">
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl border border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Live Data Chart</h2>
              <div className="h-96 bg-gray-50 dark:bg-gray-900 rounded-xl flex items-center justify-center">
                <p className="text-gray-500 dark:text-gray-400 text-lg">Interactive Chart.js placeholder<br />Irradiance, Wind, Temperature over time</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

