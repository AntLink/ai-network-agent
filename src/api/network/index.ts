import useSWR from 'swr'
import { getFetcher } from 'src/api/global-fetcher'
import {
  backendOrMock,
  applyBackendConfigPlan,
  clearGns3ConfigCache,
  closeBackendTerminalSession,
  closeGns3Project,
  createAgentPlan,
  createBackendDevice,
  createBackendConfigPlan,
  createBackendTerminalSession,
  createGns3Project,
  createGns3Snapshot,
  cancelAgentPlan,
  deleteGns3Node,
  deleteGns3Project,
  deleteBackendDevice,
  deployContainerlabLab,
  destroyContainerlabLab,
  executeBackendTerminalSessionCommand,
  executeAgentPlan,
  getApiBaseUrl,
  getBackendConfigPlan,
  loadBackendAlerts,
  loadBackendAuditLogs,
  loadBackendBackups,
  loadBackendConfigurations,
  loadBackendCredentials,
  loadBackendDashboardSummary,
  loadBackendLabDetail,
  loadBackendLabs,
  loadBackendDeviceDetail,
  loadBackendDevices,
  loadBackendDevicesPage,
  loadBackendDiscoveryResults,
  loadBackendHealthSeries,
  loadBackendSettings,
  loadBackendTaskDetail,
  loadBackendTasks,
  loadBackendTopology,
  loadContainerlabLabs,
  loadGns3Links,
  loadGns3LocalConfig,
  loadGns3Nodes,
  loadGns3Projects,
  loadGns3Snapshots,
  openGns3Project,
  rollbackBackendConfigPlan,
  restoreGns3Snapshot,
  runBackendTerminalCommand,
  updateBackendDevice,
  searchNineRouter,
  fetchNineRouterUrl,
  getNineRouterStatus,
  getNineRouterFreeModels,
  loadAgentTools,
  executeAgentTool,
  sendAgentChat,
  startGns3Node,
  stopGns3Node,
  suggestBackendTerminalCommand,
  testGns3Connection,
  saveBackendTopology,
  sendBackendTerminalInput,
} from 'src/api/network/backend-client'
import type {
  NineRouterFreeModel,
  AgentTool,
} from 'src/api/network/backend-client'
import type {
  ApiResponse,
  AgentMessage,
  Alert,
  Backup,
  Configuration,
  ConfigApplyResult,
  ConfigPlan,
  ContainerlabInventory,
  CredentialProfile,
  DashboardSummary,
  Device,
  DiscoveryResult,
  ExecutionPlan,
  Gns3Status,
  HealthPoint,
  Lab,
  NetworkInterface,
  NetworkSettings,
  RouteEntry,
  Task,
  TaskStep,
  TerminalSession,
  TerminalCommandResult,
  TerminalLiveSession,
  TerminalSuggestion,
  Topology,
} from 'src/types/network'
import type { AuditLogQuery } from 'src/api/network/backend-client'

export function useDashboardSummary() {
  return useSWR<ApiResponse<DashboardSummary>>('dashboard-summary', () =>
    backendOrMock(loadBackendDashboardSummary, '/api/network/dashboard')
  )
}

export function useNetworkHealth(range: string) {
  return useSWR<ApiResponse<HealthPoint[]>>(['network-health', range], () =>
    backendOrMock(() => loadBackendHealthSeries(range), `/api/network/health?range=${range}`)
  )
}

export function useDevices() {
  return useSWR<ApiResponse<Device[]>>('devices', () =>
    backendOrMock(loadBackendDevices, '/api/network/devices')
  )
}

export function useDevicesPage(query: { page?: number; limit?: number } = {}) {
  const page = query.page ?? 1
  const limit = query.limit ?? 25
  const key = `devices?p=${page}&l=${limit}`
  return useSWR<ApiResponse<import('src/api/network/backend-client').DevicePage>>(
    key,
    () => backendOrMock(() => loadBackendDevicesPage({ page, limit }), '/api/network/devices')
  )
}

export function useDeviceDetail(deviceId?: string) {
  return useSWR<ApiResponse<{ device: Device; interfaces: NetworkInterface[]; routes: RouteEntry[] }>>(
    deviceId ? ['device-detail', deviceId] : null,
    () => backendOrMock(() => loadBackendDeviceDetail(deviceId as string), `/api/network/devices/${deviceId}`)
  )
}

export function useAgentMessages() {
  return useSWR<ApiResponse<AgentMessage[]>>('agent-messages', () =>
    backendOrMock(async () => [], '/api/network/agent/messages')
  )
}

export function useExecutionPlan() {
  return useSWR<ApiResponse<ExecutionPlan>>('execution-plan', () =>
    backendOrMock(async () => ({
      id: '',
      task: '',
      devices: [],
      plannedActions: [],
      risk: 'low' as const,
      requiresApproval: true,
    }), '/api/network/agent/plan')
  )
}

export function useTasks() {
  return useSWR<ApiResponse<Task[]>>('tasks', () =>
    backendOrMock(loadBackendTasks, '/api/network/tasks')
  )
}

export function useTaskDetail(taskId?: string) {
  return useSWR<ApiResponse<{ task: Task; steps: TaskStep[] }>>(
    taskId ? ['task-detail', taskId] : null,
    () => backendOrMock(() => loadBackendTaskDetail(taskId as string), `/api/network/tasks/${taskId}`)
  )
}

export function useTerminalSession() {
  return useSWR<ApiResponse<TerminalSession>>('/api/network/terminal/session', getFetcher)
}

export function runTerminalCommand(device: Device, command: string): Promise<TerminalCommandResult> {
  return runBackendTerminalCommand(device, command)
}

export function createTerminalSession(deviceId: string): Promise<TerminalLiveSession> {
  return createBackendTerminalSession(deviceId)
}

export function closeTerminalSession(sessionId: string): Promise<void> {
  return closeBackendTerminalSession(sessionId)
}

export function sendTerminalInput(sessionId: string, data: string) {
  return sendBackendTerminalInput(sessionId, data)
}

export function executeTerminalSessionCommand(session: TerminalLiveSession, command: string): Promise<TerminalCommandResult> {
  return executeBackendTerminalSessionCommand(session, command)
}

export function suggestTerminalCommand(sessionId: string, partial: string): Promise<TerminalSuggestion[]> {
  return suggestBackendTerminalCommand(sessionId, partial)
}

export { getApiBaseUrl }

export function useLabs() {
  return useSWR<ApiResponse<Lab[]>>('labs', () =>
    backendOrMock(loadBackendLabs, '/api/network/labs')
  )
}

export function useLabDetail(labId?: string) {
  return useSWR<ApiResponse<{ lab: Lab; topology: Topology }>>(
    labId ? ['lab-detail', labId] : null,
    () => backendOrMock(() => loadBackendLabDetail(labId as string), `/api/network/labs/${labId}`)
  )
}

export function useTopology(projectId?: string) {
  return useSWR<ApiResponse<Topology>>(
    projectId ? ['topology', projectId] : 'topology',
    () => backendOrMock(() => loadBackendTopology(projectId), projectId ? `/api/network/topology?project_id=${encodeURIComponent(projectId)}` : '/api/network/topology')
  )
}

export function saveTopologySnapshot(topology: Topology, projectId?: string) {
  return saveBackendTopology(topology, projectId)
}

export function useGns3Status() {
  return useSWR<ApiResponse<Gns3Status>>('gns3-status', () =>
    backendOrMock(async (): Promise<Gns3Status> => {
      const localConfig = await loadGns3LocalConfig()
      const projects = await loadGns3Projects()
      const counts = await Promise.allSettled(projects.map(async (project) => ({
        projectId: project.project_id,
        nodes: (await loadGns3Nodes(project.project_id)).length,
      })))
      const countMap = new Map(
        counts.flatMap((result) =>
          result.status === 'fulfilled' ? [[result.value.projectId, result.value.nodes] as const] : []
        )
      )
      return {
        server: localConfig.found ? 'connected' : 'disconnected',
        vm: 'connected',
        controller: localConfig.controller_url.replace('/v2', ''),
        projects: projects.map((p) => ({
          id: p.project_id,
          name: p.name,
          nodes: countMap.get(p.project_id) ?? p.nodes_count,
          status: (p.status === 'opened' ? 'running' : 'stopped') as 'running' | 'stopped',
          created: p.created_at,
        })),
      }
    }, '/api/network/gns3')
  )
}

export function loadGns3ProjectList(password?: string) {
  return loadGns3Projects(password)
}

export function openGns3ProjectAction(projectId: string, password?: string) {
  return openGns3Project(projectId, password)
}

export function closeGns3ProjectAction(projectId: string, password?: string) {
  return closeGns3Project(projectId, password)
}

export function deleteGns3ProjectAction(projectId: string, password?: string) {
  return deleteGns3Project(projectId, password)
}

export function createGns3ProjectAction(name: string, password?: string) {
  return createGns3Project(name, password)
}

export function loadGns3NodeList(projectId: string, password?: string) {
  return loadGns3Nodes(projectId, password)
}

export function startGns3NodeAction(projectId: string, nodeId: string, password?: string) {
  return startGns3Node(projectId, nodeId, password)
}

export function stopGns3NodeAction(projectId: string, nodeId: string, password?: string) {
  return stopGns3Node(projectId, nodeId, password)
}

export function deleteGns3NodeAction(projectId: string, nodeId: string, password?: string) {
  return deleteGns3Node(projectId, nodeId, password)
}

export function loadGns3LinkList(projectId: string, password?: string) {
  return loadGns3Links(projectId, password)
}

export function loadGns3SnapshotList(projectId: string, password?: string) {
  return loadGns3Snapshots(projectId, password)
}

export function createGns3SnapshotAction(projectId: string, name: string, password?: string) {
  return createGns3Snapshot(projectId, name, password)
}

export function restoreGns3SnapshotAction(projectId: string, snapshotId: string, password?: string) {
  return restoreGns3Snapshot(projectId, snapshotId, password)
}

export function testGns3ConnectionAction(password?: string) {
  return testGns3Connection(password)
}

export function clearGns3Cache() {
  clearGns3ConfigCache()
}

export function useContainerlab() {
  return useSWR<ApiResponse<ContainerlabInventory>>('containerlab', () =>
    backendOrMock(async (): Promise<ContainerlabInventory> => {
      const labs = await loadContainerlabLabs()
      return {
        topologyFiles: [],
        runningLabs: labs.map((l) => ({
          id: l.id,
          name: l.name,
          engine: 'containerlab' as const,
          nodes: l.nodes.length,
          status: l.status === 'deploying' || l.status === 'running' ? 'running' as const : 'stopped' as const,
          cpu: 0,
          ram: 0,
          created: l.created_at,
        })),
        nodes: labs.flatMap((l) => l.nodes.map((n) => ({
          name: n.name,
          kind: n.kind,
          image: '-',
          status: n.status === 'running' ? 'running' as const : 'stopped' as const,
        }))),
        images: [],
        yaml: '',
      }
    }, '/api/network/containerlab')
  )
}

export function deployContainerlabAction(name: string, topologyFile: string) {
  return deployContainerlabLab(name, topologyFile)
}

export function destroyContainerlabAction(labId: string) {
  return destroyContainerlabLab(labId)
}

export function useConfigurations() {
  return useSWR<ApiResponse<Configuration[]>>('configurations', () =>
    backendOrMock(loadBackendConfigurations, '/api/network/configurations')
  )
}

export function createConfigPlan(input: {
  deviceId: string
  commands: string[]
  verify?: Array<{ command: string; expect?: string }>
  saveOnSuccess?: boolean
  description?: string
}): Promise<ConfigPlan> {
  return createBackendConfigPlan(input)
}

export function getConfigPlan(planId: string): Promise<ConfigPlan> {
  return getBackendConfigPlan(planId)
}

export function applyConfigPlan(planId: string, approvedBy: string): Promise<ConfigApplyResult> {
  return applyBackendConfigPlan(planId, approvedBy)
}

export function rollbackConfigPlan(input: { deviceId: string; planId?: string; backupId?: string }): Promise<ConfigApplyResult> {
  return rollbackBackendConfigPlan(input)
}

export function useBackups() {
  return useSWR<ApiResponse<Backup[]>>('backups', () =>
    backendOrMock(loadBackendBackups, '/api/network/backups')
  )
}

export function useAlerts() {
  return useSWR<ApiResponse<Alert[]>>('alerts', () =>
    backendOrMock(loadBackendAlerts, '/api/network/alerts')
  )
}

export function useAuditLogs(query: AuditLogQuery = {}) {
  const { page = 1, limit = 25, search, action, device, result, source, user } = query
  const key = `audit-logs?p=${page}&l=${limit}&s=${search ?? ''}&a=${action ?? ''}&d=${device ?? ''}&r=${result ?? ''}&src=${source ?? ''}&u=${user ?? ''}`
  return useSWR<ApiResponse<import('src/api/network/backend-client').AuditLogPage>>(
    key,
    () => backendOrMock(() => loadBackendAuditLogs(query), '/api/network/audit')
  )
}

export function useCredentials() {
  return useSWR<ApiResponse<CredentialProfile[]>>('credentials', () =>
    backendOrMock(loadBackendCredentials, '/api/network/credentials')
  )
}

export function useDiscoveryResults() {
  return useSWR<ApiResponse<DiscoveryResult[]>>('discovery', () =>
    backendOrMock(loadBackendDiscoveryResults, '/api/network/discovery')
  )
}

export function useNetworkSettings() {
  return useSWR<ApiResponse<NetworkSettings>>('settings', () =>
    backendOrMock(loadBackendSettings, '/api/network/settings')
  )
}

export function sendAgentChatMessage(message: string, deviceId?: string): Promise<AgentMessage> {
  return sendAgentChat(message, deviceId)
}

export function createAgentExecutionPlan(intent: string, deviceIds: string[]): Promise<ExecutionPlan> {
  return createAgentPlan(intent, deviceIds)
}

export function createDevice(input: {
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
}) {
  return createBackendDevice(input)
}

export function updateDevice(
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
) {
  return updateBackendDevice(deviceId, input)
}

export function deleteDevice(deviceId: string) {
  return deleteBackendDevice(deviceId)
}

export function executeAgentExecutionPlan(planId: string, approvedBy: string) {
  return executeAgentPlan(planId, approvedBy)
}

export function cancelAgentExecutionPlan(planId: string, cancelledBy: string) {
  return cancelAgentPlan(planId, cancelledBy)
}

export function useNineRouterStatus() {
  return useSWR<ApiResponse<{ status: string; url?: string; error?: string }>>('ninerouter-status', () =>
    backendOrMock(getNineRouterStatus, '/api/network/ninerouter/status')
  )
}

export function useNineRouterFreeModels() {
  return useSWR<ApiResponse<NineRouterFreeModel[]>>('ninerouter-free-models', () =>
    backendOrMock(getNineRouterFreeModels, '/api/network/ninerouter/models/free')
  )
}

export function searchWeb(query: string, maxResults?: number, searchType?: string) {
  return searchNineRouter(query, maxResults, searchType)
}

export function fetchWebUrl(url: string, format?: string, maxCharacters?: number) {
  return fetchNineRouterUrl(url, format, maxCharacters)
}

export function useAgentTools() {
  return useSWR<ApiResponse<AgentTool[]>>('agent-tools', () =>
    backendOrMock(loadAgentTools, '/api/network/agent/tools')
  )
}

export function runAgentTool(toolName: string, params: Record<string, unknown>) {
  return executeAgentTool(toolName, params)
}
