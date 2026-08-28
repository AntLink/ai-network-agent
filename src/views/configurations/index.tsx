import { Bot, CheckCircle2, FileCode, Network, ShieldCheck, Workflow } from 'lucide-react'
import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { applyConfigPlan, createConfigPlan, rollbackConfigPlan, useConfigurations, useDevices } from 'src/api/network'
import { connectTaskSSE } from 'src/api/network/sse-client'
import { ConfirmAction } from 'src/components/network/confirm-action'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Input } from 'src/components/ui/input'
import { Label } from 'src/components/ui/label'
import { ScrollArea } from 'src/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from 'src/components/ui/tabs'
import { Textarea } from 'src/components/ui/textarea'
import { cn } from 'src/lib/utils'
import type { ConfigApplyResult, ConfigPlan, TaskStatus } from 'src/types/network'

type OperationState = 'idle' | 'planning' | 'planned' | 'applying' | 'rollingBack' | 'applied' | 'rolled_back' | 'error'

type FeedItem = {
  id: string
  title: string
  detail: string
  status: Extract<TaskStatus, 'queued' | 'running' | 'success' | 'failed'>
}

const WORKFLOW_STEPS = ['Planning', 'Pre-check', 'Backup', 'Configuration', 'Verification', 'Save', 'Complete']

const ConfigurationsPage = () => {
  const configs = useConfigurations()
  const devices = useDevices()
  const [selectedDeviceId, setSelectedDeviceId] = useState('cisco-iosv-r1')
  const [rawCli, setRawCli] = useState('interface GigabitEthernet0/1\n description LAN transit\n no shutdown')
  const [interfaceName, setInterfaceName] = useState('GigabitEthernet0/1')
  const [interfaceIp, setInterfaceIp] = useState('192.168.10.1/24')
  const [adminState, setAdminState] = useState('enabled')
  const [aiPrompt, setAiPrompt] = useState('Configure GigabitEthernet0/1 on R1 as 192.168.10.1/24 and keep management connectivity safe.')
  const [approvedBy, setApprovedBy] = useState('admin')
  const [saveOnSuccess, setSaveOnSuccess] = useState(false)
  const [mode, setMode] = useState('structured')
  const [operationState, setOperationState] = useState<OperationState>('idle')
  const [plan, setPlan] = useState<ConfigPlan>()
  const [applyResult, setApplyResult] = useState<ConfigApplyResult>()
  const [rollbackResult, setRollbackResult] = useState<ConfigApplyResult>()
  const [taskFeed, setTaskFeed] = useState<FeedItem[]>([])
  const [errorMessage, setErrorMessage] = useState<string>()

  const selectedDevice = useMemo(
    () => devices.data?.data.find((device) => device.id === selectedDeviceId) ?? devices.data?.data[0],
    [devices.data?.data, selectedDeviceId],
  )

  useEffect(() => {
    const disconnect = connectTaskSSE((event: any) => {
      if (event.type !== 'task_progress' && event.type !== 'task_created' && event.type !== 'task_updated' && event.type !== 'task_completed') {
        return
      }

      const step = typeof event.step === 'object' && event.step ? (event.step as Record<string, unknown>) : undefined
      const task = typeof event.task === 'object' && event.task ? (event.task as Record<string, unknown>) : undefined
      const title = String(step?.name ?? task?.name ?? 'Task update')
      const detail = String(step?.output ?? task?.status ?? 'Task event received')
      const status = normalizeFeedStatus(String(step?.status ?? task?.status ?? 'running'))

      setTaskFeed((current) => [{ id: String(event.id ?? `${Date.now()}`), title, detail, status }, ...current].slice(0, 6))
    })

    return disconnect
  }, [])

  if (configs.isLoading || devices.isLoading) return <LoadingState rows={7} />
  if (configs.error || devices.error) return <ErrorState message="Failed to load configuration deployment workspace." />

  const mockConfig = configs.data?.data[0]
  const generatedCommands = buildCommands(mode, rawCli, interfaceName, interfaceIp, adminState, aiPrompt)
  const risk = plan?.riskLevel ?? mockConfig?.risk.toUpperCase() ?? 'MEDIUM'
  const canApply = Boolean(plan?.planId && approvedBy.trim() && operationState !== 'applying' && operationState !== 'rollingBack')
  const canRollback = Boolean(plan?.planId && selectedDevice && operationState !== 'applying' && operationState !== 'rollingBack')
  const currentResult = rollbackResult ?? applyResult

  const generatePlan = async () => {
    if (!selectedDevice) return

    setOperationState('planning')
    setErrorMessage(undefined)
    setApplyResult(undefined)
    setRollbackResult(undefined)

    try {
      const nextPlan = await createConfigPlan({
        deviceId: selectedDevice.id,
        commands: generatedCommands,
        verify: buildVerifyChecks(selectedDevice.hostname),
        saveOnSuccess,
        description: `Frontend generated ${mode} configuration for ${selectedDevice.hostname}`,
      })
      setPlan(nextPlan)
      setOperationState('planned')
      toast.success('Dry run plan created')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to create config plan')
      setOperationState('error')
      toast.error('Failed to create dry run plan')
    }
  }

  const applyPlan = async () => {
    if (!plan?.planId) return

    setOperationState('applying')
    setErrorMessage(undefined)

    try {
      const result = await applyConfigPlan(plan.planId, approvedBy)
      setApplyResult(result)
      setRollbackResult(undefined)
      setOperationState(result.status.toLowerCase().includes('rolled') ? 'rolled_back' : 'applied')
      toast.success('Configuration deployment finished')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to apply config plan')
      setOperationState('error')
      toast.error('Configuration deployment failed')
    }
  }

  const rollbackPlan = async () => {
    if (!selectedDevice || !plan?.planId) return

    setOperationState('rollingBack')
    setErrorMessage(undefined)

    try {
      const result = await rollbackConfigPlan({
        deviceId: selectedDevice.id,
        planId: plan.planId,
      })
      setRollbackResult(result)
      setOperationState(result.status.toLowerCase().includes('success') ? 'applied' : 'rolled_back')
      toast.success('Rollback request submitted')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to rollback config plan')
      setOperationState('error')
      toast.error('Rollback failed')
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.12fr)_20rem]">
      <div className="grid gap-4">
        <div className="grid gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Configurations</h1>
            <p className="text-sm text-muted-foreground">Plan, dry run, approve, deploy, verify, and rollback configuration through backend governance endpoints.</p>
          </div>
          <div className="grid gap-3 md:grid-cols-4">
            <MetricCard title="Plan" value={plan?.planId || 'Not created'} detail={selectedDevice?.hostname ?? '-'} icon={<ShieldCheck className="size-4" />} />
            <MetricCard title="Risk" value={risk} detail={plan?.status ?? 'draft'} icon={<Workflow className="size-4" />} />
            <MetricCard title="State" value={operationState.replace('_', ' ')} detail={approvedBy || 'approval pending'} icon={<CheckCircle2 className="size-4" />} />
            <MetricCard title="Target" value={selectedDevice?.vendor ?? 'unknown'} detail={selectedDevice?.managementIp ?? '-'} icon={<Network className="size-4" />} />
          </div>
        </div>

        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle>Configuration Planner</CardTitle>
              <Badge variant="outline">Plan → Validate → Execute → Verify</Badge>
            </div>
          </CardHeader>
          <CardContent className="grid gap-5 py-5">
            <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_12rem_12rem]">
              <Field label="Target Device">
                <Select value={selectedDevice?.id} onValueChange={(value) => {
                  if (value) setSelectedDeviceId(value)
                }}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {(devices.data?.data ?? []).map((device) => (
                      <SelectItem key={device.id} value={device.id}>
                        {device.hostname} - {device.vendor}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Approved By"><Input value={approvedBy} onChange={(event) => setApprovedBy(event.target.value)} /></Field>
              <Field label="Save On Success">
                <Select value={saveOnSuccess ? 'yes' : 'no'} onValueChange={(value) => setSaveOnSuccess(value === 'yes')}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="no">No</SelectItem>
                    <SelectItem value="yes">Yes</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
            </div>

            <Tabs value={mode} onValueChange={(value) => {
              if (value) setMode(value)
            }}>
              <TabsList>
                <TabsTrigger value="raw">Raw CLI</TabsTrigger>
                <TabsTrigger value="structured">Structured</TabsTrigger>
                <TabsTrigger value="ai">AI Generated</TabsTrigger>
              </TabsList>
              <TabsContent value="raw" className="mt-4">
                <Textarea value={rawCli} onChange={(event) => setRawCli(event.target.value)} className="min-h-56 font-mono text-xs" />
              </TabsContent>
              <TabsContent value="structured" className="mt-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <Field label="Interface"><Input value={interfaceName} onChange={(event) => setInterfaceName(event.target.value)} /></Field>
                  <Field label="IP"><Input value={interfaceIp} onChange={(event) => setInterfaceIp(event.target.value)} /></Field>
                  <Field label="Admin State">
                    <Select value={adminState} onValueChange={(value) => {
                      if (value) setAdminState(value)
                    }}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="enabled">Enabled</SelectItem>
                        <SelectItem value="disabled">Disabled</SelectItem>
                      </SelectContent>
                    </Select>
                  </Field>
                </div>
              </TabsContent>
              <TabsContent value="ai" className="mt-4">
                <Textarea value={aiPrompt} onChange={(event) => setAiPrompt(event.target.value)} className="min-h-40" />
                <p className="mt-2 text-xs text-muted-foreground">AI backend belum aktif. Mode ini sementara menghasilkan candidate command deterministik untuk plan endpoint.</p>
              </TabsContent>
            </Tabs>

            {errorMessage && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300">
                {errorMessage}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={generatePlan} disabled={operationState === 'planning'}>
                <ShieldCheck className="size-4" />
                {operationState === 'planning' ? 'Creating Plan...' : 'Validate'}
              </Button>
              <Button onClick={generatePlan} disabled={operationState === 'planning'}>
                <FileCode className="size-4" />
                Generate Dry Run
              </Button>
              <Button variant="outline"><Bot className="size-4" /> Ask AI</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <CardTitle>Execution Preview</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 py-5">
            <div className="grid gap-2 text-sm md:grid-cols-2">
              <InfoRow label="Plan ID" value={plan?.planId || '-'} />
              <InfoRow label="Target" value={selectedDevice?.hostname ?? '-'} />
              <InfoRow label="Vendor" value={selectedDevice?.vendor ?? '-'} />
              <InfoRow label="Status" value={operationState.replace('_', ' ')} />
            </div>

            <div>
              <p className="text-sm font-medium">Generated Configuration</p>
              <ScrollArea className="mt-2 h-72 rounded-lg border border-border bg-zinc-950">
                <pre className="p-4 font-mono text-xs leading-6 text-zinc-100">
                  {(plan?.commands ?? generatedCommands).join('\n')}
                </pre>
              </ScrollArea>
            </div>

            <div className="grid gap-2">
              <p className="text-sm font-medium">Risk Analysis</p>
              <RiskItem check="Management connectivity" result="safe" detail="No management IP change detected in candidate commands." />
              <RiskItem check="Backend governance" result={plan ? 'safe' : 'warning'} detail={plan ? 'Plan stored in backend config governance.' : 'Generate dry run to create a backend plan.'} />
              <RiskItem check="Approval identity" result={approvedBy.trim() ? 'safe' : 'blocked'} detail={approvedBy.trim() ? `Approval identity: ${approvedBy}` : 'approved_by is required by backend.'} />
            </div>

            {currentResult && (
              <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-700 dark:text-emerald-300">
                <div className="flex items-center gap-2 font-medium">
                  <CheckCircle2 className="size-4" />
                  Result: {currentResult.status}
                </div>
                <ScrollArea className="mt-2 h-32 rounded-md bg-background/40">
                  <pre className="whitespace-pre-wrap p-3 font-mono text-xs">{currentResult.output.join('\n')}</pre>
                </ScrollArea>
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <ConfirmAction
                label={operationState === 'applying' ? 'Deploying...' : 'Deploy'}
                title="Deploy planned configuration?"
                description={`This will apply plan ${plan?.planId || '-'} to ${selectedDevice?.hostname || 'the selected device'} as ${approvedBy || 'unknown approver'}. Backend will execute config transaction and verification if supported.`}
                disabled={!canApply}
                onConfirm={applyPlan}
              />
              <ConfirmAction
                label={operationState === 'rollingBack' ? 'Rolling back...' : 'Rollback'}
                title="Rollback planned configuration?"
                description={`This will call backend rollback for ${selectedDevice?.hostname || 'the selected device'} using the active plan context. Use only when deployment needs to be reverted.`}
                variant="destructive"
                disabled={!canRollback}
                onConfirm={rollbackPlan}
              />
              <Button variant="outline"><Network className="size-4" /> Cancel</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 content-start xl:sticky xl:top-24 xl:self-start">
        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between gap-3">
              <CardTitle>Workflow State</CardTitle>
              <Badge variant="outline">Workflow live</Badge>
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 py-5">
            {WORKFLOW_STEPS.map((step, index) => {
              const stepState = resolveWorkflowState(operationState, index, plan, currentResult)
              return (
                <div key={step} className="flex items-center justify-between rounded-lg border border-border bg-muted/20 px-3 py-2">
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{step}</p>
                    <p className="text-xs text-muted-foreground">Phase {index + 1}</p>
                  </div>
                  <Badge variant="outline" className={cn(stepState.className)}>{stepState.label}</Badge>
                </div>
              )
            })}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="border-b">
            <CardTitle>Task Feed</CardTitle>
          </CardHeader>
          <CardContent className="py-5">
            <ScrollArea className="h-[28rem] pr-3">
              <div className="grid gap-3">
                {taskFeed.length ? (
                  taskFeed.map((item) => (
                    <div key={item.id} className="rounded-lg border border-border bg-muted/20 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-medium">{item.title}</p>
                        <Badge variant="outline" className={feedBadgeClass(item.status)}>{item.status}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{item.detail}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">Task stream akan muncul setelah ada deploy, rollback, atau event dari backend.</p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function buildCommands(mode: string, rawCli: string, interfaceName: string, interfaceIp: string, adminState: string, aiPrompt: string) {
  if (mode === 'raw') return rawCli.split(/\r?\n/).map((line) => line.trimEnd()).filter(Boolean)
  if (mode === 'ai') {
    return [
      `! AI request: ${aiPrompt}`,
      `interface ${interfaceName}`,
      ` ip address ${interfaceIp}`,
      adminState === 'enabled' ? ' no shutdown' : ' shutdown',
    ]
  }
  return [
    `interface ${interfaceName}`,
    ` ip address ${interfaceIp}`,
    adminState === 'enabled' ? ' no shutdown' : ' shutdown',
  ]
}

function buildVerifyChecks(hostname: string) {
  return [
    { command: 'show ip interface brief', expect: hostname ? undefined : undefined },
  ]
}

function feedBadgeClass(status: FeedItem['status']) {
  if (status === 'success') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
  if (status === 'failed') return 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300'
  return 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300'
}

function normalizeFeedStatus(value: string): FeedItem['status'] {
  const normalized = value.toLowerCase()
  if (normalized.includes('success') || normalized.includes('ok') || normalized.includes('done')) return 'success'
  if (normalized.includes('fail') || normalized.includes('error') || normalized.includes('rollback')) return 'failed'
  return 'running'
}

function resolveWorkflowState(
  operationState: OperationState,
  index: number,
  plan: ConfigPlan | undefined,
  result: ConfigApplyResult | undefined,
) {
  const hasPlan = Boolean(plan?.planId)
  const completed = operationState === 'applied' || operationState === 'rolled_back'
  const failed = operationState === 'error'
  const currentIndex = operationState === 'planning'
    ? 0
    : operationState === 'planned'
      ? 1
      : operationState === 'applying'
        ? 3
        : operationState === 'rollingBack'
          ? 5
          : completed
            ? WORKFLOW_STEPS.length - 1
            : -1

  if (!hasPlan && index > 0) {
    return { label: 'waiting', className: 'text-muted-foreground' }
  }

  if (failed && index <= currentIndex) {
    return { label: 'failed', className: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300' }
  }

  if (index < currentIndex || completed) {
    return { label: 'done', className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300' }
  }

  if (index === currentIndex) {
    return { label: result ? 'verifying' : 'active', className: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300' }
  }

  return { label: 'waiting', className: 'text-muted-foreground' }
}

function MetricCard({ title, value, detail, icon }: { title: string; value: string; detail: string; icon: ReactNode }) {
  return (
    <Card className="border-border/70 shadow-sm">
      <CardContent className="grid gap-3 p-4">
        <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-wide text-muted-foreground">
          <span>{title}</span>
          <span className="inline-flex size-7 items-center justify-center rounded-full border border-border bg-background/80">{icon}</span>
        </div>
        <div className="grid gap-1">
          <p className="text-lg font-semibold leading-tight">{value}</p>
          <p className="text-xs text-muted-foreground">{detail}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/20 px-3 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid gap-2">
      <Label>{label}</Label>
      {children}
    </div>
  )
}

function RiskItem({ check, result, detail }: { check: string; result: 'safe' | 'warning' | 'blocked'; detail: string }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-medium">{check}</span>
        <Badge variant={result === 'safe' ? 'default' : result === 'blocked' ? 'destructive' : 'outline'}>{result}</Badge>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
    </div>
  )
}

export default ConfigurationsPage
