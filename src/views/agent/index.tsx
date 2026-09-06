import { useEffect, useRef, useState } from 'react'
import { useDevices, useExecutionPlan, useGns3Status, useLabs, useNineRouterStatus } from 'src/api/network'
import { NetworkChat } from 'src/components/assistant-ui'
import { AgentSessionList } from 'src/components/assistant-ui/session-list'
import { SessionToolbar } from 'src/components/assistant-ui/session-toolbar'
import { ProjectSelector } from 'src/components/assistant-ui/project-selector'
import { BackendStatusPanel, SessionPanel } from 'src/components/assistant-ui/panels'
import { ExecutionPlanCard } from 'src/components/agent/execution-plan-card'
import { createAgentSession, deleteAgentSession, getAgentSessions, renameAgentSession, updateAgentSession } from 'src/api/agent'
import type { AgentSession, AgentWorkflowSnapshot } from 'src/types/agent'
import { AgentErrorState } from './agent-error-state'
import { AgentLoadingState } from './agent-loading-state'
import { AgentShell } from './agent-shell'
import { toast } from 'sonner'
import { resolveEnvironmentFromProjectId } from 'src/api/environments'

const AgentPage = () => {
  const plan = useExecutionPlan()
  const devices = useDevices()
  const labs = useLabs()
  const gns3Status = useGns3Status()
  const nineRouterStatus = useNineRouterStatus()
  const [selectedDevice, setSelectedDevice] = useState<string>('all-devices')
  const [selectedLab, setSelectedLab] = useState<string>('all-labs')
  const [selectedProject, setSelectedProject] = useState<string>('all-projects')
  const [agentMode, setAgentMode] = useState<string>('guarded')
  const [contextCollapsed, setContextCollapsed] = useState(false)
  const [sessions, setSessions] = useState<AgentSession[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [activeSession, setActiveSession] = useState<AgentSession | undefined>()
  const [workflowSnapshot, setWorkflowSnapshot] = useState<AgentWorkflowSnapshot | undefined>()
  const sessionSyncRef = useRef(false)
  const gns3Projects = gns3Status.data?.data.projects ?? []

  useEffect(() => {
    if (selectedProject !== 'all-projects') return
    const preferred = activeSession?.projectId ?? gns3Projects.find((project) => project.status === 'running')?.id ?? gns3Projects[0]?.id
    if (preferred) {
      setSelectedProject(preferred)
    }
  }, [activeSession?.projectId, gns3Projects, selectedProject])

  const loadSessions = async () => {
    setSessionsLoading(true)
    try {
      const nextSessions = await getAgentSessions()
      setSessions(nextSessions)
      setActiveSession((current) => (current && nextSessions.some((session) => session.id === current.id) ? current : nextSessions[0]))
    } catch {
      setSessions([])
    } finally {
      setSessionsLoading(false)
    }
  }

  const handleNewSession = async () => {
    const session = await createAgentSession({
      deviceIds: selectedDevice !== 'all-devices' ? [selectedDevice] : [],
      labId: selectedLab !== 'all-labs' ? selectedLab : undefined,
      projectId: selectedProject !== 'all-projects' ? selectedProject : undefined,
      environment: selectedProject !== 'all-projects' ? resolveEnvironmentFromProjectId(selectedProject) : 'lab',
    })
    setSessions((current) => [session, ...current])
    setActiveSession(session)
  }

  useEffect(() => {
    void loadSessions()
  }, [])

  const handleSelectSession = (session: AgentSession) => {
    setActiveSession((current) => (current?.id === session.id ? current : session))
  }

  const handleDeleteSession = async (session: AgentSession) => {
    await deleteAgentSession(session.id)
    let nextActiveSession: AgentSession | undefined
    setSessions((current) => {
      const nextSessions = current.filter((item) => item.id !== session.id)
      nextActiveSession = nextSessions[0]
      return nextSessions
    })

    setActiveSession((current) => {
      if (!current || current.id !== session.id) return current
      return nextActiveSession
    })

    if (activeSession?.id === session.id && !nextActiveSession) {
      setSelectedDevice('all-devices')
      setSelectedLab('all-labs')
      setSelectedProject('all-projects')
    }
  }

  const handleRenameSession = async (session: AgentSession, title: string) => {
    if (!title || title.trim() === '' || title.trim() === session.title) return
    const updated = await renameAgentSession(session.id, title.trim())
    setSessions((current) => current.map((item) => (item.id === updated.id ? updated : item)))
    if (activeSession?.id === updated.id) {
      setActiveSession(updated)
    }
  }

  useEffect(() => {
    if (!activeSession) {
      sessionSyncRef.current = true
      setSelectedDevice((current) => (current === 'all-devices' ? current : 'all-devices'))
      setSelectedLab((current) => (current === 'all-labs' ? current : 'all-labs'))
      setSelectedProject((current) => (current === 'all-projects' ? current : 'all-projects'))
      queueMicrotask(() => {
        sessionSyncRef.current = false
      })
      return
    }

    sessionSyncRef.current = true
    const nextDeviceIds = activeSession.deviceIds
    const nextSelectedDevice = nextDeviceIds.length > 0 ? nextDeviceIds[0] : 'all-devices'
    const nextSelectedLab = activeSession.labId ?? 'all-labs'
    const nextSelectedProject = activeSession.projectId ?? 'all-projects'

    if (selectedDevice !== nextSelectedDevice) {
      setSelectedDevice(nextSelectedDevice)
    }

    if (selectedLab !== nextSelectedLab) {
      setSelectedLab(nextSelectedLab)
    }

    if (selectedProject !== nextSelectedProject) {
      setSelectedProject(nextSelectedProject)
    }

    queueMicrotask(() => {
      sessionSyncRef.current = false
    })
  }, [activeSession?.id, activeSession?.labId, activeSession?.projectId, activeSession?.deviceIds?.join('|'), gns3Projects])

  useEffect(() => {
    if (!activeSession) return
    if (sessionSyncRef.current) return

    const nextDeviceIds = selectedDevice !== 'all-devices' ? [selectedDevice] : []
    const nextLabId = selectedLab !== 'all-labs' ? selectedLab : undefined
    const nextProjectId = selectedProject !== 'all-projects' ? selectedProject : undefined
    const nextEnvironment = nextProjectId ? resolveEnvironmentFromProjectId(nextProjectId) : 'lab'

    const currentDeviceIds = activeSession.deviceIds ?? []
    const currentLabId = activeSession.labId
    const currentProjectId = activeSession.projectId

    const deviceChanged =
      nextDeviceIds.length !== currentDeviceIds.length ||
      nextDeviceIds.some((deviceId, index) => deviceId !== currentDeviceIds[index])
    const labChanged = (nextLabId ?? undefined) !== (currentLabId ?? undefined)
    const projectChanged = (nextProjectId ?? undefined) !== (currentProjectId ?? undefined)

    if (!deviceChanged && !labChanged && !projectChanged) return

    void updateAgentSession(activeSession.id, {
      deviceIds: nextDeviceIds,
      labId: nextLabId,
      projectId: nextProjectId,
      environment: nextEnvironment,
      status: activeSession.status,
    }).then((updated) => {
      setActiveSession(updated)
      setSessions((current) => current.map((item) => (item.id === updated.id ? updated : item)))
    }).catch(() => undefined)
  }, [activeSession?.id, activeSession?.status, selectedDevice, selectedLab, selectedProject])

  if (plan.isLoading || devices.isLoading || labs.isLoading || sessionsLoading) {
    return <AgentLoadingState />
  }

  if (plan.error || devices.error || labs.error) {
    return <AgentErrorState message="Failed to load AI agent workspace." />
  }

  const onlineDevices = (devices.data?.data ?? []).filter((device) => device.status === 'online').length
  const deviceList = devices.data?.data ?? []
  const selectedDeviceLabel =
    selectedDevice === 'all-devices'
      ? 'All devices'
      : deviceList.find((device) => device.id === selectedDevice)?.hostname ?? selectedDevice
  const selectedLabLabel =
    selectedLab === 'all-labs'
      ? 'All labs'
      : labs.data?.data.find((lab) => lab.id === selectedLab)?.name ?? selectedLab
  const selectedProjectLabel =
    selectedProject === 'all-projects'
      ? 'All projects'
      : gns3Projects.find((project) => project.id === selectedProject)?.name ?? selectedProject
  const selectedEnvironmentLabel = selectedProject === 'all-projects'
    ? 'lab'
    : resolveEnvironmentFromProjectId(selectedProject)
  const apiStatus = plan.isLoading || devices.isLoading || labs.isLoading ? 'connecting' : 'connected'
  const aiStatus = nineRouterStatus.error
    ? 'disconnected'
    : nineRouterStatus.data?.data?.status ?? 'connecting'
  const gns3ConnectionStatus = gns3Status.error
    ? 'disconnected'
    : gns3Status.data?.data?.server ?? 'connecting'

  return (
    <AgentShell
      onlineDevices={onlineDevices}
      devices={deviceList}
      labs={labs.data?.data ?? []}
      selectedDevice={selectedDevice}
      selectedLab={selectedLab}
      selectedProject={selectedProjectLabel}
      selectedEnvironment={selectedEnvironmentLabel}
      onSelectedDeviceChange={setSelectedDevice}
      onSelectedLabChange={setSelectedLab}
      agentMode={agentMode}
      onAgentModeChange={setAgentMode}
      activeSession={activeSession}
      sessionCount={sessions.length}
      apiStatus={apiStatus}
      gns3Status={gns3ConnectionStatus}
      gns3Controller={gns3Status.data?.data?.controller}
      aiStatus={aiStatus}
      contextCollapsed={contextCollapsed}
      onToggleContextCollapsed={() => setContextCollapsed((current) => !current)}
      sessionsPanel={
        <div className="flex h-full min-h-0 flex-1 flex-col gap-1.5">
          <SessionToolbar
            onNewSession={() => {
              void handleNewSession().catch(() => toast.error('Failed to create session'))
            }}
            onRefresh={() => {
              void loadSessions()
            }}
          />
          <div className="px-1">
            <ProjectSelector
              projects={gns3Projects}
              value={selectedProject}
              onValueChange={setSelectedProject}
            />
          </div>
          <AgentSessionList
            sessions={sessions}
            loading={sessionsLoading}
            activeSessionId={activeSession?.id}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
            onRenameSession={handleRenameSession}
          />
        </div>
      }
      chatPanel={
        <NetworkChat
          sessionId={activeSession?.id}
          deviceId={selectedDevice !== 'all-devices' ? selectedDevice : undefined}
          deviceIds={activeSession?.deviceIds ?? (selectedDevice !== 'all-devices' ? [selectedDevice] : [])}
          labId={activeSession?.labId ?? (selectedLab !== 'all-labs' ? selectedLab : undefined)}
          projectId={activeSession?.projectId ?? (selectedProject !== 'all-projects' ? selectedProject : undefined)}
          environment={selectedProject !== 'all-projects' ? resolveEnvironmentFromProjectId(selectedProject) : 'lab'}
          mode={agentMode}
          onSessionCreated={(session) => {
            setSessions((current) => {
              const withoutDuplicate = current.filter((item) => item.id !== session.id)
              return [session, ...withoutDuplicate]
            })
            setActiveSession(session)
          }}
          onSessionUpdated={(session) => {
            setSessions((current) => current.map((item) => (item.id === session.id ? session : item)))
            setActiveSession((current) => {
              if (!current) return session
              return current.id === session.id ? session : current
            })
          }}
          onWorkflowChange={setWorkflowSnapshot}
        />
      }
      contextPanel={
        <div className="grid gap-5">
          <SessionPanel
            session={activeSession}
            deviceLabel={selectedDeviceLabel}
            labLabel={selectedLabLabel}
            projectLabel={selectedProjectLabel}
            environmentLabel={selectedEnvironmentLabel}
            mode={agentMode}
            workflowSnapshot={workflowSnapshot}
          />
          <BackendStatusPanel
            apiStatus={apiStatus}
            apiUrl="http://localhost:8000"
            gns3Status={gns3ConnectionStatus}
            gns3Controller={gns3Status.data?.data?.controller}
            aiStatus={aiStatus}
          />
          {plan.data?.data ? <ExecutionPlanCard plan={plan.data.data} /> : null}
        </div>
      }
    />
  )
}

export default AgentPage
