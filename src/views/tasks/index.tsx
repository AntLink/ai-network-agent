import { Clock, RefreshCw, UserRound, Workflow } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useTaskDetail, useTasks } from 'src/api/network'
import { connectTaskSSE } from 'src/api/network/sse-client'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { TaskStatusBadge } from 'src/components/network/task-status-badge'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { ScrollArea } from 'src/components/ui/scroll-area'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import { cn } from 'src/lib/utils'
import type { TaskStep } from 'src/types/network'

type FeedEvent = {
  id: string
  title: string
  detail: string
  status: 'queued' | 'running' | 'success' | 'failed'
}

const TasksPage = () => {
  const tasks = useTasks()
  const [selectedTaskId, setSelectedTaskId] = useState('task-ospf-r1-r2')
  const detail = useTaskDetail(selectedTaskId)
  const [liveEvents, setLiveEvents] = useState<FeedEvent[]>([])

  useEffect(() => {
    if (!tasks.data?.data?.length) return
    if (!tasks.data.data.find((task) => task.id === selectedTaskId)) {
      setSelectedTaskId(tasks.data.data[0].id)
    }
  }, [selectedTaskId, tasks.data?.data])

  useEffect(() => {
    const disconnect = connectTaskSSE((event: any) => {
      void tasks.mutate()
      void detail.mutate()

      if (event.type !== 'task_progress' && event.type !== 'task_created' && event.type !== 'task_updated' && event.type !== 'task_completed') {
        return
      }

      const task = typeof event.task === 'object' && event.task ? (event.task as Record<string, unknown>) : undefined
      const step = typeof event.step === 'object' && event.step ? (event.step as Record<string, unknown>) : undefined
      const title = String(step?.name ?? task?.name ?? 'Task update')
      const detailText = String(step?.output ?? task?.status ?? 'Task event received')
      const status = normalizeStatus(String(step?.status ?? task?.status ?? 'running'))

      setLiveEvents((current) => [{ id: String(event.id ?? `${Date.now()}`), title, detail: detailText, status }, ...current].slice(0, 6))
    })

    return disconnect
  }, [detail, tasks])

  const taskData = useMemo(() => tasks.data?.data ?? [], [tasks.data?.data])
  const selectedTask = taskData.find((task) => task.id === selectedTaskId)
  const selectedSteps = detail.data?.data?.steps ?? []
  const statusCounts = useMemo(() => {
    const counts = { queued: 0, running: 0, success: 0, failed: 0, cancelled: 0 }
    taskData.forEach((task) => {
      counts[task.status] += 1
    })
    return counts
  }, [taskData])

  if (tasks.isLoading) return <LoadingState rows={6} />
  if (tasks.error) return <ErrorState message="Failed to load automation tasks." />

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_20rem]">
      <div className="grid gap-4">
        <div className="grid gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Automation Tasks</h1>
            <p className="text-sm text-muted-foreground">Execution history for AI agent, user, scheduler, and API initiated work.</p>
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            <MetricCard title="Queued" value={String(statusCounts.queued)} detail="Waiting for execution" />
            <MetricCard title="Running" value={String(statusCounts.running)} detail="Active jobs" />
            <MetricCard title="Success" value={String(statusCounts.success)} detail="Completed jobs" />
            <MetricCard title="Failed" value={String(statusCounts.failed)} detail="Jobs needing review" />
          </div>
        </div>

        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between gap-3">
              <CardTitle>Task Queue</CardTitle>
              <Button variant="outline" size="sm" onClick={() => void tasks.mutate()}>
                <RefreshCw className="size-4" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent className="py-5">
            {taskData.length ? (
              <div className="overflow-x-auto rounded-lg border border-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Task</TableHead>
                      <TableHead>Device</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Started</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Agent</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {taskData.map((task) => (
                      <TableRow key={task.id} className={cn(selectedTaskId === task.id && 'bg-muted/50')}>
                        <TableCell className="font-medium">
                          <div className="grid gap-1">
                            <span>{task.name}</span>
                            <span className="text-xs text-muted-foreground">{task.id}</span>
                          </div>
                        </TableCell>
                        <TableCell>{task.device}</TableCell>
                        <TableCell>{task.action}</TableCell>
                        <TableCell><TaskStatusBadge status={task.status} /></TableCell>
                        <TableCell>{task.started}</TableCell>
                        <TableCell>{task.duration}</TableCell>
                        <TableCell>{task.user}</TableCell>
                        <TableCell>{task.agent}</TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="outline" onClick={() => setSelectedTaskId(task.id)}>
                            Open
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <EmptyState title="No automation tasks found." />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 content-start xl:sticky xl:top-24 xl:self-start">
        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between gap-3">
              <CardTitle>Execution Timeline</CardTitle>
              {selectedTask ? <Badge variant="outline">{selectedTask.status}</Badge> : null}
            </div>
          </CardHeader>
          <CardContent className="py-5">
            {detail.isLoading && <LoadingState rows={4} />}
            {detail.error && <ErrorState message="Failed to load task detail." />}
            {detail.data?.data && (
              <div className="grid gap-4">
                <div>
                  <h2 className="text-base font-semibold">{detail.data.data.task.name}</h2>
                  <div className="mt-2 flex flex-wrap gap-2 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><Clock className="size-4" /> {detail.data.data.task.duration}</span>
                    <span className="flex items-center gap-1"><UserRound className="size-4" /> {detail.data.data.task.user}</span>
                    <span className="flex items-center gap-1"><Workflow className="size-4" /> {detail.data.data.task.agent}</span>
                    <span className="flex items-center gap-1"><Workflow className="size-4" /> {selectedSteps.length} steps</span>
                  </div>
                </div>

                <ScrollArea className="h-[24rem] pr-3">
                  <div className="grid gap-3">
                    {detail.data.data.steps.length ? detail.data.data.steps.map((step, index) => (
                      <StepCard key={step.id} step={step} index={index} />
                    )) : (
                      <EmptyState title="No execution steps found." />
                    )}
                  </div>
                </ScrollArea>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <CardTitle>Live Feed</CardTitle>
          </CardHeader>
          <CardContent className="py-5">
            <ScrollArea className="h-[22rem] pr-3">
              <div className="grid gap-3">
                {liveEvents.length ? liveEvents.map((event) => (
                  <div key={event.id} className="rounded-lg border border-border bg-muted/20 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium">{event.title}</p>
                      <Badge variant="outline" className={feedBadgeClass(event.status)}>{event.status}</Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">{event.detail}</p>
                  </div>
                )) : (
                  <p className="text-sm text-muted-foreground">Event stream akan tampil saat ada deploy, verify, atau rollback dari backend.</p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function StepCard({ step, index }: { step: TaskStep; index: number }) {
  return (
    <div className="relative rounded-lg border border-border bg-muted/20 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{index + 1}. {step.name}</p>
          <p className="mt-1 text-xs text-muted-foreground">{step.timestamp}</p>
        </div>
        <TaskStatusBadge status={step.status} />
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{step.output}</p>
      {step.errors && <p className="mt-2 text-sm text-red-600">{step.errors}</p>}
    </div>
  )
}

function MetricCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <Card className="border-border/70 shadow-sm">
      <CardContent className="grid gap-2 p-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{title}</p>
        <p className="text-lg font-semibold">{value}</p>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  )
}

function feedBadgeClass(status: FeedEvent['status']) {
  if (status === 'success') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
  if (status === 'failed') return 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300'
  return 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300'
}

function normalizeStatus(value: string): FeedEvent['status'] {
  const normalized = value.toLowerCase()
  if (normalized.includes('success') || normalized.includes('ok') || normalized.includes('done')) return 'success'
  if (normalized.includes('fail') || normalized.includes('error') || normalized.includes('rollback')) return 'failed'
  return 'running'
}

export default TasksPage
