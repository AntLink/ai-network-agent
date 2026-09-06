import { Skeleton } from 'src/components/ui/skeleton'

export function AgentLoadingState() {
  return (
    <div className="grid gap-4">
      <div className="grid gap-3 rounded-2xl border border-border bg-background/70 p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="grid gap-2">
            <Skeleton className="h-4 w-28 rounded-full" />
            <Skeleton className="h-8 w-72 max-w-full rounded-lg" />
            <Skeleton className="h-4 w-[28rem] max-w-full rounded-full" />
          </div>
          <div className="flex flex-wrap gap-2">
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-32 rounded-full" />
            <Skeleton className="h-8 w-28 rounded-full" />
            <Skeleton className="h-8 w-28 rounded-full" />
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[16rem_minmax(0,1fr)_minmax(20rem,0.45fr)]">
        <Skeleton className="h-[680px] w-full rounded-3xl" />
        <div className="grid gap-4">
          <Skeleton className="h-[160px] w-full rounded-3xl" />
          <Skeleton className="h-[500px] w-full rounded-3xl" />
        </div>
        <Skeleton className="h-[680px] w-full rounded-3xl" />
      </div>
    </div>
  )
}
