import { useMemo, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router'
import { Eye, MoreHorizontal, PencilLine, Play, RotateCcw, Search, Server, ServerCog, ShieldCheck, Terminal, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Input } from 'src/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from 'src/components/ui/dropdown-menu'
import { EmptyState } from 'src/components/network/page-state'
import { StatusBadge, VendorBadge } from 'src/components/network/status-badge'
import { cn } from 'src/lib/utils'
import type { Device } from 'src/types/network'

type DeviceStatusTableProps = {
  devices: Device[]
  compact?: boolean
  onAddDevice?: () => void
  onEditDevice?: (device: Device) => void
  onDeleteDevice?: (device: Device) => void
  footer?: ReactNode
  allowManagementActions?: boolean
}

const allValue = 'all'

export function DeviceStatusTable({ devices, compact = false, onAddDevice, onEditDevice, onDeleteDevice, footer, allowManagementActions = true }: DeviceStatusTableProps) {
  const [query, setQuery] = useState('')
  const [vendor, setVendor] = useState(allValue)
  const [status, setStatus] = useState(allValue)
  const [lab, setLab] = useState(allValue)
  const [tag, setTag] = useState(allValue)
  const navigate = useNavigate()

  const options = useMemo(
    () => ({
      vendors: Array.from(new Set(devices.map((device) => device.vendor))),
      statuses: Array.from(new Set(devices.map((device) => device.status))),
      labs: Array.from(new Set(devices.map((device) => device.lab))),
      tags: Array.from(new Set(devices.flatMap((device) => device.tags))),
    }),
    [devices]
  )

  const filteredDevices = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    return devices.filter((device) => {
      const matchesQuery =
        !normalizedQuery ||
        [device.hostname, device.managementIp, device.serial, device.model, device.platform].some((value) =>
          value.toLowerCase().includes(normalizedQuery)
        )

      return (
        matchesQuery &&
        (vendor === allValue || device.vendor === vendor) &&
        (status === allValue || device.status === status) &&
        (lab === allValue || device.lab === lab) &&
        (tag === allValue || device.tags.includes(tag))
      )
    })
  }, [devices, lab, query, status, tag, vendor])

  const statusCounts = useMemo(() => ({
    online: filteredDevices.filter((device) => device.status === 'online').length,
    warning: filteredDevices.filter((device) => device.status === 'warning').length,
    offline: filteredDevices.filter((device) => device.status === 'offline').length,
  }), [filteredDevices])

  const handleSSH = (device: Device) => {
    navigate('/terminal', { state: { deviceId: device.id } })
  }

  const handleConfigure = (device: Device) => {
    navigate('/configurations', { state: { deviceId: device.id } })
  }

  const handleBackup = async (device: Device) => {
    toast.info(`Backup requested for ${device.hostname}`)
    // TODO: Call POST /api/v1/cisco/{device_id}/config/backup or similar
  }

  return (
    <Card className="overflow-hidden rounded-2xl border-border/70 bg-card shadow-sm">
      <CardHeader className="gap-3 border-b border-border/70 bg-transparent px-4 py-3">
        <div className="-mx-4 -mt-3 flex flex-wrap items-center justify-between gap-3 border-b border-border/70 bg-muted/10 px-4 py-3">
          <div>
            <div className="flex items-center gap-2">
              {!compact && <span className="rounded-lg bg-muted p-1.5 text-muted-foreground"><Server className="size-4" /></span>}
              <CardTitle>{compact ? 'Device Status Overview' : allowManagementActions ? 'Direct devices' : 'Edge devices'}</CardTitle>
              {!compact && <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium tabular-nums">{filteredDevices.length}</span>}
            </div>
            <p className="text-sm text-muted-foreground">
              {allowManagementActions ? 'Koneksi langsung melalui IP public atau management address.' : 'Perangkat yang terdeteksi dan dikelola melalui Edge connector.'}
            </p>
          </div>
          {!compact && (
            <div className="flex flex-wrap items-center gap-2">
              {allowManagementActions && <Button size="sm" variant="outline" onClick={() => onAddDevice?.() ?? toast.info('Add Device coming soon')}><ServerCog className="size-4" /> Add Device</Button>}
              <Button size="sm" variant="outline" onClick={() => navigate('/discovery')}><Search className="size-4" /> Discover Devices</Button>
              {allowManagementActions && <Button size="sm" onClick={() => toast.info('Import CSV coming soon')}><RotateCcw className="size-4" /> Import CSV</Button>}
            </div>
          )}
        </div>

        {!compact && (
          <div className="flex flex-wrap items-center gap-2">
            <Input className="w-full sm:w-60" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search hostname, IP, serial, model..." />
            <FilterSelect className="w-[120px]" label="Vendor" value={vendor} values={options.vendors} onChange={setVendor} />
            <FilterSelect className="w-[120px]" label="Status" value={status} values={options.statuses} onChange={setStatus} />
            <FilterSelect className="w-[120px]" label="Lab" value={lab} values={options.labs} onChange={setLab} />
            <FilterSelect className="w-[120px]" label="Tag" value={tag} values={options.tags} onChange={setTag} />
          </div>
        )}
        {!compact && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <StatusSummary label="Online" value={statusCounts.online} tone="success" />
            <StatusSummary label="Warning" value={statusCounts.warning} tone="warning" />
            <StatusSummary label="Offline" value={statusCounts.offline} tone="muted" />
          </div>
        )}
      </CardHeader>
      <CardContent className="px-4 py-4">
        {filteredDevices.length === 0 ? (
          <EmptyState title="No devices match the current filters." />
        ) : (
          <>
            <div className="overflow-x-auto rounded-xl border border-border/70">
            <Table className="min-w-[1180px]">
              <TableHeader>
                <TableRow>
                  <TableHead>Device</TableHead>
                  <TableHead>Vendor</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Management IP</TableHead>
                  <TableHead>Platform</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>CPU</TableHead>
                  <TableHead>Memory</TableHead>
                  <TableHead>Latency</TableHead>
                  <TableHead>Open Ports</TableHead>
                  <TableHead>Last Seen</TableHead>
                  <TableHead>Execution Context</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDevices.map((device) => (
                  <TableRow key={device.id} className="hover:bg-muted/40">
                    <TableCell>
                      <div className="whitespace-nowrap font-medium">{device.hostname}</div>
                      <div className="max-w-44 truncate text-xs text-muted-foreground" title={device.tags.includes('discovered') ? 'Edge Discovery' : device.id}>
                        {device.tags.includes('discovered') ? 'Edge Discovery' : device.id}
                      </div>
                    </TableCell>
                    <TableCell><VendorBadge vendor={device.vendor} /></TableCell>
                    <TableCell className="whitespace-nowrap">{device.model}</TableCell>
                    <TableCell className="whitespace-nowrap font-mono text-xs">{device.managementIp}</TableCell>
                    <TableCell className="whitespace-nowrap">{device.platform}</TableCell>
                    <TableCell><StatusBadge status={device.status} /></TableCell>
                    <TableCell className="whitespace-nowrap">{device.cpu}%</TableCell>
                    <TableCell className="whitespace-nowrap">{device.memory}%</TableCell>
                    <TableCell className="whitespace-nowrap">{device.latencyMs === null ? '-' : `${device.latencyMs} ms`}</TableCell>
                    <TableCell className="min-w-44">
                      {device.openPorts?.length
                        ? <div className="flex max-w-64 flex-wrap gap-1">{device.openPorts.map((item) => <span key={`${item.port}-${item.service}`} className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{item.port}/{item.service}</span>)}</div>
                        : '-'}
                    </TableCell>
                    <TableCell className="whitespace-nowrap">{device.lastSeen}</TableCell>
                    <TableCell>
                      <div className="font-medium">{contextLabel(device)}</div>
                      <div className="max-w-44 truncate text-xs text-muted-foreground">{contextDetail(device)}</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end">
                        <DropdownMenu modal={false}>
                          <DropdownMenuTrigger className="inline-flex size-8 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground" aria-label={`Actions for ${device.hostname}`} title="Actions">
                            <MoreHorizontal className="size-4" />
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48">
                            <DropdownMenuItem className="flex items-center gap-2" onClick={() => navigate(`/devices/${device.id}`, { state: { device } })}>
                              {allowManagementActions ? <MoreHorizontal className="size-4" /> : <Eye className="size-4" />} {allowManagementActions ? 'Open device' : 'Open'}
                            </DropdownMenuItem>
                            <DropdownMenuItem className="flex items-center gap-2" onClick={() => handleSSH(device)}>
                              <Terminal className="size-4" /> SSH
                            </DropdownMenuItem>
                            <DropdownMenuItem className="flex items-center gap-2" onClick={() => handleSSH(device)}>
                              <Play className="size-4" /> Run command
                            </DropdownMenuItem>
                            <DropdownMenuItem className="flex items-center gap-2" onClick={() => handleConfigure(device)}>
                              <ServerCog className="size-4" /> Configure
                            </DropdownMenuItem>
                            {allowManagementActions && (
                              <>
                                <DropdownMenuItem className="flex items-center gap-2" onClick={() => void handleBackup(device)}>
                                  <ShieldCheck className="size-4" /> Backup
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem className="flex items-center gap-2" onClick={() => onEditDevice?.(device)}>
                                  <PencilLine className="size-4" /> Edit device
                                </DropdownMenuItem>
                                <DropdownMenuItem variant="destructive" className="flex items-center gap-2" onClick={() => onDeleteDevice?.(device)}>
                                  <Trash2 className="size-4" /> Delete device
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {footer && (
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3">{footer}</div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

function FilterSelect({
  className,
  label,
  value,
  values,
  onChange,
}: {
  className?: string
  label: string
  value: string
  values: string[]
  onChange: (value: string) => void
}) {
  return (
    <Select value={value} onValueChange={(nextValue) => onChange(nextValue ?? allValue)}>
      <SelectTrigger className={cn('w-full', className)}>
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={allValue}>{label}: All</SelectItem>
        {values.map((item) => (
          <SelectItem key={item} value={item}>
            {item}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function StatusSummary({ label, value, tone }: { label: string; value: number; tone: 'success' | 'warning' | 'muted' }) {
  const toneClass = tone === 'success'
    ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300'
    : tone === 'warning'
      ? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300'
      : 'border-border bg-muted/50 text-muted-foreground'
  return <span className={cn('rounded-full border px-2 py-1', toneClass)}>{label} <span className="font-semibold tabular-nums">{value}</span></span>
}

function contextLabel(device: Device) {
  if (device.source === 'edge' || device.executionLocation === 'EDGE' || device.edgeId) return 'Edge'
  if (device.source === 'gns3' || device.deviceType === 'virtual') return 'GNS3'
  return 'Direct IP'
}

function contextDetail(device: Device) {
  if (contextLabel(device) === 'Edge') {
    return [device.edgeId, device.customerId, device.siteId].filter(Boolean).join(' / ') || 'Customer LAN'
  }
  if (contextLabel(device) === 'GNS3') return device.projectName || device.lab || 'GNS3 project'
  return device.managementIp || 'Direct management address'
}
