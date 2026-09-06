export type Vendor = 'cisco' | 'mikrotik' | 'aruba' | 'linux' | 'other'
export type DeviceStatus = 'online' | 'offline' | 'warning' | 'unknown'
export type LabEngine = 'gns3' | 'containerlab' | 'vrnetlab'
export type TaskStatus = 'queued' | 'running' | 'success' | 'failed' | 'cancelled'
export type RiskLevel = 'low' | 'medium' | 'high'

export type ApiResponse<T> = {
  status: number
  data: T
  msg?: string
}

export interface Device {
  id: string
  hostname: string
  vendor: Vendor
  model: string
  platform: string
  managementIp: string
  status: DeviceStatus
  cpu: number
  memory: number
  latencyMs: number | null
  lastSeen: string
  lab: string
  tags: string[]
  osVersion: string
  uptime: string
  serial: string
  deviceType: 'physical' | 'virtual'
  connection: {
    protocol: 'ssh' | 'api' | 'netconf'
    status: 'connected' | 'disconnected' | 'degraded'
    lastLogin: string
    authMethod: 'password' | 'ssh-key' | 'token'
    privilegeLevel: string
  }
}

export interface NetworkInterface {
  id: string
  deviceId: string
  name: string
  description: string
  ipAddress: string
  adminStatus: 'up' | 'down'
  operationalStatus: 'up' | 'down'
  speed: string
  duplex: string
  rx: string
  tx: string
  errors: number
}

export interface RouteEntry {
  id: string
  deviceId: string
  network: string
  prefix: string
  protocol: 'connected' | 'static' | 'ospf' | 'bgp'
  nextHop: string
  interface: string
  metric: number
}

export interface Lab {
  id: string
  name: string
  engine: LabEngine
  nodes: number
  status: 'running' | 'stopped' | 'degraded'
  cpu: number
  ram: number
  created: string
}

export interface Gns3Project {
  id: string
  name: string
  nodes: number
  status: 'running' | 'stopped' | 'degraded'
  created: string
}

export interface Gns3Status {
  server: 'connected' | 'disconnected'
  vm: 'connected' | 'disconnected' | 'warning'
  controller: string
  projects: Gns3Project[]
}

export interface ContainerlabInventory {
  topologyFiles: Array<{ name: string; status: 'valid' | 'invalid'; updated: string }>
  runningLabs: Lab[]
  nodes: Array<{ name: string; kind: string; image: string; status: 'running' | 'stopped' }>
  images: Array<{ name: string; size: string; source: string }>
  yaml: string
}

export interface Task {
  id: string
  name: string
  device: string
  action: string
  status: TaskStatus
  started: string
  duration: string
  user: string
  agent: string
  executionLocation?: 'CENTRAL' | 'EDGE' | 'LAB'
  attemptId?: string
  output?: unknown
}

export interface TaskStep {
  id: string
  taskId: string
  name: string
  status: TaskStatus
  timestamp: string
  output: string
  errors?: string
}

export interface Alert {
  id: string
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  device: string
  message: string
  createdAt: string
  status: 'open' | 'acknowledged' | 'resolved'
}

export interface AuditLog {
  id: string
  time: string
  user: string
  action: string
  device: string
  result: 'success' | 'failed' | 'pending'
  source: 'user' | 'ai-agent' | 'automation' | 'api'
  details: string
}

export interface Backup {
  id: string
  deviceId: string
  device: string
  backupTime: string
  type: 'running' | 'startup' | 'candidate'
  size: string
  createdBy: string
}

export interface Configuration {
  id: string
  deviceId: string
  mode: 'raw-cli' | 'structured' | 'ai-generated'
  candidate: string
  risk: RiskLevel
  generated: string
  validation: Array<{ check: string; result: 'safe' | 'warning' | 'blocked'; detail: string }>
}

export interface ConfigPlan {
  planId: string
  deviceId: string
  commands: string[]
  verify: Array<{ command: string; expect?: string | null }>
  saveOnSuccess: boolean
  description: string
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: string
  createdAt: string
  updatedAt: string
  report?: unknown
}

export interface ConfigApplyResult {
  planId: string
  approvedBy: string
  status: string
  output: string[]
  raw: unknown
}

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt: string
}

export interface ExecutionPlan {
  id: string
  task: string
  devices: string[]
  plannedActions: string[]
  risk: RiskLevel
  requiresApproval: boolean
}

export interface TerminalSession {
  id: string
  deviceId: string
  prompt: string
  protocol: 'ssh'
  host: string
  status: 'connected' | 'disconnected' | 'reconnecting'
  output: string[]
  history: string[]
}

export interface TerminalCommandResult {
  deviceId: string
  command: string
  status: 'ok' | 'applied' | 'failed' | 'blocked'
  endpoint: string
  output: string[]
  raw: unknown
}

export interface TerminalLiveSession {
  sessionId: string
  deviceId: string
  hostname: string
  vendor: Vendor
  managementAddress: string
  prompt: string
  status: 'connected' | 'disconnected' | 'reconnecting'
}

export interface TerminalSuggestion {
  value: string
  description: string
}

export interface CredentialProfile {
  id: string
  name: string
  vendor: Vendor
  username: string
  authType: 'password' | 'ssh-key' | 'api-token'
  secretPreview: string
  lastTest: string
  status: 'valid' | 'failed' | 'untested'
}

export interface DiscoveryResult {
  id: string
  ip: string
  hostname: string
  vendor: Vendor
  platform: string
  ssh: 'open' | 'closed' | 'unknown'
  snmp: 'open' | 'closed' | 'unknown'
  status: 'ready' | 'ignored' | 'added'
}

export interface NetworkSettings {
  general: {
    workspaceName: string
    timezone: string
    defaultView: string
  }
  ai: {
    provider: string
    model: string
    temperature: number
    maximumTokens: number
    requireApproval: boolean
    automaticBackup: boolean
    postChangeValidation: boolean
    automaticRollback: boolean
    allowDestructiveCommands: boolean
  }
  ssh: {
    timeoutSeconds: number
    commandTimeoutSeconds: number
    strictHostKeyChecking: boolean
  }
}

export interface HealthPoint {
  time: string
  online: number
  offline: number
  latency: number
  packetLoss: number
  configFailures: number
}

export interface DashboardSummary {
  totalDevices: {
    total: number
    online: number
    offline: number
    warning: number
  }
  activeLabs: {
    total: number
    gns3: number
    containerlab: number
  }
  aiOperations: {
    totalToday: number
    success: number
    running: number
    failed: number
  }
  networkHealth: {
    score: number
    label: string
  }
}

export interface Topology {
  id: string
  name: string
  projectId?: string
  nodes: Array<{
    id: string
    hostname: string
    vendor: Vendor
    kind?: 'router' | 'switch' | 'host' | 'cloud' | 'nat' | 'firewall' | 'loopback' | 'other'
    nodeType?: 'qemu' | 'vpcs' | 'dynamips' | 'cloud' | 'ethernet_switch' | 'docker' | 'other'
    status: DeviceStatus
    ip: string
  }>
  links: Array<{
    id: string
    source: string
    target: string
    sourceInterface: string
    targetInterface: string
    status: 'up' | 'down'
  }>
  layout?: Record<string, { x: number; y: number }>
}
