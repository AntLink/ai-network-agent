import { Layers3, Server, ShieldCheck } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router'
import { EnvironmentSwitcher } from 'src/components/environment/environment-switcher'
import { EnvironmentWorkflow } from 'src/components/environment/environment-workflow'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { ScrollArea } from 'src/components/ui/scroll-area'
import { Separator } from 'src/components/ui/separator'
import { ProjectSelector } from 'src/components/assistant-ui/project-selector'
import { useEnvironmentOverview, useEnvironmentProfiles, useEnvironmentWorkflow, getEnvironmentProfile, resolveEnvironmentFromProjectId } from 'src/api/environments'
import { useProjectInventory } from 'src/api/inventory'
import type { EnvironmentType } from 'src/types/environment'

interface EnvironmentPageProps {
  environment?: EnvironmentType
}

export function EnvironmentPage({ environment = 'lab' }: EnvironmentPageProps) {
  const navigate = useNavigate()
  const { data: profiles, isLoading: profilesLoading, error: profilesError } = useEnvironmentProfiles()
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useEnvironmentOverview()
  const { data: workflow, isLoading: workflowLoading } = useEnvironmentWorkflow(environment)
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')

  const activeProject = useMemo(() => {
    const projects = overview?.data.projects ?? []
    const scoped = projects.filter((project) => resolveEnvironmentFromProjectId(project.id) === environment)
    return scoped.find((project) => project.id === selectedProjectId) ?? scoped[0] ?? projects.find((project) => project.id === selectedProjectId) ?? projects[0]
  }, [environment, overview?.data.projects, selectedProjectId])

  useEffect(() => {
    if (!activeProject?.id) return
    if (selectedProjectId !== activeProject.id) {
      setSelectedProjectId(activeProject.id)
    }
  }, [activeProject?.id, selectedProjectId])

  const { data: inventory, isLoading: inventoryLoading, error: inventoryError } = useProjectInventory(activeProject?.id)

  if (profilesLoading || overviewLoading || workflowLoading || inventoryLoading) {
    return <LoadingState rows={6} />
  }

  if (profilesError || overviewError || inventoryError) {
    return <ErrorState message="Failed to load environment dashboard." />
  }

  const environmentProfile = getEnvironmentProfile(environment)
  const projects = overview?.data.projects ?? []
  const summary = overview?.data.summary

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="grid gap-1">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Layers3 className="size-4" />
            Environment control
          </div>
          <h1 className="text-2xl font-semibold tracking-normal">Lab / Staging / Production</h1>
          <p className="text-sm text-muted-foreground">
            Environment-aware workflow for project-scoped inventory, approvals, backup, and safe deployment.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" onClick={() => navigate('/agent')}>
            <ShieldCheck className="size-4" />
            Open Agent
          </Button>
          <Button onClick={() => navigate('/topology-builder')}>
            <Server className="size-4" />
            Topology Builder
          </Button>
        </div>
      </div>

      <EnvironmentSwitcher profiles={profiles?.data ?? []} value={environment} onChange={(next) => navigate(`/environments/${next === 'lab' ? 'lab' : next}`)} />

      <div className="grid gap-4 lg:grid-cols-[1.35fr_0.9fr]">
        <Card>
          <CardHeader className="border-b">
            <CardTitle className="flex items-center justify-between gap-3">
              <span>{environmentProfile.name} overview</span>
              <Badge variant="outline" className={environmentProfile.badge}>
                {environmentProfile.id}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 py-5">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <StatCard title="Total Devices" value={`${summary?.totalDevices.total ?? 0}`} detail={`${summary?.totalDevices.online ?? 0} online`} />
              <StatCard title="Active Labs" value={`${summary?.activeLabs.total ?? 0}`} detail={`${summary?.activeLabs.gns3 ?? 0} GNS3`} />
              <StatCard title="AI Ops" value={`${summary?.aiOperations.totalToday ?? 0}`} detail={`${summary?.aiOperations.success ?? 0} success`} />
              <StatCard title="Health" value={`${summary?.networkHealth.score ?? 0}%`} detail={summary?.networkHealth.label ?? 'Unknown'} />
            </div>

            <Separator />

            <div className="grid gap-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">Active project</p>
                  <p className="text-sm text-muted-foreground">{activeProject?.name ?? 'No project selected'}</p>
                </div>
                <Badge variant="outline">{activeProject ? resolveEnvironmentFromProjectId(activeProject.id) : environment}</Badge>
              </div>
              <ProjectSelector
                projects={(overview?.data.projects ?? []).filter((project) => resolveEnvironmentFromProjectId(project.id) === environment)}
                value={activeProject?.id ?? selectedProjectId}
                onValueChange={setSelectedProjectId}
              />
              <div className="grid gap-2 rounded-xl border bg-muted/20 p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-muted-foreground">Project ID</span>
                  <span className="font-mono text-xs">{activeProject?.id ?? '-'}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-muted-foreground">Nodes</span>
                  <span className="font-medium">{inventory?.data.nodes.length ?? 0}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-muted-foreground">Links</span>
                  <span className="font-medium">{inventory?.data.links.length ?? 0}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <EnvironmentWorkflow profile={environmentProfile} steps={workflow?.data ?? []} />
      </div>

      <Card>
        <CardHeader className="border-b">
          <CardTitle>Project inventory</CardTitle>
        </CardHeader>
        <CardContent className="py-5">
          <ScrollArea className="max-h-[28rem] rounded-lg border">
            <div className="grid gap-3 p-4">
              {(inventory?.data.nodes ?? []).map((node) => (
                <div key={node.nodeId} className="grid gap-2 rounded-xl border bg-card p-4 shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="grid gap-1">
                      <p className="font-semibold">{node.hostname}</p>
                      <p className="text-xs text-muted-foreground">{node.platform}</p>
                    </div>
                    <Badge variant={node.status === 'online' ? 'default' : node.status === 'warning' ? 'secondary' : 'outline'}>
                      {node.status}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{node.vendor}</Badge>
                    <Badge variant="outline">{node.environment}</Badge>
                    <Badge variant="outline">{node.projectName}</Badge>
                  </div>
              <div className="grid gap-1 text-xs text-muted-foreground">
                    <span>Management IP: {node.managementIp ?? '-'}</span>
                    <span>Capabilities: {node.capabilities.map((item) => item.label).join(', ') || '-'}</span>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b">
          <CardTitle className="flex items-center justify-between gap-3">
            <span>Environment projects</span>
            <Badge variant="outline">{projects.length} projects</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 py-5 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((project) => {
            const projectEnvironment = resolveEnvironmentFromProjectId(project.id)
            return (
              <div key={project.id} className="rounded-xl border bg-muted/20 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium">{project.name}</p>
                    <p className="text-xs text-muted-foreground">{project.id}</p>
                  </div>
                  <Badge variant="outline">{projectEnvironment}</Badge>
                </div>
                <div className="mt-3 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Nodes</span>
                  <span>{project.nodes}</span>
                </div>
              </div>
            )
          })}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border bg-muted/20 p-4">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight">{value}</p>
      <p className="text-sm text-muted-foreground">{detail}</p>
    </div>
  )
}
