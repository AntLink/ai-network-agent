import { Activity, Bot, FlaskConical, Server } from 'lucide-react'
import { Card, CardContent } from 'src/components/ui/card'
import type { DashboardSummary } from 'src/types/network'

const items = [
  {
    key: 'devices',
    title: 'Total Devices',
    icon: Server,
    getValue: (summary: DashboardSummary) => `${summary.totalDevices.total} Devices`,
    details: (summary: DashboardSummary) => [
      `${summary.totalDevices.online} Online`,
      `${summary.totalDevices.offline} Offline`,
      `${summary.totalDevices.warning} Warning`,
    ],
  },
  {
    key: 'labs',
    title: 'Active Labs',
    icon: FlaskConical,
    getValue: (summary: DashboardSummary) => `${summary.activeLabs.total} Active Labs`,
    details: (summary: DashboardSummary) => [`GNS3: ${summary.activeLabs.gns3}`, `Containerlab: ${summary.activeLabs.containerlab}`],
  },
  {
    key: 'ai',
    title: 'AI Operations',
    icon: Bot,
    getValue: (summary: DashboardSummary) => `${summary.aiOperations.totalToday} Tasks Today`,
    details: (summary: DashboardSummary) => [
      `${summary.aiOperations.success} Success`,
      `${summary.aiOperations.running} Running`,
      `${summary.aiOperations.failed} Failed`,
    ],
  },
  {
    key: 'health',
    title: 'Network Health',
    icon: Activity,
    getValue: (summary: DashboardSummary) => `${summary.networkHealth.score}%`,
    details: (summary: DashboardSummary) => [summary.networkHealth.label],
  },
]

export function SummaryCards({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon
        return (
          <Card key={item.key}>
            <CardContent className="py-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{item.title}</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-normal">{item.getValue(summary)}</h2>
                </div>
                <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="size-5" />
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {item.details(summary).map((detail) => (
                  <span key={detail} className="rounded-md border border-border bg-muted/40 px-2 py-1 text-xs text-muted-foreground">
                    {detail}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
