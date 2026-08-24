import { useState, useEffect } from 'react';
import { api } from '../api/client';

export function MonitoringDashboard() {
  const [devices, setDevices] = useState<any[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30);

  useEffect(() => {
    loadDevices();
  }, []);

  useEffect(() => {
    if (!autoRefresh || !selectedDevice) return;
    const interval = setInterval(() => {
      loadMetrics();
    }, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, selectedDevice, refreshInterval]);

  useEffect(() => {
    if (selectedDevice) {
      loadMetrics();
    }
  }, [selectedDevice]);

  async function loadDevices() {
    try {
      const data = await api.devices.listDevices();
      setDevices(data);
    } catch (err) {
      console.error('Failed to load devices:', err);
    }
  }

  async function loadMetrics() {
    if (!selectedDevice) return;
    try {
      setLoading(true);
      const data = await api.getMonitoring(selectedDevice, ['cpu', 'memory', 'disk', 'temperature', 'voltage']);
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  }

  const formatMetric = (value: any) => {
    if (typeof value === 'string') return value;
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  const renderMetricCard = (title: string, value: any) => (
    <div className="p-4 bg-gray-50 rounded-lg">
      <p className="text-sm text-gray-500">{title}</p>
      <pre className="font-mono text-sm text-gray-800 whitespace-pre-wrap mt-1 max-h-40 overflow-auto">
        {formatMetric(value)}
      </pre>
    </div>
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Monitoring Dashboard</h2>
        <div className="flex items-center gap-4">
          <div className="form-group" style={{marginBottom: 0}}>
            <label className="label" style={{display: 'block', marginBottom: '0.25rem'}}>Device</label>
            <select
              value={selectedDevice}
              onChange={(e) => setSelectedDevice(e.target.value)}
              className="input w-64"
            >
              <option value="">Select device...</option>
              {devices.map(d => (
                <option key={d.id} value={d.id}>
                  {d.hostname || d.id} ({d.vendor})
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              Auto-refresh
            </label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="input w-24"
              disabled={!autoRefresh}
            >
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>1m</option>
              <option value={300}>5m</option>
            </select>
            <button onClick={loadMetrics} disabled={loading} className="btn btn-primary btn-sm">
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {!selectedDevice ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">Select a device to view monitoring metrics</p>
        </div>
      ) : metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {metrics.cpu && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">CPU</p>
              <pre className="font-mono text-sm text-gray-800 whitespace-pre-wrap mt-1 max-h-40 overflow-auto">
                {JSON.stringify(metrics.cpu, null, 2)}
              </pre>
            </div>
          )}
          {metrics.memory && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Memory</p>
              <pre className="font-mono text-sm text-gray-800 whitespace-pre-wrap mt-1 max-h-40 overflow-auto">
                {JSON.stringify(metrics.memory, null, 2)}
              </pre>
            </div>
          )}
          {metrics.disk && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Disk</p>
              <pre className="font-mono text-sm text-gray-800 whitespace-pre-wrap mt-1 max-h-40 overflow-auto">
                {JSON.stringify(metrics.disk, null, 2)}
              </pre>
            </div>
          )}
          {metrics.temperature && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Temperature</p>
              <pre className="font-mono text-sm text-gray-800 whitespace-pre-wrap mt-1 max-h-40 overflow-auto">
                {JSON.stringify(metrics.temperature, null, 2)}
              </pre>
            </div>
          )}
          {metrics.voltage && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Voltage</p>
              <pre className="font-mono text-sm text-gray-800 whitespace-pre-wrap mt-1 max-h-40 overflow-auto">
                {JSON.stringify(metrics.voltage, null, 2)}
              </pre>
            </div>
          )}
          {metrics.health && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Health</p>
              <pre className="font-mono text-sm text-gray-800 whitespace-pre-wrap mt-1 max-h-40 overflow-auto">
                {JSON.stringify(metrics.health, null, 2)}
              </pre>
            </div>
          )}
          {Object.keys(metrics).length === 0 && (
            <div className="col-span-full card text-center py-12 text-gray-500">
              No metrics available for this device
            </div>
          )}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-500">No metrics loaded yet</p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}