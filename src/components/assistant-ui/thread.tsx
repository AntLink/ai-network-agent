import { useEffect, useMemo } from 'react'
import { ThreadPrimitive, useAuiState } from '@assistant-ui/react'
import { AgentEmptyThreadState, AssistantMessage, UserMessage } from './message-renderers'
import { AgentComposer } from './composer'
import type { AgentStreamEvent } from 'src/types/agent'
import { deriveWorkflowSnapshot } from './workflow-state'

export function NetworkChatThread({
  streamEvents,
  liveText,
  persistedTextsById,
  onWorkflowChange,
}: {
  streamEvents: AgentStreamEvent[]
  liveText: string
  persistedTextsById: Record<string, string>
  onWorkflowChange?: (state: ReturnType<typeof deriveWorkflowSnapshot>) => void
}) {
  const threadRunning = useAuiState((state) => state.thread.isRunning)
  const workflowSnapshot = useMemo(
    () => deriveWorkflowSnapshot(streamEvents, threadRunning),
    [streamEvents, threadRunning],
  )

  useEffect(() => {
    onWorkflowChange?.(workflowSnapshot)
  }, [onWorkflowChange, workflowSnapshot])

  return (
    <ThreadPrimitive.Root className="flex h-full flex-col">
      <ThreadPrimitive.Viewport className="bubble-scrollbar relative flex-1 overflow-y-auto overflow-x-hidden scroll-smooth px-2 md:px-3 [scrollbar-gutter:stable_both-edges] before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:z-10 before:h-4 before:bg-gradient-to-b before:from-background before:to-transparent before:content-[''] after:pointer-events-none after:absolute after:inset-x-0 after:bottom-0 after:z-10 after:h-4 after:bg-gradient-to-t after:from-background after:to-transparent after:content-['']">
        <div className="mx-auto min-w-0 max-w-4xl py-4 pr-1 md:pr-2">
          <AgentEmptyThreadState />
          <ThreadPrimitive.Messages>
            {({ message }) =>
              message.role === 'user' ? (
                <UserMessage />
              ) : (
                <AssistantMessage
                  streamText={liveText}
                  fallbackText={persistedTextsById[message.id] ?? ''}
                  streamEvents={streamEvents}
                  workflowSnapshot={workflowSnapshot}
                />
              )
            }
          </ThreadPrimitive.Messages>
        </div>
      </ThreadPrimitive.Viewport>
      <AgentComposer />
    </ThreadPrimitive.Root>
  )
}
