import type {
  ApiResponse,
  AuditLog,
  ConfigApplyResult,
  ConfigPlan,
  DashboardSummary,
  Device,
  DeviceStatus,
  HealthPoint,
  NetworkInterface,
  RouteEntry,
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

export async function loadBackendDevices(): Promise<Device[]> {
  const payload = await apiRequest<unknown>('/api/v1/devices')
  return extractArray(payload).map(normalizeDevice)
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

export async function loadBackendTopology(): Promise<Topology> {
  const payload = await apiRequest<unknown>('/api/v1/topology')
  const record = asRecord(payload)
  const nodes = extractArray(record.nodes)
  const links = extractArray(record.links)

  return {
    id: stringValue(record.id, 'backend-topology'),
    name: stringValue(record.name, 'Backend Topology'),
    nodes: nodes.map((node, index) => {
      const item = asRecord(node)
      return {
        id: stringValue(item.id, `node-${index}`),
        hostname: stringValue(item.hostname ?? item.name ?? item.label, `Node ${index + 1}`),
        vendor: normalizeVendor(item.vendor ?? item.type ?? item.platform),
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

export async function loadBackendAuditLogs(): Promise<AuditLog[]> {
  const payload = await apiRequest<unknown>('/api/v1/audit')
  return extractArray(asRecord(payload).events ?? payload).map((event, index) => {
    const item = asRecord(event)
    return {
      id: stringValue(item.id, `audit-${index}`),
      time: stringValue(item.time ?? item.timestamp, '-'),
      user: stringValue(item.user, 'system'),
      action: stringValue(item.action, 'Unknown action'),
      device: stringValue(item.device ?? item.device_id, '-'),
      result: normalizeAuditResult(item.result),
      source: 'api',
      details: stringValue(item.details ?? item.command, '-'),
    }
  })
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
  return stringValue(item.managementIp ?? item.management_ip ?? item.management_address ?? item.host ?? item.ip, '-').split('/')[0]
}

function normalizeVendor(value: unknown): Vendor {
  const normalized = String(value ?? '').toLowerCase()
  if (normalized.includes('cisco') || normalized.includes('ios')) return 'cisco'
  if (normalized.includes('mikrotik') || normalized.includes('routeros')) return 'mikrotik'
  if (normalized.includes('aruba') || normalized.includes('aos')) return 'aruba'
  if (normalized.includes('linux') || normalized.includes('ubuntu')) return 'linux'
  return 'other'
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

function average(values: number[]) {
  if (!values.length) return 0
  return Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
}

function makeHealthLabel(range: string, index: number, total: number) {
  if (range === '1H' || range === '6H') return `-${total - index - 1}h`
  if (range === '24H') return `${index * 3}h`
  return `D${index + 1}`
}
