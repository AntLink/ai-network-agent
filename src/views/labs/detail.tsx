import { Link, useParams } from 'react-router'
import { ArrowLeft, Bot, Box, Cable, FileText, Network, Server, Terminal } from 'lucide-react'
import { useLabDetail } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { LifecycleBadge } from 'src/components/network/status-badge'
import { TopologyCanvas } from 'src/components/topology/topology-canvas'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from 'src/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'

const LabDetailPage = () => {
  const { id } = useParams()
  const { data, error, isLoading } = useLabDetail(id)

  if (isLoading) return <LoadingState rows={7} />
  if (error) return <ErrorState message="Failed to load lab detail." />
  if (!data?.data) return <EmptyState title="Lab detail not found." />

  const { lab, topology } = data.data
  const isGns3 = lab.engine === 'gns3'
  const topologyHealth = deriveTopologyHealth(topology.nodes)
  const tabs = isGns3
    ? [
        { value: 'topology', label: 'Topology', icon: Network },
        { value: 'nodes', label: 'Nodes', icon: Server },
        { value: 'links', label: 'Links', icon: Cable },
        { value: 'console', label: 'Console', icon: Terminal },
        { value: 'agent', label: 'Agent', icon: Bot },
        { value: 'logs', label: 'Logs', icon: FileText },
      ]
    : [
        { value: 'topology', label: 'Topology', icon: Network },
        { value: 'nodes', label: 'Nodes', icon: Server },
        { value: 'inventory', label: 'Inventory', icon: Box },
        { value: 'logs', label: 'Logs', icon: FileText },
      ]

  return (
    <div className="grid gap-4">
      <div className="rounded-2xl border bg-gradient-to-r from-slate-500/10 via-card to-card px-4 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="icon" nativeButton={false} render={<Link to="/labs" />}>
              <ArrowLeft className="size-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-semibold tracking-normal">{lab.name}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Badge variant="outline">{isGns3 ? 'GNS3' : 'Containerlab'}</Badge>
                <LifecycleBadge status={lab.status === 'running' ? 'running' : lab.status === 'degraded' ? 'degraded' : 'stopped'} />
                <span className="text-sm text-muted-foreground">{lab.nodes} nodes</span>
                <span className="text-sm text-muted-foreground">Created {lab.created}</span>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <StatPill label="Engine" value={isGns3 ? 'GNS3' : 'Containerlab'} />
            <StatPill label="State" value={lab.status} />
            <StatPill label="Nodes" value={`${lab.nodes}`} />
            <StatPill label="Topology" value={isGns3 ? 'Project' : 'Inventory'} />
          </div>
        </div>
      </div>

      <Tabs defaultValue="topology">
        <TabsList className="w-full justify-start overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <TabsTrigger key={tab.value} value={tab.value}>
                <Icon className="size-4" /> {tab.label}
              </TabsTrigger>
            )
          })}
        </TabsList>

        <TabsContent value="topology" className="mt-4">
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_19rem]">
            <TopologyCanvas topology={topology} />
            <Card>
              <CardHeader className="rounded-t-2xl border-b bg-gradient-to-r from-slate-500/10 via-card to-card">
                <div className="flex items-center justify-between gap-3">
                  <CardTitle>{isGns3 ? 'Project Snapshot' : 'Lab Inventory'}</CardTitle>
                  <LifecycleBadge status={topologyHealth} />
                </div>
              </CardHeader>
              <CardContent className="grid gap-3 py-5">
                <div className="grid grid-cols-2 gap-2">
                  <MiniStat label="Nodes" value={`${topology.nodes.length}`} />
                  <MiniStat label="Links" value={`${topology.links.length}`} />
                </div>
                <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm text-muted-foreground">
                  {isGns3
                    ? 'Topology ini diambil dari GNS3 project dan bisa dibuka ulang dari halaman GNS3.'
                    : 'Topology inventory ini dirangkai dari Containerlab backend dan mengikuti node yang tersedia.'}
                </div>
                <div className="grid gap-2">
                  {topology.nodes.slice(0, 5).map((node) => (
                    <div key={node.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm">
                      <span className="font-medium">{node.hostname}</span>
                      <Badge variant={node.status === 'online' ? 'default' : 'secondary'}>{node.status}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="nodes" className="mt-4">
          <Card>
            <CardHeader><CardTitle>Nodes</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-lg border border-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Hostname</TableHead>
                      <TableHead>Vendor</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>IP</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {topology.nodes.map((node) => (
                      <TableRow key={node.id}>
                        <TableCell className="font-medium">{node.hostname}</TableCell>
                        <TableCell>{node.vendor}</TableCell>
                        <TableCell>{node.status}</TableCell>
                        <TableCell className="font-mono text-xs">{node.ip}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="links" className="mt-4">
          <Card>
            <CardHeader><CardTitle>Links</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-lg border border-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Source</TableHead>
                      <TableHead>Interface A</TableHead>
                      <TableHead>Target</TableHead>
                      <TableHead>Interface B</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {topology.links.map((link) => (
                      <TableRow key={link.id}>
                        <TableCell>{link.source}</TableCell>
                        <TableCell>{link.sourceInterface}</TableCell>
                        <TableCell>{link.target}</TableCell>
                        <TableCell>{link.targetInterface}</TableCell>
                        <TableCell>{link.status}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {!isGns3 ? (
          <TabsContent value="inventory" className="mt-4">
            <Card>
              <CardHeader className="rounded-t-2xl border-b bg-gradient-to-r from-slate-500/10 via-card to-card">
                <CardTitle>Containerlab Inventory</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 py-5">
                <div className="grid gap-2 md:grid-cols-3">
                  <MiniStat label="Topology Nodes" value={`${topology.nodes.length}`} />
                  <MiniStat label="Topology Links" value={`${topology.links.length}`} />
                  <MiniStat label="Status" value={lab.status} />
                </div>
                <EmptyState title="Containerlab backend actions will be wired here next." />
              </CardContent>
            </Card>
          </TabsContent>
        ) : null}

        {(isGns3 ? ['console', 'agent', 'logs'] : ['logs']).map((tab) => (
          <TabsContent key={tab} value={tab} className="mt-4">
            <EmptyState title={`${tab} workspace is prepared for backend integration.`} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/80 px-3 py-2">
      <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-base font-semibold">{value}</p>
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

export default LabDetailPage
