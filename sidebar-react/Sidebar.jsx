import React from 'react';
import { Bars3Icon, XMarkIcon, SunIcon, MoonIcon, ChartBarIcon, WrenchScrewdriverIcon, CloudIcon, DevicePhoneMobileIcon } from '@heroicons/react/24/outline';

const Sidebar = ({ activeTab, setActiveTab, isDark, setIsDark }) => {
  const [isMobileOpen, setIsMobileOpen] = React.useState(false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: ChartBarIcon },
    { id: 'sensors', label: 'Sensors', icon: DevicePhoneMobileIcon },
    { id: 'weather', label: 'Weather', icon: CloudIcon },
    { id: 'analytics', label: 'Analytics', icon: ChartBarIcon },
    { id: 'settings', label: 'Settings', icon: WrenchScrewdriverIcon },
  ];

  return (
    <>
      {/* Mobile hamburger */}
      <button 
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-lg shadow-lg border"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <XMarkIcon className="h-6 w-6" /> : <Bars3Icon className="h-6 w-6" />}
      </button>

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 shadow-lg
        transform ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        transition-transform duration-300 ease-in-out md:relative md:translate-x-0
        ${isMobileOpen ? 'md:hidden' : ''}
      `}>
        
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            EnergyR5
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Weather Dashboard</p>
        </div>

        {/* Nav */}
        <nav className="p-4 space-y-2 mt-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={`
                  w-full flex items-center p-3 rounded-xl transition-all duration-200
                  ${activeTab === item.id 
                    ? 'bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 shadow-md font-medium' 
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                  }
                `}
                onClick={() => {
                  setActiveTab(item.id);
                  setIsMobileOpen(false);
                }}
              >
                <Icon className="h-5 w-5 mr-3 flex-shrink-0" />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Theme Toggle */}
        <div className="absolute bottom-6 left-6 right-6">
          <button
            className="w-full flex items-center justify-center p-3 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200 border"
            onClick={() => setIsDark(!isDark)}
          >
            {isDark ? <SunIcon className="h-5 w-5 mr-2" /> : <MoonIcon className="h-5 w-5 mr-2" />}
            {isDark ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </aside>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;

