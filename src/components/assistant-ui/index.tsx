import { useEffect, useMemo, useRef, useState } from 'react'
import { AssistantRuntimeProvider, useLocalRuntime, type ThreadMessageLike } from '@assistant-ui/react'
import { createNetworkChatAdapter } from './chat-adapter'
import { NetworkChatThread } from './thread'
import { appendAgentSessionMessage, getAgentSession, type AgentMessageRecord } from 'src/api/agent'
import type { AgentSession, AgentStreamEvent, AgentWorkflowSnapshot } from 'src/types/agent'
import { normalizeMarkdownTables } from './message-renderers/utils'

function toThreadMessageLike(message: AgentMessageRecord): ThreadMessageLike {
  return {
    role: message.role as 'user' | 'assistant',
    content: [{ type: 'text', text: normalizeMarkdownTables(message.content) }],
  }
}

function buildMessageTextMap(messages: AgentMessageRecord[]): Record<string, string> {
  return messages.reduce<Record<string, string>>((acc, message) => {
    acc[message.id] = normalizeMarkdownTables(message.content)
    return acc
  }, {})
}

function pickFinalMessageText(runtimeText: string, liveText: string): string {
  const runtime = runtimeText.trim()
  const live = liveText.trim()

  if (live.length >= runtime.length) return live
  return runtime
}

/**
 * Wraps the assistant-ui runtime (custom backend adapter) around the
 * ChatGPT-style thread UI. Persists messages to the backend per session.
 */
export function NetworkChat({
  sessionId,
  deviceId,
  deviceIds,
  labId,
  projectId,
  environment,
  mode,
  onSessionCreated,
  onSessionUpdated,
  onWorkflowChange,
}: {
  sessionId?: string
  deviceId?: string
  deviceIds?: string[]
  labId?: string
  projectId?: string
  environment?: 'lab' | 'staging' | 'production'
  mode?: string
  onSessionCreated?: (session: AgentSession) => void
  onSessionUpdated?: (session: AgentSession) => void
  onWorkflowChange?: (snapshot: AgentWorkflowSnapshot) => void
}) {
  const contextRef = useRef({ sessionId, deviceId, deviceIds, labId, projectId, environment, mode })
  contextRef.current = { sessionId, deviceId, deviceIds, labId, projectId, environment, mode }
  const [streamEvents, setStreamEvents] = useState<AgentStreamEvent[]>([])
  const [liveText, setLiveText] = useState('')
  const liveTextRef = useRef('')
  const [persistedTextsById, setPersistedTextsById] = useState<Record<string, string>>({})
  const skipNextEmptySessionLoadRef = useRef(false)
  const savedMessageIdsRef = useRef<Set<string>>(new Set())

  const adapter = useMemo(
    () =>
          createNetworkChatAdapter(
            () => contextRef.current,
            {
              onRunStart: () => {
                setStreamEvents([])
            setLiveText('')
            liveTextRef.current = ''
          },
          onTextChunk: (text) => {
            liveTextRef.current += text
            setLiveText((currentText) => `${currentText}${text}`)
          },
              onSessionCreated: (session) => {
                contextRef.current.sessionId = session.id
                skipNextEmptySessionLoadRef.current = true
                onSessionCreated?.(session)
              },
              onMessagePersisted: (messageId) => {
                savedMessageIdsRef.current.add(messageId)
              },
              onEvent: (event) => {
                setStreamEvents((current) => {
                  const next = current.filter((item) => item.id !== event.id)
                  return [...next, event]
                })
          },
        },
      ),
    [],
  )

  const runtime = useLocalRuntime(adapter)

  // Load session messages into the thread when the active session changes.
  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    setStreamEvents([])
    setLiveText('')
    liveTextRef.current = ''
    getAgentSession(sessionId)
      .then(({ messages }) => {
        if (cancelled) return
        if (messages.length === 0 && skipNextEmptySessionLoadRef.current) {
          skipNextEmptySessionLoadRef.current = false
          return
        }
        skipNextEmptySessionLoadRef.current = false
        const threadMessages = messages.map(toThreadMessageLike)
        runtime.thread.reset(threadMessages)
        setPersistedTextsById(buildMessageTextMap(messages))
        savedMessageIdsRef.current = new Set(messages.map((message) => message.id))
      })
      .catch(() => {
        // session not found or backend down; leave thread empty
      })
    return () => {
      cancelled = true
    }
  }, [sessionId, runtime])

  // Persist user/assistant messages to the backend as each run completes.
  useEffect(() => {
    const runEndHandler = () => {
      const currentSessionId = contextRef.current.sessionId ?? sessionId
      if (!currentSessionId) return

      const threadMessages = runtime.thread.getState().messages
      const latestLiveText = liveTextRef.current
      const knownMessageIds = savedMessageIdsRef.current

      const pendingMessages = threadMessages.filter((message) => !knownMessageIds.has(message.id))
      if (!pendingMessages.length) return

      Promise.all(
        pendingMessages.map((message) => {
          const runtimeText = message.content
            .filter((part) => part.type === 'text')
            .map((part) => (part as { type: 'text'; text: string }).text)
            .join('\n')
          const text =
            message.role === 'assistant'
              ? pickFinalMessageText(runtimeText, latestLiveText)
              : runtimeText
          if (text.trim()) {
            knownMessageIds.add(message.id)
          }
          return appendAgentSessionMessage(currentSessionId, {
            id: message.id,
            role: message.role === 'user' ? 'user' : 'assistant',
            content: text,
            type: 'message',
            createdAt: new Date().toISOString(),
          }).catch(() => undefined)
        }),
      )
        .catch(() => undefined)
        .finally(() => {
          void getAgentSession(currentSessionId)
            .then(({ session, messages }) => {
              if (!messages.length) return
              setPersistedTextsById(buildMessageTextMap(messages))
              savedMessageIdsRef.current = new Set(messages.map((message) => message.id))
              onSessionUpdated?.(session)
            })
            .catch(() => undefined)
        })
    }

    return runtime.thread.unstable_on('runEnd', runEndHandler)
  }, [onSessionUpdated, runtime, sessionId])

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <NetworkChatThread
        streamEvents={streamEvents}
        liveText={liveText}
        persistedTextsById={persistedTextsById}
        onWorkflowChange={onWorkflowChange}
      />
    </AssistantRuntimeProvider>
  )
}
