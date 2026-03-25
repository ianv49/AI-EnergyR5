import React, { useEffect, useState } from 'react';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load from existing data/collect*.txt via fetch (GH Pages)
    Promise.all([
      fetch('../data/collect1.txt').then(r => r.text()),
      fetch('../data/collect5.txt').then(r => r.text()),
      // Add more
    ]).then(([collect1, collect5]) => {
      // Parse like existing JS
      setData({ collect1: parseTxt(collect1), collect5: parseTxt(collect5) });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const parseTxt = (text) => {
    // Same parser from index.html
    const lines = text.split('\n');
    let data = [], summary = {};
    // ... parsing logic
    return { data, summary };
  };

  if (loading) return <div className="flex justify-center items-center h-64"><div>Loading dashboard...</div></div>;

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-bold mb-4">Collect5 (Meteostat)</h2>
          <p>Rows: <span className="font-bold">{data?.collect5.summary.rows || 0}</span></p>
          <p>Max Irradiance: <span className="font-bold">{Math.max(...data?.collect5.data.map(d => d.irr) || [0])}</span></p>
        </div>
        {/* More cards */}
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-lg border border-gray-200 dark:border-gray-700">
        <h2 className="text-2xl font-bold mb-6">Live Data Table</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 font-semibold">Time</th>
                <th className="text-left py-3 px-4 font-semibold">Temp</th>
                <th className="text-left py-3 px-4 font-semibold">Irr</th>
                <th className="text-left py-3 px-4 font-semibold">Wind</th>
              </tr>
            </thead>
            <tbody>
              {data?.collect5.data.slice(0,20).map((row, i) => (
                <tr key={i} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750">
                  <td className="py-3 px-4">{row.timestamp}</td>
                  <td className="py-3 px-4 font-mono">{row.temp?.toFixed(1)}</td>
                  <td className="py-3 px-4 font-bold text-orange-600 dark:text-orange-400">{row.irr?.toFixed(1)}</td>
                  <td className="py-3 px-4">{row.wind?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

