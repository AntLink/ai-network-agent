import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { MoreHorizontal, PencilLine, Play, RotateCcw, Search, ServerCog, ShieldCheck, Terminal, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Input } from 'src/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import { EmptyState } from 'src/components/network/page-state'
import { StatusBadge, VendorBadge } from 'src/components/network/status-badge'
import { buttonVariants } from 'src/components/ui/button'
import { cn } from 'src/lib/utils'
import type { Device } from 'src/types/network'

type DeviceStatusTableProps = {
  devices: Device[]
  compact?: boolean
  onAddDevice?: () => void
  onEditDevice?: (device: Device) => void
  onDeleteDevice?: (device: Device) => void
}

const allValue = 'all'

export function DeviceStatusTable({ devices, compact = false, onAddDevice, onEditDevice, onDeleteDevice }: DeviceStatusTableProps) {
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
    <Card>
      <CardHeader className="gap-4 border-b">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>{compact ? 'Device Status Overview' : 'Devices'}</CardTitle>
            <p className="text-sm text-muted-foreground">Cisco IOSv, MikroTik CHR, Aruba AOS-CX, Linux, and lab nodes.</p>
          </div>
          {!compact && (
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => onAddDevice?.() ?? toast.info('Add Device coming soon')}><ServerCog className="size-4" /> Add Device</Button>
              <Button variant="outline" onClick={() => navigate('/discovery')}><Search className="size-4" /> Discover Devices</Button>
              <Button onClick={() => toast.info('Import CSV coming soon')}><RotateCcw className="size-4" /> Import CSV</Button>
            </div>
          )}
        </div>

        {!compact && (
          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-5">
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search hostname, IP, serial, model..." />
            <FilterSelect label="Vendor" value={vendor} values={options.vendors} onChange={setVendor} />
            <FilterSelect label="Status" value={status} values={options.statuses} onChange={setStatus} />
            <FilterSelect label="Lab" value={lab} values={options.labs} onChange={setLab} />
            <FilterSelect label="Tag" value={tag} values={options.tags} onChange={setTag} />
          </div>
        )}
      </CardHeader>
      <CardContent className="py-5">
        {filteredDevices.length === 0 ? (
          <EmptyState title="No devices match the current filters." />
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <Table>
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
                  <TableHead>Last Seen</TableHead>
                  <TableHead>Device Type</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDevices.map((device) => (
                  <TableRow key={device.id}>
                    <TableCell>
                      <div className="font-medium">{device.hostname}</div>
                      <div className="text-xs text-muted-foreground">{device.lab}</div>
                    </TableCell>
                    <TableCell><VendorBadge vendor={device.vendor} /></TableCell>
                    <TableCell>{device.model}</TableCell>
                    <TableCell className="font-mono text-xs">{device.managementIp}</TableCell>
                    <TableCell>{device.platform}</TableCell>
                    <TableCell><StatusBadge status={device.status} /></TableCell>
                    <TableCell>{device.cpu}%</TableCell>
                    <TableCell>{device.memory}%</TableCell>
                    <TableCell>{device.latencyMs === null ? '-' : `${device.latencyMs} ms`}</TableCell>
                    <TableCell>{device.lastSeen}</TableCell>
                    <TableCell>
                      {device.deviceType === 'physical' ? 'Physical' : 'Virtual'}
                    </TableCell>
                    <TableCell>
                      <div className="flex min-w-80 justify-end gap-1">
                        <Link className={cn(buttonVariants({ size: 'sm' }))} to={`/devices/${device.id}`}>
                          Open
                        </Link>
                        <Button size="icon-sm" variant="outline" title="SSH" onClick={() => handleSSH(device)}>
                          <Terminal className="size-4" />
                        </Button>
                        <Button size="icon-sm" variant="outline" title="Run Command" onClick={() => handleSSH(device)}>
                          <Play className="size-4" />
                        </Button>
                        <Button size="icon-sm" variant="outline" title="Configure" onClick={() => handleConfigure(device)}>
                          <ServerCog className="size-4" />
                        </Button>
                        <Button size="icon-sm" variant="outline" title="Backup" onClick={() => handleBackup(device)}>
                          <ShieldCheck className="size-4" />
                        </Button>
                        <Button size="icon-sm" variant="outline" title="Edit device" onClick={() => onEditDevice?.(device)}>
                          <PencilLine className="size-4" />
                        </Button>
                        <Button size="icon-sm" variant="destructive" title="Delete device" onClick={() => onDeleteDevice?.(device)}>
                          <Trash2 className="size-4" />
                        </Button>
                        <Button size="icon-sm" variant="ghost" title="More">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function FilterSelect({
  label,
  value,
  values,
  onChange,
}: {
  label: string
  value: string
  values: string[]
  onChange: (value: string) => void
}) {
  return (
    <Select value={value} onValueChange={(nextValue) => onChange(nextValue ?? allValue)}>
      <SelectTrigger>
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
