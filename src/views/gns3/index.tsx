import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { ExternalLink, Eye, Loader2, Network, PencilLine, Play, Plus, RefreshCw, Square, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import {
  clearGns3Cache,
  closeGns3ProjectAction,
  createGns3ProjectAction,
  deleteGns3NodeAction,
  deleteGns3ProjectAction,
  loadGns3NodeList,
  openGns3ProjectAction,
  startGns3NodeAction,
  stopGns3NodeAction,
  testGns3ConnectionAction,
  useGns3Status,
} from 'src/api/network'
import { loadBackendTopology } from 'src/api/network/backend-client'
import type { Gns3Node } from 'src/api/network/backend-client'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from 'src/components/ui/dialog'
import { Input } from 'src/components/ui/input'
import { Label } from 'src/components/ui/label'
import { ScrollArea } from 'src/components/ui/scroll-area'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import { TopologyCanvas } from 'src/components/topology/topology-canvas'
import type { Topology } from 'src/types/network'

const Gns3Page = () => {
  const navigate = useNavigate()
  const { data, error, isLoading, mutate } = useGns3Status()
  const [testing, setTesting] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [creating, setCreating] = useState(false)
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [nodes, setNodes] = useState<Gns3Node[]>([])
  const [loadingNodes, setLoadingNodes] = useState(false)
  const [actionBusy, setActionBusy] = useState<string | null>(null)
  const [topologyOpen, setTopologyOpen] = useState(false)
  const [topologyData, setTopologyData] = useState<Topology | null>(null)
  const [loadingTopology, setLoadingTopology] = useState(false)
  const [topologyProjectName, setTopologyProjectName] = useState('')

  const status = data?.data

  const summary = useMemo(() => ({
    total: status?.projects.length ?? 0,
    running: status?.projects.filter((project) => project.status === 'running').length ?? 0,
    stopped: status?.projects.filter((project) => project.status === 'stopped').length ?? 0,
    server: status?.server ?? 'disconnected',
  }), [status])

  const handleTestConnection = useCallback(async () => {
    setTesting(true)
    try {
      const result = await testGns3ConnectionAction()
      toast.success(`GNS3 connected. Found ${result.projects_count} projects.`)
      clearGns3Cache()
      mutate()
    } catch (err) {
      toast.error(`Connection failed: ${String(err)}`)
    } finally {
      setTesting(false)
    }
  }, [mutate])

  const handleRefresh = useCallback(() => {
    clearGns3Cache()
    mutate()
  }, [mutate])

  const handleCreateProject = useCallback(async () => {
    if (!newProjectName.trim()) return
    setCreating(true)
    try {
      await createGns3ProjectAction(newProjectName.trim())
      toast.success(`Project created: ${newProjectName.trim()}`)
      setCreateOpen(false)
      setNewProjectName('')
      clearGns3Cache()
      mutate()
    } catch (err) {
      toast.error(`Create failed: ${String(err)}`)
    } finally {
      setCreating(false)
    }
  }, [mutate, newProjectName])

  const handleOpenProject = useCallback(async (projectId: string) => {
    setActionBusy(`open-${projectId}`)
    try {
      await openGns3ProjectAction(projectId)
      toast.success('Project opened')
      clearGns3Cache()
      mutate()
    } catch (err) {
      toast.error(`Open failed: ${String(err)}`)
    } finally {
      setActionBusy(null)
    }
  }, [mutate])

  const handleCloseProject = useCallback(async (projectId: string) => {
    setActionBusy(`close-${projectId}`)
    try {
      await closeGns3ProjectAction(projectId)
      toast.success('Project closed')
      clearGns3Cache()
      mutate()
    } catch (err) {
      toast.error(`Close failed: ${String(err)}`)
    } finally {
      setActionBusy(null)
    }
  }, [mutate])

  const handleDeleteProject = useCallback(async (projectId: string, name: string) => {
    if (!window.confirm(`Delete project "${name}"? This cannot be undone.`)) return
    setActionBusy(`delete-${projectId}`)
    try {
      await deleteGns3ProjectAction(projectId)
      toast.success('Project deleted')
      clearGns3Cache()
      mutate()
    } catch (err) {
      toast.error(`Delete failed: ${String(err)}`)
    } finally {
      setActionBusy(null)
    }
  }, [mutate])

  const handleViewNodes = useCallback(async (projectId: string) => {
    setSelectedProject(projectId)
    setLoadingNodes(true)
    try {
      const nodeList = await loadGns3NodeList(projectId)
      setNodes(nodeList)
    } catch (err) {
      toast.error(`Load nodes failed: ${String(err)}`)
      setNodes([])
    } finally {
      setLoadingNodes(false)
    }
  }, [])

  const handleStartNode = useCallback(async (nodeId: string) => {
    if (!selectedProject) return
    setActionBusy(`start-${nodeId}`)
    try {
      await startGns3NodeAction(selectedProject, nodeId)
      toast.success('Node started')
      const nodeList = await loadGns3NodeList(selectedProject)
      setNodes(nodeList)
    } catch (err) {
      toast.error(`Start failed: ${String(err)}`)
    } finally {
      setActionBusy(null)
    }
  }, [selectedProject])

  const handleStopNode = useCallback(async (nodeId: string) => {
    if (!selectedProject) return
    setActionBusy(`stop-${nodeId}`)
    try {
      await stopGns3NodeAction(selectedProject, nodeId)
      toast.success('Node stopped')
      const nodeList = await loadGns3NodeList(selectedProject)
      setNodes(nodeList)
    } catch (err) {
      toast.error(`Stop failed: ${String(err)}`)
    } finally {
      setActionBusy(null)
    }
  }, [selectedProject])

  const handleDeleteNode = useCallback(async (nodeId: string, name: string) => {
    if (!selectedProject) return
    if (!window.confirm(`Delete node "${name}"?`)) return
    setActionBusy(`delnode-${nodeId}`)
    try {
      await deleteGns3NodeAction(selectedProject, nodeId)
      toast.success('Node deleted')
      const nodeList = await loadGns3NodeList(selectedProject)
      setNodes(nodeList)
    } catch (err) {
      toast.error(`Delete failed: ${String(err)}`)
    } finally {
      setActionBusy(null)
    }
  }, [selectedProject])

  const handleViewTopology = useCallback(async (projectId: string, projectName: string) => {
    setLoadingTopology(true)
    setTopologyProjectName(projectName)
    setTopologyOpen(true)
    try {
      setTopologyData(await loadBackendTopology(projectId))
    } catch (err) {
      toast.error(`Topology failed: ${String(err)}`)
      setTopologyData(null)
    } finally {
      setLoadingTopology(false)
    }
  }, [])

  const handleEditTopology = useCallback((projectId: string) => {
    navigate(`/topology-builder?projectId=${encodeURIComponent(projectId)}`)
  }, [navigate])

  if (isLoading) return <LoadingState rows={6} />
  if (error) return <ErrorState message="Failed to load GNS3 status." />

  return (
    <div className="grid gap-4">
      <div className="grid gap-3">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">GNS3</h1>
            <p className="text-sm text-muted-foreground">GNS3 server, VM, controller endpoint, and project lifecycle management.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={handleTestConnection} disabled={testing}>
              {testing ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
              Test Connection
            </Button>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="size-4" /> Refresh
            </Button>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" /> New Project
            </Button>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatusCard title="GNS3 Server" value={summary.server} />
          <StatusCard title="GNS3 VM" value={status?.vm ?? 'disconnected'} />
          <StatusCard title="Projects" value={String(summary.total)} />
          <StatusCard title="Running Projects" value={String(summary.running)} />
        </div>
      </div>

      <Card className="shadow-sm">
        <CardHeader className="border-b">
          <CardTitle>Projects</CardTitle>
        </CardHeader>
        <CardContent className="py-5">
          {status?.projects.length ? (
            <ScrollArea className="h-[26rem] rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Project</TableHead>
                    <TableHead>Nodes</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {status.projects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell className="font-medium">{project.name}</TableCell>
                      <TableCell>{project.nodes}</TableCell>
                      <TableCell>
                        <Badge variant={project.status === 'running' ? 'default' : 'outline'}>{project.status}</Badge>
                      </TableCell>
                      <TableCell>{project.created}</TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="outline" onClick={() => handleViewNodes(project.id)}>
                            <Eye className="size-4" /> Nodes
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewTopology(project.id, project.name)}
                            disabled={loadingTopology}
                          >
                            <Network className="size-4" /> Topology
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => navigate(`/topology?projectId=${encodeURIComponent(project.id)}`)}>
                            <ExternalLink className="size-4" /> Open Page
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => handleEditTopology(project.id)}>
                            <PencilLine className="size-4" /> Edit Topology
                          </Button>
                          {project.status === 'stopped' ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleOpenProject(project.id)}
                              disabled={actionBusy === `open-${project.id}`}
                            >
                              {actionBusy === `open-${project.id}` ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
                              Open
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleCloseProject(project.id)}
                              disabled={actionBusy === `close-${project.id}`}
                            >
                              {actionBusy === `close-${project.id}` ? <Loader2 className="size-4 animate-spin" /> : <Square className="size-4" />}
                              Close
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDeleteProject(project.id, project.name)}
                            disabled={actionBusy === `delete-${project.id}`}
                          >
                            {actionBusy === `delete-${project.id}` ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          ) : (
            <EmptyState title="No GNS3 projects found." />
          )}
        </CardContent>
      </Card>

      {selectedProject && (
        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle>Nodes - {status?.projects.find((p) => p.id === selectedProject)?.name ?? selectedProject}</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => { setSelectedProject(null); setNodes([]) }}>Close</Button>
            </div>
          </CardHeader>
          <CardContent className="py-5">
            {loadingNodes ? (
              <LoadingState rows={3} />
            ) : nodes.length ? (
              <ScrollArea className="h-[22rem] rounded-lg border border-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Console</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {nodes.map((node) => (
                      <TableRow key={node.node_id}>
                        <TableCell className="font-medium">{node.name}</TableCell>
                        <TableCell>{node.node_type}</TableCell>
                        <TableCell>
                          <Badge variant={node.status === 'started' || node.status === 'running' ? 'default' : 'outline'}>{node.status}</Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {node.console_host && node.console_port ? `${node.console_host}:${node.console_port}` : '-'}
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-2">
                            {node.status === 'started' || node.status === 'running' ? (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleStopNode(node.node_id)}
                                disabled={actionBusy === `stop-${node.node_id}`}
                              >
                                {actionBusy === `stop-${node.node_id}` ? <Loader2 className="size-4 animate-spin" /> : <Square className="size-4" />}
                                Stop
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleStartNode(node.node_id)}
                                disabled={actionBusy === `start-${node.node_id}`}
                              >
                                {actionBusy === `start-${node.node_id}` ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
                                Start
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleDeleteNode(node.node_id, node.name)}
                              disabled={actionBusy === `delnode-${node.node_id}`}
                            >
                              {actionBusy === `delnode-${node.node_id}` ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            ) : (
              <EmptyState title="No nodes in this project." />
            )}
          </CardContent>
        </Card>
      )}

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create GNS3 Project</DialogTitle>
            <DialogDescription>Enter a name for the new project.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="project-name">Project Name</Label>
              <Input
                id="project-name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="e.g. Cisco-IPsec-Lab"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateProject} disabled={creating || !newProjectName.trim()}>
              {creating ? <Loader2 className="size-4 animate-spin mr-2" /> : null}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={topologyOpen} onOpenChange={setTopologyOpen}>
        <DialogContent className="sm:max-w-7xl overflow-hidden" style={{ maxWidth: '80rem' }}>
          <DialogHeader>
            <DialogTitle>
              <Network className="mr-2 inline size-4" />
              Topology - {topologyProjectName}
            </DialogTitle>
            <DialogDescription>Auto-generated from GNS3 project nodes and links.</DialogDescription>
          </DialogHeader>
          <div className="py-2">
            {loadingTopology ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="size-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">Loading topology...</span>
              </div>
            ) : topologyData && topologyData.nodes.length > 0 ? (
              <ScrollArea className="bubble-scrollbar max-h-[calc(100vh-14rem)] rounded-lg">
                <div className="flex gap-4 pr-2">
                  <div className="min-w-0 flex-1">
                    <TopologyCanvas topology={topologyData} />
                  </div>
                  <TopologySidebar topology={topologyData} />
                </div>
              </ScrollArea>
            ) : (
              <div className="py-16 text-center text-sm text-muted-foreground">No topology data. Start the project nodes first.</div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTopologyOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function TopologySidebar({ topology }: { topology: Topology }) {
  const connections = useMemo(() => {
    const map: Record<string, Array<{ remote: string; localIf: string; remoteIf: string }>> = {}
    for (const node of topology.nodes) map[node.id] = []
    for (const link of topology.links) {
      map[link.source]?.push({ remote: link.target, localIf: link.sourceInterface, remoteIf: link.targetInterface })
      map[link.target]?.push({ remote: link.source, localIf: link.targetInterface, remoteIf: link.sourceInterface })
    }
    return map
  }, [topology])

  const nodeMap = useMemo(() => {
    const result: Record<string, Topology['nodes'][number]> = {}
    for (const node of topology.nodes) result[node.id] = node
    return result
  }, [topology])

  const vendorColor: Record<string, string> = {
    cisco: 'border-l-blue-500',
    mikrotik: 'border-l-cyan-500',
    aruba: 'border-l-purple-500',
    linux: 'border-l-emerald-500',
    other: 'border-l-orange-500',
  }

  return (
    <div className="bubble-scrollbar w-72 shrink-0 scroll-smooth overflow-y-auto overscroll-contain rounded-lg border border-border bg-card" style={{ maxHeight: '36rem' }}>
      <div className="border-b px-4 py-3">
        <p className="text-sm font-medium">Nodes ({topology.nodes.length})</p>
        <p className="text-xs text-muted-foreground">Links: {topology.links.length}</p>
      </div>
      <div className="divide-y">
        {topology.nodes.map((node) => {
          const conns = connections[node.id] ?? []
          return (
            <div key={node.id} className={`border-l-2 px-4 py-3 ${vendorColor[node.vendor] ?? 'border-l-border'}`}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">{node.hostname}</p>
                <Badge variant={node.status === 'online' ? 'default' : 'outline'} className="text-[10px]">{node.status}</Badge>
              </div>
              <p className="mt-0.5 font-mono text-xs text-muted-foreground">{node.ip}</p>
              <p className="mt-1 text-[11px] text-muted-foreground capitalize">{node.vendor}</p>
              {conns.length > 0 && (
                <div className="mt-2 space-y-1">
                  {conns.map((c, index) => (
                    <div key={index} className="flex items-center gap-1.5 text-[11px]">
                      <span className="font-mono text-muted-foreground">{c.localIf}</span>
                      <span className="text-muted-foreground/50">→</span>
                      <span className="font-medium">{nodeMap[c.remote]?.hostname ?? c.remote}</span>
                      <span className="font-mono text-muted-foreground">{c.remoteIf}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function StatusCard({ title, value, mono = false }: { title: string; value: string; mono?: boolean }) {
  return (
    <Card className="shadow-sm">
      <CardContent className="py-5">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className={mono ? 'mt-2 font-mono text-sm font-semibold' : 'mt-2 text-xl font-semibold capitalize'}>{value}</p>
      </CardContent>
    </Card>
  )
}

export default Gns3Page
