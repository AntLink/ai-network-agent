import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { api } from '../api/client';
const emptyResource = (label) => ({ label, data: null });
function vendorText(device, deviceId) {
    return `${device?.vendor || ''} ${device?.platform || ''} ${device?.hostname || ''} ${deviceId}`.toLowerCase();
}
function vendorKind(device, deviceId) {
    const text = vendorText(device, deviceId);
    if (text.includes('cisco') || text.includes('iosv') || text.includes('ios-xe'))
        return 'cisco';
    if (text.includes('mikrotik') || text.includes('routeros') || text.includes('chr'))
        return 'mikrotik';
    return 'generic';
}
function deviceProfile(device, deviceId) {
    const text = vendorText(device, deviceId);
    const kind = vendorKind(device, deviceId);
    if (kind === 'mikrotik')
        return 'mikrotik-router';
    if (kind === 'cisco' && (text.includes('switch') || text.includes('ios-l2') || text.includes('iosvl2') || text.includes('sw'))) {
        return 'cisco-switch';
    }
    if (kind === 'cisco')
        return 'cisco-router';
    return 'generic';
}
function profileLabel(profile) {
    switch (profile) {
        case 'cisco-router':
            return 'Cisco Router';
        case 'cisco-switch':
            return 'Cisco Switch';
        case 'mikrotik-router':
            return 'MikroTik Router';
        default:
            return 'Generic SSH Device';
    }
}
function profileTone(profile) {
    switch (profile) {
        case 'cisco-router':
            return 'device-hero device-hero-cisco-router';
        case 'cisco-switch':
            return 'device-hero device-hero-cisco-switch';
        case 'mikrotik-router':
            return 'device-hero device-hero-mikrotik-router';
        default:
            return 'device-hero device-hero-generic';
    }
}
function profileAccent(profile) {
    switch (profile) {
        case 'cisco-router':
            return 'Cisco routing';
        case 'cisco-switch':
            return 'Cisco switching';
        case 'mikrotik-router':
            return 'MikroTik RouterOS';
        default:
            return 'Generic SSH';
    }
}
function dataText(data) {
    if (!data)
        return 'No data available';
    if (typeof data === 'string')
        return data;
    if (typeof data.raw === 'string')
        return data.raw;
    if (Array.isArray(data.data))
        return JSON.stringify(data.data, null, 2);
    if (typeof data.output === 'string')
        return data.output;
    return JSON.stringify(data, null, 2);
}
function countLines(data) {
    const text = dataText(data);
    if (!text || text === 'No data available')
        return 0;
    return text.split('\n').filter((line) => line.trim()).length;
}
function displayValue(value) {
    if (value === null || value === undefined || value === '')
        return '-';
    if (typeof value === 'boolean')
        return value ? 'true' : 'false';
    if (Array.isArray(value))
        return `${value.length} item`;
    if (typeof value === 'object')
        return Object.entries(value)
            .map(([key, item]) => `${key}: ${displayValue(item)}`)
            .join(', ');
    return String(value);
}
function healthStatus(health, fallbackHealth = null) {
    const source = health || fallbackHealth || {};
    if (source.status)
        return source.status;
    if (source.reachable === false)
        return 'Unreachable';
    if (source.flash_ok === false || source.resource_error)
        return 'Degraded';
    if (source.reachable === true || source.ssh_banner || source.resource)
        return 'Online';
    if (source.ok === true)
        return 'Online';
    if (source.ok === false)
        return 'Unreachable';
    return 'Unknown';
}
function rowsFromRaw(text) {
    return text
        .split('\n')
        .map((line, index) => ({ line: index + 1, content: line }))
        .filter((row) => row.content.trim());
}
function normalizeTableData(data) {
    if (!data)
        return null;
    const candidate = Array.isArray(data)
        ? data
        : Array.isArray(data.data)
            ? data.data
            : Array.isArray(data.items)
                ? data.items
                : null;
    if (candidate && candidate.length > 0) {
        if (candidate.every((item) => item && typeof item === 'object' && !Array.isArray(item))) {
            const columns = Array.from(new Set(candidate.flatMap((item) => Object.keys(item)))).slice(0, 8);
            return { columns, rows: candidate };
        }
        return {
            columns: ['value'],
            rows: candidate.map((value) => ({ value })),
        };
    }
    if (data && typeof data === 'object') {
        const entries = Object.entries(data)
            .filter(([key]) => !['raw', 'data', 'output'].includes(key))
            .map(([key, value]) => ({ key, value }));
        if (entries.length > 0) {
            return { columns: ['key', 'value'], rows: entries };
        }
    }
    const raw = typeof data?.raw === 'string'
        ? data.raw
        : typeof data?.output === 'string'
            ? data.output
            : typeof data === 'string'
                ? data
                : '';
    if (raw.trim()) {
        return { columns: ['line', 'content'], rows: rowsFromRaw(raw) };
    }
    return null;
}
function DataTable({ data }) {
    const table = normalizeTableData(data);
    if (!table) {
        return _jsx("div", { className: "empty-table", children: "No table data available" });
    }
    return (_jsx("div", { className: "table-shell", children: _jsxs("table", { className: "table data-table", children: [_jsx("thead", { children: _jsx("tr", { children: table.columns.map((column) => (_jsx("th", { children: column.replace(/_/g, ' ') }, column))) }) }), _jsx("tbody", { children: table.rows.map((row, index) => (_jsx("tr", { children: table.columns.map((column) => (_jsx("td", { className: column === 'content' ? 'font-mono text-sm' : undefined, children: displayValue(row[column]) }, column))) }, index))) })] }) }));
}
function ResourceCard({ resource }) {
    return (_jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx("h4", { children: resource.label }), _jsx("span", { className: `badge ${resource.error ? 'badge-error' : 'badge-info'}`, children: resource.error ? 'Error' : `${countLines(resource.data)} rows` })] }), resource.error ? (_jsx("div", { className: "resource-error", children: resource.error })) : (_jsx(DataTable, { data: resource.data }))] }));
}
function CommandList({ commands }) {
    if (!commands?.length)
        return _jsx("div", { className: "empty-table", children: "No commands" });
    return (_jsx("div", { className: "table-shell", children: _jsx("table", { className: "table data-table", children: _jsx("tbody", { children: commands.map((command, index) => (_jsxs("tr", { children: [_jsx("th", { children: index + 1 }), _jsx("td", { className: "font-mono text-sm", children: command })] }, `${command}-${index}`))) }) }) }));
}
function ConfigView({ data, profile }) {
    if (!data) {
        return _jsx(ResourceCard, { resource: { label: 'Running Configuration', data: null } });
    }
    const parsed = data?.data ?? data;
    const summaryRows = profile === 'mikrotik-router'
        ? [
            ['Hostname', parsed.hostname],
            ['Interfaces', parsed.interfaces?.length],
            ['IP addresses', parsed.ip_addresses?.length],
            ['Bridges', parsed.bridges?.length],
            ['Bridge ports', parsed.bridge_ports?.length],
            ['Static routes', parsed.static_routes?.length],
            ['Firewall rules', parsed.firewall?.length],
            ['DHCP leases', parsed.dhcp_leases?.length],
        ]
        : [
            ['Hostname', parsed.hostname],
            ['Version', parsed.version],
            ['Interfaces', parsed.interfaces?.length],
            ['VLANs', parsed.vlans?.length],
            ['Routing protocols', parsed.routing?.protocols?.length],
            ['Static routes', parsed.routing?.static_routes?.length],
            ['Users', parsed.users?.length],
            ['Line sections', parsed.line_sections?.length],
        ];
    return (_jsxs("div", { className: "resource-grid", children: [_jsx(OverviewTable, { title: profile === 'mikrotik-router' ? 'RouterOS Export Summary' : 'Config Summary', rows: summaryRows }), parsed.interfaces?.length > 0 && (_jsx(ResourceCard, { resource: { label: 'Interfaces', data: parsed.interfaces } })), parsed.vlans?.length > 0 && (_jsx(ResourceCard, { resource: { label: 'VLANs', data: parsed.vlans } })), parsed.routing?.static_routes?.length > 0 && (_jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx("h4", { children: "Static Routes" }), _jsxs("span", { className: "badge badge-info", children: [parsed.routing.static_routes.length, " routes"] })] }), _jsx(CommandList, { commands: parsed.routing.static_routes })] })), parsed.routing?.protocols?.length > 0 && (_jsx(ResourceCard, { resource: { label: 'Routing Protocols', data: parsed.routing.protocols } })), parsed.users?.length > 0 && (_jsx(ResourceCard, { resource: { label: 'Users', data: parsed.users } })), parsed.line_sections?.length > 0 && (_jsx(ResourceCard, { resource: { label: 'Line Sections', data: parsed.line_sections } })), parsed.services?.length > 0 && (_jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx("h4", { children: "Services" }), _jsxs("span", { className: "badge badge-info", children: [parsed.services.length, " commands"] })] }), _jsx(CommandList, { commands: parsed.services })] })), parsed.global?.length > 0 && (_jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx("h4", { children: "Global Commands" }), _jsxs("span", { className: "badge badge-info", children: [parsed.global.length, " commands"] })] }), _jsx(CommandList, { commands: parsed.global })] }))] }));
}
function CiscoCpuMemoryView({ resource }) {
    if (resource.error) {
        return _jsx(ResourceCard, { resource: resource });
    }
    const data = resource.data?.data ?? resource.data;
    if (!data) {
        return _jsx(ResourceCard, { resource: resource });
    }
    const cpuRows = [
        ['Five seconds', data.cpu?.five_seconds !== null && data.cpu?.five_seconds !== undefined ? `${data.cpu.five_seconds}%` : '-'],
        ['Interrupt', data.cpu?.interrupt !== null && data.cpu?.interrupt !== undefined ? `${data.cpu.interrupt}%` : '-'],
        ['One minute', data.cpu?.one_minute !== null && data.cpu?.one_minute !== undefined ? `${data.cpu.one_minute}%` : '-'],
        ['Five minutes', data.cpu?.five_minutes !== null && data.cpu?.five_minutes !== undefined ? `${data.cpu.five_minutes}%` : '-'],
        ['Summary', data.cpu?.summary || '-'],
    ];
    const memorySummaryRows = [
        ['Total', data.memory?.summary?.total_bytes ? `${data.memory.summary.total_bytes} bytes` : '-'],
        ['Used', data.memory?.summary?.used_bytes ? `${data.memory.summary.used_bytes} bytes` : '-'],
        ['Free', data.memory?.summary?.free_bytes ? `${data.memory.summary.free_bytes} bytes` : '-'],
        ['Used %', data.memory?.summary?.used_percent !== null && data.memory?.summary?.used_percent !== undefined ? `${data.memory.summary.used_percent}%` : '-'],
        ['Free %', data.memory?.summary?.free_percent !== null && data.memory?.summary?.free_percent !== undefined ? `${data.memory.summary.free_percent}%` : '-'],
    ];
    return (_jsxs("div", { className: "resource-grid", children: [_jsx(OverviewTable, { title: "CPU Utilization", rows: cpuRows }), _jsx(OverviewTable, { title: "Memory Summary", rows: memorySummaryRows }), _jsx(ResourceCard, { resource: { label: 'Memory Pools', data: data.memory?.pools || [] } }), _jsx(ResourceCard, { resource: { label: 'CPU Processes', data: data.processes || [] } }), data.warnings?.length > 0 && (_jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx("h4", { children: "Warnings" }), _jsx("span", { className: "badge badge-warning", children: data.warnings.length })] }), _jsx(CommandList, { commands: data.warnings })] }))] }));
}
function OverviewTable({ title, rows }) {
    return (_jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx("h4", { children: title }), _jsxs("span", { className: "badge badge-info", children: [rows.length, " items"] })] }), _jsx("div", { className: "table-shell", children: _jsx("table", { className: "table data-table", children: _jsx("tbody", { children: rows.map(([label, value]) => (_jsxs("tr", { children: [_jsx("th", { children: label }), _jsx("td", { children: displayValue(value) })] }, label))) }) }) })] }));
}
function SkeletonLine({ className = '' }) {
    return _jsx("div", { className: `skeleton-line ${className}`.trim() });
}
function DetailSkeleton() {
    return (_jsxs("div", { className: "detail-skeleton", children: [_jsxs("div", { className: "skeleton-hero", children: [_jsx(SkeletonLine, { className: "skeleton-chip" }), _jsxs("div", { className: "skeleton-hero-body", children: [_jsx(SkeletonLine, { className: "skeleton-title" }), _jsx(SkeletonLine, { className: "skeleton-subtitle" }), _jsxs("div", { className: "skeleton-chip-row", children: [_jsx(SkeletonLine, { className: "skeleton-chip" }), _jsx(SkeletonLine, { className: "skeleton-chip" }), _jsx(SkeletonLine, { className: "skeleton-chip" })] })] }), _jsx(SkeletonLine, { className: "skeleton-button" })] }), _jsxs("div", { className: "detail-highlights", children: [_jsxs("div", { className: "stat-tile skeleton-tile", children: [_jsx(SkeletonLine, { className: "skeleton-line-short" }), _jsx(SkeletonLine, { className: "skeleton-line-med" })] }), _jsxs("div", { className: "stat-tile skeleton-tile", children: [_jsx(SkeletonLine, { className: "skeleton-line-short" }), _jsx(SkeletonLine, { className: "skeleton-line-med" })] }), _jsxs("div", { className: "stat-tile skeleton-tile", children: [_jsx(SkeletonLine, { className: "skeleton-line-short" }), _jsx(SkeletonLine, { className: "skeleton-line-med" })] })] }), _jsxs("div", { className: "tabs skeleton-tabs", children: [_jsx(SkeletonLine, { className: "skeleton-tab" }), _jsx(SkeletonLine, { className: "skeleton-tab" }), _jsx(SkeletonLine, { className: "skeleton-tab" }), _jsx(SkeletonLine, { className: "skeleton-tab" })] }), _jsxs("div", { className: "overview-grid", children: [_jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx(SkeletonLine, { className: "skeleton-card-title" }), _jsx(SkeletonLine, { className: "skeleton-badge" })] }), _jsxs("div", { className: "skeleton-table", children: [_jsx(SkeletonLine, {}), _jsx(SkeletonLine, {}), _jsx(SkeletonLine, {}), _jsx(SkeletonLine, {})] })] }), _jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx(SkeletonLine, { className: "skeleton-card-title" }), _jsx(SkeletonLine, { className: "skeleton-badge" })] }), _jsxs("div", { className: "skeleton-table", children: [_jsx(SkeletonLine, {}), _jsx(SkeletonLine, {}), _jsx(SkeletonLine, {}), _jsx(SkeletonLine, {})] })] }), _jsxs("div", { className: "resource-card", children: [_jsxs("div", { className: "resource-card-header", children: [_jsx(SkeletonLine, { className: "skeleton-card-title" }), _jsx(SkeletonLine, { className: "skeleton-badge" })] }), _jsxs("div", { className: "skeleton-table", children: [_jsx(SkeletonLine, {}), _jsx(SkeletonLine, {}), _jsx(SkeletonLine, {}), _jsx(SkeletonLine, {})] })] })] })] }));
}
async function safeLoad(label, loader) {
    try {
        return { label, data: await loader() };
    }
    catch (err) {
        return {
            label,
            data: null,
            error: err instanceof Error ? err.message : 'Failed to load resource',
        };
    }
}
async function loadSequential(loaders) {
    const loaded = [];
    for (const loader of loaders) {
        loaded.push(await loader());
    }
    return Object.fromEntries(loaded.map((item) => [item.label, item]));
}
export function DeviceDetail({ deviceId, onBack, onLoadStateChange, onNotify }) {
    const [device, setDevice] = useState(null);
    const [facts, setFacts] = useState(null);
    const [interfaces, setInterfaces] = useState(null);
    const [config, setConfig] = useState(null);
    const [health, setHealth] = useState(null);
    const [resources, setResources] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');
    useEffect(() => {
        loadDevice();
    }, [deviceId]);
    async function loadDevice() {
        onLoadStateChange?.(true, `Memuat detail ${deviceId}...`);
        try {
            setLoading(true);
            setError(null);
            const deviceData = await api.devices.getDevice(deviceId).catch(() => null);
            const profile = deviceProfile(deviceData, deviceId);
            const baseLoaders = [
                () => safeLoad('Health', () => api.devices.health(deviceId)),
                () => safeLoad('Facts', () => api.devices.facts(deviceId)),
            ];
            const baseResources = await loadSequential(baseLoaders);
            setDevice(deviceData);
            setFacts(baseResources.Facts?.data || null);
            setHealth(baseResources.Health?.data || null);
            setInterfaces(null);
            setConfig(null);
            const vendorResources = await loadVendorResources(profile);
            setResources({ ...baseResources, ...vendorResources });
            const primaryInterfaces = vendorResources['Cisco Interfaces Detail']?.data ||
                vendorResources['MikroTik Interfaces']?.data ||
                vendorResources.Interfaces?.data ||
                null;
            setInterfaces(primaryInterfaces);
            setConfig(vendorResources['Running Configuration']?.data || null);
            onNotify?.(`Detail ${deviceData?.hostname || deviceId} berhasil dimuat`, 'success');
        }
        catch (err) {
            const message = err instanceof Error ? err.message : 'Failed to load device';
            setError(message);
            onNotify?.(`Gagal memuat ${deviceId}: ${message}`, 'error');
        }
        finally {
            setLoading(false);
            onLoadStateChange?.(false);
        }
    }
    async function loadVendorResources(profile) {
        const loadersByProfile = {
            'cisco-router': [
                () => safeLoad('Cisco Version', () => api.ciscoGetVersion(deviceId)),
                () => safeLoad('Cisco Interfaces Detail', () => api.ciscoGetInterfacesDetail(deviceId)),
                () => safeLoad('Cisco Routing Table', () => api.ciscoGetRoutes(deviceId)),
                () => safeLoad('Cisco ARP Table', () => api.ciscoGetArp(deviceId)),
                () => safeLoad('Cisco CDP Neighbors', () => api.ciscoGetCdpNeighbors(deviceId)),
                () => safeLoad('Cisco ACLs', () => api.ciscoGetAcls(deviceId)),
                () => safeLoad('Cisco NAT Translations', () => api.ciscoGetNatTranslations(deviceId)),
                () => safeLoad('Cisco CPU / Memory', () => api.ciscoGetCpuMemory(deviceId)),
                () => safeLoad('Running Configuration', () => api.devices.config(deviceId)),
            ],
            'cisco-switch': [
                () => safeLoad('Cisco Version', () => api.ciscoGetVersion(deviceId)),
                () => safeLoad('Cisco Interfaces Detail', () => api.ciscoGetInterfacesDetail(deviceId)),
                () => safeLoad('Cisco VLANs', () => api.devices.vlans(deviceId)),
                () => safeLoad('Cisco ARP Table', () => api.ciscoGetArp(deviceId)),
                () => safeLoad('Cisco CDP Neighbors', () => api.ciscoGetCdpNeighbors(deviceId)),
                () => safeLoad('Cisco CPU / Memory', () => api.ciscoGetCpuMemory(deviceId)),
                () => safeLoad('Running Configuration', () => api.devices.config(deviceId)),
            ],
            'mikrotik-router': [
                () => safeLoad('MikroTik Health', () => api.mikrotikHealth(deviceId)),
                () => safeLoad('MikroTik Interfaces', () => api.mikrotikInterfaceList(deviceId)),
                () => safeLoad('MikroTik IP Addresses', () => api.mikrotikResourceIpAddresses(deviceId)),
                () => safeLoad('MikroTik Static Routes', () => api.mikrotikResourceStaticRoutes(deviceId)),
                () => safeLoad('MikroTik Bridges', () => api.mikrotikResourceBridges(deviceId)),
                () => safeLoad('MikroTik Bridge Ports', () => api.mikrotikResourceBridgePorts(deviceId)),
                () => safeLoad('MikroTik DHCP Servers', () => api.mikrotikResourceDhcpServers(deviceId)),
                () => safeLoad('MikroTik DHCP Leases', () => api.mikrotikResourceDhcpLeases(deviceId)),
                () => safeLoad('MikroTik Firewall NAT', () => api.mikrotikResourceFirewallNat(deviceId)),
                () => safeLoad('MikroTik Firewall Filter', () => api.mikrotikResourceFirewallFilter(deviceId)),
                () => safeLoad('MikroTik OSPF', () => api.mikrotikResourceOspf(deviceId)),
                () => safeLoad('MikroTik BGP', () => api.mikrotikResourceBgp(deviceId)),
                () => safeLoad('Running Configuration', () => api.devices.config(deviceId)),
            ],
            generic: [
                () => safeLoad('Interfaces', () => api.devices.interfaces(deviceId)),
                () => safeLoad('Routes', () => api.devices.routes(deviceId)),
                () => safeLoad('Running Configuration', () => api.devices.config(deviceId)),
            ],
        };
        return loadSequential(loadersByProfile[profile]);
    }
    if (loading) {
        return (_jsx(DetailSkeleton, {}));
    }
    if (error) {
        return (_jsxs("div", { className: "card", children: [_jsxs("div", { className: "text-red-600", children: ["Error: ", error] }), _jsx("button", { onClick: onBack, className: "btn btn-secondary mt-4", children: "Back" })] }));
    }
    const kind = vendorKind(device, deviceId);
    const isCisco = kind === 'cisco';
    const isMikroTik = kind === 'mikrotik';
    const profile = deviceProfile(device, deviceId);
    const isCiscoRouter = profile === 'cisco-router';
    const isCiscoSwitch = profile === 'cisco-switch';
    const tabsByProfile = {
        'cisco-router': [
            { id: 'overview', label: 'Router Overview' },
            { id: 'interfaces', label: 'Interfaces' },
            { id: 'ip', label: 'IP / ARP' },
            { id: 'routing', label: 'Routing' },
            { id: 'services', label: 'ACL / NAT' },
            { id: 'config', label: 'Config' },
            { id: 'facts', label: 'Facts' },
        ],
        'cisco-switch': [
            { id: 'overview', label: 'Switch Overview' },
            { id: 'interfaces', label: 'Ports' },
            { id: 'vlans', label: 'VLAN / L2' },
            { id: 'ip', label: 'Mgmt / Neighbors' },
            { id: 'services', label: 'System' },
            { id: 'config', label: 'Config' },
            { id: 'facts', label: 'Facts' },
        ],
        'mikrotik-router': [
            { id: 'overview', label: 'RouterOS Overview' },
            { id: 'interfaces', label: 'Interfaces' },
            { id: 'ip', label: 'IP / DHCP' },
            { id: 'vlans', label: 'Bridge / VLAN' },
            { id: 'routing', label: 'Routing' },
            { id: 'services', label: 'Firewall' },
            { id: 'config', label: 'Export' },
            { id: 'facts', label: 'Facts' },
        ],
        generic: [
            { id: 'overview', label: 'Overview' },
            { id: 'interfaces', label: 'Interfaces' },
            { id: 'routing', label: 'Routing' },
            { id: 'config', label: 'Config' },
            { id: 'facts', label: 'Facts' },
        ],
    };
    const tabs = tabsByProfile[profile];
    const activeTabAllowed = tabs.some((tab) => tab.id === activeTab);
    const currentTab = activeTabAllowed ? activeTab : 'overview';
    const resource = (label) => resources[label] || emptyResource(label);
    const mikrotikHealth = resource('MikroTik Health').data;
    const healthRows = [
        ['Profile', profileLabel(profile)],
        ['Health status', healthStatus(health, mikrotikHealth)],
        ['Reachable', health?.reachable ?? mikrotikHealth?.reachable ?? health?.ok ?? mikrotikHealth?.ok ?? '-'],
        ['SSH banner', health?.ssh_banner || mikrotikHealth?.ssh_banner || '-'],
        ['Flash OK', health?.flash_ok ?? '-'],
        ['Reason', health?.reason || mikrotikHealth?.reason || health?.message || health?.detail || '-'],
    ];
    const vendorRows = isCiscoRouter
        ? [
            ['Version lines', countLines(resource('Cisco Version').data)],
            ['Interface detail lines', countLines(resource('Cisco Interfaces Detail').data)],
            ['Route lines', countLines(resource('Cisco Routing Table').data)],
            ['ARP entries/lines', countLines(resource('Cisco ARP Table').data)],
            ['CDP neighbor lines', countLines(resource('Cisco CDP Neighbors').data)],
            ['ACL lines', countLines(resource('Cisco ACLs').data)],
            ['NAT lines', countLines(resource('Cisco NAT Translations').data)],
        ]
        : isCiscoSwitch
            ? [
                ['Version lines', countLines(resource('Cisco Version').data)],
                ['Port detail lines', countLines(resource('Cisco Interfaces Detail').data)],
                ['VLAN lines', countLines(resource('Cisco VLANs').data)],
                ['ARP entries/lines', countLines(resource('Cisco ARP Table').data)],
                ['CDP neighbor lines', countLines(resource('Cisco CDP Neighbors').data)],
                ['CPU / Memory lines', countLines(resource('Cisco CPU / Memory').data)],
            ]
            : isMikroTik
                ? [
                    ['IP address rows', countLines(resource('MikroTik IP Addresses').data)],
                    ['Interface rows', countLines(resource('MikroTik Interfaces').data)],
                    ['Static route rows', countLines(resource('MikroTik Static Routes').data)],
                    ['Bridge rows', countLines(resource('MikroTik Bridges').data)],
                    ['Bridge port rows', countLines(resource('MikroTik Bridge Ports').data)],
                    ['DHCP lease rows', countLines(resource('MikroTik DHCP Leases').data)],
                    ['Firewall NAT rows', countLines(resource('MikroTik Firewall NAT').data)],
                    ['Firewall filter rows', countLines(resource('MikroTik Firewall Filter').data)],
                ]
                : [
                    ['Interface lines', countLines(interfaces)],
                    ['Route lines', countLines(resource('Routes').data)],
                    ['VLAN lines', countLines(resource('VLANs').data)],
                ];
    const heroClass = profileTone(profile);
    const deviceSummaryTiles = [
        { label: 'Vendor profile', value: profileLabel(profile) },
        { label: 'Access mode', value: profileAccent(profile) },
        { label: 'Health', value: healthStatus(health, mikrotikHealth) },
    ];
    return (_jsxs("div", { children: [_jsxs("div", { className: heroClass, children: [_jsx("button", { onClick: onBack, className: "btn btn-secondary btn-sm", children: "Back" }), _jsxs("div", { className: "device-hero-body", children: [_jsx("p", { className: "eyebrow", children: "Device detail" }), _jsxs("div", { className: "device-title-row", children: [_jsx("h1", { children: device?.hostname || deviceId }), _jsx("span", { className: `badge ${isCisco ? 'badge-info' : isMikroTik ? 'badge-warning' : 'badge-success'}`, children: profileLabel(profile) })] }), _jsxs("p", { children: [device?.platform || 'Unknown platform', " / ", device?.management_address || 'No management IP', " / ", profileAccent(profile)] }), _jsxs("div", { className: "device-chip-row", children: [_jsxs("span", { className: "device-chip", children: ["ID: ", deviceId] }), _jsxs("span", { className: "device-chip", children: ["Console: ", device?.console_host && device?.console_port ? `${device.console_host}:${device.console_port}` : '-'] }), _jsxs("span", { className: "device-chip", children: ["Status: ", device?.status || 'Unknown'] })] })] }), _jsx("button", { onClick: loadDevice, className: "btn btn-primary btn-sm", children: "Refresh" })] }), _jsx("div", { className: "detail-highlights", children: deviceSummaryTiles.map((tile) => (_jsxs("div", { className: "stat-tile", children: [_jsx("span", { children: tile.label }), _jsx("strong", { children: tile.value })] }, tile.label))) }), _jsx("div", { className: "tabs", children: tabs.map((tab) => (_jsx("button", { onClick: () => setActiveTab(tab.id), className: `tab ${currentTab === tab.id ? 'active' : ''}`, children: tab.label }, tab.id))) }), currentTab === 'overview' && (_jsxs("div", { className: "overview-grid", children: [_jsx(OverviewTable, { title: profile === 'cisco-switch' ? 'Switch Identity' : profile === 'cisco-router' ? 'Router Identity' : profile === 'mikrotik-router' ? 'RouterOS Identity' : 'Device Identity', rows: [
                            ['Device ID', deviceId],
                            ['Hostname', device?.hostname || '-'],
                            ['Vendor', device?.vendor || 'Unknown'],
                            ['UI Profile', profileLabel(profile)],
                            ['Platform', device?.platform || 'Unknown'],
                            ['Management IP', device?.management_address || '-'],
                            ['Console', device?.console_host && device?.console_port ? `${device.console_host}:${device.console_port}` : '-'],
                            ['Status', device?.status || 'Unknown'],
                        ] }), _jsx(OverviewTable, { title: "Health", rows: healthRows }), _jsx(OverviewTable, { title: `${profileLabel(profile)} Snapshot`, rows: vendorRows })] })), currentTab === 'interfaces' && (_jsx("div", { className: "resource-grid", children: _jsx(ResourceCard, { resource: isCisco ? resource('Cisco Interfaces Detail') : isMikroTik ? resource('MikroTik Interfaces') : resource('Interfaces') }) })), currentTab === 'ip' && (_jsx("div", { className: "resource-grid", children: isMikroTik ? (_jsxs(_Fragment, { children: [_jsx(ResourceCard, { resource: resource('MikroTik IP Addresses') }), _jsx(ResourceCard, { resource: resource('MikroTik DHCP Servers') }), _jsx(ResourceCard, { resource: resource('MikroTik DHCP Leases') })] })) : isCiscoRouter ? (_jsxs(_Fragment, { children: [_jsx(ResourceCard, { resource: resource('Cisco ARP Table') }), _jsx(ResourceCard, { resource: resource('Cisco CDP Neighbors') })] })) : (_jsxs(_Fragment, { children: [_jsx(ResourceCard, { resource: resource('Cisco ARP Table') }), _jsx(ResourceCard, { resource: resource('Cisco CDP Neighbors') })] })) })), currentTab === 'vlans' && (_jsxs("div", { className: "resource-grid", children: [isCiscoSwitch && _jsx(ResourceCard, { resource: resource('Cisco VLANs') }), isMikroTik && _jsx(ResourceCard, { resource: resource('MikroTik Bridges') }), isMikroTik && _jsx(ResourceCard, { resource: resource('MikroTik Bridge Ports') })] })), currentTab === 'routing' && (_jsxs("div", { className: "resource-grid", children: [_jsx(ResourceCard, { resource: isCiscoRouter ? resource('Cisco Routing Table') : isMikroTik ? resource('MikroTik Static Routes') : resource('Routes') }), isMikroTik && _jsx(ResourceCard, { resource: resource('MikroTik OSPF') }), isMikroTik && _jsx(ResourceCard, { resource: resource('MikroTik BGP') })] })), currentTab === 'services' && (_jsx("div", { className: "resource-grid", children: isCiscoRouter ? (_jsxs(_Fragment, { children: [_jsx(CiscoCpuMemoryView, { resource: resource('Cisco CPU / Memory') }), _jsx(ResourceCard, { resource: resource('Cisco ACLs') }), _jsx(ResourceCard, { resource: resource('Cisco NAT Translations') })] })) : isCiscoSwitch ? (_jsxs(_Fragment, { children: [_jsx(CiscoCpuMemoryView, { resource: resource('Cisco CPU / Memory') }), _jsx(ResourceCard, { resource: resource('Cisco CDP Neighbors') })] })) : isMikroTik ? (_jsxs(_Fragment, { children: [_jsx(ResourceCard, { resource: resource('MikroTik Health') }), _jsx(ResourceCard, { resource: resource('MikroTik Firewall NAT') }), _jsx(ResourceCard, { resource: resource('MikroTik Firewall Filter') })] })) : (_jsx(ResourceCard, { resource: { label: 'Generic Health', data: health } })) })), currentTab === 'config' && (_jsx(ConfigView, { data: config, profile: profile })), currentTab === 'facts' && (_jsxs("div", { className: "resource-grid", children: [_jsx(ResourceCard, { resource: { label: 'Facts', data: facts } }), isCisco && _jsx(ResourceCard, { resource: resource('Cisco Version') })] }))] }));
}
