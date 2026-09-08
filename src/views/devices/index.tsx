import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Cable, ChevronLeft, ChevronRight, Eye, Globe2, Loader2, MoreHorizontal, Play, Radio, Server, ServerCog, Terminal } from 'lucide-react'
import { useNavigate } from 'react-router'
import { createDevice, deleteDevice, updateDevice, useDevicesPage, useEdgeRuntimeStatuses } from 'src/api/network'
import { DeviceStatusTable } from 'src/components/network/device-status-table'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { toast } from 'sonner'
import { Button } from 'src/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from 'src/components/ui/dialog'
import { Input } from 'src/components/ui/input'
import { Label } from 'src/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Badge } from 'src/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from 'src/components/ui/dropdown-menu'
import { StatusBadge } from 'src/components/network/status-badge'
import type { Device } from 'src/types/network'
import type { EdgeRuntimeStatus } from 'src/api/network/backend-client'

const PAGE_SIZES = [10, 25, 50, 100]
type DeviceScope = 'edge' | 'direct'

type DeviceFormState = {
  id: string
  hostname: string
  managementAddress: string
  vendor: 'cisco' | 'mikrotik' | 'aruba' | 'linux' | 'other'
  platform: string
  transport: 'ssh' | 'api' | 'netconf'
  status: 'active' | 'offline' | 'warning'
  deviceType: 'physical' | 'virtual'
  model: string
  serial: string
  lab: string
  consoleHost: string
  consolePort: string
  osVersion: string
  uptime: string
  privilegeLevel: string
  tags: string
}

function createEmptyDeviceForm(): DeviceFormState {
  return {
    id: '',
    hostname: '',
    managementAddress: '',
    vendor: 'cisco',
    platform: 'ios',
    transport: 'ssh',
    status: 'active',
    deviceType: 'virtual',
    model: '',
    serial: '',
    lab: 'Backend Inventory',
    consoleHost: '',
    consolePort: '',
    osVersion: '',
    uptime: '',
    privilegeLevel: '',
    tags: '',
  }
}

function slugifyDeviceName(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

const DevicesPage = () => {
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(25)
  const { data, error, isLoading, isValidating, mutate } = useDevicesPage({ page, limit })
  const { data: edgeStatuses, isLoading: edgeStatusesLoading, error: edgeStatusesError } = useEdgeRuntimeStatuses()
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [editSubmitting, setEditSubmitting] = useState(false)
  const [deleteSubmitting, setDeleteSubmitting] = useState(false)
  const [editingDevice, setEditingDevice] = useState<Device | null>(null)
  const [deletingDevice, setDeletingDevice] = useState<Device | null>(null)
  const [form, setForm] = useState<DeviceFormState>(() => createEmptyDeviceForm())
  const [scope, setScope] = useState<DeviceScope>('edge')

  useEffect(() => {
    if (limit > 0) setPage((current) => current)
  }, [limit])

  const rawData = data?.data as unknown
  const isArray = Array.isArray(rawData)
  const pageData = isArray ? null : (rawData as { devices?: Device[]; total?: number; page?: number; pages?: number } | null)
  const devices = isArray ? (rawData as Device[]) : (pageData?.devices ?? [])
  const total = isArray ? (rawData as Device[]).length : (pageData?.total ?? devices.length)
  const pages = isArray ? 1 : (pageData?.pages ?? 1)
  const tableLoading = isValidating && !!data

  const scopeCounts = useMemo(() => ({
    edge: edgeStatuses?.length ?? devices.filter((device) => (device.source ?? inferDeviceSource(device)) === 'edge').length,
    direct: devices.filter((device) => (device.source ?? inferDeviceSource(device)) === 'direct').length,
  }), [devices, edgeStatuses])

  const visibleDevices = useMemo(() => devices.filter((device) => {
    if ((device.source ?? inferDeviceSource(device)) !== scope) return false
    return true
  }), [devices, scope])

  if (isLoading && !data) {
    return <LoadingState rows={6} />
  }

  if (error && !data) {
    return <ErrorState message="Failed to load device inventory." />
  }

  const handleLimitChange = (value: string | null) => {
    if (value) { setLimit(Number(value)); setPage(1) }
  }

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-primary/10 p-2 text-primary"><Server className="size-5" /></div>
            <h1 className="text-2xl font-semibold tracking-normal">Devices</h1>
          </div>
          <p className="text-sm text-muted-foreground">Kelola perangkat melalui Edge atau koneksi langsung.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          {tableLoading && <Loader2 className="size-3.5 animate-spin" />}
          <Badge variant="secondary">{total} perangkat</Badge>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <ScopeCard active={scope === 'edge'} title="Edge Devices" detail="Customer LAN melalui Edge" count={scopeCounts.edge} onClick={() => setScope('edge')} />
        <ScopeCard active={scope === 'direct'} title="Direct Devices" detail="IP langsung / public address" count={scopeCounts.direct} onClick={() => setScope('direct')} />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/70 bg-card/80 px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2.5">
          <Badge variant="outline">{scope === 'edge' ? 'EDGE ROUTING VIEW' : 'DIRECT IP VIEW'}</Badge>
          <span className="text-sm text-muted-foreground">{scope === 'edge' ? `${edgeStatuses?.length ?? 0} Edge terdeteksi` : `${visibleDevices.length} perangkat ditampilkan`}</span>
        </div>
        {scope === 'edge' && <span className="flex items-center gap-1.5 text-xs text-emerald-600"><Radio className="size-3.5" /> Live refresh</span>}
      </div>

      {scope === 'edge' ? (
        <EdgeRuntimeList
          statuses={edgeStatuses ?? []}
          isLoading={edgeStatusesLoading}
          hasError={Boolean(edgeStatusesError)}
        />
      ) : visibleDevices.length ? (
        <>
          <DeviceStatusTable
            devices={visibleDevices}
            footer={
              <>
                <p className="text-sm text-muted-foreground">
                  Page {page} of {pages}
                </p>
                <div className="flex items-center gap-2">
                  <Select value={String(limit)} onValueChange={handleLimitChange}>
                    <SelectTrigger className="h-8 w-[100px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PAGE_SIZES.map((size) => (
                        <SelectItem key={size} value={String(size)}>{size} / page</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
                    <ChevronLeft className="size-4" /> Prev
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(pages, p + 1))} disabled={page >= pages}>
                    Next <ChevronRight className="size-4" />
                  </Button>
                </div>
              </>
            }
            onAddDevice={() => {
              setForm(createEmptyDeviceForm())
              setCreateOpen(true)
            }}
            onEditDevice={(device) => {
              setEditingDevice(device)
              setForm(deviceToForm(device))
              setEditOpen(true)
            }}
            onDeleteDevice={(device) => {
              setDeletingDevice(device)
              setDeleteOpen(true)
            }}
          />
        </>
      ) : (
        <EmptyState title="No direct devices found." />
      )}

      <Dialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open)
          if (!open) setForm(createEmptyDeviceForm())
        }}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add Device</DialogTitle>
            <DialogDescription>Add a new device to the backend inventory file and refresh the devices table.</DialogDescription>
          </DialogHeader>
          <form
            className="grid gap-4"
            onSubmit={async (event) => {
              event.preventDefault()
              const id = form.id.trim() || slugifyDeviceName(form.hostname)
              if (!id || !form.hostname.trim() || !form.managementAddress.trim()) {
                toast.error('ID, hostname, dan management address wajib diisi')
                return
              }

              setCreateSubmitting(true)
              try {
                await createDevice({
                  id,
                  hostname: form.hostname.trim(),
                  managementAddress: form.managementAddress.trim(),
                  vendor: form.vendor,
                  platform: form.platform.trim(),
                  transport: form.transport,
                  status: form.status,
                  deviceType: form.deviceType,
                  model: form.model.trim() || undefined,
                  serial: form.serial.trim() || undefined,
                  lab: form.lab.trim() || undefined,
                  consoleHost: form.consoleHost.trim() || undefined,
                  consolePort: form.consolePort.trim() ? Number(form.consolePort.trim()) : undefined,
                  osVersion: form.osVersion.trim() || undefined,
                  uptime: form.uptime.trim() || undefined,
                  privilegeLevel: form.privilegeLevel.trim() || undefined,
                  tags: form.tags
                    .split(',')
                    .map((tag) => tag.trim())
                    .filter(Boolean),
                })
                await mutate()
                toast.success('Device added successfully')
                setCreateOpen(false)
                setForm(createEmptyDeviceForm())
              } catch (error) {
                toast.error(error instanceof Error ? error.message : 'Failed to add device')
              } finally {
                setCreateSubmitting(false)
              }
            }}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Device ID">
                <Input value={form.id} onChange={(event) => setForm((current) => ({ ...current, id: event.target.value }))} placeholder="cisco-iosv-r3" />
              </Field>
              <Field label="Hostname">
                <Input value={form.hostname} onChange={(event) => setForm((current) => ({ ...current, hostname: event.target.value }))} placeholder="R3" />
              </Field>
              <Field label="Management Address">
                <Input value={form.managementAddress} onChange={(event) => setForm((current) => ({ ...current, managementAddress: event.target.value }))} placeholder="172.22.45.250" />
              </Field>
              <Field label="Vendor">
                <Select value={form.vendor} onValueChange={(value) => setForm((current) => ({ ...current, vendor: value as DeviceFormState['vendor'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cisco">Cisco</SelectItem>
                    <SelectItem value="mikrotik">MikroTik</SelectItem>
                    <SelectItem value="aruba">Aruba</SelectItem>
                    <SelectItem value="linux">Linux</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Platform">
                <Input value={form.platform} onChange={(event) => setForm((current) => ({ ...current, platform: event.target.value }))} placeholder="ios / routeros / aos-cx" />
              </Field>
              <Field label="Device Type">
                <Select value={form.deviceType} onValueChange={(value) => setForm((current) => ({ ...current, deviceType: value as DeviceFormState['deviceType'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="virtual">Virtual</SelectItem>
                    <SelectItem value="physical">Physical</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Transport">
                <Select value={form.transport} onValueChange={(value) => setForm((current) => ({ ...current, transport: value as DeviceFormState['transport'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ssh">SSH</SelectItem>
                    <SelectItem value="api">API</SelectItem>
                    <SelectItem value="netconf">NETCONF</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Status">
                <Select value={form.status} onValueChange={(value) => setForm((current) => ({ ...current, status: value as DeviceFormState['status'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="warning">Warning</SelectItem>
                    <SelectItem value="offline">Offline</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Model">
                <Input value={form.model} onChange={(event) => setForm((current) => ({ ...current, model: event.target.value }))} placeholder="IOSv / CHR / AOS-CX" />
              </Field>
              <Field label="Serial">
                <Input value={form.serial} onChange={(event) => setForm((current) => ({ ...current, serial: event.target.value }))} placeholder="Optional" />
              </Field>
              <Field label="Lab">
                <Input value={form.lab} onChange={(event) => setForm((current) => ({ ...current, lab: event.target.value }))} placeholder="Backend Inventory" />
              </Field>
              <Field label="Console Host">
                <Input value={form.consoleHost} onChange={(event) => setForm((current) => ({ ...current, consoleHost: event.target.value }))} placeholder="172.22.46.196" />
              </Field>
              <Field label="Console Port">
                <Input value={form.consolePort} onChange={(event) => setForm((current) => ({ ...current, consolePort: event.target.value }))} placeholder="5006" inputMode="numeric" />
              </Field>
              <Field label="OS Version">
                <Input value={form.osVersion} onChange={(event) => setForm((current) => ({ ...current, osVersion: event.target.value }))} placeholder="15.6 / RouterOS 7.x" />
              </Field>
              <Field label="Uptime">
                <Input value={form.uptime} onChange={(event) => setForm((current) => ({ ...current, uptime: event.target.value }))} placeholder="1d 2h" />
              </Field>
              <Field label="Privilege Level">
                <Input value={form.privilegeLevel} onChange={(event) => setForm((current) => ({ ...current, privilegeLevel: event.target.value }))} placeholder="15 / full" />
              </Field>
              <Field label="Tags">
                <Input value={form.tags} onChange={(event) => setForm((current) => ({ ...current, tags: event.target.value }))} placeholder="lab, core, cisco" />
              </Field>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)} disabled={createSubmitting}>
                Cancel
              </Button>
                <Button type="submit" disabled={createSubmitting}>
                  {createSubmitting ? 'Saving...' : 'Create Device'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
      </Dialog>

      <Dialog
        open={editOpen}
        onOpenChange={(open) => {
          setEditOpen(open)
          if (!open) {
            setEditingDevice(null)
            setForm(createEmptyDeviceForm())
          }
        }}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Device</DialogTitle>
            <DialogDescription>Update device metadata and refresh the inventory table.</DialogDescription>
          </DialogHeader>
          <form
            className="grid gap-4"
            onSubmit={async (event) => {
              event.preventDefault()
              if (!editingDevice) return
              if (!form.hostname.trim() || !form.managementAddress.trim()) {
                toast.error('Hostname dan management address wajib diisi')
                return
              }

              setEditSubmitting(true)
              try {
                await updateDevice(editingDevice.id, {
                  hostname: form.hostname.trim(),
                  managementAddress: form.managementAddress.trim(),
                  vendor: form.vendor,
                  platform: form.platform.trim(),
                  transport: form.transport,
                  status: form.status,
                  deviceType: form.deviceType,
                  model: form.model.trim() || undefined,
                  serial: form.serial.trim() || undefined,
                  lab: form.lab.trim() || undefined,
                  consoleHost: form.consoleHost.trim() || undefined,
                  consolePort: form.consolePort.trim() ? Number(form.consolePort.trim()) : undefined,
                  osVersion: form.osVersion.trim() || undefined,
                  uptime: form.uptime.trim() || undefined,
                  privilegeLevel: form.privilegeLevel.trim() || undefined,
                  tags: form.tags
                    .split(',')
                    .map((tag) => tag.trim())
                    .filter(Boolean),
                })
                await mutate()
                toast.success('Device updated successfully')
                setEditOpen(false)
                setEditingDevice(null)
                setForm(createEmptyDeviceForm())
              } catch (error) {
                toast.error(error instanceof Error ? error.message : 'Failed to update device')
              } finally {
                setEditSubmitting(false)
              }
            }}
          >
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Device ID">
                <Input value={form.id} disabled placeholder="cisco-iosv-r3" />
              </Field>
              <Field label="Hostname">
                <Input value={form.hostname} onChange={(event) => setForm((current) => ({ ...current, hostname: event.target.value }))} placeholder="R3" />
              </Field>
              <Field label="Management Address">
                <Input value={form.managementAddress} onChange={(event) => setForm((current) => ({ ...current, managementAddress: event.target.value }))} placeholder="172.22.45.250" />
              </Field>
              <Field label="Vendor">
                <Select value={form.vendor} onValueChange={(value) => setForm((current) => ({ ...current, vendor: value as DeviceFormState['vendor'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cisco">Cisco</SelectItem>
                    <SelectItem value="mikrotik">MikroTik</SelectItem>
                    <SelectItem value="aruba">Aruba</SelectItem>
                    <SelectItem value="linux">Linux</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Platform">
                <Input value={form.platform} onChange={(event) => setForm((current) => ({ ...current, platform: event.target.value }))} placeholder="ios / routeros / aos-cx" />
              </Field>
              <Field label="Device Type">
                <Select value={form.deviceType} onValueChange={(value) => setForm((current) => ({ ...current, deviceType: value as DeviceFormState['deviceType'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="virtual">Virtual</SelectItem>
                    <SelectItem value="physical">Physical</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Transport">
                <Select value={form.transport} onValueChange={(value) => setForm((current) => ({ ...current, transport: value as DeviceFormState['transport'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ssh">SSH</SelectItem>
                    <SelectItem value="api">API</SelectItem>
                    <SelectItem value="netconf">NETCONF</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Status">
                <Select value={form.status} onValueChange={(value) => setForm((current) => ({ ...current, status: value as DeviceFormState['status'] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="warning">Warning</SelectItem>
                    <SelectItem value="offline">Offline</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Model">
                <Input value={form.model} onChange={(event) => setForm((current) => ({ ...current, model: event.target.value }))} placeholder="IOSv / CHR / AOS-CX" />
              </Field>
              <Field label="Serial">
                <Input value={form.serial} onChange={(event) => setForm((current) => ({ ...current, serial: event.target.value }))} placeholder="Optional" />
              </Field>
              <Field label="Lab">
                <Input value={form.lab} onChange={(event) => setForm((current) => ({ ...current, lab: event.target.value }))} placeholder="Backend Inventory" />
              </Field>
              <Field label="Console Host">
                <Input value={form.consoleHost} onChange={(event) => setForm((current) => ({ ...current, consoleHost: event.target.value }))} placeholder="172.22.46.196" />
              </Field>
              <Field label="Console Port">
                <Input value={form.consolePort} onChange={(event) => setForm((current) => ({ ...current, consolePort: event.target.value }))} placeholder="5006" inputMode="numeric" />
              </Field>
              <Field label="OS Version">
                <Input value={form.osVersion} onChange={(event) => setForm((current) => ({ ...current, osVersion: event.target.value }))} placeholder="15.6 / RouterOS 7.x" />
              </Field>
              <Field label="Uptime">
                <Input value={form.uptime} onChange={(event) => setForm((current) => ({ ...current, uptime: event.target.value }))} placeholder="1d 2h" />
              </Field>
              <Field label="Privilege Level">
                <Input value={form.privilegeLevel} onChange={(event) => setForm((current) => ({ ...current, privilegeLevel: event.target.value }))} placeholder="15 / full" />
              </Field>
              <Field label="Tags">
                <Input value={form.tags} onChange={(event) => setForm((current) => ({ ...current, tags: event.target.value }))} placeholder="lab, core, cisco" />
              </Field>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditOpen(false)} disabled={editSubmitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={editSubmitting}>
                {editSubmitting ? 'Saving...' : 'Update Device'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={deleteOpen}
        onOpenChange={(open) => {
          setDeleteOpen(open)
          if (!open) setDeletingDevice(null)
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Device</DialogTitle>
            <DialogDescription>
              {deletingDevice
                ? `Delete ${deletingDevice.hostname} (${deletingDevice.id}) from backend inventory? This action cannot be undone.`
                : 'Delete this device from backend inventory?'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setDeleteOpen(false)} disabled={deleteSubmitting}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deleteSubmitting || !deletingDevice}
              onClick={async () => {
                if (!deletingDevice) return
                setDeleteSubmitting(true)
                try {
                  await deleteDevice(deletingDevice.id)
                  await mutate()
                  toast.success('Device deleted successfully')
                  setDeleteOpen(false)
                  setDeletingDevice(null)
                } catch (error) {
                  toast.error(error instanceof Error ? error.message : 'Failed to delete device')
                } finally {
                  setDeleteSubmitting(false)
                }
              }}
            >
              {deleteSubmitting ? 'Deleting...' : 'Delete Device'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function EdgeRuntimeList({
  statuses,
  isLoading,
  hasError,
}: {
  statuses: EdgeRuntimeStatus[]
  isLoading: boolean
  hasError: boolean
}) {
  const navigate = useNavigate()
  if (isLoading && statuses.length === 0) return <LoadingState rows={3} />
  if (hasError && statuses.length === 0) return <ErrorState message="Failed to load live Edge sessions." />
  if (statuses.length === 0) return <EmptyState title="No active Edge sessions found." />

  return (
    <div className="overflow-hidden rounded-2xl border border-border/70 bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border/70 px-4 py-3">
        <div>
          <p className="font-medium">Active Edge connectors</p>
          <p className="text-xs text-muted-foreground">Koneksi customer LAN yang sedang terhubung ke Central.</p>
        </div>
        <Cable className="size-4 text-muted-foreground" />
      </div>
      <div className="overflow-x-auto">
      <Table className="min-w-[1180px]">
        <TableHeader>
          <TableRow>
            <TableHead>Edge ID</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>OS</TableHead>
            <TableHead>Management IP</TableHead>
            <TableHead>MAC address</TableHead>
            <TableHead>CPU</TableHead>
            <TableHead>Memory</TableHead>
            <TableHead>Latency</TableHead>
            <TableHead>Control channel</TableHead>
            <TableHead>Boot ID</TableHead>
            <TableHead>Last heartbeat</TableHead>
            <TableHead>Session age</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {statuses.map((edge) => (
            <TableRow key={edge.edge_id} className="hover:bg-muted/40">
              <TableCell className="whitespace-nowrap font-medium">{edge.edge_id}</TableCell>
              <TableCell><StatusBadge status={edge.status} /></TableCell>
              <TableCell>{edge.os || '—'}</TableCell>
              <TableCell className="font-mono text-xs">{edge.management_ip || '—'}</TableCell>
              <TableCell className="font-mono text-xs">{edge.mac_address || '—'}</TableCell>
              <TableCell className="whitespace-nowrap">{formatEdgeMetric(edge.cpu_percent, '%')}</TableCell>
              <TableCell className="whitespace-nowrap">{formatEdgeMetric(edge.memory_percent, '%')}</TableCell>
              <TableCell className="whitespace-nowrap">{formatEdgeMetric(edge.latency_ms, ' ms')}</TableCell>
              <TableCell>{edge.ready && edge.status === 'online' ? 'Ready / online' : 'Offline'}</TableCell>
              <TableCell className="font-mono text-xs">{edge.boot_id || '-'}</TableCell>
              <TableCell className="whitespace-nowrap">{edge.last_seen ? new Date(edge.last_seen).toLocaleString() : '-'}</TableCell>
              <TableCell className="whitespace-nowrap">{Math.round(edge.age_seconds)}s / {edge.ttl_seconds}s</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end">
                  <DropdownMenu modal={false}>
                    <DropdownMenuTrigger className="inline-flex size-8 items-center justify-center rounded-md border border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground" aria-label={`Actions for ${edge.edge_id}`} title="Actions">
                      <MoreHorizontal className="size-4" />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <DropdownMenuItem className="flex items-center gap-2" onClick={() => navigate(`/devices/edge/${encodeURIComponent(edge.edge_id)}`)}>
                        <Eye className="size-4" /> Open
                      </DropdownMenuItem>
                      <DropdownMenuItem className="flex items-center gap-2" onClick={() => navigate('/terminal', { state: { deviceId: edge.edge_id } })}>
                        <Terminal className="size-4" /> SSH
                      </DropdownMenuItem>
                      <DropdownMenuItem className="flex items-center gap-2" onClick={() => navigate('/terminal', { state: { deviceId: edge.edge_id } })}>
                        <Play className="size-4" /> Run command
                      </DropdownMenuItem>
                      <DropdownMenuItem className="flex items-center gap-2" onClick={() => navigate('/configurations', { state: { deviceId: edge.edge_id } })}>
                        <ServerCog className="size-4" /> Configure
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      </div>
    </div>
  )
}

function formatEdgeMetric(value: number | null | undefined, suffix: string) {
  return typeof value === 'number' && Number.isFinite(value) ? `${Math.round(value * 10) / 10}${suffix}` : '—'
}

export default DevicesPage

function ScopeCard({ active, title, detail, count, onClick }: { active: boolean; title: string; detail: string; count: number; onClick: () => void }) {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      className={`h-auto min-h-[86px] items-start justify-between rounded-2xl border-border/70 p-4 text-left shadow-sm transition-colors hover:border-primary/50 hover:bg-muted/30 ${active ? 'border-primary bg-primary/5 ring-1 ring-primary/20' : ''}`}
    >
      <span className="flex items-start gap-3">
        <span className={`mt-0.5 rounded-lg p-2 ${active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>
          {title.startsWith('Edge') ? <Cable className="size-4" /> : <Globe2 className="size-4" />}
        </span>
        <span className="grid gap-1">
          <span className="font-semibold">{title}</span>
          <span className="text-xs font-normal text-muted-foreground">{detail}</span>
        </span>
      </span>
      <span className="rounded-full bg-muted px-2.5 py-1 text-lg font-semibold tabular-nums">{count}</span>
    </Button>
  )
}

function inferDeviceSource(device: Device): NonNullable<Device['source']> {
  if (device.executionLocation === 'EDGE' || device.edgeId) return 'edge'
  if (device.deviceType === 'virtual' || device.tags.some((tag) => ['gns3', 'gns3-chr', 'm1', 'm3'].includes(tag.toLowerCase()))) return 'gns3'
  return 'direct'
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <Label className="text-xs font-medium text-muted-foreground">{label}</Label>
      {children}
    </div>
  )
}

function deviceToForm(device: Device): DeviceFormState {
  return {
    id: device.id,
    hostname: device.hostname,
    managementAddress: device.managementIp,
    vendor: device.vendor,
    platform: device.platform,
    transport: device.connection.protocol,
    status: device.status === 'unknown' ? 'warning' : device.status === 'offline' ? 'offline' : 'active',
    deviceType: device.deviceType,
    model: device.model,
    serial: device.serial,
    lab: device.lab,
    consoleHost: '',
    consolePort: '',
    osVersion: device.osVersion,
    uptime: device.uptime,
    privilegeLevel: device.connection.privilegeLevel,
    tags: device.tags.join(', '),
  }
}
