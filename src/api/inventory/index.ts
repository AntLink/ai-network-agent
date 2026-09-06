import useSWR from 'swr'
import { backendOrMock, loadBackendTopology } from 'src/api/network/backend-client'
import type { ApiResponse } from 'src/types/network'
import type { EnvironmentType } from 'src/types/environment'
import type { InventoryNode, ProjectInventory } from 'src/types/inventory'
import { getEnvironmentProfile, resolveEnvironmentFromProjectId } from 'src/api/environments'

function capabilityList(vendor: InventoryNode['vendor'], kind?: string): InventoryNode['capabilities'] {
  if (vendor === 'cisco') {
    return [
      { key: 'ssh', label: 'SSH' },
      { key: 'routing', label: 'Routing' },
      { key: 'ospf', label: 'OSPF' },
      { key: 'vlan', label: 'VLAN' },
    ]
  }

  if (vendor === 'mikrotik') {
    return [
      { key: 'ssh', label: 'SSH' },
      { key: 'routeros', label: 'RouterOS' },
      { key: 'firewall', label: 'Firewall' },
      { key: 'routing', label: 'Routing' },
    ]
  }

  if (vendor === 'aruba') {
    return [
      { key: 'ssh', label: 'SSH' },
      { key: 'switching', label: 'Switching' },
      { key: 'vlan', label: 'VLAN' },
    ]
  }

  if (vendor === 'linux') {
    return [
      { key: 'ssh', label: 'SSH' },
      { key: 'shell', label: 'Shell' },
      { key: 'networking', label: 'Networking' },
    ]
  }

  return [{ key: kind ?? 'generic', label: 'General' }]
}

function normalizeInventoryNode(item: Record<string, unknown>, projectId: string, projectName: string, environment: EnvironmentType, engine?: string): InventoryNode {
  const hostname = String(item.hostname ?? item.name ?? 'Unknown')
  const vendor = String(item.vendor ?? 'other') as InventoryNode['vendor']
  const kind = String(item.kind ?? '')
  const nodeType = String(item.nodeType ?? item.node_type ?? '')
  return {
    nodeId: String(item.id ?? item.node_id ?? hostname),
    hostname,
    vendor,
    platform: String(item.platform ?? item.node_type ?? item.kind ?? 'Unknown'),
    status: (String(item.status ?? 'unknown') as InventoryNode['status']),
    managementIp: item.ip ? String(item.ip) : undefined,
    console: item.console ? String(item.console) : undefined,
    nodeType: nodeType || undefined,
    kind: kind || undefined,
    projectId,
    projectName,
    environment,
    engine: engine as InventoryNode['engine'],
    capabilities: capabilityList(vendor, kind || nodeType),
  }
}

export async function loadProjectInventory(projectId?: string): Promise<ProjectInventory> {
  const topology = await backendOrMock(() => loadBackendTopology(projectId), projectId ? `/api/network/topology?project_id=${encodeURIComponent(projectId)}` : '/api/network/topology')
  const activeProjectId = topology.data.projectId ?? projectId ?? topology.data.id
  const projectName = topology.data.name
  const environment = resolveEnvironmentFromProjectId(activeProjectId)
  const profile = getEnvironmentProfile(environment)
  const nodes = topology.data.nodes.map((node) =>
    normalizeInventoryNode(
      {
        id: node.id,
        hostname: node.hostname,
        vendor: node.vendor,
        kind: node.kind,
        nodeType: node.nodeType,
        status: node.status,
        ip: node.ip,
      },
      activeProjectId,
      projectName,
      environment,
      profile.engine,
    )
  )

  return {
    projectId: activeProjectId,
    projectName,
    environment,
    source: projectId ? 'mixed' : 'snapshot',
    lastSyncedAt: new Date().toISOString(),
    nodes,
    links: topology.data.links.map((link) => ({
      id: link.id,
      source: link.source,
      target: link.target,
      sourceInterface: link.sourceInterface,
      targetInterface: link.targetInterface,
      status: link.status,
    })),
  }
}

export async function loadInventorySummary(projectId?: string): Promise<{
  inventory: ProjectInventory
  online: number
  offline: number
  warning: number
}> {
  const inventory = await loadProjectInventory(projectId)
  const online = inventory.nodes.filter((node) => node.status === 'online').length
  const offline = inventory.nodes.filter((node) => node.status === 'offline').length
  const warning = inventory.nodes.filter((node) => node.status === 'warning').length
  return { inventory, online, offline, warning }
}

export function useProjectInventory(projectId?: string) {
  return useSWR<ApiResponse<ProjectInventory>>(
    ['project-inventory', projectId ?? 'default'],
    async () => ({
      status: 200,
      data: await loadProjectInventory(projectId),
    })
  )
}

export function useInventorySummary(projectId?: string) {
  return useSWR<ApiResponse<{ inventory: ProjectInventory; online: number; offline: number; warning: number }>>(
    ['inventory-summary', projectId ?? 'default'],
    async () => ({
      status: 200,
      data: await loadInventorySummary(projectId),
    })
  )
}
