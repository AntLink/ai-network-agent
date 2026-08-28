import { Activity } from 'lucide-react'
import { Badge } from 'src/components/ui/badge'

export function ConnectionStatusBar({
  provider = '9Router / AI',
  connection = 'Live',
}: {
  provider?: string
  connection?: string
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant="outline" className="h-8 gap-1.5 px-3">
        <Activity className="size-3" />
        {provider}
      </Badge>
      <Badge variant="secondary" className="h-8 px-3">
        {connection}
      </Badge>
    </div>
  )
}

