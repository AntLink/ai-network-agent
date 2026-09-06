import { Hash, Layers3, MessageSquareText, SlidersHorizontal } from 'lucide-react'
import { Badge } from 'src/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import type { AgentSession, AgentWorkflowSnapshot } from 'src/types/agent'
import { WorkflowStateRail } from 'src/components/assistant-ui/workflow-state'

export function SessionPanel({
  session,
  deviceLabel,
  labLabel,
  projectLabel,
  environmentLabel,
  mode,
  workflowSnapshot,
}: {
  session?: AgentSession
  deviceLabel: string
  labLabel: string
  projectLabel: string
  environmentLabel: string
  mode: string
  workflowSnapshot?: AgentWorkflowSnapshot
}) {
  return (
    <Card className="border-border bg-background/80">
      <CardHeader className="border-b py-4">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <MessageSquareText className="size-4" />
          Session Context
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 py-4 text-sm">
        <div className="rounded-2xl border border-border bg-muted/20 px-3 py-3">
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Active Session</div>
          <div className="mt-1 truncate text-sm font-semibold text-foreground">
            {session?.title ?? 'No active session'}
          </div>
          <div className="mt-0.5 truncate text-xs text-muted-foreground">
            {session?.id ?? 'session not selected'}
          </div>
        </div>

        {workflowSnapshot ? (
          <WorkflowStateRail snapshot={workflowSnapshot} compact />
        ) : (
          <div className="rounded-2xl border border-dashed border-border bg-muted/10 px-3 py-3">
            <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Workflow</div>
            <div className="mt-1 text-sm font-medium text-foreground">Waiting for agent activity</div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              Thinking / Planning / Approval / Run / Verify will appear here.
            </div>
          </div>
        )}

        <div className="grid gap-2">
          <span className="text-xs uppercase tracking-wide text-muted-foreground">Context</span>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="h-8 gap-1.5 rounded-full px-3">
              <Layers3 className="size-3" />
              Lab: {labLabel}
            </Badge>
            <Badge variant="secondary" className="h-8 gap-1.5 rounded-full px-3">
              <Layers3 className="size-3" />
              Project: {projectLabel}
            </Badge>
            <Badge variant="secondary" className="h-8 gap-1.5 rounded-full px-3">
              <Layers3 className="size-3" />
              Env: {environmentLabel}
            </Badge>
            <Badge variant="secondary" className="h-8 gap-1.5 rounded-full px-3">
              <Hash className="size-3" />
              Device: {deviceLabel}
            </Badge>
            <Badge variant="outline" className="h-8 gap-1.5 rounded-full px-3">
              <SlidersHorizontal className="size-3" />
              Mode: {mode}
            </Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-2xl border border-border bg-muted/20 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Messages</div>
            <div className="mt-1 text-lg font-semibold leading-none">{session?.messageCount ?? 0}</div>
          </div>
          <div className="rounded-2xl border border-border bg-muted/20 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wide text-muted-foreground">Devices</div>
            <div className="mt-1 text-lg font-semibold leading-none">{session?.deviceIds?.length ?? 0}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
