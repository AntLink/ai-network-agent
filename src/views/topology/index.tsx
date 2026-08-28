import { Maximize, MousePointer2, Move, ZoomIn } from 'lucide-react'
import { useMemo } from 'react'
import { useSearchParams } from 'react-router'
import { useTopology } from 'src/api/network'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import { TopologyCanvas } from 'src/components/topology/topology-canvas'
import { LifecycleBadge } from 'src/components/network/status-badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Badge } from 'src/components/ui/badge'

const TopologyPage = () => {
  const [searchParams] = useSearchParams()
  const projectId = searchParams.get('projectId') ?? undefined
  const { data, error, isLoading } = useTopology(projectId)

  const topologyHealth = useMemo(() => deriveTopologyHealth(data?.data.nodes ?? []), [data?.data.nodes])

  if (isLoading) return <LoadingState rows={6} />
  if (error) return <ErrorState message="Failed to load topology." />

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Topology</h1>
          <p className="text-sm text-muted-foreground">Interactive topology canvas with node status, vendor, IP, interface labels, zoom, pan, and fit view.</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge variant="outline">{projectId ? 'Project Snapshot' : 'Saved Snapshot'}</Badge>
            <LifecycleBadge status={topologyHealth} />
            {projectId ? <span className="text-xs text-muted-foreground">Project ID: {projectId}</span> : null}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline"><MousePointer2 className="size-4" /> Select</Button>
          <Button variant="outline"><Move className="size-4" /> Pan</Button>
          <Button variant="outline"><ZoomIn className="size-4" /> Zoom</Button>
          <Button><Maximize className="size-4" /> Fit View</Button>
        </div>
      </div>

      <Card>
        <CardHeader className="rounded-t-2xl border-b bg-gradient-to-r from-slate-500/10 via-card to-card">
          <CardTitle>{data?.data.name ?? 'Network Topology'}</CardTitle>
        </CardHeader>
        <CardContent className="py-5">
          {data?.data && <TopologyCanvas topology={data.data} />}
        </CardContent>
      </Card>
    </div>
  )
}

function deriveTopologyHealth(nodes: Array<{ status: string }>): 'online' | 'offline' | 'warning' | 'unknown' {
  if (!nodes.length) return 'unknown'
  const statuses = nodes.map((node) => String(node.status).toLowerCase())
  const onlineCount = statuses.filter((status) => status === 'online').length
  const offlineCount = statuses.filter((status) => status === 'offline').length
  const warningCount = statuses.filter((status) => status === 'warning').length

  if (onlineCount === statuses.length) return 'online'
  if (offlineCount === statuses.length) return 'offline'
  if (warningCount > 0 || (onlineCount > 0 && offlineCount > 0)) return 'warning'
  return 'unknown'
}

export default TopologyPage
