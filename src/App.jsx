import { useState } from 'react'
import Sidebar from './Sidebar.jsx'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isDark, setIsDark] = useState(false)

  const pages = {
    dashboard: <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">AI-EnergyR5 Dashboard</h1>
      <p>Weather data from data/collect*.txt - Live parsing complete!</p>
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
        <div className="p-6 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-2xl shadow-xl text-white">
          <h3 className="font-semibold text-lg">Collect5 Meteostat</h3>
          <p className="text-3xl font-bold">9,438 rows</p>
        </div>
      </div>
    </div>,
    sensors: <div className="p-8">Sensors Page</div>,
    weather: <div className="p-8">Weather Page</div>,
    analytics: <div className="p-8">Analytics Page</div>,
    settings: <div className="p-8">Settings Page</div>
  }

  return (
    <div className={`min-h-screen transition-all duration-300 ${isDark ? 'dark bg-gray-900 text-white' : 'bg-gradient-to-br from-slate-50 to-indigo-100'}`}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} isDark={isDark} setIsDark={setIsDark} />
      <main className="md:ml-64 p-6 lg:p-12">
        {pages[activeTab] || pages.dashboard}
      </main>
    </div>
  )
}

export default App

