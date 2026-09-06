import { Badge } from 'src/components/ui/badge'
import { cn } from 'src/lib/utils'
import type { TaskStatus } from 'src/types/network'

const classes: Record<TaskStatus, string> = {
  queued: 'border-muted-foreground/30 bg-muted text-muted-foreground',
  running: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  failed: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
  cancelled: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300',
}

export function TaskStatusBadge({ status }: { status: TaskStatus }) {
  return (
    <Badge variant="outline" className={cn('capitalize', classes[status])}>
      {status}
    </Badge>
  )
}
