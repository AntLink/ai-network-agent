import useSWR from 'swr'
import { backendOrMock, loadBackendAuditLogs } from 'src/api/network/backend-client'
import type { ApiResponse } from 'src/types/network'
import type { AuditEntry, AuditTimeline } from 'src/types/audit'

function normalizeAuditEntry(item: Record<string, unknown>): AuditEntry {
  return {
    id: String(item.id ?? ''),
    time: String(item.time ?? item.created_at ?? ''),
    user: String(item.user ?? 'system'),
    action: String(item.action ?? ''),
    device: String(item.device ?? ''),
    result: (String(item.result ?? 'pending') as AuditEntry['result']),
    source: (String(item.source ?? 'automation') as AuditEntry['source']),
    details: String(item.details ?? ''),
    projectId: item.project_id ? String(item.project_id) : undefined,
    environment: item.environment ? (String(item.environment) as AuditEntry['environment']) : undefined,
  }
}

export async function loadAuditTimeline(): Promise<AuditTimeline> {
  const payload = await backendOrMock(() => loadBackendAuditLogs({ limit: 50 }), '/api/network/audit')
  const data = payload.data as unknown
  if (Array.isArray(data)) {
    const entries = data.map((item) => normalizeAuditEntry(item as Record<string, unknown>))
    return { entries, total: entries.length }
  }

  const page = data && typeof data === 'object' ? (data as Record<string, unknown>) : {}
  const entries = Array.isArray(page.logs)
    ? page.logs.map((item) => normalizeAuditEntry(item as Record<string, unknown>))
    : Array.isArray(page.items)
      ? page.items.map((item) => normalizeAuditEntry(item as Record<string, unknown>))
      : []
  return { entries, total: Number(page.total ?? entries.length) }
}

export function useAuditTimeline() {
  return useSWR<ApiResponse<AuditTimeline>>('audit-timeline', async () => ({
    status: 200,
    data: await loadAuditTimeline(),
  }))
}
