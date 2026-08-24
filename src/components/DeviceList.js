import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { api } from '../api/client';
export function DeviceList({ onDeviceClick }) {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [search, setSearch] = useState('');
    useEffect(() => {
        loadDevices();
    }, []);
    async function loadDevices() {
        try {
            setLoading(true);
            const data = await api.devices.listDevices();
            setDevices(data);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load devices');
        }
        finally {
            setLoading(false);
        }
    }
    const filteredDevices = devices.filter(d => d.id.toLowerCase().includes(search.toLowerCase()) ||
        d.hostname?.toLowerCase().includes(search.toLowerCase()) ||
        d.vendor?.toLowerCase().includes(search.toLowerCase()));
    const getStatusBadge = (status) => {
        switch (status) {
            case 'active': return _jsx("span", { className: "badge badge-success", children: "Active" });
            case 'inactive': return _jsx("span", { className: "badge badge-warning", children: "Inactive" });
            case 'error': return _jsx("span", { className: "badge badge-error", children: "Error" });
            default: return _jsx("span", { className: "badge badge-info", children: status });
        }
    };
    const getVendorIcon = (vendor) => {
        switch (vendor?.toLowerCase()) {
            case 'cisco': return '🔵';
            case 'mikrotik': return '🔴';
            case 'linux': return '🐧';
            default: return '🖥️';
        }
    };
    if (loading) {
        return (_jsx("div", { className: "flex items-center justify-center h-64", children: _jsx("div", { className: "animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" }) }));
    }
    if (error) {
        return (_jsxs("div", { className: "card", children: [_jsxs("div", { className: "text-red-600", children: ["Error: ", error] }), _jsx("button", { onClick: loadDevices, className: "btn btn-primary mt-4", children: "Retry" })] }));
    }
    return (_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsx("h2", { className: "text-xl font-semibold", children: "Devices" }), _jsx("input", { type: "text", placeholder: "Search devices...", value: search, onChange: (e) => setSearch(e.target.value), className: "input w-64" })] }), _jsx("div", { className: "card overflow-hidden", children: _jsxs("table", { className: "table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: "Name" }), _jsx("th", { children: "Vendor" }), _jsx("th", { children: "Platform" }), _jsx("th", { children: "Management IP" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "Actions" })] }) }), _jsx("tbody", { children: filteredDevices.map((device) => (_jsxs("tr", { onClick: () => onDeviceClick(device.id), className: "cursor-pointer hover:bg-gray-50", children: [_jsx("td", { className: "font-mono font-medium", children: device.hostname || device.id }), _jsx("td", { children: _jsxs("span", { className: "flex items-center gap-1", children: [getVendorIcon(device.vendor), _jsx("span", { className: "text-xs text-gray-500 capitalize", children: device.vendor })] }) }), _jsx("td", { className: "text-sm text-gray-600", children: device.platform || '-' }), _jsx("td", { className: "font-mono text-sm", children: device.management_address }), _jsx("td", { children: getStatusBadge(device.status) }), _jsx("td", { children: _jsx("button", { onClick: (e) => { e.stopPropagation(); onDeviceClick(device.id); }, className: "btn btn-sm btn-secondary", children: "Details" }) })] }, device.id))) })] }) })] }));
}
