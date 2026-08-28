import { useNavigate } from 'react-router'
import { Activity, ExternalLink, Layers3, Play, RotateCw, Server, SquareStack, SquareTerminal, Trash2, type LucideIcon } from 'lucide-react'
import { useLabs } from 'src/api/network'
import { closeGns3ProjectAction, clearGns3Cache, deleteGns3ProjectAction, openGns3ProjectAction, destroyContainerlabAction } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { LifecycleBadge } from 'src/components/network/status-badge'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { ScrollArea } from 'src/components/ui/scroll-area'
import { toast } from 'sonner'
import type { Lab } from 'src/types/network'

const LabsPage = () => {
  const navigate = useNavigate()
  const { data, error, isLoading } = useLabs()

  if (isLoading) return <LoadingState rows={5} />
  if (error) return <ErrorState message="Failed to load labs." />

  const labs = data?.data ?? []
  const summary = {
    total: labs.length,
    gns3: labs.filter((lab) => lab.engine === 'gns3').length,
    containerlab: labs.filter((lab) => lab.engine === 'containerlab').length,
    running: labs.filter((lab) => lab.status === 'running').length,
  }

  return (
    <div className="grid gap-4">
      <div className="grid gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Labs</h1>
          <p className="text-sm text-muted-foreground">Real GNS3 and Containerlab lab inventory loaded from backend services.</p>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <SummaryCard title="Total Labs" value={`${summary.total}`} detail="All discovered labs" icon={SquareStack} />
          <SummaryCard title="GNS3 Projects" value={`${summary.gns3}`} detail="Projects from GNS3 controller" icon={Layers3} />
          <SummaryCard title="Containerlab" value={`${summary.containerlab}`} detail="Running Containerlab labs" icon={Server} />
          <SummaryCard title="Active Labs" value={`${summary.running}`} detail="Currently running" icon={Activity} />
        </div>
      </div>

      {labs.length ? (
        <ScrollArea className="h-[calc(100vh-18rem)] pr-3">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {labs.map((lab) => <LabCard key={lab.id} lab={lab} navigate={navigate} />)}
          </div>
        </ScrollArea>
      ) : (
        <EmptyState title="No labs found." />
      )}
    </div>
  )
}

function LabCard({ lab, navigate }: { lab: Lab; navigate: (to: string) => void }) {
  const engineLabel = lab.engine === 'gns3' ? 'GNS3' : lab.engine === 'containerlab' ? 'Containerlab' : 'vrnetlab'
  const isGns3 = lab.engine === 'gns3'
  const isContainerlab = lab.engine === 'containerlab'

  const handleOpen = async () => {
    if (isGns3) {
      try {
        await openGns3ProjectAction(lab.id)
        clearGns3Cache()
        toast.success('GNS3 project opened.')
      } catch (error) {
        toast.error(`Failed to open GNS3 project: ${String(error)}`)
      }
      return
    }

    navigate(`/labs/${lab.id}`)
  }

  const handleInspect = () => {
    navigate(`/labs/${lab.id}`)
  }

  const handleCloseOrDestroy = async () => {
    if (isGns3) {
      try {
        await closeGns3ProjectAction(lab.id)
        clearGns3Cache()
        toast.success('GNS3 project closed.')
      } catch (error) {
        toast.error(`Failed to close GNS3 project: ${String(error)}`)
      }
      return
    }

    if (isContainerlab) {
      if (!window.confirm(`Destroy Containerlab lab "${lab.name}"?`)) return
      try {
        await destroyContainerlabAction(lab.id)
        toast.success('Containerlab lab destroyed.')
      } catch (error) {
        toast.error(`Failed to destroy Containerlab lab: ${String(error)}`)
      }
    }
  }

  const handleDelete = async () => {
    if (isGns3) {
      if (!window.confirm(`Delete GNS3 project "${lab.name}"?`)) return
      try {
        await deleteGns3ProjectAction(lab.id)
        clearGns3Cache()
        toast.success('GNS3 project deleted.')
      } catch (error) {
        toast.error(`Failed to delete GNS3 project: ${String(error)}`)
      }
    }
  }

  return (
    <Card className="overflow-hidden border-border/70 shadow-sm transition-shadow hover:shadow-md">
      <CardHeader className="rounded-t-2xl border-b bg-gradient-to-r from-slate-500/10 via-card to-card">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="truncate text-base">{lab.name}</CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              {lab.nodes} nodes | created {lab.created}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge variant="outline">{engineLabel}</Badge>
              <LifecycleBadge status={lab.status === 'running' ? 'running' : lab.status === 'degraded' ? 'degraded' : 'stopped'} />
            </div>
          </div>
          <div className="rounded-full border border-border bg-background/80 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            {lab.engine}
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4 py-5">
        <div className="grid grid-cols-2 gap-2">
          <Metric label="Nodes" value={`${lab.nodes}`} />
          <Metric label="State" value={lab.status} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={handleOpen}>
            {isGns3 ? <Play className="size-4" /> : <ExternalLink className="size-4" />}
            {isGns3 ? 'Open Project' : 'Open'}
          </Button>
          <Button size="sm" variant="outline" onClick={handleInspect}>
            <SquareTerminal className="size-4" /> Inspect
          </Button>
          <Button size="sm" variant="outline" onClick={handleCloseOrDestroy}>
            <RotateCw className="size-4" /> {isGns3 ? 'Close' : 'Destroy'}
          </Button>
          {isGns3 ? (
            <Button size="sm" variant="destructive" onClick={handleDelete}>
              <Trash2 className="size-4" /> Delete
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

function SummaryCard({
  title,
  value,
  detail,
  icon: Icon,
}: {
  title: string
  value: string
  detail: string
  icon: LucideIcon
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-5">
        <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-xl font-semibold">{value}</p>
          <p className="truncate text-xs text-muted-foreground">{detail}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
    </div>
  )
}

export default LabsPage
