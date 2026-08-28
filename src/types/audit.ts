import type { EnvironmentType } from './environment'

export interface AuditEntry {
  id: string
  time: string
  user: string
  action: string
  device: string
  result: 'success' | 'failed' | 'pending'
  source: 'user' | 'ai-agent' | 'automation' | 'api'
  details: string
  projectId?: string
  environment?: EnvironmentType
}

export interface AuditTimeline {
  entries: AuditEntry[]
  total: number
}

