import { AlertCircle, BrainCircuit, CheckCircle2, ChevronDown, ChevronRight, Clock3, Loader2, ShieldCheck, Sparkles, XCircle } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { toast } from 'sonner'
import { cancelAgentExecutionPlan, executeAgentExecutionPlan } from 'src/api/network'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import type {
  AgentAnalysisEvent,
  AgentApprovalEvent,
  AgentCommandOutputEvent,
  AgentDeviceStateEvent,
  AgentExecutionPlanEvent,
  AgentStreamEvent,
  AgentTaskProgressEvent,
  AgentToolOutputEvent,
  AgentVerificationEvent,
} from 'src/types/agent'
import { CommandOutputCard } from './command-output-card'
import { DeviceStateCard } from './device-state-card'

function riskLabel(risk: string) {
  if (risk === 'high') return 'High'
  if (risk === 'medium') return 'Medium'
  return 'Low'
}

function PlanSection({ event }: { event: AgentExecutionPlanEvent }) {
  return (
    <Card className="border-cyan-500/20 bg-cyan-500/[0.03]">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-cyan-600 dark:text-cyan-300" />
            <CardTitle className="text-sm">Execution Plan</CardTitle>
          </div>
          <Badge variant="outline">Risk {riskLabel(event.risk)}</Badge>
        </div>
        <p className="text-xs text-muted-foreground">{event.task}</p>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div className="flex flex-wrap gap-2">
          {event.devices.map((device) => (
            <Badge key={device} variant="secondary">
              {device}
            </Badge>
          ))}
        </div>
        <ol className="grid gap-2">
          {event.plannedActions.map((action, index) => (
            <li key={action} className="flex items-start gap-3 rounded-lg border border-border bg-background/70 px-3 py-2">
              <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
                {index + 1}
              </span>
              <span className="leading-5">{action}</span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}

function ApprovalSection({ event }: { event: AgentApprovalEvent }) {
  const [isApproving, setIsApproving] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)
  const [localStatus, setLocalStatus] = useState<AgentApprovalEvent['status']>(event.status)

  const canAct = localStatus === 'required' && Boolean(event.taskId)

  const handleApprove = async () => {
    if (!event.taskId) {
      toast.error('Approval ID tidak tersedia untuk dieksekusi')
      return
    }

    setIsApproving(true)
    try {
      await executeAgentExecutionPlan(event.taskId, 'user')
      setLocalStatus('approved')
      toast.success('Approval dikirim ke backend')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Gagal mengirim approval')
    } finally {
      setIsApproving(false)
    }
  }

  const handleCancel = () => {
    if (!event.taskId) {
      toast.error('Approval ID tidak tersedia untuk dibatalkan')
      return
    }

    setIsCancelling(true)
    cancelAgentExecutionPlan(event.taskId, 'user')
      .then(() => {
        setLocalStatus('cancelled')
        toast.success('Approval dibatalkan')
      })
      .catch((error) => {
        toast.error(error instanceof Error ? error.message : 'Gagal membatalkan approval')
      })
      .finally(() => {
        setIsCancelling(false)
      })
  }

  return (
    <Card className="border-amber-500/25 bg-amber-500/[0.05]">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-amber-600 dark:text-amber-300" />
            <CardTitle className="text-sm">Approval Required</CardTitle>
          </div>
          <Badge variant="outline">Risk {riskLabel(event.risk)}</Badge>
        </div>
        <p className="text-xs text-muted-foreground">{event.task}</p>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <p className="text-muted-foreground">{event.message}</p>
        <div className="flex flex-wrap gap-2">
          {event.devices.map((device) => (
            <Badge key={device} variant="secondary">
              {device}
            </Badge>
          ))}
        </div>
        {event.commands?.length ? (
          <div className="overflow-hidden rounded-xl border border-border bg-slate-950 text-xs text-slate-100 dark:text-slate-200">
            <div className="border-b border-white/10 px-3 py-1.5 text-[10px] uppercase text-slate-400">
              Commands Preview
            </div>
            <pre className="bubble-scrollbar max-h-64 overflow-auto p-3 leading-5">
              {event.commands.join('\n')}
            </pre>
          </div>
        ) : null}
        <div className="flex flex-wrap gap-2 pt-1">
          <Button size="sm" className="gap-2" disabled={!canAct || isApproving} onClick={handleApprove}>
            <ShieldCheck className="size-4" />
            {isApproving ? 'Approving...' : 'Approve & Execute'}
          </Button>
          <Button size="sm" variant="outline" disabled={localStatus !== 'required' || isCancelling} onClick={handleCancel}>
            <XCircle className="size-4" />
            {isCancelling ? 'Cancelling...' : 'Cancel'}
          </Button>
        </div>
        {localStatus !== 'required' ? (
          <p className="text-xs text-muted-foreground">Status approval: {localStatus}</p>
        ) : null}
      </CardContent>
    </Card>
  )
}

function ProgressSection({ events }: { events: AgentTaskProgressEvent[] }) {
  const total = events[0]?.total ?? events.length
  return (
    <Card className="border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Clock3 className="size-4 text-muted-foreground" />
          <CardTitle className="text-sm">Task Progress</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        {events.map((event) => (
          <div key={event.id} className="flex items-start gap-3 rounded-lg border border-border bg-background/70 px-3 py-2">
            <span
              className={[
                'mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold',
                event.status === 'success'
                  ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                  : event.status === 'failed'
                    ? 'bg-red-500/15 text-red-700 dark:text-red-300'
                    : 'bg-primary/10 text-primary',
              ].join(' ')}
            >
              {event.order}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{event.step}</span>
                <Badge variant="outline">
                  {event.order}/{total}
                </Badge>
                <Badge variant="secondary">{event.status}</Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{event.message}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function toolTitle(tool: string, data?: Record<string, unknown>): string {
  const command = typeof data?.command === 'string' ? data.command.trim() : ''
  const path = typeof data?.path === 'string' ? data.path : ''
  if (command && (tool.includes('run_command') || tool.includes('exec_readonly') || tool.includes('service_status'))) {
    return `Run: ${command}`
  }
  if (tool.includes('write_file')) return path ? `Write: ${path}` : 'Write file'
  if (tool.includes('edit_file')) return path ? `Edit: ${path}` : 'Edit file'
  if (tool.includes('read_file')) return path ? `Read: ${path}` : 'Read file'
  if (tool.includes('search_code')) return 'Search workspace'
  if (tool.includes('list_files')) return 'List files'
  if (tool.includes('config')) return 'Read config'
  if (tool.includes('interfaces')) return 'Read interfaces'
  if (tool.includes('routes')) return 'Read routes'
  if (tool.includes('facts')) return 'Read facts'
  if (tool.includes('health')) return 'Check health'
  if (tool.includes('apply') || tool.includes('deploy')) return 'Apply config'
  if (tool.includes('export')) return 'Export report'
  return tool
}

function CollapsibleEventCard({
  title,
  status,
  tone,
  children,
}: {
  title: string
  status: string
  tone: string
  children?: ReactNode
}) {
  const [expanded, setExpanded] = useState(false)
  const Icon =
    status === 'ok' ? CheckCircle2 : status === 'failed' || status === 'blocked' ? XCircle : Loader2
  const iconTone =
    status === 'ok'
      ? 'text-emerald-500'
      : status === 'failed' || status === 'blocked'
        ? 'text-red-500'
        : 'text-sky-500'

  return (
    <div className={`rounded-xl border ${tone}`}>
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        {expanded ? (
          <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
        )}
        <span className="min-w-0 flex-1 truncate text-xs font-medium">{title}</span>
        <Icon className={`size-4 shrink-0 ${iconTone} ${status === 'running' ? 'animate-spin' : ''}`} />
      </button>
      {expanded && children ? <div className="border-t border-border px-3 py-2">{children}</div> : null}
    </div>
  )
}

function CommandOutputSection({ event }: { event: AgentCommandOutputEvent }) {
  const output = Array.isArray(event.output) ? event.output.join('\n') : event.output
  const title = event.command ? `Run: ${event.command}` : 'Run command'
  const tone =
    event.status === 'ok'
      ? 'border-emerald-500/25'
      : event.status === 'blocked'
        ? 'border-amber-500/25'
        : event.status === 'failed'
          ? 'border-red-500/25'
          : 'border-sky-500/25'

  return (
    <CollapsibleEventCard title={title} status={event.status ?? 'running'} tone={tone}>
      {event.device ? <p className="mb-1 text-[11px] text-muted-foreground">Device: {event.device}</p> : null}
      <CommandOutputCard text={output} />
    </CollapsibleEventCard>
  )
}

function DeviceStateSection({ event }: { event: AgentDeviceStateEvent }) {
  return (
    <Card className="border-border bg-background/70">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-cyan-600 dark:text-cyan-300" />
            <CardTitle className="text-sm">Device State</CardTitle>
          </div>
          <Badge variant="outline" className="uppercase">
            {event.vendor ?? 'other'}
          </Badge>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          {event.device ? <span>Device: {event.device}</span> : null}
          {event.platform ? <span>Platform: {event.platform}</span> : null}
          {event.summary ? <span>{event.summary}</span> : null}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <DeviceStateCard text={event.content} />
      </CardContent>
    </Card>
  )
}

function VerificationSection({ event }: { event: AgentVerificationEvent }) {
  const tone =
    event.status === 'passed'
      ? 'border-emerald-500/25 bg-emerald-500/[0.05]'
      : event.status === 'failed'
        ? 'border-red-500/25 bg-red-500/[0.05]'
        : event.status === 'warning'
          ? 'border-amber-500/25 bg-amber-500/[0.05]'
          : 'border-sky-500/25 bg-sky-500/[0.05]'
  const icon =
    event.status === 'passed'
      ? <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-300" />
      : event.status === 'failed'
        ? <XCircle className="size-4 text-red-600 dark:text-red-300" />
        : <AlertCircle className="size-4 text-amber-600 dark:text-amber-300" />

  return (
    <Card className={tone}>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            {icon}
            <CardTitle className="text-sm">Verification</CardTitle>
          </div>
          <Badge variant="outline" className="uppercase">
            {event.status}
          </Badge>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          {event.device ? <span>Device: {event.device}</span> : null}
          <span>{event.message}</span>
        </div>
      </CardHeader>
      {event.checks?.length ? (
        <CardContent className="grid gap-2 text-sm">
          {event.checks.map((check, index) => (
            <div key={`${event.id}-${index}`} className="rounded-lg border border-border bg-background/70 px-3 py-2 text-xs leading-5 text-foreground">
              {check}
            </div>
          ))}
        </CardContent>
      ) : null}
    </Card>
  )
}

function AnalysisSection({ event }: { event: AgentAnalysisEvent }) {
  const { intent } = event
  return (
    <Card className="border-border bg-background/70">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <BrainCircuit className="size-4 text-violet-600 dark:text-violet-300" />
            <CardTitle className="text-sm">Intent Analysis</CardTitle>
          </div>
          <Badge variant="outline">{intent.type}</Badge>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">policy: {intent.policy}</Badge>
          <Badge variant="secondary">risk: {intent.risk}</Badge>
          {intent.ambiguous ? <Badge variant="secondary">ambiguous</Badge> : null}
        </div>
        {intent.targets.length ? (
          <div className="flex flex-wrap gap-2">
            {intent.targets.map((target, index) => (
              <Badge key={`${target.id ?? target.name ?? 'target'}-${index}`} variant="outline">
                {target.name ?? target.id ?? target.kind}
              </Badge>
            ))}
          </div>
        ) : null}
        {intent.suggestedTools?.length ? (
          <div className="flex flex-wrap gap-2">
            {intent.suggestedTools.map((tool) => (
              <Badge key={tool} variant="outline" className="font-mono text-[11px]">
                {tool}
              </Badge>
            ))}
          </div>
        ) : null}
        {intent.reason ? <p className="text-xs text-muted-foreground">{intent.reason}</p> : null}
      </CardContent>
    </Card>
  )
}

function ToolOutputSection({ event }: { event: AgentToolOutputEvent }) {
  const data = (event.data ?? {}) as Record<string, unknown>
  const command = typeof data.command === 'string' ? data.command : undefined
  const stdout = typeof data.stdout === 'string' ? data.stdout : undefined
  const stderr = typeof data.stderr === 'string' ? data.stderr : undefined
  const exitCode = typeof data.exit_code === 'number' ? data.exit_code : undefined
  const hasOutput = Boolean(command || stdout || stderr || exitCode !== undefined)
  const title = event.summary?.trim() || toolTitle(event.tool, data)

  const tone =
    event.status === 'ok'
      ? 'border-emerald-500/25'
      : event.status === 'approval_required'
        ? 'border-amber-500/25'
        : event.status === 'failed'
          ? 'border-red-500/25'
          : 'border-sky-500/25'

  return (
    <CollapsibleEventCard title={title} status={event.status} tone={tone}>
      <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground">
        <span>policy: {event.policy}</span>
        <span>evidence: {event.evidence}</span>
        {event.target?.hostname ? <span>device: {event.target.hostname}</span> : null}
      </div>
      {hasOutput ? (
        <div className="mt-2 flex flex-col gap-2">
          {command ? (
            <div className="overflow-hidden rounded-xl border border-border bg-slate-950">
              <div className="border-b border-white/10 px-3 py-1.5 font-mono text-[10px] uppercase text-slate-400">
                $ command
              </div>
              <pre className="bubble-scrollbar overflow-auto p-3 font-mono text-xs leading-5 text-slate-100">{command}</pre>
            </div>
          ) : null}
          {stdout ? (
            <div className="overflow-hidden rounded-xl border border-border bg-slate-950">
              <pre className="bubble-scrollbar max-h-64 overflow-auto p-3 font-mono text-xs leading-5 text-slate-100">{stdout}</pre>
            </div>
          ) : null}
          {stderr ? (
            <div className="overflow-hidden rounded-xl border border-red-500/30 bg-red-950/40">
              <pre className="bubble-scrollbar max-h-48 overflow-auto p-3 font-mono text-xs leading-5 text-red-300">{stderr}</pre>
            </div>
          ) : null}
          {exitCode !== undefined ? (
            <Badge variant="outline" className={`w-fit ${exitCode === 0 ? 'text-emerald-600 dark:text-emerald-300' : 'text-red-600 dark:text-red-300'}`}>
              exit {exitCode}
            </Badge>
          ) : null}
        </div>
      ) : (
        <div className="mt-1 flex flex-col gap-1">
          {event.error ? <p className="text-xs text-red-600 dark:text-red-300">{event.error}</p> : null}
          {event.data != null ? (
            <div className="overflow-hidden rounded-xl border border-border bg-slate-950">
              <pre className="bubble-scrollbar max-h-64 overflow-auto p-3 text-xs leading-5 text-slate-100 dark:text-slate-200">
                {typeof event.data === 'string' ? event.data : JSON.stringify(event.data, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>
      )}
    </CollapsibleEventCard>
  )
}

type ToolLikeEvent = AgentToolOutputEvent | AgentCommandOutputEvent

function isToolLike(event: AgentStreamEvent): event is ToolLikeEvent {
  return event.type === 'tool_output' || event.type === 'command_output'
}

function ToolEventGroup({ events }: { events: ToolLikeEvent[] }) {
  const [expanded, setExpanded] = useState(false)
  const count = events.length
  const anyFailed = events.some((e) =>
    e.type === 'tool_output' ? e.status === 'failed' : (e.status ?? '') === 'failed',
  )
  const allDone = events.every((e) =>
    e.type === 'tool_output' ? e.status === 'ok' : (e.status ?? 'ok') === 'ok',
  )
  const Icon = anyFailed ? XCircle : allDone ? CheckCircle2 : Loader2
  const iconTone = anyFailed ? 'text-red-500' : allDone ? 'text-emerald-500' : 'text-sky-500'

  return (
    <div className="rounded-xl border border-border">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        {expanded ? (
          <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
        )}
        <span className="min-w-0 flex-1 truncate text-xs font-medium">
          {count} action{count === 1 ? '' : 's'} {allDone ? 'completed' : anyFailed ? 'completed' : 'in progress'}
        </span>
        <Icon className={`size-4 shrink-0 ${iconTone} ${allDone || anyFailed ? '' : 'animate-spin'}`} />
      </button>
      {expanded ? (
        <div className="grid gap-2 border-t border-border p-2">
          {events.map((event) =>
            event.type === 'tool_output' ? (
              <ToolOutputSection key={event.id} event={event} />
            ) : (
              <CommandOutputSection key={event.id} event={event} />
            ),
          )}
        </div>
      ) : null}
    </div>
  )
}

export function StreamEventTimeline({ events }: { events: AgentStreamEvent[] }) {
  const plan = events.find((event) => event.type === 'plan') as AgentExecutionPlanEvent | undefined
  const approval = [...events].reverse().find((event) => event.type === 'approval') as AgentApprovalEvent | undefined
  const analysis = [...events].reverse().find((event) => event.type === 'analysis') as AgentAnalysisEvent | undefined
  const progressEvents = events.filter((event): event is AgentTaskProgressEvent => event.type === 'task_progress')
  const deviceStates = events.filter((event): event is AgentDeviceStateEvent => event.type === 'device_state')
  const verifications = events.filter((event): event is AgentVerificationEvent => event.type === 'verification')

  const toolGroups: ToolLikeEvent[][] = []
  let current: ToolLikeEvent[] = []
  for (const event of events) {
    if (isToolLike(event)) {
      current.push(event)
    } else if (current.length) {
      toolGroups.push(current)
      current = []
    }
  }
  if (current.length) toolGroups.push(current)

  const hasToolGroups = toolGroups.length > 0
  if (!plan && !approval && !analysis && progressEvents.length === 0 && !hasToolGroups && deviceStates.length === 0 && verifications.length === 0) {
    return null
  }

  return (
    <div className="grid gap-2">
      {analysis ? <AnalysisSection event={analysis} /> : null}
      {plan ? <PlanSection event={plan} /> : null}
      {approval ? <ApprovalSection event={approval} /> : null}
      {progressEvents.length ? <ProgressSection events={progressEvents} /> : null}
      {toolGroups.map((group, index) =>
        group.length === 1 ? (
          group[0].type === 'tool_output' ? (
            <ToolOutputSection key={group[0].id} event={group[0]} />
          ) : (
            <CommandOutputSection key={group[0].id} event={group[0]} />
          )
        ) : (
          <ToolEventGroup key={`group-${index}`} events={group} />
        ),
      )}
      {deviceStates.map((event) => <DeviceStateSection key={event.id} event={event} />)}
      {verifications.map((event) => <VerificationSection key={event.id} event={event} />)}
    </div>
  )
}
