import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { executeBackendCapability, useDevices, useEdgeLiveObservations, useEdgeRuntimeStatuses } from 'src/api/network'
import { DeviceStatusTable } from 'src/components/network/device-status-table'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { StatusBadge } from 'src/components/network/status-badge'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import type { Device, OpenPort } from 'src/types/network'

export default function EdgeDetailPage() {
  const { edgeId } = useParams()
  const decodedEdgeId = edgeId ? decodeURIComponent(edgeId) : ''
  const { data: statuses, isLoading: statusesLoading, error: statusesError } = useEdgeRuntimeStatuses()
  const { data: devices, isLoading: devicesLoading, error: devicesError } = useDevices()
  const { data: liveObservations, isLoading: observationsLoading, error: observationsError } = useEdgeLiveObservations(decodedEdgeId || undefined)
  const [telemetries, setTelemetries] = useState<Record<string, Record<string, unknown>>>({})
  const [telemetryLoading, setTelemetryLoading] = useState(false)
  const edge = statuses?.find((item) => item.edge_id === decodedEdgeId)
  const liveReachable = (liveObservations ?? []).filter((item) => item.fresh && ['arp', 'icmp', 'ssh', 'snmp', 'api', 'service'].includes(item.source))
  const edgeDevices = (devices?.data ?? []).filter((device) => device.edgeId === decodedEdgeId && device.tags.includes('native-alpine')).map((device) => {
    const openPorts = openPortsForIp(liveObservations ?? [], device.managementIp)
    const managementIp = String(device.managementIp ?? '').trim()
    const serial = String(device.serial ?? '').trim().toLowerCase()
    const match = liveReachable.find((observation) => {
      const observedIp = String(observation.subject.ip ?? observation.subject.address ?? '').trim()
      const observedMac = String(observation.subject.mac ?? observation.subject.mac_address ?? '').trim().toLowerCase()
      return (managementIp && observedIp === managementIp) || (serial && observedMac === serial)
    })
    if (!match) {
      return { ...device, openPorts, status: device.tags.includes('topology-only') ? 'warning' as const : 'offline' as const, edgeStatus: edge?.status, edgeLastSeen: edge?.last_seen }
    }
    return { ...device, openPorts, status: 'online' as const, lastSeen: `live Edge (${match.source})`, edgeStatus: edge?.status, edgeLastSeen: edge?.last_seen }
  })

  const discoveredDevices = buildDiscoveredDevices(liveObservations ?? [], decodedEdgeId, edge)
  const managedTargets = edgeDevices.filter((device) => device.vendor !== 'other' && device.managementIp !== 'layer2-only')
  const telemetryTargets = managedTargets.length > 0
    ? managedTargets
    : discoveredDevices.filter((device) => device.managementIp !== 'layer2-only').slice(0, 8)
  const telemetryTarget = telemetryTargets[0]
  const telemetryTargetKey = telemetryTargets.map((device) => device.id).join('|')
  const pollTelemetry = useCallback(async () => {
    if (telemetryTargets.length === 0) return
    setTelemetryLoading(true)
    try {
      const results = await Promise.allSettled(telemetryTargets.map(async (target) => ({
        deviceId: target.id,
        result: await executeBackendCapability({
          deviceId: target.id,
          capability: 'device.read.telemetry',
          credentialRef: credentialRefForTelemetry(decodedEdgeId, target),
          edgeId: decodedEdgeId,
          customerId: target.customerId,
          siteId: target.siteId,
          parameters: telemetryOids(target.vendor),
        }),
      })))
      const successful = results.flatMap((result) => result.status === 'fulfilled' ? [result.value] : [])
      if (successful.length > 0) {
        setTelemetries((previous) => Object.fromEntries([
          ...Object.entries(previous),
          ...successful.map((item) => [item.deviceId, item.result]),
        ]))
      }
    } catch {
      // Keep the last known table values when a bounded background poll fails.
    } finally {
      setTelemetryLoading(false)
    }
  }, [decodedEdgeId, telemetryTargetKey])

  const tableDevices = [...edgeDevices, ...discoveredDevices].map((device) => {
    const telemetry = telemetries[device.id]
    if (!telemetry) return device
    const data = telemetryData(telemetry)
    return {
      ...device,
      cpu: numberOrDefault(data.cpu_percent, device.cpu),
      memory: numberOrDefault(data.memory_percent, device.memory),
      latencyMs: numberOrFallback(data.latency_ms, device.latencyMs),
      platform: typeof data.sys_descr === 'string' && data.sys_descr ? 'ios' : device.platform,
      lastSeen: typeof data.polled_at === 'string' ? `live SNMP (${new Date(data.polled_at).toLocaleTimeString()})` : device.lastSeen,
    }
  })
  const displayDevices = tableDevices
    .sort((left, right) => Number(right.status === 'online') - Number(left.status === 'online'))
    .filter((device, index, all) => all.findIndex((candidate) => candidate.managementIp === device.managementIp && candidate.serial === device.serial) === index)

  useEffect(() => {
    if (edge?.status !== 'online' || !telemetryTarget) return
    void pollTelemetry()
    const timer = window.setInterval(() => void pollTelemetry(), 60_000)
    return () => window.clearInterval(timer)
  }, [edge?.status, pollTelemetry, telemetryTargetKey])

  if (statusesLoading && !statuses) return <LoadingState rows={5} />
  if (statusesError && !statuses) return <ErrorState message="Failed to load Edge status." />
  if (!edge) return <EmptyState title="Edge session tidak ditemukan atau sudah offline." />

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" nativeButton={false} render={<Link to="/devices" />}>
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold">{decodedEdgeId}</h1>
              <StatusBadge status={edge.status} />
            </div>
        <p className="text-sm text-muted-foreground">Perangkat dan status berdasarkan observasi live dari Edge.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={pollTelemetry} disabled={telemetryLoading || edge.status !== 'online'}>
            {telemetryLoading && <Loader2 className="size-4 animate-spin" />}
            Poll SNMP telemetry
          </Button>
          {devicesLoading && <Loader2 className="size-4 animate-spin text-muted-foreground" />}
        </div>
      </div>

      <Card>
        <CardHeader className="border-b">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Edge Runtime</CardTitle>
            <Badge variant="outline">{edge.ready && edge.status === 'online' ? 'CONTROL READY' : 'OFFLINE'}</Badge>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 py-5 sm:grid-cols-2 lg:grid-cols-4">
          <RuntimeValue label="Edge ID" value={edge.edge_id} />
          <RuntimeValue label="Boot ID" value={edge.boot_id || '-'} />
          <RuntimeValue label="Last heartbeat" value={edge.last_seen ? new Date(edge.last_seen).toLocaleString() : '-'} />
          <RuntimeValue label="Session age" value={`${Math.round(edge.age_seconds)}s / ${edge.ttl_seconds}s`} />
        </CardContent>
      </Card>

      {devicesError ? (
        <ErrorState message="Failed to load devices for this Edge." />
      ) : observationsError ? (
        <ErrorState message="Failed to load live discovery observations." />
      ) : displayDevices.length > 0 ? (
        <DeviceStatusTable devices={displayDevices} allowManagementActions={false} />
      ) : devicesLoading || observationsLoading ? (
        <LoadingState rows={4} />
      ) : (
        <EmptyState title="Belum ada perangkat yang terdaftar pada Edge ini." />
      )}

      <LiveObservationTable observations={liveObservations ?? []} />
    </div>
  )
}

function telemetryOids(vendor: string): Record<string, string> {
  if (vendor === 'cisco') {
    return {
      cpu_oid: '1.3.6.1.4.1.9.2.1.58.0',
      memory_percent_oid: '1.3.6.1.4.1.9.9.48.1.1.1.8.1',
    }
  }
  if (vendor === 'mikrotik') {
    return {
      // OIDs reported by `/system resource print oid` on the lab CHR.
      cpu_oid: '1.3.6.1.2.1.25.3.3.1.2.1',
      memory_used_oid: '1.3.6.1.2.1.25.2.3.1.6.65536',
      memory_total_oid: '1.3.6.1.2.1.25.2.3.1.5.65536',
    }
  }
  return {}
}

function credentialRefForTelemetry(edgeId: string, device: Device): string {
  if (device.id === 'r1-native-edge001' || edgeId === 'edge-001') return 'r1-lab'
  if (device.id === 'mt1-native-edge001') return 'mt1-lab'
  if (edgeId === 'edge-002') return 'b-r1'
  return 'r2-lab'
}

function buildDiscoveredDevices(observations: NonNullable<ReturnType<typeof useEdgeLiveObservations>['data']>, edgeId: string, edge?: { status: 'online' | 'offline'; last_seen: string }): Device[] {
  const discovered: Array<Device | null> = observations
    .filter((observation) => ['arp', 'icmp', 'snmp', 'api', 'ssh'].includes(observation.source))
    .map((observation, index) => {
      const ip = String(observation.subject.ip ?? observation.subject.address ?? '')
      const mac = String(observation.subject.mac ?? '')
      if (!ip || ip.includes('/')) return null
      const hint = String(observation.attributes.vendor_hint ?? '').toLowerCase()
      const serviceIdentity = inferServiceIdentity(observations, ip)
      const vendor = normalizeDiscoveredVendor(`${hint} ${serviceIdentity.vendorHint}`, mac)
      const serviceHint = observations.find((candidate) => candidate.source === 'service' && String(candidate.subject.ip ?? '') === ip)
      const inferredPlatform = serviceIdentity.platform || String(serviceHint?.attributes.platform_hint ?? observation.attributes.platform_hint ?? 'unknown')
      const inferredModel = serviceIdentity.model || shortModel(String(serviceHint?.attributes.model_hint ?? observation.attributes.model_hint ?? 'Unknown'))
      const online = observation.fresh && edge?.status === 'online'
      return {
        id: `discovered-${edgeId}-${ip}-${mac || index}`,
        hostname: observation.attributes.hostname ? String(observation.attributes.hostname) : ip,
        vendor,
        model: shortModel(String(observation.attributes.model ?? inferredModel)),
        platform: String(observation.attributes.platform ?? inferredPlatform),
        managementIp: ip,
        status: online ? 'online' : 'offline',
        cpu: 0,
        memory: 0,
        latencyMs: null,
        openPorts: openPortsForIp(observations, ip),
        lastSeen: online ? `live Edge (${observation.source})` : 'offline / stale',
        lab: 'Edge Discovery',
        tags: ['native-alpine', 'discovered', online ? 'online' : 'stale'],
        osVersion: '-',
        uptime: '-',
        serial: mac || `discovered-${ip}`,
        deviceType: 'physical',
        connection: { protocol: observation.source === 'snmp' ? 'api' : 'ssh', status: online ? 'connected' : 'disconnected', lastLogin: '-', authMethod: 'password', privilegeLevel: '-' },
        executionLocation: 'EDGE',
        edgeId,
        edgeStatus: edge?.status,
        edgeLastSeen: edge?.last_seen,
        source: 'edge',
      } as Device
    })
  return discovered.filter((device): device is Device => device !== null)
}

function openPortsForIp(observations: NonNullable<ReturnType<typeof useEdgeLiveObservations>['data']>, ip: string): OpenPort[] {
  if (!ip) return []
  const ports = observations
    .filter((observation) => observation.source === 'service' && observation.fresh && String(observation.subject.ip ?? '') === ip)
    .map((observation) => {
      const port = Number(observation.attributes.port)
      const service = String(observation.attributes.service ?? 'tcp')
      if (!Number.isInteger(port) || port < 1 || port > 65535) return null
      const banner = typeof observation.attributes.banner_hint === 'string' ? observation.attributes.banner_hint : ''
      return banner ? { port, service, banner } : { port, service }
    })
    .filter((item): item is OpenPort => item !== null)
  return Array.from(new Map(ports.map((item) => [item.port, item])).values()).sort((a, b) => a.port - b.port)
}

function inferServiceIdentity(observations: NonNullable<ReturnType<typeof useEdgeLiveObservations>['data']>, ip: string): { vendorHint: string; platform: string; model: string } {
  const services = observations.filter((observation) => observation.source === 'service' && observation.fresh && String(observation.subject.ip ?? '') === ip)
  const ports = new Set(services.map((observation) => Number(observation.attributes.port)))
  const banners = services.map((observation) => String(observation.attributes.banner_hint ?? '').toLowerCase()).join(' ')
  if (ports.has(139) || ports.has(3389) || ports.has(5985) || banners.includes('microsoft') || banners.includes('windows')) {
    return { vendorHint: 'microsoft', platform: 'windows', model: 'Windows' }
  }
  if (ports.has(8291) || ports.has(8728) || ports.has(8729) || banners.includes('routeros')) {
    return { vendorHint: 'mikrotik', platform: 'routeros', model: 'RouterOS' }
  }
  if (banners.includes('cisco')) return { vendorHint: 'cisco', platform: 'cisco-ios', model: 'Cisco IOS' }
  if (banners.includes('d-link') || banners.includes('dlink')) return { vendorHint: 'd-link', platform: 'network-device', model: 'D-Link' }
  return { vendorHint: '', platform: '', model: '' }
}

function shortModel(value: string): string {
  return value
    .replace(/\s*\(model unavailable\)/gi, '')
    .replace(/\s*\(inferred\)/gi, '')
    .trim() || 'Unknown'
}

function normalizeDiscoveredVendor(value: string, mac = ''): Device['vendor'] {
  if (value.includes('cisco')) return 'cisco'
  if (value.includes('mikrotik') || value.includes('routeros')) return 'mikrotik'
  if (value.includes('aruba') || value.includes('hewlett')) return 'aruba'
  if (value.includes('linux')) return 'linux'
  if (['0c:f5:2c', '0c:e7:ee', '0c:22:59'].some((prefix) => mac.toLowerCase().startsWith(prefix))) return 'cisco'
  if (mac.toLowerCase().startsWith('0c:28:e5')) return 'mikrotik'
  return 'other'
}

function telemetryData(value: Record<string, unknown>): Record<string, unknown> {
  const attempt = asRecord(value.attempt)
  const result = asRecord(attempt.result ?? value.result ?? value.output)
  return asRecord(result.data ?? value.data)
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function numberOrFallback(value: unknown, fallback: number | null): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function numberOrDefault(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function LiveObservationTable({ observations }: { observations: NonNullable<ReturnType<typeof useEdgeLiveObservations>['data']> }) {
  const latestByEvidence = new Map<string, typeof observations[number]>()
  for (const item of observations) {
    if (!(item.subject.ip || item.subject.address || item.subject.mac)) continue
    const subject = String(item.subject.ip ?? item.subject.address ?? item.subject.mac ?? '').trim().toLowerCase()
    // The summary table is one row per IP/source. Individual service ports
    // remain available in the device table and in the retained backend evidence.
    const key = `${item.source}:${subject}`
    const previous = latestByEvidence.get(key)
    if (!previous || Number(item.fresh) > Number(previous.fresh) || (item.fresh === previous.fresh && item.age_seconds < previous.age_seconds)) {
      latestByEvidence.set(key, item)
    }
  }
  const rows = Array.from(latestByEvidence.values())
    .sort((a, b) => Number(b.fresh) - Number(a.fresh) || a.age_seconds - b.age_seconds)
  if (rows.length === 0) return null

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle>Live Edge Observations</CardTitle>
        <p className="text-sm text-muted-foreground">Observasi terbaru per IP, sumber, dan port dari Edge; riwayat tetap tersimpan untuk audit.</p>
      </CardHeader>
      <CardContent className="py-5">
        <div className="overflow-x-auto rounded-lg border border-border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>IP / Address</TableHead>
                <TableHead>MAC</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Vendor hint</TableHead>
                <TableHead>State</TableHead>
                <TableHead>Freshness</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((item) => (
                <TableRow key={item.observation_id}>
                  <TableCell className="font-mono text-xs">{String(item.subject.ip ?? item.subject.address ?? '-')}</TableCell>
                  <TableCell className="font-mono text-xs">{String(item.subject.mac ?? '-')}</TableCell>
                  <TableCell className="uppercase">{item.source}</TableCell>
                  <TableCell>{String(item.attributes.vendor_hint ?? item.attributes.device_class_hint ?? '-')}</TableCell>
                  <TableCell>{item.fresh ? 'ONLINE / FRESH' : 'STALE'}</TableCell>
                  <TableCell>{item.fresh ? `${Math.round(item.age_seconds)}s / ${item.ttl_seconds}s` : 'expired'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}

function RuntimeValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
    </div>
  )
}
