import type { EnvironmentType } from './environment'
import type { Vendor } from './network'

export type DeployMode = 'lab' | 'staging' | 'production'

export interface DeployTarget {
  projectId: string
  projectName: string
  environment: EnvironmentType
  nodes: Array<{
    nodeId: string
    hostname: string
    vendor: Vendor
    managementIp?: string
  }>
}

export interface DeployPreview {
  id: string
  title: string
  mode: DeployMode
  risk: 'low' | 'medium' | 'high'
  requiresApproval: boolean
  requiresBackup: boolean
  steps: string[]
  targetCount: number
  summary: string
}

export interface DeployExecutionResult {
  id: string
  status: 'queued' | 'running' | 'success' | 'failed' | 'rolled_back'
  message: string
  startedAt: string
  completedAt?: string
}

