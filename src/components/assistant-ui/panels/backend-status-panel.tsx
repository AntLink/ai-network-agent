import { Badge } from 'src/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Activity, Cloud, Server } from 'lucide-react'

function statusTone(status?: string) {
  const normalized = String(status ?? '').toLowerCase()
  if (normalized.includes('connected') || normalized.includes('ok') || normalized.includes('healthy')) {
    return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
  }
  if (normalized.includes('warning') || normalized.includes('degraded')) {
    return 'border-amber-500/20 bg-amber-500/10 text-amber-700 dark:text-amber-300'
  }
  if (normalized.includes('error') || normalized.includes('fail') || normalized.includes('down')) {
    return 'border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-300'
  }
  return 'border-border bg-muted/50 text-muted-foreground'
}

export function BackendStatusPanel({
  apiStatus = 'connected',
  apiUrl = 'http://localhost:8000',
  gns3Status = 'connected',
  gns3Controller = 'http://localhost:3080',
  aiStatus = 'connected',
}: {
  apiStatus?: string
  apiUrl?: string
  gns3Status?: string
  gns3Controller?: string
  aiStatus?: string
}) {
  const items = [
    { label: 'Backend API', status: apiStatus, detail: apiUrl, icon: Server },
    { label: 'GNS3', status: gns3Status, detail: gns3Controller, icon: Cloud },
    { label: 'AI Provider', status: aiStatus, detail: '9Router', icon: Activity },
  ]

  return (
    <Card className="border-border bg-background/80">
      <CardHeader className="border-b py-4">
        <CardTitle className="text-sm font-medium text-muted-foreground">Connection status</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 py-4">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <div key={item.label} className="flex items-start justify-between gap-3 rounded-2xl border border-border bg-muted/20 px-3 py-2">
              <div className="flex min-w-0 items-start gap-2">
                <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{item.label}</p>
                  <p className="truncate text-xs text-muted-foreground">{item.detail}</p>
                </div>
              </div>
              <Badge variant="outline" className={`rounded-full ${statusTone(item.status)}`}>
                {item.status}
              </Badge>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
