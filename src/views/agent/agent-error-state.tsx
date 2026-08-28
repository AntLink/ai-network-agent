import { AlertTriangle } from 'lucide-react'
import { Card, CardContent } from 'src/components/ui/card'

export function AgentErrorState({ message }: { message: string }) {
  return (
    <Card className="border-red-500/20 bg-red-500/5">
      <CardContent className="grid gap-2 py-5 text-red-700 dark:text-red-300">
        <div className="flex items-center gap-3">
          <AlertTriangle className="size-5 shrink-0" />
          <span className="text-sm font-semibold">{message}</span>
        </div>
        <p className="text-xs leading-5 text-red-700/80 dark:text-red-300/80">
          Check the backend services, GNS3 status, and device inventory fetch before retrying the workspace.
        </p>
      </CardContent>
    </Card>
  )
}
