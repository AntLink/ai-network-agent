import type { Vendor } from './network'

export interface AgentSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  status: 'idle' | 'running' | 'error'
  deviceIds: string[]
  labId?: string
  projectId?: string
  environment?: 'lab' | 'staging' | 'production'
  messageCount: number
}

export interface AgentMessageRecord {
  id: string
  sessionId: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  type?: string
  createdAt: string
}

export interface AgentExecutionPlanEvent {
  id: string
  type: 'plan'
  task: string
  devices: string[]
  plannedActions: string[]
  risk: 'low' | 'medium' | 'high'
  requiresApproval: boolean
  createdAt: string
}

export interface AgentApprovalEvent {
  id: string
  type: 'approval'
  taskId: string
  task: string
  devices: string[]
  risk: 'low' | 'medium' | 'high'
  status: 'required' | 'approved' | 'cancelled'
  message: string
  commands?: string[]
  createdAt: string
}

export interface AgentTaskProgressEvent {
  id: string
  type: 'task_progress'
  taskId: string
  step: string
  status: 'queued' | 'running' | 'success' | 'failed'
  message: string
  order: number
  total: number
  createdAt: string
}

export interface AgentCommandOutputEvent {
  id: string
  type: 'command_output'
  taskId?: string
  device?: string
  deviceId?: string
  command?: string
  status?: 'ok' | 'failed' | 'blocked' | 'running'
  output: string[] | string
  createdAt: string
}

export interface AgentDeviceStateEvent {
  id: string
  type: 'device_state'
  taskId?: string
  device?: string
  deviceId?: string
  vendor?: Vendor
  platform?: string
  summary?: string
  content: string
  createdAt: string
}

export interface AgentVerificationEvent {
  id: string
  type: 'verification'
  taskId?: string
  device?: string
  status: 'passed' | 'warning' | 'failed' | 'running'
  message: string
  checks?: string[]
  createdAt: string
}

export interface AgentTextEvent {
  id: string
  type: 'text'
  text: string
  createdAt: string
}

export interface AgentIntentTarget {
  kind: string
  id?: string
  name?: string
  vendor?: string
}

export interface AgentIntent {
  type: string
  targets: AgentIntentTarget[]
  policy: 'READ_ONLY' | 'GUARDED' | 'APPROVAL_REQUIRED' | 'BLOCKED'
  confidence: number
  reason: string
  risk: 'low' | 'medium' | 'high' | 'critical'
  ambiguous: boolean
  missingContext?: string
  suggestedTools?: string[]
}

export interface AgentAnalysisEvent {
  id: string
  type: 'analysis'
  intent: AgentIntent
  createdAt: string
}

export interface AgentToolOutputEvent {
  id: string
  type: 'tool_output'
  taskId?: string
  tool: string
  policy: 'READ_ONLY' | 'GUARDED' | 'APPROVAL_REQUIRED' | 'BLOCKED'
  evidence: string
  target?: { deviceId?: string; hostname?: string; [key: string]: unknown }
  summary?: string
  data?: unknown
  raw?: string
  error?: string | null
  status: 'ok' | 'failed' | 'blocked' | 'approval_required' | 'not_implemented'
  createdAt: string
}

export interface AgentWorkflowEvent {
  id: string
  type: 'workflow_state'
  state: AgentWorkflowState
  label: string
  detail: string
  activeIndex: number
  eventsCount: number
  createdAt: string
}

export type AgentWorkflowState =
  | 'thinking'
  | 'planning'
  | 'waiting_approval'
  | 'running'
  | 'verifying'
  | 'completed'
  | 'failed'

export interface AgentWorkflowSnapshot {
  state: AgentWorkflowState
  label: string
  detail: string
  activeIndex: number
  eventsCount: number
}

export type AgentStreamEvent =
  | AgentExecutionPlanEvent
  | AgentApprovalEvent
  | AgentTaskProgressEvent
  | AgentCommandOutputEvent
  | AgentDeviceStateEvent
  | AgentVerificationEvent
  | AgentWorkflowEvent
  | AgentAnalysisEvent
  | AgentToolOutputEvent
  | AgentTextEvent
