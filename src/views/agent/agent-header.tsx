import { Activity, Sparkles } from 'lucide-react'
import { Badge } from 'src/components/ui/badge'

export function AgentHeader({
  onlineDevices,
  projectLabel,
  environmentLabel,
}: {
  onlineDevices: number
  projectLabel?: string
  environmentLabel?: string
}) {
  return (
    <section className="rounded-2xl border border-border bg-background/80 px-4 py-4 shadow-sm backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <Badge variant="outline" className="mb-2 h-8 gap-1.5 border-border bg-muted/40 px-3 text-xs text-muted-foreground">
            <Sparkles className="size-3" />
            Network Copilot
          </Badge>
          <h1 className="truncate text-xl font-semibold tracking-tight md:text-2xl">
            AI Network Agent
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            Plan, validate, and execute network work from a guarded chat workspace with lab, device, and backend status in one view.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="outline" className="h-8 rounded-full px-3">
            <Activity className="size-3" />
            {onlineDevices} online
          </Badge>
          {projectLabel ? (
            <Badge variant="outline" className="h-8 rounded-full px-3">
              Project: {projectLabel}
            </Badge>
          ) : null}
          {environmentLabel ? (
            <Badge variant="outline" className="h-8 rounded-full px-3">
              Env: {environmentLabel}
            </Badge>
          ) : null}
          <Badge variant="secondary" className="h-8 rounded-full px-3">
            Guarded workflow
          </Badge>
          <Badge variant="outline" className="h-8 rounded-full px-3">
            9Router
          </Badge>
        </div>
      </div>
    </section>
  )
}
