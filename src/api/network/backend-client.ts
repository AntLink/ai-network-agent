import type {
  AgentMessage,
  Alert,
  ApiResponse,
  AuditLog,
  Backup,
  Configuration,
  ConfigApplyResult,
  ConfigPlan,
  CredentialProfile,
  DashboardSummary,
  Device,
  DeviceStatus,
  DiscoveryResult,
  ExecutionPlan,
  HealthPoint,
  Lab,
  NetworkInterface,
  NetworkSettings,
  RouteEntry,
  Task,
  TaskStep,
  TaskStatus,
  TerminalCommandResult,
  TerminalLiveSession,
  TerminalSuggestion,
  Topology,
  Vendor,
} from 'src/types/network'

const DEFAULT_API_BASE_URL = 'http://localhost:8000'
const API_TIMEOUT_MS = 12000

type UnknownRecord = Record<string, unknown>

export class ApiClientError extends Error {
  status: number
  detail?: unknown

  constructor(message: string, status: number, detail?: unknown) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.detail = detail
  }
}

export function isBackendApiEnabled() {
  return import.meta.env.VITE_USE_MOCKS !== 'true'
}

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '')
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS)

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })

    const payload = await readJsonSafe(response)

    if (!response.ok) {
      throw new ApiClientError(extractErrorMessage(payload, response.statusText), response.status, payload)
    }

    return payload as T
  } catch (error) {
    if (error instanceof ApiClientError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiClientError(`Backend request timed out after ${API_TIMEOUT_MS}ms`, 408)
    }
    throw new ApiClientError(error instanceof Error ? error.message : 'Backend request failed', 0, error)
  } finally {
    window.clearTimeout(timeout)
  }
}

export async function mockRequest<T>(path: string): Promise<ApiResponse<T>> {
  const response = await fetch(path)
  const payload = await readJsonSafe(response)

  if (!response.ok) {
    throw new ApiClientError(extractErrorMessage(payload, response.statusText), response.status, payload)
  }

  return payload as ApiResponse<T>
}

export async function backendOrMock<T>(backendLoader: () => Promise<T>, mockPath: string): Promise<ApiResponse<T>> {
  if (!isBackendApiEnabled()) {
    return mockRequest<T>(mockPath)
  }

  try {
    return { status: 200, data: await backendLoader() }
  } catch (error) {
    if (import.meta.env.DEV) {
      console.warn(`Backend unavailable for ${mockPath}. Falling back to MSW mock.`, error)
      return mockRequest<T>(mockPath)
    }

    throw error
  }
}

type DeviceMetrics = {
  device_id: string
  status: 'online' | 'offline'
  cpu: number
  memory: number
  latency_ms: number | null
}

export async function loadBackendDeviceStatuses(): Promise<DeviceMetrics[]> {
  try {
    const payload = await apiRequest<unknown>('/api/v1/devices/batch-status')
    return extractArray(payload).map((item: unknown) => {
      const r = asRecord(item)
      return {
        device_id: String(r.device_id ?? ''),
        status: String(r.status ?? 'offline') as 'online' | 'offline',
        cpu: numberValue(r.cpu, 0),
        memory: numberValue(r.memory, 0),
        latency_ms: numberOrNull(r.latency_ms),
      }
    })
  } catch {
    return []
  }
}

export async function loadBackendDevices(): Promise<Device[]> {
  const [devices, statuses] = await Promise.all([
    apiRequest<unknown>('/api/v1/devices'),
    loadBackendDeviceStatuses(),
  ])
  const statusMap = new Map(statuses.map((s) => [s.device_id, s]))

  return extractArray(devices).map((item) => {
    const device = normalizeDevice(item)
    const m = statusMap.get(device.id)
    if (m) {
      device.status = m.status
      device.cpu = m.cpu
      device.memory = m.memory
      device.latencyMs = m.latency_ms
    }
    return device
  })
}

export interface DevicePage {
  devices: Device[]
  total: number
  page: number
  limit: number
  pages: number
}

export async function loadBackendDevicesPage(query: { page?: number; limit?: number }): Promise<DevicePage> {
  const params = new URLSearchParams()
  if (query.page) params.set('page', String(query.page))
  if (query.limit) params.set('limit', String(query.limit))
  const qs = params.toString()

  const [payload, statuses] = await Promise.all([
    apiRequest<unknown>(`/api/v1/devices${qs ? '?' + qs : ''}`),
    loadBackendDeviceStatuses(),
  ])
  const statusMap = new Map(statuses.map((s) => [s.device_id, s]))

  const record = asRecord(payload)
  const rawList = Array.isArray(payload) ? payload : extractArray(record.devices)

  const devices = rawList.map((item) => {
    const device = normalizeDevice(item)
    const m = statusMap.get(device.id)
    if (m) {
      device.status = m.status
      device.cpu = m.cpu
      device.memory = m.memory
      device.latencyMs = m.latency_ms
    }
    return device
  })

  if (Array.isArray(payload)) {
    return { devices, total: devices.length, page: query.page ?? 1, limit: query.limit ?? (devices.length || 25), pages: 1 }
  }
  return {
    devices,
    total: Number(record.total ?? devices.length),
    page: Number(record.page ?? query.page ?? 1),
    limit: Number(record.limit ?? query.limit ?? 25),
    pages: Number(record.pages ?? 1),
  }
}

export async function createBackendDevice(input: {
  id: string
  hostname: string
  managementAddress: string
  vendor: string
  platform: string
  transport?: string
  status?: string
  deviceType?: string
  consoleHost?: string
  consolePort?: number | null
  model?: string
  serial?: string
  lab?: string
  tags?: string[]
  osVersion?: string
  uptime?: string
  privilegeLevel?: string
}): Promise<unknown> {
  return apiRequest<unknown>('/api/v1/devices', {
    method: 'POST',
    body: JSON.stringify({
      id: input.id,
      hostname: input.hostname,
      management_address: input.managementAddress,
      vendor: input.vendor,
      platform: input.platform,
      transport: input.transport ?? 'ssh',
      status: input.status ?? 'active',
      device_type: input.deviceType ?? 'virtual',
      console_host: input.consoleHost || undefined,
      console_port: input.consolePort ?? undefined,
      model: input.model || undefined,
      serial: input.serial || undefined,
      lab: input.lab || undefined,
      tags: input.tags ?? [],
      os_version: input.osVersion || undefined,
      uptime: input.uptime || undefined,
      privilege_level: input.privilegeLevel || undefined,
    }),
  })
}

export async function updateBackendDevice(
  deviceId: string,
  input: {
    id?: string
    hostname?: string
    managementAddress?: string
    vendor?: string
    platform?: string
    transport?: string
    status?: string
    deviceType?: string
    consoleHost?: string
    consolePort?: number | null
    model?: string
    serial?: string
    lab?: string
    tags?: string[]
    osVersion?: string
    uptime?: string
    privilegeLevel?: string
  },
): Promise<unknown> {
  return apiRequest<unknown>(`/api/v1/devices/${encodeURIComponent(deviceId)}`, {
    method: 'PUT',
    body: JSON.stringify({
      id: input.id,
      hostname: input.hostname,
      management_address: input.managementAddress,
      vendor: input.vendor,
      platform: input.platform,
      transport: input.transport,
      status: input.status,
      device_type: input.deviceType,
      console_host: input.consoleHost || undefined,
      console_port: input.consolePort ?? undefined,
      model: input.model || undefined,
      serial: input.serial || undefined,
      lab: input.lab || undefined,
      tags: input.tags ?? undefined,
      os_version: input.osVersion || undefined,
      uptime: input.uptime || undefined,
      privilege_level: input.privilegeLevel || undefined,
    }),
  })
}

export async function deleteBackendDevice(deviceId: string): Promise<unknown> {
  return apiRequest<unknown>(`/api/v1/devices/${encodeURIComponent(deviceId)}`, {
    method: 'DELETE',
  })
}

export async function loadBackendDeviceDetail(deviceId: string): Promise<{
  device: Device
  interfaces: NetworkInterface[]
  routes: RouteEntry[]
}> {
  const [deviceResult, interfacesResult, routesResult, healthResult] = await Promise.allSettled([
    apiRequest<unknown>(`/api/v1/devices/${deviceId}`),
    apiRequest<unknown>(`/api/v1/devices/${deviceId}/interfaces`),
    apiRequest<unknown>(`/api/v1/devices/${deviceId}/routes`),
    apiRequest<unknown>(`/api/v1/devices/${deviceId}/health`),
  ])

  if (deviceResult.status === 'rejected') {
    throw deviceResult.reason
  }

  const health = healthResult.status === 'fulfilled' ? healthResult.value : undefined
  const device = normalizeDevice(deviceResult.value, health)

  return {
    device,
    interfaces: interfacesResult.status === 'fulfilled' ? normalizeInterfaces(interfacesResult.value, device.id) : [],
    routes: routesResult.status === 'fulfilled' ? normalizeRoutes(routesResult.value, device.id) : [],
  }
}

export async function loadBackendActiveLabs(): Promise<{ total: number; gns3: number; containerlab: number }> {
  // GNS3 projects via backend provider. Failure (GNS3 off) -> zeros, never breaks summary.
  try {
    const payload = await apiRequest<unknown>('/api/v1/gns3/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    const projects = extractArray(payload)
    const opened = projects.filter(
      (project) => String(asRecord(project).status ?? '').toLowerCase() === 'opened',
    ).length
    return { total: opened, gns3: opened, containerlab: 0 }
  } catch {
    return { total: 0, gns3: 0, containerlab: 0 }
  }
}

export async function loadBackendDashboardSummary(): Promise<DashboardSummary> {
  const [devicesResult, labsResult] = await Promise.allSettled([
    loadBackendDevices(),
    loadBackendActiveLabs(),
  ])
  const devices = devicesResult.status === 'fulfilled' ? devicesResult.value : []
  const activeLabs =
    labsResult.status === 'fulfilled'
      ? labsResult.value
      : { total: 0, gns3: 0, containerlab: 0 }

  const online = devices.filter((device) => device.status === 'online').length
  const offline = devices.filter((device) => device.status === 'offline').length
  const warning = devices.filter((device) => device.status === 'warning').length
  const known = online + offline + warning
  const score = devices.length ? Math.round(((online + warning * 0.5) / devices.length) * 100) : 0

  return {
    totalDevices: {
      total: devices.length,
      online,
      offline,
      warning: warning + Math.max(0, devices.length - known),
    },
    activeLabs,
    aiOperations: {
      totalToday: 0,
      success: 0,
      running: 0,
      failed: 0,
    },
    networkHealth: {
      score,
      label: score >= 90 ? 'Healthy' : score >= 70 ? 'Degraded' : 'Attention required',
    },
  }
}

export async function loadBackendHealthSeries(range: string): Promise<HealthPoint[]> {
  const devices = await loadBackendDevices()
  const online = devices.filter((device) => device.status === 'online').length
  const offline = devices.filter((device) => device.status === 'offline').length
  const warning = devices.filter((device) => device.status === 'warning').length
  const avgLatency = average(devices.map((device) => device.latencyMs).filter((value): value is number => typeof value === 'number'))
  const points = range === '1H' ? 6 : range === '6H' ? 6 : range === '24H' ? 8 : 7

  return Array.from({ length: points }, (_, index) => ({
    time: makeHealthLabel(range, index, points),
    online,
    offline,
    latency: avgLatency || 0,
    packetLoss: warning ? 0.4 : 0,
    configFailures: 0,
  }))
}

export async function loadBackendTopology(projectId?: string): Promise<Topology> {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
  return normalizeTopology(await apiRequest<unknown>(`/api/v1/topology${qs}`))
}

export async function saveBackendTopology(topology: Topology, projectId?: string): Promise<Topology> {
  return normalizeTopology(await apiRequest<unknown>('/api/v1/topology', {
    method: 'POST',
    body: JSON.stringify({
      data: topology,
      project_id: projectId ?? topology.projectId,
    }),
  }))
}

function normalizeTopology(payload: unknown): Topology {
  const record = asRecord(payload)
  const data = asRecord(record.data ?? record)
  const nodes = extractArray(data.nodes)
  const links = extractArray(data.links)

  return {
    id: stringValue(data.id, 'backend-topology'),
    name: stringValue(data.name, 'Backend Topology'),
    projectId: stringValue(data.projectId ?? data.project_id, '') || undefined,
    layout: normalizeTopologyLayout(data.layout),
    nodes: nodes.map((node, index) => {
      const item = asRecord(node)
      const hostname = stringValue(item.hostname ?? item.name ?? item.label, `Node ${index + 1}`)
      const vendor = normalizeVendor(item.vendor ?? item.type ?? item.platform)
      return {
        id: stringValue(item.id, `node-${index}`),
        hostname,
        vendor,
        kind: normalizeTopologyKind(item.kind ?? item.role ?? item.node_type ?? item.type, vendor, hostname),
        nodeType: normalizeNodeType(item.nodeType ?? item.node_type ?? item.type),
        status: normalizeStatus(item.status),
        ip: managementIp(item),
      }
    }),
    links: links.map((link, index) => {
      const item = asRecord(link)
      return {
        id: stringValue(item.id, `link-${index}`),
        source: stringValue(item.source ?? item.source_id ?? item.node_a, ''),
        target: stringValue(item.target ?? item.target_id ?? item.node_b, ''),
        sourceInterface: stringValue(item.sourceInterface ?? item.source_interface ?? item.interface_a, '-'),
        targetInterface: stringValue(item.targetInterface ?? item.target_interface ?? item.interface_b, '-'),
        status: stringValue(item.status, 'up').toLowerCase() === 'down' ? 'down' : 'up',
      }
    }),
  }
}

function normalizeTopologyKind(input: unknown, vendor: Vendor, hostname: string): Topology['nodes'][number]['kind'] {
  const value = String(input ?? '').toLowerCase()
  if (value === 'router' || value === 'switch' || value === 'host' || value === 'cloud' || value === 'nat' || value === 'firewall' || value === 'loopback' || value === 'other') {
    return value
  }

  const name = hostname.toLowerCase()
  if (name.startsWith('r') || name.includes('router') || vendor === 'mikrotik') return 'router'
  if (name.startsWith('sw') || name.includes('switch') || name.includes('vlan')) return 'switch'
  if (name.startsWith('pc') || name.startsWith('host') || name.includes('vm') || name.includes('server')) return 'host'
  if (name.includes('cloud') || name === 'nat' || name.includes('internet')) return 'cloud'
  return vendor === 'aruba' && name.includes('sw') ? 'switch' : 'other'
}

function normalizeNodeType(value: unknown): Topology['nodes'][number]['nodeType'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized === 'qemu' || normalized === 'vpcs' || normalized === 'dynamips' || normalized === 'cloud' || normalized === 'ethernet_switch' || normalized === 'docker' || normalized === 'other') {
    return normalized
  }
  return 'other'
}

function normalizeTopologyLayout(input: unknown): Record<string, { x: number; y: number }> | undefined {
  const record = asRecord(input)
  const entries = Object.entries(record).filter(([, value]) => {
    const point = asRecord(value)
    return typeof point.x === 'number' && typeof point.y === 'number'
  })

  if (entries.length === 0) return undefined

  return Object.fromEntries(
    entries.map(([id, value]) => {
      const point = asRecord(value)
      return [id, { x: Number(point.x), y: Number(point.y) }]
    })
  )
}

export interface AuditLogFilters {
  actions: string[]
  devices: string[]
  users: string[]
  results: string[]
  sources: string[]
}

export interface AuditLogPage {
  logs: AuditLog[]
  total: number
  page: number
  limit: number
  pages: number
  filters: AuditLogFilters
}

export interface AuditLogQuery {
  page?: number
  limit?: number
  search?: string
  action?: string
  device?: string
  result?: string
  source?: string
  user?: string
}

export async function loadBackendAuditLogs(query: AuditLogQuery = {}): Promise<AuditLogPage> {
  const params = new URLSearchParams()
  if (query.page) params.set('page', String(query.page))
  if (query.limit) params.set('limit', String(query.limit))
  if (query.search) params.set('search', query.search)
  if (query.action) params.set('action', query.action)
  if (query.device) params.set('device', query.device)
  if (query.result) params.set('result', query.result)
  if (query.source) params.set('source', query.source)
  if (query.user) params.set('user', query.user)

  const qs = params.toString()
  const payload = await apiRequest<unknown>(`/api/v1/audit${qs ? '?' + qs : ''}`)
  const record = asRecord(payload)
  const events = extractArray(record.events ?? payload)
  const filters = asRecord(record.filters ?? {})

  return {
    logs: events.map((event, index) => {
      const item = asRecord(event)
      return {
        id: stringValue(item.id, `audit-${index}`),
        time: stringValue(item.time ?? item.timestamp, '-'),
        user: stringValue(item.user, 'system'),
        action: stringValue(item.action, 'Unknown action'),
        device: stringValue(item.device ?? item.device_id, '-'),
        result: normalizeAuditResult(item.result),
        source: normalizeAuditSource(item.source),
        details: stringValue(item.details ?? item.command, '-'),
      }
    }),
    total: Number(record.total ?? 0),
    page: Number(record.page ?? query.page ?? 1),
    limit: Number(record.limit ?? query.limit ?? 25),
    pages: Number(record.pages ?? 1),
    filters: {
      actions: extractArray(filters.actions).map((value) => stringValue(value, '')),
      devices: extractArray(filters.devices).map((value) => stringValue(value, '')),
      users: extractArray(filters.users).map((value) => stringValue(value, '')),
      results: extractArray(filters.results).map((value) => stringValue(value, '')),
      sources: extractArray(filters.sources).map((value) => stringValue(value, '')),
    },
  }
}

export async function runBackendTerminalCommand(device: Device, command: string): Promise<TerminalCommandResult> {
  if (!isBackendApiEnabled()) {
    return {
      deviceId: device.id,
      command,
      status: 'ok',
      endpoint: '/api/network/terminal/session',
      output: [
        `${makePrompt(device)} ${command}`,
        'Mock terminal mode is active. Set VITE_USE_MOCKS=false to call FastAPI.',
        makePrompt(device),
      ],
      raw: null,
    }
  }

  const endpoint = commandEndpointForDevice(device)
  const payload = endpoint.includes('/console/exec') ? { command } : { commands: [command] }

  try {
    const response = await apiRequest<unknown>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    })

    return {
      deviceId: device.id,
      command,
      status: normalizeCommandStatus(response),
      endpoint,
      output: normalizeCommandOutput(response, device, command),
      raw: response,
    }
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 403) {
      return {
        deviceId: device.id,
        command,
        status: 'blocked',
        endpoint,
        output: [
          `${makePrompt(device)} ${command}`,
          'BLOCKED: Direct command endpoint is disabled by backend policy.',
          'Use config plan/policy/apply workflow for write-capable operations.',
          makePrompt(device),
        ],
        raw: error.detail,
      }
    }

    throw error
  }
}

export async function createBackendTerminalSession(deviceId: string): Promise<TerminalLiveSession> {
  const response = await apiRequest<unknown>('/api/v1/terminal/sessions', {
    method: 'POST',
    body: JSON.stringify({ device_id: deviceId }),
  })

  return normalizeTerminalLiveSession(asRecord(response).data ?? response)
}

export async function closeBackendTerminalSession(sessionId: string): Promise<void> {
  await apiRequest<unknown>(`/api/v1/terminal/sessions/${sessionId}`, {
    method: 'DELETE',
  })
}

export async function sendBackendTerminalInput(sessionId: string, data: string): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>(`/api/v1/terminal/sessions/${sessionId}/input`, {
    method: 'POST',
    body: JSON.stringify({ data }),
  })
}

export async function executeBackendTerminalSessionCommand(session: TerminalLiveSession, command: string): Promise<TerminalCommandResult> {
  const response = await apiRequest<unknown>(`/api/v1/terminal/sessions/${session.sessionId}/execute`, {
    method: 'POST',
    body: JSON.stringify({ command }),
  })
  const data = asRecord(response).data ?? response

  return {
    deviceId: session.deviceId,
    command,
    status: normalizeCommandStatus(response),
    endpoint: `/api/v1/terminal/sessions/${session.sessionId}/execute`,
    output: normalizeLiveTerminalOutput(data, session, command),
    raw: response,
  }
}

export async function suggestBackendTerminalCommand(sessionId: string, partial: string): Promise<TerminalSuggestion[]> {
  const response = await apiRequest<unknown>(`/api/v1/terminal/sessions/${sessionId}/suggest`, {
    method: 'POST',
    body: JSON.stringify({ partial }),
  })
  const data = asRecord(response).data ?? response
  return extractArray(asRecord(data).suggestions).map((item) => {
    const record = asRecord(item)
    return {
      value: stringValue(record.value, ''),
      description: stringValue(record.description, ''),
    }
  }).filter((item) => item.value)
}

export async function createBackendConfigPlan(input: {
  deviceId: string
  commands: string[]
  verify?: Array<{ command: string; expect?: string }>
  saveOnSuccess?: boolean
  description?: string
}): Promise<ConfigPlan> {
  const response = await apiRequest<unknown>('/api/v1/config/plan', {
    method: 'POST',
    body: JSON.stringify({
      device_id: input.deviceId,
      commands: input.commands,
      verify: input.verify ?? [],
      save_on_success: input.saveOnSuccess ?? false,
      description: input.description ?? '',
    }),
  })

  return normalizeConfigPlan(response)
}

export async function getBackendConfigPlan(planId: string): Promise<ConfigPlan> {
  return normalizeConfigPlan(await apiRequest<unknown>(`/api/v1/config/plans/${planId}`))
}

export async function applyBackendConfigPlan(planId: string, approvedBy: string): Promise<ConfigApplyResult> {
  const response = await apiRequest<unknown>('/api/v1/config/apply', {
    method: 'POST',
    body: JSON.stringify({
      plan_id: planId,
      approved_by: approvedBy,
    }),
  })
  const record = asRecord(response)

  return {
    planId,
    approvedBy,
    status: stringValue(record.status, 'applied'),
    output: extractOutputLines(record.output ?? record.report ?? response),
    raw: response,
  }
}

export async function rollbackBackendConfigPlan(input: {
  deviceId: string
  planId?: string
  backupId?: string
}): Promise<ConfigApplyResult> {
  const response = await apiRequest<unknown>('/api/v1/config/rollback', {
    method: 'POST',
    body: JSON.stringify({
      device_id: input.deviceId,
      plan_id: input.planId ?? undefined,
      backup_id: input.backupId ?? undefined,
    }),
  })
  const record = asRecord(response)

  return {
    planId: stringValue(record.plan_id ?? record.planId ?? input.planId ?? '', ''),
    approvedBy: stringValue(record.approved_by ?? record.approvedBy ?? 'system', 'system'),
    status: stringValue(record.status, 'rolled_back'),
    output: extractOutputLines(record.output ?? record.report ?? response),
    raw: response,
  }
}

function normalizeDevice(input: unknown, healthInput?: unknown): Device {
  const item = asRecord(input)
  const health = asRecord(healthInput)
  const id = stringValue(item.id ?? item.device_id, 'unknown-device')
  const hostname = stringValue(item.hostname ?? item.name ?? item.identity, id)
  const vendor = normalizeVendor(item.vendor ?? item.driver ?? item.type ?? item.platform)
  const host = managementIp(item)
  const reachable = typeof health.reachable === 'boolean' ? health.reachable : undefined
  const status = reachable === undefined ? normalizeStatus(item.status) : reachable ? 'online' : 'offline'

  return {
    id,
    hostname,
    vendor,
    model: stringValue(item.model ?? item.kind ?? item.template, vendor === 'other' ? 'Unknown' : vendor),
    platform: stringValue(item.platform ?? item.os ?? item.os_version ?? item.driver, 'Unknown'),
    managementIp: host,
    status,
    cpu: numberValue(item.cpu ?? item.cpu_percent, 0),
    memory: numberValue(item.memory ?? item.memory_percent ?? item.ram, 0),
    latencyMs: numberOrNull(item.latencyMs ?? item.latency_ms ?? item.latency),
    lastSeen: stringValue(item.lastSeen ?? item.last_seen, reachable === false ? 'unreachable' : 'live inventory'),
    lab: stringValue(item.lab ?? item.project ?? item.group, 'Backend Inventory'),
    tags: Array.isArray(item.tags) ? item.tags.map((tag) => String(tag)) : [vendor],
    osVersion: stringValue(item.osVersion ?? item.os_version ?? item.version, 'Unknown'),
    uptime: stringValue(item.uptime, '-'),
    serial: stringValue(item.serial ?? item.serial_number, id),
    deviceType: normalizeDeviceType(item.deviceType ?? item.device_type ?? item.type),
    connection: {
      protocol: normalizeProtocol(item.protocol ?? item.transport),
      status: status === 'online' ? 'connected' : status === 'warning' ? 'degraded' : 'disconnected',
      lastLogin: stringValue(item.lastLogin ?? item.last_login, '-'),
      authMethod: normalizeAuthMethod(item.authMethod ?? item.auth_method),
      privilegeLevel: stringValue(item.privilegeLevel ?? item.privilege_level, vendor === 'mikrotik' ? 'full' : '-'),
    },
  }
}

function commandEndpointForDevice(device: Device) {
  if (device.vendor === 'cisco') return `/api/v1/cisco/${device.id}/exec`
  if (device.vendor === 'mikrotik') return `/api/v1/mikrotik/${device.id}/commands/run`
  return `/api/v1/devices/${device.id}/console/exec`
}

function normalizeConfigPlan(input: unknown): ConfigPlan {
  const item = asRecord(input)
  return {
    planId: stringValue(item.plan_id ?? item.planId, ''),
    deviceId: stringValue(item.device_id ?? item.deviceId, ''),
    commands: extractOutputLines(item.commands),
    verify: extractArray(item.verify).map((verifyItem) => {
      const verify = asRecord(verifyItem)
      return {
        command: stringValue(verify.command, ''),
        expect: typeof verify.expect === 'string' ? verify.expect : null,
      }
    }).filter((verify) => verify.command),
    saveOnSuccess: Boolean(item.save_on_success ?? item.saveOnSuccess),
    description: stringValue(item.description, ''),
    riskLevel: normalizePlanRisk(item.risk_level ?? item.riskLevel),
    status: stringValue(item.status, 'planned'),
    createdAt: stringValue(item.created_at ?? item.createdAt, '-'),
    updatedAt: stringValue(item.updated_at ?? item.updatedAt, '-'),
    report: item.report,
  }
}

function normalizePlanRisk(value: unknown): ConfigPlan['riskLevel'] {
  const normalized = String(value ?? '').toUpperCase()
  if (normalized === 'LOW' || normalized === 'MEDIUM' || normalized === 'HIGH' || normalized === 'CRITICAL') return normalized
  return 'MEDIUM'
}

function normalizeTerminalLiveSession(input: unknown): TerminalLiveSession {
  const item = asRecord(input)
  return {
    sessionId: stringValue(item.session_id ?? item.sessionId, ''),
    deviceId: stringValue(item.device_id ?? item.deviceId, ''),
    hostname: stringValue(item.hostname, '-'),
    vendor: normalizeVendor(item.vendor),
    managementAddress: stringValue(item.management_address ?? item.managementAddress, '-'),
    prompt: stringValue(item.prompt, ''),
    status: normalizeConnectionStatus(item.status),
  }
}

function normalizeConnectionStatus(value: unknown): TerminalLiveSession['status'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('reconnect')) return 'reconnecting'
  if (normalized.includes('disconnect') || normalized.includes('closed')) return 'disconnected'
  return 'connected'
}

function normalizeCommandStatus(input: unknown): TerminalCommandResult['status'] {
  const status = stringValue(asRecord(input).status, 'ok').toLowerCase()
  if (status.includes('applied')) return 'applied'
  if (status.includes('fail') || status.includes('error')) return 'failed'
  return 'ok'
}

function normalizeCommandOutput(input: unknown, device: Device, command: string): string[] {
  const record = asRecord(input)
  const lines = [
    `${makePrompt(device)} ${command}`,
    ...extractOutputLines(record.output ?? record.outputs ?? record.raw ?? record.data ?? input),
    makePrompt(device),
  ]

  return lines.filter((line) => line.trim().length > 0)
}

function normalizeLiveTerminalOutput(input: unknown, session: TerminalLiveSession, command: string): string[] {
  const record = asRecord(input)
  const prompt = record.prompt && typeof record.prompt === 'string' ? record.prompt : session.prompt
  const lines = extractOutputLines(record.output ?? record.raw ?? input)
    .map((line) => line.trimEnd())
    .filter((line) => line.trim().length > 0)

  while (lines.length && prompt && lines[lines.length - 1].trim() === prompt.trim()) {
    lines.pop()
  }

  const firstCommandIndex = lines.findIndex((line) => line.trim() === command.trim())
  if (firstCommandIndex >= 0 && prompt) {
    lines[firstCommandIndex] = `${prompt}${command}`
  } else if (prompt) {
    lines.unshift(`${prompt}${command}`)
  }

  return lines
}

function extractOutputLines(input: unknown): string[] {
  if (Array.isArray(input)) {
    return input.flatMap(extractOutputLines)
  }
  if (typeof input === 'string') {
    return input.split(/\r?\n/)
  }
  if (input && typeof input === 'object') {
    return JSON.stringify(input, null, 2).split(/\r?\n/)
  }
  return [String(input ?? '')]
}

function makePrompt(device: Device) {
  return device.vendor === 'mikrotik' ? `[admin@${device.hostname}] >` : `${device.hostname}#`
}

function normalizeInterfaces(input: unknown, deviceId: string): NetworkInterface[] {
  return extractArray(asRecord(input).interfaces ?? asRecord(input).data ?? input).map((entry, index) => {
    const item = asRecord(entry)
    const name = stringValue(item.name ?? item.interface ?? item.port, `interface-${index}`)
    return {
      id: stringValue(item.id, `${deviceId}-${name}`),
      deviceId,
      name,
      description: stringValue(item.description ?? item.desc, '-'),
      ipAddress: stringValue(item.ipAddress ?? item.ip_address ?? item.address, '-'),
      adminStatus: normalizeUpDown(item.adminStatus ?? item.admin_status ?? item.admin),
      operationalStatus: normalizeUpDown(item.operationalStatus ?? item.operational_status ?? item.status ?? item.link),
      speed: stringValue(item.speed, '-'),
      duplex: stringValue(item.duplex, '-'),
      rx: stringValue(item.rx ?? item.rx_bytes, '-'),
      tx: stringValue(item.tx ?? item.tx_bytes, '-'),
      errors: numberValue(item.errors ?? item.error_count, 0),
    }
  })
}

function normalizeRoutes(input: unknown, deviceId: string): RouteEntry[] {
  return extractArray(asRecord(input).routes ?? asRecord(input).data ?? input).map((entry, index) => {
    const item = asRecord(entry)
    const network = stringValue(item.network ?? item.destination ?? item.dst ?? item.prefix, '0.0.0.0')
    return {
      id: stringValue(item.id, `${deviceId}-route-${index}`),
      deviceId,
      network,
      prefix: stringValue(item.prefix_length ?? item.mask ?? item.prefix, network.includes('/') ? `/${network.split('/')[1]}` : '-'),
      protocol: normalizeRouteProtocol(item.protocol ?? item.proto),
      nextHop: stringValue(item.nextHop ?? item.next_hop ?? item.gateway, '-'),
      interface: stringValue(item.interface ?? item.out_interface ?? item.dev, '-'),
      metric: numberValue(item.metric ?? item.distance, 0),
    }
  })
}

function readJsonSafe(response: Response) {
  return response.text().then((text) => {
    if (!text) return null
    try {
      return JSON.parse(text) as unknown
    } catch {
      return text
    }
  })
}

function extractErrorMessage(payload: unknown, fallback: string) {
  const record = asRecord(payload)
  return stringValue(record.detail ?? record.message ?? record.msg, fallback || 'Request failed')
}

function extractArray(input: unknown): unknown[] {
  if (Array.isArray(input)) return input
  const record = asRecord(input)
  if (Array.isArray(record.data)) return record.data
  if (Array.isArray(record.items)) return record.items
  if (Array.isArray(record.results)) return record.results
  return []
}

function asRecord(value: unknown): UnknownRecord {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as UnknownRecord : {}
}

function stringValue(value: unknown, fallback: string) {
  return typeof value === 'string' && value.trim() ? value : fallback
}

function numberValue(value: unknown, fallback: number) {
  const parsed = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function numberOrNull(value: unknown) {
  const parsed = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function managementIp(item: UnknownRecord) {
  const host = stringValue(item.managementIp ?? item.management_ip ?? item.management_address ?? item.host ?? item.ip, '-').split('/')[0]
  const port = item.management_port ?? item.managementPort
  if (host !== '-' && typeof port === 'number' && port > 0 && port !== 22) {
    return `${host}:${port}`
  }
  return host
}

function normalizeVendor(value: unknown): Vendor {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('cisco') || normalized.includes('ios')) return 'cisco'
  if (normalized.includes('mikrotik') || normalized.includes('routeros')) return 'mikrotik'
  if (normalized.includes('aruba') || normalized.includes('aos')) return 'aruba'
  if (normalized.includes('linux') || normalized.includes('ubuntu')) return 'linux'
  return 'other'
}

function normalizeDeviceType(value: unknown): 'physical' | 'virtual' {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('virtual') || normalized.includes('gns3') || normalized.includes('vm') || normalized.includes('emulated')) {
    return 'virtual'
  }
  return 'physical'
}

function normalizeStatus(value: unknown): DeviceStatus {
  const normalized = String(value ?? '').toLowerCase()
  if (['online', 'up', 'connected', 'reachable', 'running', 'true'].includes(normalized)) return 'online'
  if (['offline', 'down', 'disconnected', 'unreachable', 'stopped', 'false'].includes(normalized)) return 'offline'
  if (['warning', 'degraded', 'partial'].includes(normalized)) return 'warning'
  return 'unknown'
}

function normalizeUpDown(value: unknown): 'up' | 'down' {
  const normalized = String(value ?? '').toLowerCase()
  return ['up', 'true', 'enabled', 'connected', 'running'].includes(normalized) ? 'up' : 'down'
}

function normalizeRouteProtocol(value: unknown): RouteEntry['protocol'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('ospf')) return 'ospf'
  if (normalized.includes('bgp')) return 'bgp'
  if (normalized.includes('static') || normalized === 's') return 'static'
  return 'connected'
}

function normalizeProtocol(value: unknown): Device['connection']['protocol'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('netconf')) return 'netconf'
  if (normalized.includes('api')) return 'api'
  return 'ssh'
}

function normalizeAuthMethod(value: unknown): Device['connection']['authMethod'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('key')) return 'ssh-key'
  if (normalized.includes('token')) return 'token'
  return 'password'
}

function normalizeAuditResult(value: unknown): AuditLog['result'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('fail') || normalized.includes('error')) return 'failed'
  if (normalized.includes('pending') || normalized.includes('run')) return 'pending'
  return 'success'
}

function normalizeAuditSource(value: unknown): AuditLog['source'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('ai') || normalized.includes('agent')) return 'ai-agent'
  if (normalized.includes('auto')) return 'automation'
  if (normalized.includes('api') || normalized.includes('webhook')) return 'api'
  return 'user'
}

function average(values: number[]) {
  if (!values.length) return 0
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
}

function makeHealthLabel(range: string, index: number, total: number) {
  if (range === '1H' || range === '6H') return `-${total - index - 1}h`
  if (range === '24H') return `${index * 3}h`
  return `D${index + 1}`
}

// ------------------------------------------------------------------
// GNS3 backend helpers
// ------------------------------------------------------------------

type Gns3LocalConfig = {
  found: boolean
  path: string
  controller_url: string
  username: string
  auth_enabled: boolean
  password_available: boolean
}

export type Gns3Project = {
  project_id: string
  name: string
  status: string
  nodes_count: number
  created_at: string
}

export type Gns3Node = {
  node_id: string
  name: string
  status: string
  node_type: string
  console_host: string | null
  console_port: number | null
}

export type Gns3Link = {
  link_id: string
  nodes: Array<{ node_id: string; adapter_number: number; port_number: number }>
  status: string
}

export type Gns3Snapshot = {
  snapshot_id: string
  name: string
  created_at: string
}

let _cachedGns3Config: Gns3LocalConfig | null = null

export async function loadGns3LocalConfig(): Promise<Gns3LocalConfig> {
  if (_cachedGns3Config) return _cachedGns3Config
  const payload = await apiRequest<unknown>('/api/v1/gns3/local-config')
  _cachedGns3Config = payload as Gns3LocalConfig
  return _cachedGns3Config
}

export function clearGns3ConfigCache() {
  _cachedGns3Config = null
}

function gns3ConfigBody(config: Gns3LocalConfig, password?: string) {
  return {
    controller_url: config.controller_url,
    username: config.username,
    password: password || undefined,
    verify_ssl: false,
  }
}

export async function testGns3Connection(password?: string): Promise<{ status: string; projects_count: number }> {
  const config = await loadGns3LocalConfig()
  return apiRequest<unknown>('/api/v1/gns3/test-connection', {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  }) as Promise<{ status: string; projects_count: number }>
}

export async function loadGns3Projects(password?: string): Promise<Gns3Project[]> {
  const config = await loadGns3LocalConfig()
  const payload = await apiRequest<unknown>('/api/v1/gns3/projects', {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
  return extractArray(payload).map((item, index) => {
    const r = asRecord(item)
    return {
      project_id: stringValue(r.project_id ?? r.id, `proj-${index}`),
      name: stringValue(r.name, `Project ${index + 1}`),
      status: stringValue(r.status, 'closed'),
      nodes_count: numberValue(r.nodes_count ?? r.nodes, 0),
      created_at: stringValue(r.created_at ?? r.created, '-'),
    }
  })
}

export async function createGns3Project(name: string, password?: string): Promise<Gns3Project> {
  const config = await loadGns3LocalConfig()
  const payload = await apiRequest<unknown>('/api/v1/gns3/projects/create', {
    method: 'POST',
    body: JSON.stringify({ ...gns3ConfigBody(config, password), name }),
  })
  const r = asRecord(payload)
  return {
    project_id: stringValue(r.project_id ?? r.id, ''),
    name: stringValue(r.name, name),
    status: stringValue(r.status, 'closed'),
    nodes_count: numberValue(r.nodes_count, 0),
    created_at: stringValue(r.created_at, '-'),
  }
}

export async function openGns3Project(projectId: string, password?: string): Promise<unknown> {
  const config = await loadGns3LocalConfig()
  return apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/open`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
}

export async function closeGns3Project(projectId: string, password?: string): Promise<unknown> {
  const config = await loadGns3LocalConfig()
  return apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/close`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
}

export async function deleteGns3Project(projectId: string, password?: string): Promise<void> {
  const config = await loadGns3LocalConfig()
  await apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}`, {
    method: 'DELETE',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
}

export async function loadGns3Nodes(projectId: string, password?: string): Promise<Gns3Node[]> {
  const config = await loadGns3LocalConfig()
  const payload = await apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/nodes`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
  return extractArray(payload).map((item, index) => {
    const r = asRecord(item)
    return {
      node_id: stringValue(r.node_id ?? r.id, `node-${index}`),
      name: stringValue(r.name, `Node ${index + 1}`),
      status: stringValue(r.status, 'stopped'),
      node_type: stringValue(r.node_type ?? r.type, 'unknown'),
      console_host: typeof r.console_host === 'string' ? r.console_host : null,
      console_port: typeof r.console_port === 'number' ? r.console_port : null,
    }
  })
}

export async function startGns3Node(projectId: string, nodeId: string, password?: string): Promise<unknown> {
  const config = await loadGns3LocalConfig()
  return apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/nodes/${nodeId}/start`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
}

export async function stopGns3Node(projectId: string, nodeId: string, password?: string): Promise<unknown> {
  const config = await loadGns3LocalConfig()
  return apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/nodes/${nodeId}/stop`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
}

export async function deleteGns3Node(projectId: string, nodeId: string, password?: string): Promise<void> {
  const config = await loadGns3LocalConfig()
  await apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/nodes/${nodeId}`, {
    method: 'DELETE',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
}

export async function loadGns3Links(projectId: string, password?: string): Promise<Gns3Link[]> {
  const config = await loadGns3LocalConfig()
  const payload = await apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/links`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
  return extractArray(payload).map((item, index) => {
    const r = asRecord(item)
    return {
      link_id: stringValue(r.link_id ?? r.id, `link-${index}`),
      nodes: extractArray(r.nodes).map((n) => {
        const nr = asRecord(n)
        return {
          node_id: stringValue(nr.node_id, ''),
          adapter_number: numberValue(nr.adapter_number, 0),
          port_number: numberValue(nr.port_number, 0),
        }
      }),
      status: stringValue(r.status, 'up'),
    }
  })
}

export async function loadGns3Snapshots(projectId: string, password?: string): Promise<Gns3Snapshot[]> {
  const config = await loadGns3LocalConfig()
  const payload = await apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/snapshots`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
  return extractArray(payload).map((item, index) => {
    const r = asRecord(item)
    return {
      snapshot_id: stringValue(r.snapshot_id ?? r.id, `snap-${index}`),
      name: stringValue(r.name, `Snapshot ${index + 1}`),
      created_at: stringValue(r.created_at, '-'),
    }
  })
}

export async function createGns3Snapshot(projectId: string, name: string, password?: string): Promise<Gns3Snapshot> {
  const config = await loadGns3LocalConfig()
  const payload = await apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/snapshots/create`, {
    method: 'POST',
    body: JSON.stringify({ ...gns3ConfigBody(config, password), name }),
  })
  const r = asRecord(payload)
  return {
    snapshot_id: stringValue(r.snapshot_id ?? r.id, ''),
    name: stringValue(r.name, name),
    created_at: stringValue(r.created_at, '-'),
  }
}

export async function restoreGns3Snapshot(projectId: string, snapshotId: string, password?: string): Promise<unknown> {
  const config = await loadGns3LocalConfig()
  return apiRequest<unknown>(`/api/v1/gns3/projects/${projectId}/snapshots/${snapshotId}/restore`, {
    method: 'POST',
    body: JSON.stringify(gns3ConfigBody(config, password)),
  })
}

// ------------------------------------------------------------------
// Tasks backend helpers
// ------------------------------------------------------------------

export async function loadBackendTasks(): Promise<Task[]> {
  const payload = await apiRequest<unknown>('/api/v1/tasks')
  return extractArray(asRecord(payload).tasks ?? payload).map((item, index) => {
    const r = asRecord(item)
    return {
      id: stringValue(r.id, `task-${index}`),
      name: stringValue(r.name, 'Unnamed task'),
      device: stringValue(r.device_id ?? r.device, '-'),
      action: stringValue(r.action, '-'),
      status: normalizeTaskStatus(r.status),
      started: stringValue(r.started ?? r.created_at, '-'),
      duration: stringValue(r.duration, '-'),
      user: stringValue(r.user, 'system'),
      agent: stringValue(r.agent, 'manual'),
      executionLocation: r.execution_location === 'EDGE' || r.execution_location === 'LAB' ? r.execution_location : r.execution_location === 'CENTRAL' ? 'CENTRAL' : undefined,
      attemptId: typeof r.attempt_id === 'string' ? r.attempt_id : undefined,
      output: r.output,
    }
  })
}

export async function loadBackendTaskDetail(taskId: string): Promise<{ task: Task; steps: TaskStep[] }> {
  const payload = await apiRequest<unknown>(`/api/v1/tasks/${taskId}`)
  const r = asRecord(payload)
  const taskRecord = asRecord(r.task ?? r)
  return {
    task: {
      id: stringValue(taskRecord.id, taskId),
      name: stringValue(taskRecord.name, 'Unnamed task'),
      device: stringValue(taskRecord.device_id ?? taskRecord.device, '-'),
      action: stringValue(taskRecord.action, '-'),
      status: normalizeTaskStatus(taskRecord.status),
      started: stringValue(taskRecord.started ?? taskRecord.created_at, '-'),
      duration: stringValue(taskRecord.duration, '-'),
      user: stringValue(taskRecord.user, 'system'),
      agent: stringValue(taskRecord.agent, 'manual'),
      executionLocation: taskRecord.execution_location === 'EDGE' || taskRecord.execution_location === 'LAB' ? taskRecord.execution_location : taskRecord.execution_location === 'CENTRAL' ? 'CENTRAL' : undefined,
      attemptId: typeof taskRecord.attempt_id === 'string' ? taskRecord.attempt_id : undefined,
      output: taskRecord.output,
    },
    steps: extractArray(r.steps ?? taskRecord.steps).map((step, index) => {
      const s = asRecord(step)
      return {
        id: stringValue(s.id, `step-${index}`),
        taskId: taskId,
        name: stringValue(s.name, `Step ${index + 1}`),
        status: normalizeTaskStatus(s.status),
        timestamp: stringValue(s.timestamp ?? s.created_at, '-'),
        output: stringValue(s.output, ''),
        errors: typeof s.errors === 'string' ? s.errors : undefined,
      }
    }),
  }
}

function normalizeTaskStatus(value: unknown): TaskStatus {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('running') || normalized.includes('progress')) return 'running'
  if (normalized.includes('success') || normalized.includes('complete') || normalized.includes('done')) return 'success'
  if (normalized.includes('fail') || normalized.includes('error')) return 'failed'
  if (normalized.includes('cancel')) return 'cancelled'
  return 'queued'
}

// ------------------------------------------------------------------
// Alerts backend helpers
// ------------------------------------------------------------------

export async function loadBackendAlerts(): Promise<Alert[]> {
  const payload = await apiRequest<unknown>('/api/v1/alerts')
  return extractArray(asRecord(payload).alerts ?? payload).map((item, index) => {
    const r = asRecord(item)
    return {
      id: stringValue(r.id, `alert-${index}`),
      type: stringValue(r.type, 'system'),
      severity: normalizeSeverity(r.severity),
      device: stringValue(r.device_id ?? r.device, '-'),
      message: stringValue(r.message, ''),
      createdAt: stringValue(r.created_at ?? r.createdAt, '-'),
      status: normalizeAlertStatus(r.status),
    }
  })
}

function normalizeSeverity(value: unknown): Alert['severity'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('critical')) return 'critical'
  if (normalized.includes('high') || normalized.includes('major')) return 'high'
  if (normalized.includes('medium') || normalized.includes('warning')) return 'medium'
  if (normalized.includes('low') || normalized.includes('minor')) return 'low'
  return 'info'
}

function normalizeAlertStatus(value: unknown): Alert['status'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('ack')) return 'acknowledged'
  if (normalized.includes('resolv') || normalized.includes('close')) return 'resolved'
  return 'open'
}

// ------------------------------------------------------------------
// Backups backend helpers
// ------------------------------------------------------------------

export async function loadBackendBackups(): Promise<Backup[]> {
  const payload = await apiRequest<unknown>('/api/v1/backups')
  return extractArray(asRecord(payload).backups ?? payload).map((item, index) => {
    const r = asRecord(item)
    return {
      id: stringValue(r.id, `backup-${index}`),
      deviceId: stringValue(r.device_id ?? r.deviceId, '-'),
      device: stringValue(r.device ?? r.device_id, '-'),
      backupTime: stringValue(r.backup_time ?? r.backupTime, '-'),
      type: normalizeBackupType(r.type),
      size: stringValue(r.size, '-'),
      createdBy: stringValue(r.created_by ?? r.createdBy, 'system'),
    }
  })
}

function normalizeBackupType(value: unknown): Backup['type'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('startup')) return 'startup'
  if (normalized.includes('candidate')) return 'candidate'
  return 'running'
}

// ------------------------------------------------------------------
// Credentials backend helpers
// ------------------------------------------------------------------

export async function loadBackendCredentials(): Promise<CredentialProfile[]> {
  const payload = await apiRequest<unknown>('/api/v1/credentials')
  return extractArray(asRecord(payload).credentials ?? payload).map((item, index) => {
    const r = asRecord(item)
    return {
      id: stringValue(r.id, `cred-${index}`),
      name: stringValue(r.name, ''),
      vendor: normalizeVendor(r.vendor),
      username: stringValue(r.username, ''),
      authType: normalizeAuthType(r.auth_type),
      secretPreview: stringValue(r.secret_preview, '****'),
      lastTest: stringValue(r.last_test, '-'),
      status: normalizeCredStatus(r.status),
    }
  })
}

function normalizeAuthType(value: unknown): CredentialProfile['authType'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('key')) return 'ssh-key'
  if (normalized.includes('token')) return 'api-token'
  return 'password'
}

function normalizeCredStatus(value: unknown): CredentialProfile['status'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('valid') || normalized.includes('pass')) return 'valid'
  if (normalized.includes('fail') || normalized.includes('error')) return 'failed'
  return 'untested'
}

// ------------------------------------------------------------------
// Settings backend helpers
// ------------------------------------------------------------------

export async function loadBackendSettings(): Promise<NetworkSettings> {
  const payload = await apiRequest<unknown>('/api/v1/settings')
  const r = asRecord(payload)
  const general = asRecord(r.general)
  const ai = asRecord(r.ai)
  const ssh = asRecord(r.ssh)
  return {
    general: {
      workspaceName: stringValue(general.workspace_name, 'AI Network Agent'),
      timezone: stringValue(general.timezone, 'UTC'),
      defaultView: stringValue(general.default_view, 'dashboard'),
    },
    ai: {
      provider: stringValue(ai.provider, 'openai'),
      model: stringValue(ai.model, 'gpt-4'),
      temperature: numberValue(ai.temperature, 0.7),
      maximumTokens: numberValue(ai.maximum_tokens, 4096),
      requireApproval: Boolean(ai.require_approval),
      automaticBackup: Boolean(ai.automatic_backup),
      postChangeValidation: Boolean(ai.post_change_validation),
      automaticRollback: Boolean(ai.automatic_rollback),
      allowDestructiveCommands: Boolean(ai.allow_destructive_commands),
    },
    ssh: {
      timeoutSeconds: numberValue(ssh.timeout_seconds, 30),
      commandTimeoutSeconds: numberValue(ssh.command_timeout_seconds, 60),
      strictHostKeyChecking: Boolean(ssh.strict_host_key_checking),
    },
  }
}

// ------------------------------------------------------------------
// Discovery backend helpers
// ------------------------------------------------------------------

export async function loadBackendDiscoveryResults(): Promise<DiscoveryResult[]> {
  const payload = await apiRequest<unknown>('/api/v1/discovery')
  return extractArray(asRecord(payload).results ?? payload).flatMap((item) => {
    const r = asRecord(item)
    return extractArray(r.devices).map((device, index) => {
      const d = asRecord(device)
      return {
        id: stringValue(d.id, `disc-${index}`),
        ip: stringValue(d.ip, '-'),
        hostname: stringValue(d.hostname, '-'),
        vendor: normalizeVendor(d.vendor),
        platform: stringValue(d.platform, 'Unknown'),
        ssh: normalizeProbeStatus(d.ssh),
        snmp: normalizeProbeStatus(d.snmp),
        status: normalizeDiscoveryStatus(d.status),
      }
    })
  })
}

function normalizeProbeStatus(value: unknown): 'open' | 'closed' | 'unknown' {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('open') || normalized.includes('true')) return 'open'
  if (normalized.includes('closed') || normalized.includes('false')) return 'closed'
  return 'unknown'
}

function normalizeDiscoveryStatus(value: unknown): DiscoveryResult['status'] {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('added')) return 'added'
  if (normalized.includes('ignored')) return 'ignored'
  return 'ready'
}

// ------------------------------------------------------------------
// Agent backend helpers
// ------------------------------------------------------------------

export async function sendAgentChat(
  message: string,
  deviceId?: string,
  options?: {
    sessionId?: string
    deviceIds?: string[]
    labId?: string
    projectId?: string
    environment?: 'lab' | 'staging' | 'production'
    mode?: string
  },
): Promise<AgentMessage> {
  const payload = await apiRequest<unknown>('/api/v1/agent/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      device_id: deviceId,
      session_id: options?.sessionId,
      device_ids: options?.deviceIds ?? (deviceId ? [deviceId] : []),
      lab_id: options?.labId,
      project_id: options?.projectId,
      environment: options?.environment ?? 'lab',
      mode: options?.mode ?? 'guarded',
    }),
  })
  const r = asRecord(payload)
  return {
    id: stringValue(r.id, `msg-${Date.now()}`),
    role: 'assistant',
    content: stringValue(r.content, ''),
    createdAt: stringValue(r.created_at, new Date().toISOString()),
  }
}

export async function createAgentPlan(intent: string, deviceIds: string[]): Promise<ExecutionPlan> {
  const payload = await apiRequest<unknown>('/api/v1/agent/plan', {
    method: 'POST',
    body: JSON.stringify({ intent, device_ids: deviceIds }),
  })
  const r = asRecord(payload)
  return {
    id: stringValue(r.id, `plan-${Date.now()}`),
    task: stringValue(r.task, intent),
    devices: extractArray(r.devices).map(String),
    plannedActions: extractArray(r.planned_actions).map(String),
    risk: normalizePlanRisk(r.risk) as ExecutionPlan['risk'],
    requiresApproval: Boolean(r.requires_approval),
  }
}

export async function executeAgentPlan(planId: string, approvedBy: string): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>('/api/v1/agent/execute', {
    method: 'POST',
    body: JSON.stringify({
      plan_id: planId,
      approved_by: approvedBy,
    }),
  })
}

export async function cancelAgentPlan(planId: string, cancelledBy: string): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>('/api/v1/agent/cancel', {
    method: 'POST',
    body: JSON.stringify({
      plan_id: planId,
      cancelled_by: cancelledBy,
    }),
  })
}

// ------------------------------------------------------------------
// Containerlab backend helpers
// ------------------------------------------------------------------

export type ContainerlabLab = {
  id: string
  name: string
  topology_file: string
  status: string
  created_at: string
  nodes: Array<{ name: string; kind: string; status: string }>
}

export async function loadContainerlabLabs(): Promise<ContainerlabLab[]> {
  const payload = await apiRequest<unknown>('/api/v1/containerlab/labs')
  return extractArray(asRecord(payload).labs ?? payload).map((item, index) => {
    const r = asRecord(item)
    return {
      id: stringValue(r.id, `clab-${index}`),
      name: stringValue(r.name, `Lab ${index + 1}`),
      topology_file: stringValue(r.topology_file, ''),
      status: stringValue(r.status, 'stopped'),
      created_at: stringValue(r.created_at, '-'),
      nodes: extractArray(r.nodes).map((n) => {
        const nr = asRecord(n)
        return {
          name: stringValue(nr.name, ''),
          kind: stringValue(nr.kind, 'unknown'),
          status: stringValue(nr.status, 'stopped'),
        }
      }),
    }
  })
}

export async function loadBackendLabs(): Promise<Lab[]> {
  const [gns3Result, containerlabResult] = await Promise.allSettled([
    loadGns3Projects(),
    loadContainerlabLabs(),
  ])

  const labs: Lab[] = []

  if (gns3Result.status === 'fulfilled') {
    const nodeCounts = await Promise.allSettled(
      gns3Result.value.map(async (project) => {
        const nodes = await loadGns3Nodes(project.project_id)
        return { projectId: project.project_id, nodes: nodes.length }
      })
    )
    const nodeCountByProject = new Map(
      nodeCounts.flatMap((result) =>
        result.status === 'fulfilled' ? [[result.value.projectId, result.value.nodes] as const] : []
      )
    )

    labs.push(
      ...gns3Result.value.map((project) => ({
        id: project.project_id,
        name: project.name,
        engine: 'gns3' as const,
        nodes: nodeCountByProject.get(project.project_id) ?? project.nodes_count,
        status: (project.status === 'opened' ? 'running' : project.status === 'degraded' ? 'degraded' : 'stopped') as Lab['status'],
        cpu: 0,
        ram: 0,
        created: project.created_at,
      }))
    )
  }

  if (containerlabResult.status === 'fulfilled') {
    labs.push(...containerlabResult.value.map((lab) => ({
      id: lab.id,
      name: lab.name,
      engine: 'containerlab' as const,
      nodes: lab.nodes.length,
      status: (lab.status === 'running' || lab.status === 'deploying' ? 'running' : 'stopped') as Lab['status'],
      cpu: 0,
      ram: 0,
      created: lab.created_at,
    })))
  }

  return labs.sort((a, b) => a.created < b.created ? 1 : -1)
}

export async function loadBackendLabDetail(labId: string): Promise<{ lab: Lab; topology: Topology }> {
  const labs = await loadBackendLabs()
  const lab = labs.find((item) => item.id === labId)
  if (!lab) {
    throw new Error('Lab not found')
  }

  if (lab.engine === 'gns3') {
    const topology = await loadBackendTopology(lab.id)
    return {
      lab: {
        ...lab,
        nodes: topology.nodes.length || lab.nodes,
      },
      topology,
    }
  }

  const inventory = await loadContainerlabLabs()
  const found = inventory.find((item) => item.id === labId)
  if (!found) {
    return {
      lab,
      topology: {
        id: lab.id,
        name: lab.name,
        nodes: [],
        links: [],
      },
    }
  }

  return {
    lab,
    topology: {
      id: lab.id,
      name: lab.name,
      nodes: found.nodes.map((node, index) => ({
        id: `${lab.id}-node-${index}`,
        hostname: node.name,
        vendor: node.kind.includes('mikrotik') ? 'mikrotik' : node.kind.includes('cisco') ? 'cisco' : node.kind.includes('aruba') ? 'aruba' : 'linux',
        status: node.status === 'running' ? 'online' : 'offline',
        ip: '-',
      })),
      links: [],
    },
  }
}

export async function deployContainerlabLab(name: string, topologyFile: string): Promise<ContainerlabLab> {
  const payload = await apiRequest<unknown>('/api/v1/containerlab/labs/deploy', {
    method: 'POST',
    body: JSON.stringify({ name, topology_file: topologyFile }),
  })
  const r = asRecord(payload)
  return {
    id: stringValue(r.id, ''),
    name: stringValue(r.name, name),
    topology_file: stringValue(r.topology_file, topologyFile),
    status: stringValue(r.status, 'deploying'),
    created_at: stringValue(r.created_at, '-'),
    nodes: [],
  }
}

export async function destroyContainerlabLab(labId: string): Promise<void> {
  await apiRequest<unknown>(`/api/v1/containerlab/labs/${labId}/destroy`, {
    method: 'POST',
  })
}

// ------------------------------------------------------------------
// 9Router backend helpers
// ------------------------------------------------------------------

export type NineRouterSearchResult = {
  title: string
  url: string
  snippet: string
  score?: number
  published_at?: string | null
}

export type NineRouterSearchResponse = {
  provider: string
  query: string
  results: NineRouterSearchResult[]
  answer?: string | null
}

export type NineRouterFetchResponse = {
  provider: string
  url: string
  title?: string
  content?: {
    format: string
    text: string
    length?: number
  }
  metadata?: Record<string, unknown>
}

export async function searchNineRouter(query: string, maxResults?: number, searchType?: string): Promise<NineRouterSearchResponse> {
  return apiRequest<NineRouterSearchResponse>('/api/v1/ninerouter/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      max_results: maxResults ?? 5,
      search_type: searchType ?? 'web',
    }),
  })
}

export async function fetchNineRouterUrl(url: string, format?: string, maxCharacters?: number): Promise<NineRouterFetchResponse> {
  return apiRequest<NineRouterFetchResponse>('/api/v1/ninerouter/fetch', {
    method: 'POST',
    body: JSON.stringify({
      url,
      format: format ?? 'markdown',
      max_characters: maxCharacters ?? 12000,
    }),
  })
}

export async function getNineRouterStatus(): Promise<{ status: string; url?: string; error?: string }> {
  return apiRequest<{ status: string; url?: string; error?: string }>('/api/v1/ninerouter/status')
}

export type NineRouterFreeModel = {
  id: string
  name: string
  description: string
  tier: string
}

export async function getNineRouterFreeModels(): Promise<NineRouterFreeModel[]> {
  const payload = await apiRequest<unknown>('/api/v1/ninerouter/models/free')
  const record = asRecord(payload)
  return extractArray(record.models).map((item) => {
    const r = asRecord(item)
    return {
      id: stringValue(r.id, ''),
      name: stringValue(r.name, ''),
      description: stringValue(r.description, ''),
      tier: stringValue(r.tier, 'free'),
    }
  }).filter((m) => m.id)
}

// ------------------------------------------------------------------
// Agent tools backend helpers
// ------------------------------------------------------------------

export type AgentTool = {
  name: string
  description: string
  parameters: Record<string, unknown>
}

export async function loadAgentTools(): Promise<AgentTool[]> {
  const payload = await apiRequest<unknown>('/api/v1/agent/tools')
  return extractArray(asRecord(payload).tools).map((item) => {
    const r = asRecord(item)
    return {
      name: stringValue(r.name, ''),
      description: stringValue(r.description, ''),
      parameters: asRecord(r.parameters),
    }
  }).filter((t) => t.name)
}

export async function executeAgentTool(toolName: string, params: Record<string, unknown>): Promise<Record<string, unknown>> {
  return apiRequest<Record<string, unknown>>('/api/v1/agent/tools/execute', {
    method: 'POST',
    body: JSON.stringify({ tool: toolName, ...params }),
  })
}

// ------------------------------------------------------------------
// Configurations backend helpers
// ------------------------------------------------------------------

export async function loadBackendConfigurations(): Promise<Configuration[]> {
  const payload = await apiRequest<unknown>('/api/v1/config/plans')
  const plans = extractArray(asRecord(payload).plans ?? payload)
  return plans.map((item, index) => {
    const r = asRecord(item)
    const commands = extractOutputLines(r.commands)
    return {
      id: stringValue(r.plan_id ?? r.id, `config-${index}`),
      deviceId: stringValue(r.device_id ?? r.deviceId, '-'),
      mode: 'raw-cli' as const,
      candidate: commands.join('\n'),
      risk: normalizePlanRisk(r.risk_level ?? r.risk) as Configuration['risk'],
      generated: stringValue(r.created_at ?? r.createdAt, '-'),
      validation: extractArray(r.checks).map((check) => {
        const c = asRecord(check)
        return {
          check: stringValue(c.check, ''),
          result: stringValue(c.result, 'safe') as 'safe' | 'warning' | 'blocked',
          detail: stringValue(c.detail, ''),
        }
      }),
    }
  })
}
