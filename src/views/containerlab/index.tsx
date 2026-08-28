import { Bot, GitBranch, Play, Search, ShieldCheck, Square } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useContainerlab, deployContainerlabAction, destroyContainerlabAction } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from 'src/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import { Textarea } from 'src/components/ui/textarea'

const ContainerlabPage = () => {
  const { data, error, isLoading, mutate } = useContainerlab()
  const [yaml, setYaml] = useState('')
  const [deploying, setDeploying] = useState(false)
  const [destroying, setDestroying] = useState<string | null>(null)

  if (isLoading) return <LoadingState rows={6} />
  if (error) return <ErrorState message="Failed to load Containerlab data." />

  const inventory = data?.data
  const editorValue = yaml || inventory?.yaml || ''

  const handleDeploy = async () => {
    if (!editorValue.trim()) {
      toast.error('Please enter topology YAML')
      return
    }
    setDeploying(true)
    try {
      await deployContainerlabAction('new-lab', editorValue)
      toast.success('Lab deployment started')
      mutate()
    } catch {
      toast.error('Failed to deploy lab')
    } finally {
      setDeploying(false)
    }
  }

  const handleDestroy = async (labId: string) => {
    if (!window.confirm('Destroy this lab? This cannot be undone.')) return
    setDestroying(labId)
    try {
      await destroyContainerlabAction(labId)
      toast.success('Lab destroyed')
      mutate()
    } catch {
      toast.error('Failed to destroy lab')
    } finally {
      setDestroying(null)
    }
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Containerlab</h1>
          <p className="text-sm text-muted-foreground">Topology files, running labs, node inventory, images, validation, and graph actions.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline"><ShieldCheck className="size-4" /> Validate</Button>
          <Button onClick={handleDeploy} disabled={deploying}>
            <Play className="size-4" />
            {deploying ? 'Deploying...' : 'Deploy'}
          </Button>
          <Button variant="outline"><Search className="size-4" /> Inspect</Button>
          <Button variant="outline"><GitBranch className="size-4" /> Graph</Button>
          <Button variant="outline"><Bot className="size-4" /> AI Generate</Button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(24rem,0.8fr)]">
        <Tabs defaultValue="topology-files" className="gap-0">
          <div className="overflow-x-auto rounded-xl border border-border bg-card px-2 shadow-sm [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <TabsList variant="line" className="h-12 min-w-max justify-start gap-2 bg-transparent p-0">
              <TabsTrigger className="h-12 flex-none px-3" value="topology-files">Topology Files</TabsTrigger>
              <TabsTrigger className="h-12 flex-none px-3" value="running-labs">Running Labs</TabsTrigger>
              <TabsTrigger className="h-12 flex-none px-3" value="nodes">Nodes</TabsTrigger>
              <TabsTrigger className="h-12 flex-none px-3" value="images">Images</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="topology-files" className="mt-5">
            <Card>
              <CardHeader className="border-b"><CardTitle>Topology Files</CardTitle></CardHeader>
              <CardContent className="py-5">
                {inventory?.topologyFiles.length ? (
                  <div className="overflow-x-auto rounded-lg border border-border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>File</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Updated</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {inventory.topologyFiles.map((file) => (
                          <TableRow key={file.name}>
                            <TableCell className="font-medium">{file.name}</TableCell>
                            <TableCell><Badge variant={file.status === 'valid' ? 'default' : 'destructive'}>{file.status}</Badge></TableCell>
                            <TableCell>{file.updated}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <EmptyState title="No topology files found." />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="running-labs" className="mt-5">
            <Card>
              <CardHeader className="border-b"><CardTitle>Running Labs</CardTitle></CardHeader>
              <CardContent className="py-5">
                {inventory?.runningLabs.length ? (
                  <div className="overflow-x-auto rounded-lg border border-border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Lab</TableHead>
                          <TableHead>Engine</TableHead>
                          <TableHead>Nodes</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {inventory.runningLabs.map((lab) => (
                          <TableRow key={lab.id}>
                            <TableCell className="font-medium">{lab.name}</TableCell>
                            <TableCell>{lab.engine}</TableCell>
                            <TableCell>{lab.nodes}</TableCell>
                            <TableCell><Badge variant={lab.status === 'running' ? 'default' : 'outline'}>{lab.status}</Badge></TableCell>
                            <TableCell className="text-right">
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDestroy(lab.id)}
                                disabled={destroying === lab.id}
                              >
                                <Square className="size-4" />
                                {destroying === lab.id ? 'Destroying...' : 'Destroy'}
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <EmptyState title="No running labs." />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="nodes" className="mt-5">
            <Card>
              <CardHeader className="border-b"><CardTitle>Nodes</CardTitle></CardHeader>
              <CardContent className="py-5">
                {inventory?.nodes.length ? (
                  <div className="overflow-x-auto rounded-lg border border-border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Kind</TableHead>
                          <TableHead>Image</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {inventory.nodes.map((node) => (
                          <TableRow key={node.name}>
                            <TableCell className="font-medium">{node.name}</TableCell>
                            <TableCell>{node.kind}</TableCell>
                            <TableCell className="font-mono text-xs">{node.image}</TableCell>
                            <TableCell><Badge variant={node.status === 'running' ? 'default' : 'outline'}>{node.status}</Badge></TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <EmptyState title="No nodes found." />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="images" className="mt-5">
            <Card>
              <CardHeader className="border-b"><CardTitle>Images</CardTitle></CardHeader>
              <CardContent className="py-5">
                {inventory?.images.length ? (
                  <div className="overflow-x-auto rounded-lg border border-border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Image</TableHead>
                          <TableHead>Size</TableHead>
                          <TableHead>Source</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {inventory.images.map((image) => (
                          <TableRow key={image.name}>
                            <TableCell className="font-mono text-xs">{image.name}</TableCell>
                            <TableCell>{image.size}</TableCell>
                            <TableCell>{image.source}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <EmptyState title="No images found." />
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <Card className="content-start">
          <CardHeader className="border-b"><CardTitle>Topology Editor</CardTitle></CardHeader>
          <CardContent className="py-5">
            <Textarea
              value={editorValue}
              onChange={(e) => setYaml(e.target.value)}
              className="min-h-[400px] font-mono text-sm"
              placeholder="Enter Containerlab topology YAML..."
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default ContainerlabPage
