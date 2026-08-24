import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface Device {
  id: string;
  hostname?: string;
  management_address: string;
  vendor?: string;
  platform?: string;
  status: string;
}

interface Props {
  onDeviceClick: (deviceId: string) => void;
}

export function DeviceList({ onDeviceClick }: Props) {
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadDevices();
  }, []);

  async function loadDevices() {
    try {
      setLoading(true);
      const data = await api.devices.listDevices();
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load devices');
    } finally {
      setLoading(false);
    }
  }

  const filteredDevices = devices.filter(d =>
    d.id.toLowerCase().includes(search.toLowerCase()) ||
    d.hostname?.toLowerCase().includes(search.toLowerCase()) ||
    d.vendor?.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <span className="badge badge-success">Active</span>;
      case 'inactive': return <span className="badge badge-warning">Inactive</span>;
      case 'error': return <span className="badge badge-error">Error</span>;
      default: return <span className="badge badge-info">{status}</span>;
    }
  };

  const getVendorIcon = (vendor?: string) => {
    switch (vendor?.toLowerCase()) {
      case 'cisco': return '🔵';
      case 'mikrotik': return '🔴';
      case 'linux': return '🐧';
      default: return '🖥️';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-red-600">Error: {error}</div>
        <button onClick={loadDevices} className="btn btn-primary mt-4">Retry</button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Devices</h2>
        <input
          type="text"
          placeholder="Search devices..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input w-64"
        />
      </div>
      
      <div className="card overflow-hidden">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Vendor</th>
              <th>Platform</th>
              <th>Management IP</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredDevices.map((device) => (
              <tr key={device.id} onClick={() => onDeviceClick(device.id)} className="cursor-pointer hover:bg-gray-50">
                <td className="font-mono font-medium">{device.hostname || device.id}</td>
                <td>
                  <span className="flex items-center gap-1">
                    {getVendorIcon(device.vendor)}
                    <span className="text-xs text-gray-500 capitalize">{device.vendor}</span>
                  </span>
                </td>
                <td className="text-sm text-gray-600">{device.platform || '-'}</td>
                <td className="font-mono text-sm">{device.management_address}</td>
                <td>{getStatusBadge(device.status)}</td>
                <td>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDeviceClick(device.id); }}
                    className="btn btn-sm btn-secondary"
                  >
                    Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
