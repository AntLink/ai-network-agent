import { useEffect, useState } from 'react'
import { NetworkChat } from 'src/components/assistant-ui'
import { AgentSessionList } from 'src/components/assistant-ui/session-list'
import { SessionToolbar } from 'src/components/assistant-ui/session-toolbar'
import { createAgentSession, deleteAgentSession, getAgentSessions, renameAgentSession } from 'src/api/agent'
import type { AgentSession } from 'src/types/agent'

export default function AiAssistantPage() {
  const [sessions, setSessions] = useState<AgentSession[]>([])
  const [activeSession, setActiveSession] = useState<AgentSession | undefined>()
  const [loading, setLoading] = useState(true)

  const loadSessions = async () => {
    setLoading(true)
    try {
      const next = await getAgentSessions()
      setSessions(next)
      setActiveSession((current) => (current && next.some((s) => s.id === current.id) ? current : next[0]))
    } catch {
      setSessions([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadSessions()
  }, [])

  const handleNewSession = async () => {
    const session = await createAgentSession({})
    setSessions((current) => [session, ...current])
    setActiveSession(session)
  }

  const handleDeleteSession = async (session: AgentSession) => {
    await deleteAgentSession(session.id)
    setSessions((current) => current.filter((item) => item.id !== session.id))
    setActiveSession((current) => (current?.id === session.id ? undefined : current))
  }

  const handleRenameSession = async (session: AgentSession, title: string) => {
    if (!title || !title.trim() || title.trim() === session.title) return
    const updated = await renameAgentSession(session.id, title.trim())
    setSessions((current) => current.map((item) => (item.id === updated.id ? updated : item)))
    if (activeSession?.id === updated.id) setActiveSession(updated)
  }

  return (
    <div className="flex h-[calc(100vh-160px)] w-full overflow-hidden rounded-xl border border-border">
      <aside className="flex w-64 shrink-0 flex-col gap-1.5 border-r border-border p-2">
        <SessionToolbar
          onNewSession={() => {
            void handleNewSession()
          }}
          onRefresh={() => {
            void loadSessions()
          }}
        />
        <AgentSessionList
          sessions={sessions}
          loading={loading}
          activeSessionId={activeSession?.id}
          onSelectSession={setActiveSession}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
        />
      </aside>
      <main className="flex min-w-0 flex-1 flex-col">
        <NetworkChat
          sessionId={activeSession?.id}
          environment="lab"
          mode="guarded"
          onSessionCreated={(session) => {
            setSessions((current) => [session, ...current.filter((item) => item.id !== session.id)])
            setActiveSession(session)
          }}
          onSessionUpdated={(session) => {
            setSessions((current) => current.map((item) => (item.id === session.id ? session : item)))
            setActiveSession((current) => (current?.id === session.id ? session : current))
          }}
        />
      </main>
    </div>
  )
}
