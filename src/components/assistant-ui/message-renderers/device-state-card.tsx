import { parseJsonBlock } from './utils'

type DataRecord = Record<string, unknown>

function isPlainObject(value: unknown): value is DataRecord {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function titleize(key: string) {
  return key
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

function normalizeVendor(value: unknown): string {
  const text = String(value ?? '').toLowerCase()
  if (text.includes('mikrotik') || text.includes('routeros')) return 'mikrotik'
  if (text.includes('cisco') || text.includes('iosv') || text.includes('ios')) return 'cisco'
  if (text.includes('aruba') || text.includes('aos-cx') || text.includes('aoscx')) return 'aruba'
  if (text.includes('linux') || ['debian', 'ubuntu', 'centos', 'rocky', 'alma', 'fedora'].includes(text)) return 'linux'
  return 'other'
}

function vendorLabel(vendor: string) {
  const labels: Record<string, string> = {
    cisco: 'Cisco',
    mikrotik: 'MikroTik',
    aruba: 'Aruba',
    linux: 'Linux',
    other: 'Other',
  }
  return labels[vendor] ?? 'Other'
}

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) return '-'
  if (Array.isArray(value)) {
    if (!value.length) return '-'
    if (value.every((item) => !isPlainObject(item) && !Array.isArray(item))) {
      return value.map((item) => String(item)).join(', ')
    }
    return `${value.length} item(s)`
  }
  if (isPlainObject(value)) return JSON.stringify(value, null, 2)
  return String(value)
}

function valueNode(value: unknown) {
  if (isPlainObject(value)) {
    return (
      <pre className="whitespace-pre-wrap break-words rounded-lg border border-border bg-background px-3 py-2 font-mono text-[11px] leading-5 text-foreground">
        {JSON.stringify(value, null, 2)}
      </pre>
    )
  }

  return <span className="min-w-0 break-words font-mono text-foreground">{stringifyValue(value)}</span>
}

function vendorPriority(vendor: string): string[] {
  if (vendor === 'cisco') return ['hostname', 'vendor', 'platform', 'status', 'management_ip', 'management_address', 'model', 'id', 'device_id', 'note']
  if (vendor === 'mikrotik') return ['hostname', 'vendor', 'platform', 'status', 'management_address', 'management_ip', 'model', 'id', 'device_id', 'note']
  if (vendor === 'linux') return ['hostname', 'vendor', 'platform', 'status', 'management_ip', 'management_address', 'kernel_interfaces', 'routing_table_entries', 'id', 'device_id', 'note']
  if (vendor === 'aruba') return ['hostname', 'vendor', 'platform', 'status', 'management_ip', 'management_address', 'model', 'id', 'device_id', 'note']
  return ['hostname', 'vendor', 'platform', 'status', 'management_ip', 'management_address', 'model', 'id', 'device_id', 'note']
}

function orderedSummaryKeys(data: DataRecord) {
  const vendor = normalizeVendor(data.vendor ?? data.platform)
  const priority = vendorPriority(vendor)
  const keys = Object.keys(data)
  return [
    ...priority.filter((key) => keys.includes(key)),
    ...keys.filter((key) => !priority.includes(key) && !['interfaces', 'routes', 'devices', 'data'].includes(key)).sort((a, b) => a.localeCompare(b)),
  ]
}

function sectionTitle(vendor: string) {
  if (vendor === 'cisco') return 'Cisco NOC Summary'
  if (vendor === 'mikrotik') return 'MikroTik RouterOS Summary'
  if (vendor === 'linux') return 'Linux Host Summary'
  if (vendor === 'aruba') return 'Aruba AOS-CX Summary'
  return 'Device State Summary'
}

function renderSummaryRows(data: DataRecord) {
  const vendor = normalizeVendor(data.vendor ?? data.platform)
  return orderedSummaryKeys(data).map((key) => (
    <div key={key} className="grid grid-cols-[150px_minmax(0,1fr)] gap-3 border-t border-border px-3 py-2 text-xs first:border-t-0 sm:grid-cols-[200px_minmax(0,1fr)]">
      <span className="font-medium text-muted-foreground">{titleize(key)}</span>
      <div className="min-w-0">
        {key === 'vendor' ? (
          <span className="inline-flex items-center rounded-full border border-border bg-muted/40 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-foreground">
            {vendorLabel(String(data[key] ?? vendor))}
          </span>
        ) : (
          valueNode(data[key])
        )}
      </div>
    </div>
  ))
}

function collectColumns(rows: unknown[]): string[] {
  const columns: string[] = []
  for (const row of rows) {
    if (!isPlainObject(row)) continue
    for (const key of Object.keys(row)) {
      if (!columns.includes(key)) columns.push(key)
    }
  }
  return columns
}

function renderTable(title: string, rows: unknown[], vendor: string) {
  if (!Array.isArray(rows) || rows.length === 0) return null

  const columns = collectColumns(rows)
  if (!columns.length) return null

  const preferred = vendor === 'cisco'
    ? ['name', 'interface', 'description', 'ip_address', 'ip', 'admin_status', 'oper_status', 'status', 'speed', 'duplex', 'rx', 'tx', 'errors', 'dst', 'gateway', 'dev', 'protocol', 'metric']
    : vendor === 'mikrotik'
      ? ['name', 'disabled', 'running', 'status', 'address', 'interface', 'network', 'gateway', 'distance', 'scope', 'target-scope']
      : vendor === 'linux'
        ? ['name', 'type', 'state', 'ipv4', 'ipv6', 'gateway', 'dev', 'protocol', 'metric']
        : ['name', 'status', 'type', 'address', 'interface', 'gateway', 'dev', 'protocol', 'metric']

  const orderedColumns = [
    ...preferred.filter((key) => columns.includes(key)),
    ...columns.filter((key) => !preferred.includes(key)),
  ]

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-background/60">
      <div className="border-b border-border bg-muted/30 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </div>
      <div className="bubble-scrollbar overflow-x-auto">
        <table className="min-w-full border-collapse text-xs">
          <thead className="bg-muted/20 text-left text-muted-foreground">
            <tr>
              {orderedColumns.map((col) => (
                <th key={col} className="whitespace-nowrap border-b border-border px-3 py-1.5 font-medium">
                  {titleize(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className="border-t border-border/60 align-top">
                {orderedColumns.map((col) => (
                  <td key={col} className="max-w-[320px] whitespace-pre-wrap break-words px-3 py-2 font-mono text-[11px] leading-5">
                    {isPlainObject(row) ? stringifyValue(row[col]) : stringifyValue(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function renderNestedObject(title: string, value: unknown) {
  if (!isPlainObject(value)) return null
  const entries = Object.entries(value)
  if (!entries.length) return null

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-background/60">
      <div className="border-b border-border bg-muted/30 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </div>
      <div className="divide-y divide-border">
        {entries.map(([key, nestedValue]) => (
          <div key={key} className="grid grid-cols-[150px_minmax(0,1fr)] gap-3 px-3 py-2 text-xs sm:grid-cols-[200px_minmax(0,1fr)]">
            <span className="font-medium text-muted-foreground">{titleize(key)}</span>
            <div className="min-w-0">{valueNode(nestedValue)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function renderRawJson(data: DataRecord) {
  return (
    <details className="rounded-xl border border-border bg-background/50">
      <summary className="cursor-pointer px-3 py-2 text-xs font-medium text-muted-foreground">
        Raw JSON
      </summary>
      <pre className="bubble-scrollbar max-h-[28rem] overflow-auto border-t border-border bg-slate-950 px-3 py-3 text-[11px] leading-5 text-slate-100 whitespace-pre-wrap break-words dark:text-slate-200">
        {JSON.stringify(data, null, 2)}
      </pre>
    </details>
  )
}

export function DeviceStateCard({ text }: { text: string }) {
  const data = parseJsonBlock(text)
  if (!data) {
    return (
      <pre className="bubble-scrollbar my-2 max-h-[28rem] overflow-auto rounded-xl border border-border bg-slate-950 p-3 text-xs text-slate-100 dark:text-slate-200">
        {text}
      </pre>
    )
  }

  const vendor = normalizeVendor(data.vendor ?? data.platform)
  const interfaces = Array.isArray(data.interfaces)
    ? data.interfaces
    : Array.isArray(data.data)
      ? data.data
      : Array.isArray(data.devices)
        ? data.devices
        : null
  const routes = Array.isArray(data.routes) ? data.routes : null
  const hasStructuredContent = Boolean(interfaces || routes || Object.keys(data).length)

  return (
    <div className="my-2 max-w-full overflow-hidden rounded-xl border border-border bg-background">
      <div className="flex items-center justify-between gap-2 border-b border-border bg-muted/40 px-3 py-1.5">
        <div className="min-w-0">
          <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Device State</div>
          <div className="truncate text-xs font-medium text-foreground">{sectionTitle(vendor)}</div>
        </div>
        <span className="rounded-full border border-border bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary">
          {vendorLabel(vendor)}
        </span>
      </div>

      <div className="space-y-3 p-3">
        <div className="rounded-xl border border-border bg-background/60">
          {renderSummaryRows(data)}
        </div>

        {renderNestedObject('Operator Note', data.note)}

        {renderTable(
          vendor === 'cisco'
            ? 'Cisco Interfaces'
            : vendor === 'mikrotik'
              ? 'RouterOS Interfaces'
              : vendor === 'linux'
                ? 'Linux Interfaces'
                : 'Interfaces / Devices',
          interfaces ?? [],
          vendor,
        )}

        {renderTable(
          vendor === 'cisco'
            ? 'Cisco Routing Table'
            : vendor === 'mikrotik'
              ? 'RouterOS Routes'
              : vendor === 'linux'
                ? 'Linux Routes'
                : 'Routing Table',
          routes ?? [],
          vendor,
        )}

        {!hasStructuredContent ? (
          <pre className="bubble-scrollbar max-h-[28rem] overflow-auto rounded-xl border border-border bg-slate-950 p-3 text-xs text-slate-100 dark:text-slate-200">
            {text}
          </pre>
        ) : null}

        {renderRawJson(data)}
      </div>
    </div>
  )
}
