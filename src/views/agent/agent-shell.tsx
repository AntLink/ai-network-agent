import type { ReactNode } from 'react'
import { ChevronLeft, ChevronRight, ShieldCheck, TerminalSquare } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Button } from 'src/components/ui/button'
import { AgentHeader } from './agent-header'
import { AgentLayout } from './agent-layout'
import { DeviceSelector } from 'src/components/assistant-ui/device-selector'
import { LabSelector } from 'src/components/assistant-ui/lab-selector'
import { SafetyModeSwitcher } from 'src/components/assistant-ui/safety-mode-switcher'
import { ConnectionStatusBar } from 'src/components/assistant-ui/connection-status-bar'
import type { AgentSession } from 'src/types/agent'
import type { Device, Lab } from 'src/types/network'

export function AgentShell({
  onlineDevices,
  devices,
  labs,
  selectedDevice,
  selectedLab,
  selectedProject,
  selectedEnvironment,
  onSelectedDeviceChange,
  onSelectedLabChange,
  agentMode,
  onAgentModeChange,
  activeSession,
  sessionCount,
  apiStatus,
  gns3Status,
  gns3Controller,
  aiStatus,
  contextCollapsed,
  onToggleContextCollapsed,
  sessionsPanel,
  chatPanel,
  contextPanel,
}: {
  onlineDevices: number
  devices: Device[]
  labs: Lab[]
  selectedDevice: string
  selectedLab: string
  selectedProject?: string
  selectedEnvironment?: string
  onSelectedDeviceChange: (value: string) => void
  onSelectedLabChange: (value: string) => void
  agentMode: string
  onAgentModeChange: (value: string) => void
  activeSession?: AgentSession
  sessionCount: number
  apiStatus: string
  gns3Status: string
  gns3Controller?: string
  aiStatus: string
  contextCollapsed: boolean
  onToggleContextCollapsed: () => void
  sessionsPanel: ReactNode
  chatPanel: ReactNode
  contextPanel: ReactNode
}) {
  return (
    <div className="grid gap-4">
      <AgentHeader
        onlineDevices={onlineDevices}
        projectLabel={selectedProject}
        environmentLabel={selectedEnvironment}
      />

      <AgentLayout
        contextCollapsed={contextCollapsed}
        sessions={
          <Card className="flex h-[calc(100vh-13rem)] min-h-[40rem] flex-col overflow-hidden">
            <CardHeader className="border-b px-3 py-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Chat history</CardTitle>
            </CardHeader>
            <CardContent className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden px-2.5 py-2">
              <div className="rounded-lg border border-border/60 bg-muted/20 px-3 py-2 text-xs text-muted-foreground">
                <span className="block truncate font-medium text-foreground">{activeSession?.title ?? 'No active session'}</span>
                <span className="mt-0.5 block">{sessionCount} sessions available</span>
              </div>
              <div className="min-h-0 flex-1 overflow-hidden">{sessionsPanel}</div>
            </CardContent>
          </Card>
        }
        chat={
          <Card className="overflow-hidden">
            <CardHeader className="border-b py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle className="flex items-center gap-2 text-base font-medium">
                    <TerminalSquare className="size-4 text-muted-foreground" />
                    Copilot
                  </CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">Ask for inspection, troubleshooting, config planning, or lab automation.</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <DeviceSelector
                    devices={devices}
                    value={selectedDevice}
                    onValueChange={onSelectedDeviceChange}
                  />
                  <LabSelector labs={labs} value={selectedLab} onValueChange={onSelectedLabChange} />
                  <SafetyModeSwitcher value={agentMode} onValueChange={onAgentModeChange} />
                  <ConnectionStatusBar provider={`AI ${aiStatus}`} connection={`${apiStatus} / GNS3 ${gns3Status}`} />
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="h-8 rounded-full px-3"
                    onClick={onToggleContextCollapsed}
                  >
                    {contextCollapsed ? <ChevronLeft className="size-4" /> : <ChevronRight className="size-4" />}
                    {contextCollapsed ? 'Show details' : 'Hide details'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-[calc(100vh-17rem)] min-h-[36rem]">{chatPanel}</div>
            </CardContent>
          </Card>
        }
        context={
          <aside className="grid content-start gap-4">
            {contextPanel}
            <Card className="border-border bg-background/80">
              <CardHeader className="border-b py-4">
                <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <ShieldCheck className="size-4 text-muted-foreground" />
                  Safety Boundary
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 py-4 text-sm">
                <p className="text-muted-foreground">The browser never stores credentials and never opens SSH. Agent actions are routed through backend APIs, policy checks, backups, and audit logs.</p>
                <div className="rounded-2xl border border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                  Guarded workflow enabled. Approval required before any config deployment.
                </div>
                <div className="rounded-2xl border border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                  GNS3 controller: {gns3Controller ?? 'not detected'}
                </div>
              </CardContent>
            </Card>
          </aside>
        }
      />
    </div>
  )
}
