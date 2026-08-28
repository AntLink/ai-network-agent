import { RefreshCw, Plus } from 'lucide-react'
import { Button } from 'src/components/ui/button'

export function SessionToolbar({
  onNewSession,
  onRefresh,
}: {
  onNewSession: () => void
  onRefresh: () => void
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button size="sm" variant="secondary" className="h-9 flex-1 rounded-lg" onClick={onNewSession}>
        <Plus className="size-4" />
        New Chat
      </Button>
      <Button size="icon-sm" variant="ghost" className="h-9 w-9 rounded-lg" onClick={onRefresh} title="Refresh sessions">
        <RefreshCw className="size-4" />
      </Button>
    </div>
  )
}
