import { Badge } from 'src/components/ui/badge'
import { cn } from 'src/lib/utils'
import type { DeviceStatus, Vendor } from 'src/types/network'

export type LifecycleStatus = 'running' | 'stopped' | 'degraded' | 'online' | 'offline' | 'warning' | 'unknown'

const vendorLabels: Record<Vendor, string> = {
  cisco: 'Cisco',
  mikrotik: 'MikroTik',
  aruba: 'Aruba',
  linux: 'Linux',
  other: 'Other',
}

const vendorClasses: Record<Vendor, string> = {
  cisco: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  mikrotik: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  aruba: 'border-orange-500/30 bg-orange-500/10 text-orange-700 dark:text-orange-300',
  linux: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300',
  other: 'border-muted-foreground/30 bg-muted text-muted-foreground',
}

const statusClasses: Record<DeviceStatus, string> = {
  online: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  offline: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  unknown: 'border-muted-foreground/30 bg-muted text-muted-foreground',
}

const lifecycleClasses: Record<LifecycleStatus, string> = {
  running: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  online: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  stopped: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
  offline: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
  degraded: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  warning: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  unknown: 'border-muted-foreground/30 bg-muted text-muted-foreground',
}

export function VendorBadge({ vendor }: { vendor: Vendor }) {
  return (
    <Badge variant="outline" className={cn('capitalize', vendorClasses[vendor])}>
      {vendorLabels[vendor]}
    </Badge>
  )
}

export function StatusBadge({ status }: { status: DeviceStatus }) {
  return (
    <Badge variant="outline" className={cn('capitalize', statusClasses[status])}>
      {status}
    </Badge>
  )
}

export function LifecycleBadge({ status }: { status: LifecycleStatus }) {
  const label =
    status === 'online' ? 'Online' :
    status === 'offline' ? 'Offline' :
    status === 'running' ? 'Running' :
    status === 'stopped' ? 'Stopped' :
    status === 'degraded' ? 'Degraded' :
    status === 'warning' ? 'Warning' :
    'Unknown'

  return (
    <Badge variant="outline" className={cn('capitalize', lifecycleClasses[status])}>
      {label}
    </Badge>
  )
}
