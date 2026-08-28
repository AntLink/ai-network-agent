import { apiRequest } from './network/backend-client'
import type { AgentMessageRecord, AgentSession } from 'src/types/agent'

export type { AgentMessageRecord, AgentSession } from 'src/types/agent'

function normalizeSession(item: Record<string, unknown>): AgentSession {
  return {
    id: String(item.id ?? ''),
    title: String(item.title ?? 'New Chat'),
    createdAt: String(item.created_at ?? ''),
    updatedAt: String(item.updated_at ?? ''),
    status: (item.status as AgentSession['status']) ?? 'idle',
    deviceIds: Array.isArray(item.device_ids) ? item.device_ids.map(String) : [],
    labId: item.lab_id ? String(item.lab_id) : undefined,
    projectId: item.project_id ? String(item.project_id) : undefined,
    environment: item.environment ? (String(item.environment) as AgentSession['environment']) : undefined,
    messageCount: Number(item.message_count ?? 0),
  }
}

function normalizeMessage(item: Record<string, unknown>): AgentMessageRecord {
  return {
    id: String(item.id ?? ''),
    sessionId: String(item.session_id ?? ''),
    role: (item.role as AgentMessageRecord['role']) ?? 'user',
    content: String(item.content ?? ''),
    type: item.type ? String(item.type) : undefined,
    createdAt: String(item.created_at ?? ''),
  }
}

export async function getAgentSessions(): Promise<AgentSession[]> {
  const payload = await apiRequest<Record<string, unknown>>('/api/v1/agent/sessions')
  const sessions = Array.isArray(payload?.sessions) ? payload.sessions : []
  return sessions
    .map((item) => normalizeSession(item as Record<string, unknown>))
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
}

export async function createAgentSession(input?: {
  title?: string
  deviceIds?: string[]
  labId?: string
  projectId?: string
  environment?: AgentSession['environment']
}): Promise<AgentSession> {
  const payload = await apiRequest<Record<string, unknown>>('/api/v1/agent/sessions', {
    method: 'POST',
    body: JSON.stringify({
      title: input?.title,
      device_ids: input?.deviceIds,
      lab_id: input?.labId,
      project_id: input?.projectId,
      environment: input?.environment,
    }),
  })
  return normalizeSession(payload)
}

export async function updateAgentSession(
  id: string,
  input: Partial<{
    title: string
    deviceIds: string[]
    labId?: string
    projectId?: string
    environment?: AgentSession['environment']
    status: AgentSession['status']
  }>,
): Promise<AgentSession> {
  const payload = await apiRequest<Record<string, unknown>>(`/api/v1/agent/sessions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({
      title: input.title,
      device_ids: input.deviceIds ?? [],
      lab_id: input.labId ?? null,
      project_id: input.projectId ?? null,
      environment: input.environment ?? null,
      status: input.status,
    }),
  })
  return normalizeSession(payload)
}

export async function getAgentSession(id: string): Promise<{
  session: AgentSession
  messages: AgentMessageRecord[]
}> {
  const payload = await apiRequest<Record<string, unknown>>(`/api/v1/agent/sessions/${id}`)
  const messages = Array.isArray(payload?.messages)
    ? payload.messages.map((item) => normalizeMessage(item as Record<string, unknown>))
    : []
  return {
    session: normalizeSession(payload),
    messages,
  }
}

export async function renameAgentSession(id: string, title: string): Promise<AgentSession> {
  const payload = await apiRequest<Record<string, unknown>>(`/api/v1/agent/sessions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
  return normalizeSession(payload)
}

export async function deleteAgentSession(id: string): Promise<void> {
  await apiRequest<unknown>(`/api/v1/agent/sessions/${id}`, { method: 'DELETE' })
}

export async function getAgentSessionMessages(id: string): Promise<AgentMessageRecord[]> {
  const payload = await apiRequest<Record<string, unknown>>(`/api/v1/agent/sessions/${id}/messages`)
  return Array.isArray(payload?.messages)
    ? payload.messages.map((item) => normalizeMessage(item as Record<string, unknown>))
    : []
}

export async function appendAgentSessionMessage(
  id: string,
  message: Omit<AgentMessageRecord, 'sessionId'> & { sessionId?: string },
): Promise<AgentMessageRecord> {
  const payload = await apiRequest<Record<string, unknown>>(`/api/v1/agent/sessions/${id}/messages`, {
    method: 'POST',
    body: JSON.stringify({
      id: message.id,
      role: message.role,
      content: message.content,
      type: message.type,
      created_at: message.createdAt,
    }),
  })
  return normalizeMessage(payload)
}
