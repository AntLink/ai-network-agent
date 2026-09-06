import { Bot, Cloud, Laptop, Loader2, Network, Plus, Router, Server, SwitchCamera } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router'
import { toast } from 'sonner'
import { saveTopologySnapshot, useGns3Status, useTopology } from 'src/api/network'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import { TopologyCanvas, type TopologyCanvasHandle } from 'src/components/topology/topology-canvas'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { ScrollArea } from 'src/components/ui/scroll-area'
import { Textarea } from 'src/components/ui/textarea'

const palette = [
  { label: 'Cisco Router', icon: Router },
  { label: 'MikroTik Router', icon: Router },
  { label: 'Aruba Switch', icon: SwitchCamera },
  { label: 'Linux', icon: Server },
  { label: 'PC', icon: Laptop },
  { label: 'NAT', icon: Network },
  { label: 'Cloud', icon: Cloud },
]

const TopologyBuilderPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const projectId = searchParams.get('projectId') ?? undefined
  const { data, error, isLoading } = useTopology(projectId)
  const { data: gns3Status, isLoading: gns3Loading } = useGns3Status()
  const [prompt, setPrompt] = useState('Create 2 Cisco routers connected through an Aruba switch and attach one MikroTik router to the switch.')
  const canvasRef = useRef<TopologyCanvasHandle>(null)

  const currentProject = useMemo(
    () => gns3Status?.data.projects.find((project) => project.id === projectId),
    [gns3Status, projectId]
  )

  const handleSelectProject = (nextProjectId: string) => {
    setSearchParams({ projectId: nextProjectId })
  }

  const handleSaveLayout = () => {
    if (!data?.data) {
      toast.error('Topology belum siap disimpan.')
      return
    }

    const layout = canvasRef.current?.exportLayout()
    const payload = layout ? { ...data.data, layout } : data.data

    saveTopologySnapshot(payload, projectId)
      .then(() => {
        const saved = canvasRef.current?.saveLayout()
        if (!saved) {
          toast.warning('Topology tersimpan, tetapi layout lokal belum sempat disimpan.')
          return
        }
        toast.success('Topology tersimpan dan siap ditampilkan di halaman Topology.')
      })
      .catch(() => {
        toast.error('Topology gagal disimpan.')
      })
  }

  if (isLoading) return <LoadingState rows={6} />
  if (error) return <ErrorState message="Failed to load topology builder." />

  return (
    <div className="grid items-start gap-4 xl:grid-cols-[18rem_minmax(0,1fr)]">
      <div className="grid gap-4 self-start xl:sticky xl:top-24">
        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <CardTitle>GNS3 Topologies</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 py-4">
            {gns3Loading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Loading GNS3 projects...
              </div>
            ) : gns3Status?.data.projects.length ? (
              <ScrollArea className="h-[18rem] pr-2">
                <div className="grid gap-2">
                  {gns3Status.data.projects.map((project) => {
                    const active = project.id === projectId
                    return (
                      <button
                        key={project.id}
                        onClick={() => handleSelectProject(project.id)}
                        className={[
                          'flex items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition-colors hover:bg-muted',
                          active ? 'border-primary bg-primary/5' : 'border-border',
                        ].join(' ')}
                      >
                        <span className="truncate font-medium">{project.name}</span>
                        <Badge variant={project.status === 'running' ? 'default' : 'outline'}>{project.status}</Badge>
                      </button>
                    )
                  })}
                </div>
              </ScrollArea>
            ) : (
              <div className="rounded-lg border border-dashed border-border p-3 text-sm text-muted-foreground">
                No GNS3 projects found.
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="self-start shadow-sm">
          <CardHeader className="border-b">
            <CardTitle>Devices</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 py-4">
            <ScrollArea className="h-[13rem] pr-2">
              <div className="grid gap-3">
                {palette.map((item) => {
                  const Icon = item.icon
                  return (
                    <button key={item.label} className="flex items-center justify-between rounded-lg border border-border p-3 text-left text-sm hover:bg-muted">
                      <span className="flex items-center gap-2">
                        <Icon className="size-4 text-muted-foreground" />
                        {item.label}
                      </span>
                      <Plus className="size-4 text-muted-foreground" />
                    </button>
                  )
                })}
              </div>
            </ScrollArea>

            <div className="grid gap-2 rounded-lg border border-border bg-muted/30 p-3">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Bot className="size-4" />
                Agent command
              </div>
              <Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} className="min-h-28" />
              <Button>
                <Bot className="size-4" /> Generate Topology
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 self-start">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Topology Builder</h1>
            <p className="text-sm text-muted-foreground">
              Drag-ready canvas for topology drafts. Generated layouts require approval before lab deployment.
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {projectId
                ? `Editing GNS3 project: ${currentProject?.name ?? projectId}`
                : 'Showing the latest saved topology snapshot.'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={handleSaveLayout}>Save Builder</Button>
          </div>
        </div>
        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between gap-3">
              <CardTitle>Canvas</CardTitle>
              {data?.data ? <Badge variant="outline">{data.data.nodes.length} nodes</Badge> : null}
            </div>
          </CardHeader>
          <CardContent className="py-4">
            {data?.data ? (
              <TopologyCanvas
                ref={canvasRef}
                topology={data.data}
                builder
                storageKey={projectId ? `topology-builder-layout-${projectId}` : 'topology-builder-layout'}
              />
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default TopologyBuilderPage
