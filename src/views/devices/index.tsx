import { useState, type ReactNode } from 'react'
import { createDevice, deleteDevice, updateDevice, useDevices } from 'src/api/network'
import { DeviceStatusTable } from 'src/components/network/device-status-table'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import { toast } from 'sonner'
import { Button } from 'src/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from 'src/components/ui/dialog'
import { Input } from 'src/components/ui/input'
import { Label } from 'src/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import type { Device } from 'src/types/network'

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
  const { data, error, isLoading, mutate } = useDevices()
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [editSubmitting, setEditSubmitting] = useState(false)
  const [deleteSubmitting, setDeleteSubmitting] = useState(false)
  const [editingDevice, setEditingDevice] = useState<Device | null>(null)
  const [deletingDevice, setDeletingDevice] = useState<Device | null>(null)
  const [form, setForm] = useState<DeviceFormState>(() => createEmptyDeviceForm())

  if (isLoading) {
    return <LoadingState rows={6} />
  }

  if (error) {
    return <ErrorState message="Failed to load device inventory." />
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Devices</h1>
        <p className="text-sm text-muted-foreground">Inventory, SSH reachability, vendor platform, and lab context.</p>
      </div>
      <DeviceStatusTable
        devices={data?.data ?? []}
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

export default DevicesPage

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
