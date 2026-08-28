import { AlertTriangle, Inbox } from 'lucide-react'
import { Card, CardContent } from 'src/components/ui/card'
import { Skeleton } from 'src/components/ui/skeleton'

export function LoadingState({ rows = 4 }: { rows?: number }) {
  return (
    <div className="grid gap-3">
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} className="h-16 w-full rounded-lg" />
      ))}
    </div>
  )
}

export function ErrorState({ message = 'Unable to load network data.' }: { message?: string }) {
  return (
    <Card className="border-red-500/20 bg-red-500/5">
      <CardContent className="flex items-center gap-3 py-5 text-red-700 dark:text-red-300">
        <AlertTriangle className="size-5" />
        <span className="text-sm font-medium">{message}</span>
      </CardContent>
    </Card>
  )
}

export function EmptyState({ title = 'No data available' }: { title?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center justify-center gap-3 py-10 text-muted-foreground">
        <Inbox className="size-5" />
        <span className="text-sm font-medium">{title}</span>
      </CardContent>
    </Card>
  )
}
