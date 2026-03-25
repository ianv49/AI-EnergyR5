const { Bars3Icon, XMarkIcon, SunIcon, MoonIcon, ChartBarIcon, WrenchScrewdriverIcon, CloudIcon, DevicePhoneMobileIcon } = HeroiconsReact.Outline;

function Sidebar({ activeTab, setActiveTab, isDark, setIsDark }) {
  const [isMobileOpen, setIsMobileOpen] = React.useState(false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: ChartBarIcon },
    { id: 'sensors', label: 'Sensors', icon: DevicePhoneMobileIcon },
    { id: 'weather', label: 'Weather', icon: CloudIcon },
    { id: 'analytics', label: 'Analytics', icon: ChartBarIcon },
    { id: 'settings', label: 'Settings', icon: WrenchScrewdriverIcon },
  ];

  return React.createElement('aside', {
    className: `fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 shadow-lg transform ${
      isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
    } transition-transform duration-300 ease-in-out md:relative md:translate-x-0`
  }, [
    // Mobile button
    React.createElement('button', {
      className: 'md:hidden fixed top-4 left-4 z-50 p-2 bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-lg shadow-lg border',
      onClick: () => setIsMobileOpen(!isMobileOpen)
    }, isMobileOpen ? React.createElement(XMarkIcon, { className: 'h-6 w-6' }) : React.createElement(Bars3Icon, { className: 'h-6 w-6' })),

    // Header
    React.createElement('div', { className: 'p-6 border-b border-gray-200 dark:border-gray-700' }, [
      React.createElement('h1', { className: 'text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent' }, 'EnergyR5'),
      React.createElement('p', { className: 'text-xs text-gray-500 dark:text-gray-400 mt-1' }, 'Weather Dashboard')
    ]),

    // Nav
    React.createElement('nav', { className: 'p-4 space-y-2 mt-4' }, navItems.map(item => {
      const Icon = item.icon;
      return React.createElement('button', {
        key: item.id,
        className: `w-full flex items-center p-3 rounded-xl transition-all duration-200 ${
          activeTab === item.id ? 'bg-indigo-50 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 shadow-md font-medium' : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
        }`,
        onClick: () => {
          setActiveTab(item.id);
          setIsMobileOpen(false);
        }
      }, [
        React.createElement(Icon, { className: 'h-5 w-5 mr-3 flex-shrink-0' }),
        item.label
      ]);
    })),

    // Theme Toggle
    React.createElement('div', { className: 'absolute bottom-6 left-6 right-6' }, [
      React.createElement('button', {
        className: 'w-full flex items-center justify-center p-3 bg-gray-100 dark:bg-gray-800 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200 border',
        onClick: () => setIsDark(!isDark)
      }, [
        isDark ? React.createElement(SunIcon, { className: 'h-5 w-5 mr-2' }) : React.createElement(MoonIcon, { className: 'h-5 w-5 mr-2' }),
        isDark ? 'Light Mode' : 'Dark Mode'
      ])
    ])
  ]);
}

function App() {
  const [activeTab, setActiveTab] = React.useState('dashboard');
  const [isDark, setIsDark] = React.useState(false);

  const pages = {
    dashboard: React.createElement('div', { className: 'p-8' }, 'Dashboard - Weather Data from collect*.txt'),
    sensors: React.createElement('div', { className: 'p-8' }, 'Sensors Page'),
    weather: React.createElement('div', { className: 'p-8' }, 'Weather Page'),
    analytics: React.createElement('div', { className: 'p-8' }, 'Analytics Page'),
    settings: React.createElement('div', { className: 'p-8' }, 'Settings Page')
  };

  return React.createElement('div', {
    className: `min-h-screen transition-colors duration-300 ${isDark ? 'dark bg-gray-900 text-white' : 'bg-gradient-to-br from-blue-50 to-indigo-100 text-gray-900'}`
  }, [
    React.createElement(Sidebar, { activeTab, setActiveTab, isDark, setIsDark }),
    React.createElement('main', { className: 'md:ml-64 p-6 lg:p-8' }, pages[activeTab] || pages.dashboard)
  ]);
}

ReactDOM.render(React.createElement(App), document.getElementById('root'));

