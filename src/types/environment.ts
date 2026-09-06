import type { LabEngine, Vendor } from './network'

export type EnvironmentType = 'lab' | 'staging' | 'production'

export type EnvironmentRisk = 'low' | 'medium' | 'high'

export interface EnvironmentPolicy {
  approvalRequired: boolean
  backupRequired: boolean
  rollbackEnabled: boolean
  destructiveCommandsAllowed: boolean
  postChangeValidation: boolean
}

export interface EnvironmentProfile {
  id: EnvironmentType
  name: string
  description: string
  engine?: LabEngine
  color: string
  badge: string
  policy: EnvironmentPolicy
}

export interface EnvironmentProjectBinding {
  projectId: string
  projectName: string
  environment: EnvironmentType
  labEngine?: LabEngine
  vendorFocus?: Vendor[]
  lastSyncedAt: string
}

export interface EnvironmentWorkflowStep {
  key: string
  title: string
  status: 'pending' | 'running' | 'success' | 'failed'
  description: string
}

