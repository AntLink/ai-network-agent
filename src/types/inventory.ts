import type { DeviceStatus, LabEngine, Vendor } from './network'
import type { EnvironmentType } from './environment'

export interface InventoryNodeCapability {
  key: string
  label: string
}

export interface InventoryNode {
  nodeId: string
  hostname: string
  vendor: Vendor
  platform: string
  status: DeviceStatus
  managementIp?: string
  console?: string
  nodeType?: string
  kind?: string
  projectId: string
  projectName: string
  environment: EnvironmentType
  engine?: LabEngine
  capabilities: InventoryNodeCapability[]
}

export interface InventoryLink {
  id: string
  source: string
  target: string
  sourceInterface: string
  targetInterface: string
  status: 'up' | 'down'
}

export interface ProjectInventory {
  projectId: string
  projectName: string
  environment: EnvironmentType
  source: 'live' | 'snapshot' | 'mixed'
  lastSyncedAt: string
  nodes: InventoryNode[]
  links: InventoryLink[]
}

export interface InventorySummary {
  totalProjects: number
  totalNodes: number
  onlineNodes: number
  offlineNodes: number
  warningNodes: number
}

