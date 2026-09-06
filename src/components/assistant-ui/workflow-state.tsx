import { CheckCircle2, Circle, CircleX, ListChecks, Loader2, Sparkles } from 'lucide-react'
import type { AgentApprovalEvent, AgentCommandOutputEvent, AgentExecutionPlanEvent, AgentStreamEvent, AgentTaskProgressEvent, AgentVerificationEvent, AgentWorkflowEvent, AgentWorkflowSnapshot, AgentWorkflowState } from 'src/types/agent'
import { Badge } from 'src/components/ui/badge'

export const workflowOrder: Array<{ key: AgentWorkflowState; label: string }> = [
  { key: 'thinking', label: 'Thinking' },
  { key: 'planning', label: 'Planning' },
  { key: 'waiting_approval', label: 'Waiting approval' },
  { key: 'running', label: 'Running' },
  { key: 'verifying', label: 'Verifying' },
  { key: 'completed', label: 'Completed' },
  { key: 'failed', label: 'Failed' },
]

export function workflowTone(state: AgentWorkflowState) {
  if (state === 'completed') return 'border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
  if (state === 'failed') return 'border-red-500/25 bg-red-500/10 text-red-700 dark:text-red-300'
  if (state === 'waiting_approval') return 'border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300'
  if (state === 'running' || state === 'verifying') return 'border-sky-500/25 bg-sky-500/10 text-sky-700 dark:text-sky-300'
  return 'border-border bg-background text-muted-foreground'
}

function latestEvent<T extends AgentStreamEvent>(events: AgentStreamEvent[], type: T['type']): T | undefined {
  return [...events].reverse().find((event): event is T => event.type === type)
}

export function deriveWorkflowSnapshot(events: AgentStreamEvent[], threadRunning: boolean): AgentWorkflowSnapshot {
  const explicitWorkflow = latestEvent<AgentWorkflowEvent>(events, 'workflow_state')
  if (explicitWorkflow) {
    return {
      state: explicitWorkflow.state,
      label: explicitWorkflow.label,
      detail: explicitWorkflow.detail,
      activeIndex: explicitWorkflow.activeIndex,
      eventsCount: explicitWorkflow.eventsCount ?? events.length,
    }
  }

  const hasFailure = events.some((event) => {
    if (event.type === 'approval' && event.status === 'cancelled') return true
    if (event.type === 'task_progress' && event.status === 'failed') return true
    if (event.type === 'command_output' && event.status === 'failed') return true
    if (event.type === 'verification' && event.status === 'failed') return true
    return false
  })

  const waitingApproval = latestEvent<AgentApprovalEvent>(events, 'approval')
  const planning = latestEvent<AgentExecutionPlanEvent>(events, 'plan')
  const runningProgress = latestEvent<AgentTaskProgressEvent>(events, 'task_progress')
  const runningCommand = latestEvent<AgentCommandOutputEvent>(events, 'command_output')
  const verifying = latestEvent<AgentVerificationEvent>(events, 'verification')

  if (hasFailure) {
    return {
      state: 'failed',
      label: 'Failed',
      detail: 'One of the execution steps failed or was cancelled.',
      activeIndex: 6,
      eventsCount: events.length,
    }
  }

  if (waitingApproval?.status === 'required') {
    return {
      state: 'waiting_approval',
      label: 'Waiting approval',
      detail: waitingApproval.message || `Approval required for ${waitingApproval.task || 'the current change'}.`,
      activeIndex: 2,
      eventsCount: events.length,
    }
  }

  if (verifying) {
    const detail = verifying.status === 'running'
      ? verifying.message || 'Post-change validation is running.'
      : verifying.message || 'Verification is in progress.'
    return {
      state: 'verifying',
      label: 'Verifying',
      detail,
      activeIndex: 4,
      eventsCount: events.length,
    }
  }

  if (runningProgress?.status === 'running' || runningCommand?.status === 'running') {
    return {
      state: 'running',
      label: 'Running',
      detail: runningProgress?.message || runningCommand?.command || 'Applying approved changes.',
      activeIndex: 3,
      eventsCount: events.length,
    }
  }

  if (planning) {
    return {
      state: 'planning',
      label: 'Planning',
      detail: planning.task || `Planning ${planning.plannedActions.length} actions across ${planning.devices.length} devices.`,
      activeIndex: 1,
      eventsCount: events.length,
    }
  }

  if (threadRunning) {
    return {
      state: 'thinking',
      label: 'Thinking',
      detail: 'Collecting device context and preparing the workflow.',
      activeIndex: 0,
      eventsCount: events.length,
    }
  }

  if (events.length > 0) {
    return {
      state: 'completed',
      label: 'Completed',
      detail: 'Workflow finished and results are ready.',
      activeIndex: 5,
      eventsCount: events.length,
    }
  }

  return {
    state: 'thinking',
    label: 'Thinking',
    detail: 'Waiting for the first agent action.',
    activeIndex: 0,
    eventsCount: events.length,
  }
}

export function WorkflowStateRail({
  snapshot,
  compact = false,
}: {
  snapshot: AgentWorkflowSnapshot
  compact?: boolean
}) {
  const gridClassName = compact ? 'grid gap-2 sm:grid-cols-2 xl:grid-cols-3' : 'grid gap-2 sm:grid-cols-2 xl:grid-cols-7'

  return (
    <div className={compact ? 'rounded-2xl border border-border bg-muted/10 p-3' : 'mb-4 rounded-2xl border border-border bg-muted/10 p-4'}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-muted-foreground" />
            <p className="text-sm font-medium">Agent workflow</p>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{snapshot.detail}</p>
        </div>
        <Badge variant="outline" className={workflowTone(snapshot.state)}>
          {snapshot.label}
        </Badge>
      </div>
      <div className={compact ? 'mt-3' : 'mt-4'}>
        <div className={gridClassName}>
          {workflowOrder.map((step, index) => {
            const active = step.key === snapshot.state
            const completed = snapshot.activeIndex > index
            const tone =
              active
                ? workflowTone(step.key)
                : completed
                  ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
                  : 'border-border bg-background text-muted-foreground'

            return (
              <div key={step.key} className={`rounded-xl border px-3 py-2 text-xs transition-all duration-300 ${active ? 'shadow-sm scale-[1.01]' : ''} ${tone}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{step.label}</span>
                  {completed ? (
                    <CheckCircle2 className="size-3.5" />
                  ) : active ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <span className="size-3.5 rounded-full border border-current/40" />
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
        <span>{snapshot.eventsCount} streamed events</span>
        <span>Plan • Validate • Execute • Verify</span>
      </div>
    </div>
  )
}

const workflowProgressSteps = workflowOrder.filter((step) => step.key !== 'failed')

export function WorkflowInline({
  snapshot,
  visible = false,
}: {
  snapshot: AgentWorkflowSnapshot
  visible?: boolean
}) {
  if (!visible) return null

  const failed = snapshot.state === 'failed'
  const completed = snapshot.state === 'completed'
  const stepIndex = workflowProgressSteps.findIndex((step) => step.key === snapshot.state)
  const active = !failed && !completed

  return (
    <div className="my-2 w-full overflow-hidden rounded-xl border border-border bg-muted/20">
      <div className="flex items-center gap-1.5 border-b border-border px-3 py-2">
        <ListChecks className="size-4 text-muted-foreground" />
        <span className="text-[11px] font-medium tracking-wide text-muted-foreground">Agent tasks</span>
        <span className="ml-auto flex items-center gap-1.5 text-[11px] font-medium text-foreground">
          {failed ? (
            <CircleX className="size-3.5 text-red-500" />
          ) : active ? (
            <Loader2 className="size-3.5 animate-spin text-primary" />
          ) : (
            <CheckCircle2 className="size-3.5 text-emerald-500" />
          )}
          {failed ? 'Failed' : snapshot.label}
        </span>
      </div>
      <div className="py-1">
        {workflowProgressSteps.map((step, index) => {
          const status: 'todo' | 'in_progress' | 'done' | 'failed' = failed
            ? index === stepIndex
              ? 'failed'
              : 'todo'
            : completed
              ? 'done'
              : index === stepIndex
                ? 'in_progress'
                : index < stepIndex
                  ? 'done'
                  : 'todo'

          const tone =
            status === 'failed'
              ? 'text-red-500'
              : status === 'in_progress'
                ? 'text-primary'
                : status === 'done'
                  ? 'text-emerald-500'
                  : 'text-muted-foreground/60'

          const Icon =
            status === 'done' ? CheckCircle2 : status === 'in_progress' ? Loader2 : status === 'failed' ? CircleX : Circle

          return (
            <div key={step.key} className="flex items-center gap-3 px-4 py-1.5">
              <Icon className={`size-4 shrink-0 ${tone} ${status === 'in_progress' ? 'animate-spin' : ''}`} />
              <span
                className={`text-xs leading-5 ${
                  status === 'done' ? 'text-muted-foreground' : status === 'in_progress' ? 'text-foreground' : 'text-muted-foreground'
                }`}
              >
                {step.label}
              </span>
              {status === 'in_progress' && snapshot.detail ? (
                <span className="truncate text-[11px] text-muted-foreground">{snapshot.detail}</span>
              ) : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function WorkflowStreamBar({
  snapshot,
  visible = false,
}: {
  snapshot: AgentWorkflowSnapshot
  visible?: boolean
}) {
  if (!visible) return null

  const failed = snapshot.state === 'failed'
  const completed = snapshot.state === 'completed'
  const stepIndex = workflowProgressSteps.findIndex((step) => step.key === snapshot.state)
  const denominator = Math.max(workflowProgressSteps.length - 1, 1)
  const progress = failed || completed ? 100 : Math.round((Math.max(stepIndex, 0) / denominator) * 100)
  const streaming = !failed && !completed

  return (
    <div className="border-t border-border bg-background/95 px-3 py-2 backdrop-blur">
      <div className="mx-auto flex max-w-4xl flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 text-[11px] font-semibold text-foreground">
            {failed ? (
              <CircleX className="size-3 text-red-500" />
            ) : streaming ? (
              <Loader2 className="size-3 animate-spin text-primary" />
            ) : (
              <CheckCircle2 className="size-3 text-emerald-500" />
            )}
            {failed ? 'Failed' : snapshot.label}
          </span>
          <div className="h-1 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full rounded-full transition-all duration-700 ${failed ? 'bg-red-500' : 'bg-primary'}`}
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-[10px] tabular-nums text-muted-foreground">{progress}%</span>
        </div>
        <div className="flex items-center gap-1 overflow-x-auto">
          {workflowProgressSteps.map((step, index) => {
            const status: 'failed' | 'active' | 'done' | 'pending' = failed
              ? 'failed'
              : completed
                ? 'done'
                : index === stepIndex
                  ? 'active'
                  : index < stepIndex
                    ? 'done'
                    : 'pending'

            const tone =
              status === 'failed'
                ? 'bg-red-500/10 text-red-500 dark:text-red-300'
                : status === 'active'
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : status === 'done'
                    ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300'
                    : 'bg-muted text-muted-foreground'

            return (
              <div
                key={step.key}
                className={`flex min-w-0 flex-1 items-center justify-center gap-1 whitespace-nowrap rounded-full px-2 py-1 text-[10px] font-medium transition-all duration-300 ${tone}`}
              >
                {status === 'active' ? (
                  <Loader2 className="size-3 shrink-0 animate-spin" />
                ) : status === 'done' ? (
                  <CheckCircle2 className="size-3 shrink-0" />
                ) : null}
                <span className="hidden lg:inline">{step.label}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
