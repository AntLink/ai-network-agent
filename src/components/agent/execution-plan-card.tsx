import { AlertTriangle, CheckCircle2, ShieldCheck, XCircle } from 'lucide-react'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { cn } from 'src/lib/utils'
import type { ExecutionPlan, RiskLevel } from 'src/types/network'

const riskClass: Record<RiskLevel, string> = {
  low: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  medium: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  high: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
}

export function ExecutionPlanCard({ plan }: { plan: ExecutionPlan }) {
  return (
    <Card>
      <CardHeader className="border-b">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>AI Plan</CardTitle>
            <p className="text-sm text-muted-foreground">Network changes require review and approval before execution.</p>
          </div>
          <Badge variant="outline" className={cn('uppercase', riskClass[plan.risk])}>
            Risk {plan.risk}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="grid gap-5 py-5">
        <div>
          <p className="text-xs font-medium text-muted-foreground">Task</p>
          <p className="mt-1 text-sm font-semibold">{plan.task}</p>
        </div>

        <div>
          <p className="text-xs font-medium text-muted-foreground">Devices</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {plan.devices.map((device) => (
              <Badge key={device} variant="secondary">{device}</Badge>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-muted-foreground">Planned Actions</p>
          <ol className="mt-3 grid gap-2">
            {plan.plannedActions.map((action, index) => (
              <li key={action} className="flex gap-3 rounded-lg border border-border bg-muted/30 p-3 text-sm">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-background text-xs font-semibold">
                  {index + 1}
                </span>
                {action}
              </li>
            ))}
          </ol>
        </div>

        <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200">
          <div className="flex gap-2">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <span>No destructive action or configuration push will run before approval.</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button><ShieldCheck className="size-4" /> Approve & Execute</Button>
          <Button variant="outline"><CheckCircle2 className="size-4" /> Modify Plan</Button>
          <Button variant="destructive"><XCircle className="size-4" /> Cancel</Button>
        </div>
      </CardContent>
    </Card>
  )
}
