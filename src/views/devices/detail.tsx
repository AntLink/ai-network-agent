import { Link, useParams } from 'react-router'
import { ArrowLeft, Download, GitCompare, RotateCcw, ShieldCheck, Terminal } from 'lucide-react'
import { useDeviceDetail } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { StatusBadge, VendorBadge } from 'src/components/network/status-badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Progress } from 'src/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from 'src/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'

const DeviceDetailPage = () => {
  const { id } = useParams()
  const { data, error, isLoading } = useDeviceDetail(id)

  if (isLoading) {
    return <LoadingState rows={7} />
  }

  if (error) {
    return <ErrorState message="Failed to load device detail." />
  }

  if (!data?.data) {
    return <EmptyState title="Device detail is not available." />
  }

  const { device, interfaces, routes } = data.data

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" nativeButton={false} render={<Link to="/devices" />}>
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-normal">{device.hostname}</h1>
              <VendorBadge vendor={device.vendor} />
              <StatusBadge status={device.status} />
            </div>
            <p className="text-sm text-muted-foreground">
              {device.model} · {device.managementIp} · {device.platform}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline"><Terminal className="size-4" /> SSH</Button>
          <Button><ShieldCheck className="size-4" /> Backup Config</Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="gap-0">
        <div className="overflow-x-auto rounded-xl border border-border bg-card px-2 shadow-sm [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <TabsList variant="line" className="h-12 min-w-max justify-start gap-2 bg-transparent p-0">
            <TabsTrigger className="h-12 flex-none px-3" value="overview">Overview</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="interfaces">Interfaces</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="routing">Routing</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="configuration">Configuration</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="commands">Commands</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="backups">Backups</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="metrics">Metrics</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="logs">Logs</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="overview" className="mt-5">
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
            <Card>
              <CardHeader><CardTitle>Device Overview</CardTitle></CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <DetailTile label="Hostname" value={device.hostname} />
                <DetailTile label="Vendor" value={device.vendor} />
                <DetailTile label="Model" value={device.model} />
                <DetailTile label="OS Version" value={device.osVersion} />
                <DetailTile label="Uptime" value={device.uptime} />
                <DetailTile label="Management IP" value={device.managementIp} />
                <MetricTile label="CPU" value={device.cpu} />
                <MetricTile label="RAM" value={device.memory} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Connection</CardTitle></CardHeader>
              <CardContent className="grid gap-3">
                <DetailTile label="SSH Status" value={device.connection.status} />
                <DetailTile label="Last Login" value={device.connection.lastLogin} />
                <DetailTile label="Authentication Method" value={device.connection.authMethod} />
                <DetailTile label="Privilege Level" value={device.connection.privilegeLevel} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="interfaces" className="mt-5">
          <Card>
            <CardHeader><CardTitle>Interfaces</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-lg border border-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Interface</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>IP Address</TableHead>
                      <TableHead>Admin Status</TableHead>
                      <TableHead>Operational Status</TableHead>
                      <TableHead>Speed</TableHead>
                      <TableHead>Duplex</TableHead>
                      <TableHead>RX</TableHead>
                      <TableHead>TX</TableHead>
                      <TableHead>Errors</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {interfaces.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{item.name}</TableCell>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="font-mono text-xs">{item.ipAddress}</TableCell>
                        <TableCell>{item.adminStatus.toUpperCase()}</TableCell>
                        <TableCell>{item.operationalStatus.toUpperCase()}</TableCell>
                        <TableCell>{item.speed}</TableCell>
                        <TableCell>{item.duplex}</TableCell>
                        <TableCell>{item.rx}</TableCell>
                        <TableCell>{item.tx}</TableCell>
                        <TableCell>{item.errors}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="routing" className="mt-5">
          <Card>
            <CardHeader><CardTitle>Routing Table</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-lg border border-border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Network</TableHead>
                      <TableHead>Prefix</TableHead>
                      <TableHead>Protocol</TableHead>
                      <TableHead>Next Hop</TableHead>
                      <TableHead>Interface</TableHead>
                      <TableHead>Metric</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {routes.map((route) => (
                      <TableRow key={route.id}>
                        <TableCell className="font-mono text-xs">{route.network}</TableCell>
                        <TableCell>{route.prefix}</TableCell>
                        <TableCell className="uppercase">{route.protocol}</TableCell>
                        <TableCell>{route.nextHop}</TableCell>
                        <TableCell>{route.interface}</TableCell>
                        <TableCell>{route.metric}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="configuration" className="mt-5">
          <Card>
            <CardHeader className="border-b">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CardTitle>Configuration</CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline"><GitCompare className="size-4" /> Compare</Button>
                  <Button variant="outline"><Download className="size-4" /> Download</Button>
                  <Button><RotateCcw className="size-4" /> Restore</Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 py-5 lg:grid-cols-2">
              <ConfigPanel title="Running Configuration" lines={['hostname ' + device.hostname, 'ip ssh version 2', 'service timestamps debug datetime msec']} />
              <ConfigPanel title="Candidate Configuration" lines={['+ interface GigabitEthernet0/1', '+ description LAN transit', '+ no shutdown']} />
            </CardContent>
          </Card>
        </TabsContent>

        {['commands', 'backups', 'metrics', 'logs'].map((tab) => (
          <TabsContent key={tab} value={tab} className="mt-5">
            <EmptyState title={`${tab} view will be implemented in the next phase.`} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

function DetailTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold capitalize">{value}</p>
    </div>
  )
}

function MetricTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      <div className="mb-2 flex items-center justify-between text-xs font-medium text-muted-foreground">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <Progress value={value} />
    </div>
  )
}

function ConfigPanel({ title, lines }: { title: string; lines: string[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <div className="border-b bg-muted/40 px-3 py-2 text-sm font-medium">{title}</div>
      <pre className="min-h-52 overflow-x-auto bg-background p-4 text-xs leading-6 text-foreground">
        {lines.map((line) => `${line}\n`)}
      </pre>
    </div>
  )
}

export default DeviceDetailPage
