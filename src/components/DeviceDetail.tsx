import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface Props {
  deviceId: string;
  onBack: () => void;
  onLoadStateChange?: (loading: boolean, message?: string) => void;
  onNotify?: (message: string, kind?: 'info' | 'success' | 'error') => void;
}

type TabId = 'overview' | 'interfaces' | 'ip' | 'vlans' | 'routing' | 'services' | 'config' | 'facts';
type DeviceProfile = 'cisco-router' | 'cisco-switch' | 'mikrotik-router' | 'generic';

type ResourceState = {
  label: string;
  data: any;
  error?: string;
};

const emptyResource = (label: string): ResourceState => ({ label, data: null });

function vendorText(device: any, deviceId: string) {
  return `${device?.vendor || ''} ${device?.platform || ''} ${device?.hostname || ''} ${deviceId}`.toLowerCase();
}

function vendorKind(device: any, deviceId: string): 'cisco' | 'mikrotik' | 'generic' {
  const text = vendorText(device, deviceId);
  if (text.includes('cisco') || text.includes('iosv') || text.includes('ios-xe')) return 'cisco';
  if (text.includes('mikrotik') || text.includes('routeros') || text.includes('chr')) return 'mikrotik';
  return 'generic';
}

function deviceProfile(device: any, deviceId: string): DeviceProfile {
  const text = vendorText(device, deviceId);
  const kind = vendorKind(device, deviceId);
  if (kind === 'mikrotik') return 'mikrotik-router';
  if (kind === 'cisco' && (text.includes('switch') || text.includes('ios-l2') || text.includes('iosvl2') || text.includes('sw'))) {
    return 'cisco-switch';
  }
  if (kind === 'cisco') return 'cisco-router';
  return 'generic';
}

function profileLabel(profile: DeviceProfile) {
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

function profileTone(profile: DeviceProfile) {
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

function profileAccent(profile: DeviceProfile) {
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

function dataText(data: any) {
  if (!data) return 'No data available';
  if (typeof data === 'string') return data;
  if (typeof data.raw === 'string') return data.raw;
  if (Array.isArray(data.data)) return JSON.stringify(data.data, null, 2);
  if (typeof data.output === 'string') return data.output;
  return JSON.stringify(data, null, 2);
}

function countLines(data: any) {
  const text = dataText(data);
  if (!text || text === 'No data available') return 0;
  return text.split('\n').filter((line: string) => line.trim()).length;
}

function displayValue(value: any): string {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (Array.isArray(value)) return `${value.length} item`;
  if (typeof value === 'object') return Object.entries(value)
    .map(([key, item]) => `${key}: ${displayValue(item)}`)
    .join(', ');
  return String(value);
}

function healthStatus(health: any, fallbackHealth: any = null) {
  const source = health || fallbackHealth || {};
  if (source.status) return source.status;
  if (source.reachable === false) return 'Unreachable';
  if (source.flash_ok === false || source.resource_error) return 'Degraded';
  if (source.reachable === true || source.ssh_banner || source.resource) return 'Online';
  if (source.ok === true) return 'Online';
  if (source.ok === false) return 'Unreachable';
  return 'Unknown';
}

function rowsFromRaw(text: string) {
  return text
    .split('\n')
    .map((line, index) => ({ line: index + 1, content: line }))
    .filter((row) => row.content.trim());
}

function normalizeTableData(data: any): { columns: string[]; rows: Record<string, any>[] } | null {
  if (!data) return null;

  const candidate = Array.isArray(data)
    ? data
    : Array.isArray(data.data)
      ? data.data
      : Array.isArray(data.items)
        ? data.items
        : null;

  if (candidate && candidate.length > 0) {
    if (candidate.every((item: any) => item && typeof item === 'object' && !Array.isArray(item))) {
      const columns = Array.from(
        new Set(candidate.flatMap((item: Record<string, any>) => Object.keys(item))),
      ).slice(0, 8) as string[];
      return { columns, rows: candidate };
    }
    return {
      columns: ['value'],
      rows: candidate.map((value: any) => ({ value })),
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

function DataTable({ data }: { data: any }) {
  const table = normalizeTableData(data);

  if (!table) {
    return <div className="empty-table">No table data available</div>;
  }

  return (
    <div className="table-shell">
      <table className="table data-table">
        <thead>
          <tr>
            {table.columns.map((column) => (
              <th key={column}>{column.replace(/_/g, ' ')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, index) => (
            <tr key={index}>
              {table.columns.map((column) => (
                <td key={column} className={column === 'content' ? 'font-mono text-sm' : undefined}>
                  {displayValue(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ResourceCard({ resource }: { resource: ResourceState }) {
  return (
    <div className="resource-card">
      <div className="resource-card-header">
        <h4>{resource.label}</h4>
        <span className={`badge ${resource.error ? 'badge-error' : 'badge-info'}`}>
          {resource.error ? 'Error' : `${countLines(resource.data)} rows`}
        </span>
      </div>
      {resource.error ? (
        <div className="resource-error">{resource.error}</div>
      ) : (
        <DataTable data={resource.data} />
      )}
    </div>
  );
}

function CommandList({ commands }: { commands: string[] }) {
  if (!commands?.length) return <div className="empty-table">No commands</div>;
  return (
    <div className="table-shell">
      <table className="table data-table">
        <tbody>
          {commands.map((command, index) => (
            <tr key={`${command}-${index}`}>
              <th>{index + 1}</th>
              <td className="font-mono text-sm">{command}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ConfigView({ data, profile }: { data: any; profile: DeviceProfile }) {
  if (!data) {
    return <ResourceCard resource={{ label: 'Running Configuration', data: null }} />;
  }

  const parsed = data?.data ?? data;
  const summaryRows: Array<[string, any]> = profile === 'mikrotik-router'
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

  return (
    <div className="resource-grid">
      <OverviewTable title={profile === 'mikrotik-router' ? 'RouterOS Export Summary' : 'Config Summary'} rows={summaryRows} />
      {parsed.interfaces?.length > 0 && (
        <ResourceCard resource={{ label: 'Interfaces', data: parsed.interfaces }} />
      )}
      {parsed.vlans?.length > 0 && (
        <ResourceCard resource={{ label: 'VLANs', data: parsed.vlans }} />
      )}
      {parsed.routing?.static_routes?.length > 0 && (
        <div className="resource-card">
          <div className="resource-card-header">
            <h4>Static Routes</h4>
            <span className="badge badge-info">{parsed.routing.static_routes.length} routes</span>
          </div>
          <CommandList commands={parsed.routing.static_routes} />
        </div>
      )}
      {parsed.routing?.protocols?.length > 0 && (
        <ResourceCard resource={{ label: 'Routing Protocols', data: parsed.routing.protocols }} />
      )}
      {parsed.users?.length > 0 && (
        <ResourceCard resource={{ label: 'Users', data: parsed.users }} />
      )}
      {parsed.line_sections?.length > 0 && (
        <ResourceCard resource={{ label: 'Line Sections', data: parsed.line_sections }} />
      )}
      {parsed.services?.length > 0 && (
        <div className="resource-card">
          <div className="resource-card-header">
            <h4>Services</h4>
            <span className="badge badge-info">{parsed.services.length} commands</span>
          </div>
          <CommandList commands={parsed.services} />
        </div>
      )}
      {parsed.global?.length > 0 && (
        <div className="resource-card">
          <div className="resource-card-header">
            <h4>Global Commands</h4>
            <span className="badge badge-info">{parsed.global.length} commands</span>
          </div>
          <CommandList commands={parsed.global} />
        </div>
      )}
    </div>
  );
}

function CiscoCpuMemoryView({ resource }: { resource: ResourceState }) {
  if (resource.error) {
    return <ResourceCard resource={resource} />;
  }

  const data = resource.data?.data ?? resource.data;
  if (!data) {
    return <ResourceCard resource={resource} />;
  }

  const cpuRows: Array<[string, any]> = [
    ['Five seconds', data.cpu?.five_seconds !== null && data.cpu?.five_seconds !== undefined ? `${data.cpu.five_seconds}%` : '-'],
    ['Interrupt', data.cpu?.interrupt !== null && data.cpu?.interrupt !== undefined ? `${data.cpu.interrupt}%` : '-'],
    ['One minute', data.cpu?.one_minute !== null && data.cpu?.one_minute !== undefined ? `${data.cpu.one_minute}%` : '-'],
    ['Five minutes', data.cpu?.five_minutes !== null && data.cpu?.five_minutes !== undefined ? `${data.cpu.five_minutes}%` : '-'],
    ['Summary', data.cpu?.summary || '-'],
  ];

  const memorySummaryRows: Array<[string, any]> = [
    ['Total', data.memory?.summary?.total_bytes ? `${data.memory.summary.total_bytes} bytes` : '-'],
    ['Used', data.memory?.summary?.used_bytes ? `${data.memory.summary.used_bytes} bytes` : '-'],
    ['Free', data.memory?.summary?.free_bytes ? `${data.memory.summary.free_bytes} bytes` : '-'],
    ['Used %', data.memory?.summary?.used_percent !== null && data.memory?.summary?.used_percent !== undefined ? `${data.memory.summary.used_percent}%` : '-'],
    ['Free %', data.memory?.summary?.free_percent !== null && data.memory?.summary?.free_percent !== undefined ? `${data.memory.summary.free_percent}%` : '-'],
  ];

  return (
    <div className="resource-grid">
      <OverviewTable title="CPU Utilization" rows={cpuRows} />
      <OverviewTable title="Memory Summary" rows={memorySummaryRows} />
      <ResourceCard resource={{ label: 'Memory Pools', data: data.memory?.pools || [] }} />
      <ResourceCard resource={{ label: 'CPU Processes', data: data.processes || [] }} />
      {data.warnings?.length > 0 && (
        <div className="resource-card">
          <div className="resource-card-header">
            <h4>Warnings</h4>
            <span className="badge badge-warning">{data.warnings.length}</span>
          </div>
          <CommandList commands={data.warnings} />
        </div>
      )}
    </div>
  );
}

function OverviewTable({ title, rows }: { title: string; rows: Array<[string, any]> }) {
  return (
    <div className="resource-card">
      <div className="resource-card-header">
        <h4>{title}</h4>
        <span className="badge badge-info">{rows.length} items</span>
      </div>
      <div className="table-shell">
        <table className="table data-table">
          <tbody>
            {rows.map(([label, value]) => (
              <tr key={label}>
                <th>{label}</th>
                <td>{displayValue(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SkeletonLine({ className = '' }: { className?: string }) {
  return <div className={`skeleton-line ${className}`.trim()} />;
}

function DetailSkeleton() {
  return (
    <div className="detail-skeleton">
      <div className="skeleton-hero">
        <SkeletonLine className="skeleton-chip" />
        <div className="skeleton-hero-body">
          <SkeletonLine className="skeleton-title" />
          <SkeletonLine className="skeleton-subtitle" />
          <div className="skeleton-chip-row">
            <SkeletonLine className="skeleton-chip" />
            <SkeletonLine className="skeleton-chip" />
            <SkeletonLine className="skeleton-chip" />
          </div>
        </div>
        <SkeletonLine className="skeleton-button" />
      </div>

      <div className="detail-highlights">
        <div className="stat-tile skeleton-tile"><SkeletonLine className="skeleton-line-short" /><SkeletonLine className="skeleton-line-med" /></div>
        <div className="stat-tile skeleton-tile"><SkeletonLine className="skeleton-line-short" /><SkeletonLine className="skeleton-line-med" /></div>
        <div className="stat-tile skeleton-tile"><SkeletonLine className="skeleton-line-short" /><SkeletonLine className="skeleton-line-med" /></div>
      </div>

      <div className="tabs skeleton-tabs">
        <SkeletonLine className="skeleton-tab" />
        <SkeletonLine className="skeleton-tab" />
        <SkeletonLine className="skeleton-tab" />
        <SkeletonLine className="skeleton-tab" />
      </div>

      <div className="overview-grid">
        <div className="resource-card">
          <div className="resource-card-header">
            <SkeletonLine className="skeleton-card-title" />
            <SkeletonLine className="skeleton-badge" />
          </div>
          <div className="skeleton-table">
            <SkeletonLine />
            <SkeletonLine />
            <SkeletonLine />
            <SkeletonLine />
          </div>
        </div>
        <div className="resource-card">
          <div className="resource-card-header">
            <SkeletonLine className="skeleton-card-title" />
            <SkeletonLine className="skeleton-badge" />
          </div>
          <div className="skeleton-table">
            <SkeletonLine />
            <SkeletonLine />
            <SkeletonLine />
            <SkeletonLine />
          </div>
        </div>
        <div className="resource-card">
          <div className="resource-card-header">
            <SkeletonLine className="skeleton-card-title" />
            <SkeletonLine className="skeleton-badge" />
          </div>
          <div className="skeleton-table">
            <SkeletonLine />
            <SkeletonLine />
            <SkeletonLine />
            <SkeletonLine />
          </div>
        </div>
      </div>
    </div>
  );
}

async function safeLoad(label: string, loader: () => Promise<any>): Promise<ResourceState> {
  try {
    return { label, data: await loader() };
  } catch (err) {
    return {
      label,
      data: null,
      error: err instanceof Error ? err.message : 'Failed to load resource',
    };
  }
}

async function loadSequential(loaders: Array<() => Promise<ResourceState>>) {
  const loaded: ResourceState[] = [];
  for (const loader of loaders) {
    loaded.push(await loader());
  }
  return Object.fromEntries(loaded.map((item) => [item.label, item]));
}

export function DeviceDetail({ deviceId, onBack, onLoadStateChange, onNotify }: Props) {
  const [device, setDevice] = useState<any>(null);
  const [facts, setFacts] = useState<any>(null);
  const [interfaces, setInterfaces] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [resources, setResources] = useState<Record<string, ResourceState>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('overview');

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

      const primaryInterfaces =
        vendorResources['Cisco Interfaces Detail']?.data ||
        vendorResources['MikroTik Interfaces']?.data ||
        vendorResources.Interfaces?.data ||
        null;
      setInterfaces(primaryInterfaces);
      setConfig(vendorResources['Running Configuration']?.data || null);
      onNotify?.(`Detail ${deviceData?.hostname || deviceId} berhasil dimuat`, 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load device';
      setError(message);
      onNotify?.(`Gagal memuat ${deviceId}: ${message}`, 'error');
    } finally {
      setLoading(false);
      onLoadStateChange?.(false);
    }
  }

  async function loadVendorResources(profile: DeviceProfile) {
    const loadersByProfile: Record<DeviceProfile, Array<() => Promise<ResourceState>>> = {
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
    return (
      <DetailSkeleton />
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="text-red-600">Error: {error}</div>
        <button onClick={onBack} className="btn btn-secondary mt-4">Back</button>
      </div>
    );
  }

  const kind = vendorKind(device, deviceId);
  const isCisco = kind === 'cisco';
  const isMikroTik = kind === 'mikrotik';
  const profile = deviceProfile(device, deviceId);
  const isCiscoRouter = profile === 'cisco-router';
  const isCiscoSwitch = profile === 'cisco-switch';
  const tabsByProfile: Record<DeviceProfile, Array<{ id: TabId; label: string }>> = {
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

  const resource = (label: string) => resources[label] || emptyResource(label);
  const mikrotikHealth = resource('MikroTik Health').data;
  const healthRows: Array<[string, any]> = [
    ['Profile', profileLabel(profile)],
    ['Health status', healthStatus(health, mikrotikHealth)],
    ['Reachable', health?.reachable ?? mikrotikHealth?.reachable ?? health?.ok ?? mikrotikHealth?.ok ?? '-'],
    ['SSH banner', health?.ssh_banner || mikrotikHealth?.ssh_banner || '-'],
    ['Flash OK', health?.flash_ok ?? '-'],
    ['Reason', health?.reason || mikrotikHealth?.reason || health?.message || health?.detail || '-'],
  ];
  const vendorRows: Array<[string, any]> = isCiscoRouter
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

  return (
    <div>
      <div className={heroClass}>
        <button onClick={onBack} className="btn btn-secondary btn-sm">Back</button>
        <div className="device-hero-body">
          <p className="eyebrow">Device detail</p>
          <div className="device-title-row">
            <h1>{device?.hostname || deviceId}</h1>
            <span className={`badge ${isCisco ? 'badge-info' : isMikroTik ? 'badge-warning' : 'badge-success'}`}>
              {profileLabel(profile)}
            </span>
          </div>
          <p>{device?.platform || 'Unknown platform'} / {device?.management_address || 'No management IP'} / {profileAccent(profile)}</p>
          <div className="device-chip-row">
            <span className="device-chip">ID: {deviceId}</span>
            <span className="device-chip">Console: {device?.console_host && device?.console_port ? `${device.console_host}:${device.console_port}` : '-'}</span>
            <span className="device-chip">Status: {device?.status || 'Unknown'}</span>
          </div>
        </div>
        <button onClick={loadDevice} className="btn btn-primary btn-sm">Refresh</button>
      </div>

      <div className="detail-highlights">
        {deviceSummaryTiles.map((tile) => (
          <div key={tile.label} className="stat-tile">
            <span>{tile.label}</span>
            <strong>{tile.value}</strong>
          </div>
        ))}
      </div>

      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab ${currentTab === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {currentTab === 'overview' && (
        <div className="overview-grid">
          <OverviewTable
            title={profile === 'cisco-switch' ? 'Switch Identity' : profile === 'cisco-router' ? 'Router Identity' : profile === 'mikrotik-router' ? 'RouterOS Identity' : 'Device Identity'}
            rows={[
              ['Device ID', deviceId],
              ['Hostname', device?.hostname || '-'],
              ['Vendor', device?.vendor || 'Unknown'],
              ['UI Profile', profileLabel(profile)],
              ['Platform', device?.platform || 'Unknown'],
              ['Management IP', device?.management_address || '-'],
              ['Console', device?.console_host && device?.console_port ? `${device.console_host}:${device.console_port}` : '-'],
              ['Status', device?.status || 'Unknown'],
            ]}
          />
          <OverviewTable title="Health" rows={healthRows} />
          <OverviewTable
            title={`${profileLabel(profile)} Snapshot`}
            rows={vendorRows}
          />
        </div>
      )}

      {currentTab === 'interfaces' && (
        <div className="resource-grid">
          <ResourceCard resource={isCisco ? resource('Cisco Interfaces Detail') : isMikroTik ? resource('MikroTik Interfaces') : resource('Interfaces')} />
        </div>
      )}

      {currentTab === 'ip' && (
        <div className="resource-grid">
          {isMikroTik ? (
            <>
              <ResourceCard resource={resource('MikroTik IP Addresses')} />
              <ResourceCard resource={resource('MikroTik DHCP Servers')} />
              <ResourceCard resource={resource('MikroTik DHCP Leases')} />
            </>
          ) : isCiscoRouter ? (
            <>
              <ResourceCard resource={resource('Cisco ARP Table')} />
              <ResourceCard resource={resource('Cisco CDP Neighbors')} />
            </>
          ) : (
            <>
              <ResourceCard resource={resource('Cisco ARP Table')} />
              <ResourceCard resource={resource('Cisco CDP Neighbors')} />
            </>
          )}
        </div>
      )}

      {currentTab === 'vlans' && (
        <div className="resource-grid">
          {isCiscoSwitch && <ResourceCard resource={resource('Cisco VLANs')} />}
          {isMikroTik && <ResourceCard resource={resource('MikroTik Bridges')} />}
          {isMikroTik && <ResourceCard resource={resource('MikroTik Bridge Ports')} />}
        </div>
      )}

      {currentTab === 'routing' && (
        <div className="resource-grid">
          <ResourceCard resource={isCiscoRouter ? resource('Cisco Routing Table') : isMikroTik ? resource('MikroTik Static Routes') : resource('Routes')} />
          {isMikroTik && <ResourceCard resource={resource('MikroTik OSPF')} />}
          {isMikroTik && <ResourceCard resource={resource('MikroTik BGP')} />}
        </div>
      )}

      {currentTab === 'services' && (
        <div className="resource-grid">
          {isCiscoRouter ? (
            <>
              <CiscoCpuMemoryView resource={resource('Cisco CPU / Memory')} />
              <ResourceCard resource={resource('Cisco ACLs')} />
              <ResourceCard resource={resource('Cisco NAT Translations')} />
            </>
          ) : isCiscoSwitch ? (
            <>
              <CiscoCpuMemoryView resource={resource('Cisco CPU / Memory')} />
              <ResourceCard resource={resource('Cisco CDP Neighbors')} />
            </>
          ) : isMikroTik ? (
            <>
              <ResourceCard resource={resource('MikroTik Health')} />
              <ResourceCard resource={resource('MikroTik Firewall NAT')} />
              <ResourceCard resource={resource('MikroTik Firewall Filter')} />
            </>
          ) : (
            <ResourceCard resource={{ label: 'Generic Health', data: health }} />
          )}
        </div>
      )}

      {currentTab === 'config' && (
        <ConfigView data={config} profile={profile} />
      )}

      {currentTab === 'facts' && (
        <div className="resource-grid">
          <ResourceCard resource={{ label: 'Facts', data: facts }} />
          {isCisco && <ResourceCard resource={resource('Cisco Version')} />}
        </div>
      )}
    </div>
  );
}
