import type {
  ChatModelAdapter,
  ChatModelRunOptions,
  ChatModelRunResult,
} from '@assistant-ui/react'
import type { AgentStreamEvent } from 'src/types/agent'
import type { AgentSession, AgentIntent, AgentToolOutputEvent } from 'src/types/agent'
import { getApiBaseUrl } from 'src/api/network/backend-client'
import { appendAgentSessionMessage, createAgentSession } from 'src/api/agent'

/**
 * Creates a ChatModelAdapter that streams assistant-ui messages from the
 * AI Network Agent FastAPI backend SSE endpoint (`/api/v1/agent/chat/stream`).
 */
export function createNetworkChatAdapter(
  getContext?: () => {
    sessionId?: string
    deviceId?: string
    deviceIds?: string[]
    labId?: string
    projectId?: string
    environment?: 'lab' | 'staging' | 'production'
    mode?: string
  },
  callbacks?: {
    onRunStart?: () => void
    onTextChunk?: (text: string) => void
    onEvent?: (event: AgentStreamEvent) => void
    onSessionCreated?: (session: AgentSession) => void
    onMessagePersisted?: (messageId: string) => void
  },
): ChatModelAdapter {
  return {
    async *run(options: ChatModelRunOptions): AsyncGenerator<ChatModelRunResult, void> {
      const { messages, abortSignal } = options
      callbacks?.onRunStart?.()

      const history = messages.map((message) => {
        const text = message.content
          .map((part) => (part.type === 'text' ? part.text : ''))
          .filter(Boolean)
          .join('\n')
        return { role: message.role, text }
      })

      const lastUser = [...history].reverse().find((m) => m.role === 'user')
      const prompt = lastUser?.text ?? ''
      const context = getContext?.() ?? {}
      let sessionId = context.sessionId
      const promptTitle = buildSessionTitle(prompt)

      if (!sessionId) {
        const created = await createAgentSession({
          title: promptTitle,
          deviceIds: context.deviceIds ?? (context.deviceId ? [context.deviceId] : []),
          labId: context.labId,
          projectId: context.projectId,
          environment: context.environment,
        })
        sessionId = created.id
        callbacks?.onSessionCreated?.(created)
      }

      const userMessageId = extractMessageId(lastUser)
      if (sessionId && userMessageId && prompt.trim()) {
        await appendAgentSessionMessage(sessionId, {
          id: userMessageId,
          role: 'user',
          content: prompt,
          type: 'message',
          createdAt: new Date().toISOString(),
        }).then(() => {
          callbacks?.onMessagePersisted?.(userMessageId)
        }).catch(() => undefined)
      }

      const controller = new AbortController()
      const onAbort = () => controller.abort()
      abortSignal?.addEventListener('abort', onAbort)

      const emitEvent = (event: AgentStreamEvent) => {
        callbacks?.onEvent?.(event)
      }

      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/agent/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: prompt,
              history,
              session_id: sessionId,
              device_id: context.deviceId ?? '',
              device_ids: context.deviceIds ?? [],
              lab_id: context.labId ?? '',
              project_id: context.projectId ?? '',
              environment: context.environment ?? 'lab',
              mode: context.mode ?? 'guarded',
            }),
          signal: controller.signal,
        })

        if (!response.ok || !response.body) {
          throw new Error(`Agent backend responded ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed.startsWith('data: ')) continue

            let raw: Record<string, unknown>
            try {
              raw = JSON.parse(trimmed.slice(6)) as Record<string, unknown>
            } catch {
              continue
            }

            const eventType = normalizeStreamEventType(String(raw.type ?? raw.event ?? raw.kind ?? ''))
            const createdAt = String(raw.createdAt ?? raw.created_at ?? new Date().toISOString())
            const eventId = String(raw.id ?? raw.event_id ?? raw.taskId ?? raw.task_id ?? `${eventType}-${Date.now()}`)

            if (eventType === 'text' && typeof raw.text === 'string') {
              callbacks?.onTextChunk?.(raw.text)
              yield { content: [{ type: 'text', text: raw.text }] }
              continue
            }

            if (eventType === 'plan') {
              emitEvent({
                id: eventId,
                type: 'plan',
                task: String(raw.task ?? raw.title ?? raw.message ?? ''),
                devices: extractStringArray(raw.devices ?? raw.device_ids ?? raw.targets),
                plannedActions: extractStringArray(raw.plannedActions ?? raw.planned_actions ?? raw.steps ?? raw.actions),
                risk: (String(raw.risk ?? raw.risk_level ?? 'low').toLowerCase() as 'low' | 'medium' | 'high'),
                requiresApproval: Boolean(raw.requiresApproval ?? raw.requires_approval),
                createdAt,
              })
              continue
            }

            if (eventType === 'workflow_state') {
              emitEvent({
                id: eventId,
                type: 'workflow_state',
                state: normalizeWorkflowState(raw.state ?? raw.workflow_state ?? raw.phase ?? raw.status ?? raw.step),
                label: String(raw.label ?? raw.title ?? raw.name ?? 'Workflow'),
                detail: String(raw.detail ?? raw.message ?? raw.summary ?? ''),
                activeIndex: Number(raw.activeIndex ?? raw.active_index ?? raw.index ?? 0),
                eventsCount: Number(raw.eventsCount ?? raw.events_count ?? raw.count ?? 0),
                createdAt,
              })
              continue
            }

            if (eventType === 'approval') {
              emitEvent({
                id: eventId,
                type: 'approval',
                taskId: String(raw.taskId ?? raw.task_id ?? ''),
                task: String(raw.task ?? raw.title ?? raw.message ?? ''),
                devices: extractStringArray(raw.devices ?? raw.device_ids ?? raw.targets),
                risk: (String(raw.risk ?? 'low').toLowerCase() as 'low' | 'medium' | 'high'),
                status: (String(raw.status ?? 'required').toLowerCase() as 'required' | 'approved' | 'cancelled'),
                message: String(raw.message ?? ''),
                commands: extractOptionalStringArray(raw.commands ?? raw.command ?? raw.preview_commands),
                createdAt,
              })
              continue
            }

            if (eventType === 'task_progress' || eventType === 'task_created' || eventType === 'task_updated' || eventType === 'task_completed') {
              emitEvent({
                id: eventId,
                type: 'task_progress',
                taskId: String(raw.taskId ?? raw.task_id ?? ''),
                step: String(raw.step ?? raw.stage ?? raw.phase ?? eventType.replace(/_/g, ' ')),
                status: normalizeTaskProgressStatus(eventType, raw.status),
                message: String(raw.message ?? raw.detail ?? raw.summary ?? ''),
                order: Number(raw.order ?? raw.step_order ?? raw.index ?? 0),
                total: Number(raw.total ?? raw.step_total ?? raw.count ?? 0),
                createdAt,
              })
              continue
            }

            if (eventType === 'command_output' || eventType === 'tool_output' || eventType === 'tool') {
              if (eventType === 'tool_output' || eventType === 'tool') {
                emitEvent({
                  id: eventId,
                  type: 'tool_output',
                  taskId: String(raw.taskId ?? raw.task_id ?? '') || undefined,
                  tool: String(raw.tool ?? raw.name ?? ''),
                  policy: normalizePolicy(raw.policy),
                  evidence: String(raw.evidence ?? 'backend_snapshot'),
                  target: isPlainObject(raw.target) ? (raw.target as AgentToolOutputEvent['target']) : undefined,
                  summary: typeof raw.summary === 'string' ? raw.summary : '',
                  data: raw.data,
                  raw: typeof raw.raw === 'string' ? raw.raw : undefined,
                  error: raw.error == null ? null : String(raw.error),
                  status: normalizeToolStatus(raw.status),
                  createdAt,
                })
                continue
              }
              emitEvent({
                id: eventId,
                type: 'command_output',
                taskId: String(raw.taskId ?? raw.task_id ?? '') || undefined,
                device: String(raw.device ?? raw.hostname ?? raw.node ?? ''),
                deviceId: String(raw.deviceId ?? raw.device_id ?? '') || undefined,
                command: String(raw.command ?? raw.cli ?? raw.tool ?? ''),
                status: (String(raw.status ?? 'running').toLowerCase() as 'ok' | 'failed' | 'blocked' | 'running'),
                output: extractOutputValue(raw.output ?? raw.outputs ?? raw.text ?? raw.message ?? raw.data),
                createdAt,
              })
              continue
            }

            if (eventType === 'analysis' || eventType === 'start') {
              const container = (eventType === 'start' ? raw.analysis : raw.intent) ?? raw.intent
              const intentRaw =
                isPlainObject(container) && isPlainObject(container.intent) ? container.intent : container
              if (isPlainObject(intentRaw)) {
                emitEvent({
                  id: eventId,
                  type: 'analysis',
                  intent: normalizeIntent(intentRaw as Record<string, unknown>),
                  createdAt,
                })
              }
              continue
            }

            if (eventType === 'device_state' || eventType === 'device_snapshot' || eventType === 'state_snapshot') {
              const content =
                typeof raw.content === 'string'
                  ? raw.content
                  : typeof raw.text === 'string'
                    ? raw.text
                    : JSON.stringify(raw.data ?? raw.state ?? raw.snapshot ?? raw, null, 2)
              emitEvent({
                id: eventId,
                type: 'device_state',
                taskId: String(raw.taskId ?? raw.task_id ?? '') || undefined,
                device: String(raw.device ?? raw.hostname ?? raw.node ?? ''),
                deviceId: String(raw.deviceId ?? raw.device_id ?? '') || undefined,
                vendor: normalizeVendor(String(raw.vendor ?? raw.platform ?? 'other')),
                platform: String(raw.platform ?? raw.os ?? ''),
                summary: String(raw.summary ?? raw.message ?? ''),
                content,
                createdAt,
              })
              continue
            }

            if (eventType === 'verification' || eventType === 'verify' || eventType === 'post_check' || eventType === 'validation') {
              emitEvent({
                id: eventId,
                type: 'verification',
                taskId: String(raw.taskId ?? raw.task_id ?? '') || undefined,
                device: String(raw.device ?? raw.hostname ?? raw.node ?? ''),
                status: normalizeVerificationStatus(raw.status ?? raw.result ?? raw.state ?? eventType),
                message: String(raw.message ?? raw.summary ?? raw.detail ?? ''),
                checks: extractOptionalStringArray(raw.checks ?? raw.results ?? raw.verifications),
                createdAt,
              })
              continue
            }

            if (eventType === 'error') {
              throw new Error(String(raw.message ?? 'Stream error'))
            }
          }
        }
      } finally {
        abortSignal?.removeEventListener('abort', onAbort)
      }
    },
  }
}

export const networkChatAdapter = createNetworkChatAdapter()

function buildSessionTitle(prompt: string): string | undefined {
  const normalized = prompt.replace(/\s+/g, ' ').trim()
  if (!normalized) return undefined

  const cleaned = normalized
    .replace(/^(tolong|please|bantu|cek|lihat|tampilkan|show|inspect|analyze)\s+/i, '')
    .trim()

  const titleSource = cleaned || normalized
  const clipped = titleSource.slice(0, 52).replace(/[.,;:!?]+$/g, '')
  if (!clipped) return undefined
  return clipped
}

function normalizeVendor(value: string) {
  const text = value.toLowerCase()
  if (text.includes('mikrotik') || text.includes('routeros')) return 'mikrotik'
  if (text.includes('cisco') || text.includes('ios')) return 'cisco'
  if (text.includes('aruba') || text.includes('aos-cx')) return 'aruba'
  if (text.includes('linux') || text.includes('ubuntu') || text.includes('debian')) return 'linux'
  return 'other'
}

function extractMessageId(message: unknown): string | undefined {
  if (!message || typeof message !== 'object') return undefined
  const candidate = (message as { id?: unknown }).id
  return typeof candidate === 'string' && candidate.trim() ? candidate : undefined
}

function normalizeStreamEventType(value: string) {
  const normalized = value.toLowerCase()
  if (['text', 'message', 'assistant_message', 'delta', 'text_delta'].includes(normalized)) return 'text'
  if (['plan', 'execution_plan', 'agent_plan'].includes(normalized)) return 'plan'
  if (['workflow_state', 'workflow-state', 'workflow', 'agent_state', 'agent-state'].includes(normalized)) return 'workflow_state'
  if (['approval', 'approval_required', 'approval_request'].includes(normalized)) return 'approval'
  if (['task_progress', 'task-created', 'task_created', 'task-updated', 'task_updated', 'task_completed', 'task-completed'].includes(normalized)) return normalized.replace(/-/g, '_')
  if (['command_output', 'command-output'].includes(normalized)) return 'command_output'
  if (['tool_output', 'tool-output', 'tool'].includes(normalized)) return 'tool_output'
  if (['device_state', 'device-state', 'device_snapshot', 'device-snapshot', 'state_snapshot', 'state-snapshot'].includes(normalized)) return 'device_state'
  if (['verification', 'verify', 'post_check', 'post-check', 'validation'].includes(normalized)) return 'verification'
  if (['analysis', 'start'].includes(normalized)) return normalized
  if (['error', 'fail', 'failed'].includes(normalized)) return 'error'
  return normalized
}

function extractStringArray(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String).filter((item) => item.trim().length > 0)
  if (typeof value === 'string' && value.trim()) return [value]
  return []
}

function extractOptionalStringArray(value: unknown): string[] | undefined {
  const items = extractStringArray(value)
  return items.length ? items : undefined
}

function extractOutputValue(value: unknown): string[] | string {
  if (Array.isArray(value)) return value.map(String)
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

function normalizeTaskProgressStatus(eventType: string, statusValue: unknown): 'queued' | 'running' | 'success' | 'failed' {
  const status = String(statusValue ?? '').toLowerCase()
  if (status.includes('success') || status.includes('done') || eventType === 'task_completed') return 'success'
  if (status.includes('fail') || status.includes('error')) return 'failed'
  if (status.includes('queue') || eventType === 'task_created') return 'queued'
  return 'running'
}

function normalizeVerificationStatus(value: unknown): 'passed' | 'warning' | 'failed' | 'running' {
  const status = String(value ?? '').toLowerCase()
  if (status.includes('pass') || status.includes('ok') || status.includes('success')) return 'passed'
  if (status.includes('warn')) return 'warning'
  if (status.includes('fail') || status.includes('error')) return 'failed'
  return 'running'
}

function normalizeWorkflowState(value: unknown) {
  const status = String(value ?? '').toLowerCase()
  if (status.includes('think')) return 'thinking'
  if (status.includes('plan')) return 'planning'
  if (status.includes('approve') || status.includes('wait')) return 'waiting_approval'
  if (status.includes('run')) return 'running'
  if (status.includes('verify') || status.includes('check')) return 'verifying'
  if (status.includes('fail') || status.includes('error')) return 'failed'
  return 'completed'
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function normalizePolicy(value: unknown): AgentIntent['policy'] {
  const policy = String(value ?? '').toUpperCase()
  if (policy === 'APPROVAL_REQUIRED') return 'APPROVAL_REQUIRED'
  if (policy === 'BLOCKED') return 'BLOCKED'
  if (policy === 'GUARDED') return 'GUARDED'
  return 'READ_ONLY'
}

function normalizeToolStatus(value: unknown): AgentToolOutputEvent['status'] {
  const status = String(value ?? 'ok').toLowerCase()
  if (status.includes('approval')) return 'approval_required'
  if (status.includes('block')) return 'blocked'
  if (status.includes('not_implemented') || status.includes('not implemented')) return 'not_implemented'
  if (status.includes('fail') || status.includes('error')) return 'failed'
  return 'ok'
}

function normalizeIntent(raw: Record<string, unknown>): AgentIntent {
  const targets = Array.isArray(raw.targets)
    ? raw.targets.filter(isPlainObject).map((target) => ({
        kind: String(target.kind ?? 'device'),
        id: typeof target.id === 'string' ? target.id : undefined,
        name: typeof target.name === 'string' ? target.name : undefined,
        vendor: typeof target.vendor === 'string' ? target.vendor : undefined,
      }))
    : []
  const risk = String(raw.risk ?? 'low').toLowerCase() as AgentIntent['risk']
  return {
    type: String(raw.type ?? 'unknown'),
    targets,
    policy: normalizePolicy(raw.policy),
    confidence: Number(raw.confidence ?? 0),
    reason: String(raw.reason ?? ''),
    risk: risk === 'medium' || risk === 'high' || risk === 'critical' ? risk : 'low',
    ambiguous: Boolean(raw.ambiguous),
    missingContext: typeof raw.missing_context === 'string' ? raw.missing_context : undefined,
    suggestedTools: Array.isArray(raw.suggested_tools) ? raw.suggested_tools.map(String) : undefined,
  }
}
