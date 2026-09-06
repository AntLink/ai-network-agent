import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { useNetworkSettings } from 'src/api/network'
import { apiRequest } from 'src/api/network/backend-client'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Input } from 'src/components/ui/input'
import { Label } from 'src/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Switch } from 'src/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from 'src/components/ui/tabs'

const SettingsPage = () => {
  const { data, error, isLoading, mutate } = useNetworkSettings()
  const [saving, setSaving] = useState(false)
  const [aiProvider, setAiProvider] = useState<string>('9router')
  const [aiModel, setAiModel] = useState<string>('opencode-cheap')

  // Load saved AI settings when data arrives
  useEffect(() => {
    if (!data?.data?.ai) return
    const savedProvider = data.data.ai.provider
    const savedModel = data.data.ai.model
    if (savedProvider) setAiProvider(savedProvider)
    if (savedModel) setAiModel(savedModel)
  }, [data])

  if (isLoading) return <LoadingState rows={7} />
  if (error) return <ErrorState message="Failed to load settings." />

  const settings = data?.data

  const handleSaveAI = async () => {
    setSaving(true)
    try {
      // Save AI settings to backend agent settings
      await apiRequest('/api/v1/agent/settings', {
        method: 'PATCH',
        body: JSON.stringify({
          provider: aiProvider,
          model: aiModel,
        }),
      })

      // Also save to main settings
      await apiRequest('/api/v1/settings', {
        method: 'PATCH',
        body: JSON.stringify({
          ai: {
            provider: aiProvider,
            model: aiModel,
            temperature: settings?.ai.temperature ?? 0.7,
            maximum_tokens: settings?.ai.maximumTokens ?? 4096,
            require_approval: settings?.ai.requireApproval ?? true,
            automatic_backup: settings?.ai.automaticBackup ?? true,
            post_change_validation: settings?.ai.postChangeValidation ?? true,
            automatic_rollback: settings?.ai.automaticRollback ?? false,
            allow_destructive_commands: settings?.ai.allowDestructiveCommands ?? false,
          },
        }),
      })

      toast.success('AI settings saved successfully')
      mutate()
    } catch {
      toast.error('Failed to save AI settings')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveGeneral = async () => {
    setSaving(true)
    try {
      await apiRequest('/api/v1/settings', {
        method: 'PATCH',
        body: JSON.stringify({
          general: {
            workspace_name: settings?.general.workspaceName ?? 'AI Network Agent',
            timezone: settings?.general.timezone ?? 'UTC',
            default_view: settings?.general.defaultView ?? 'dashboard',
          },
        }),
      })
      toast.success('General settings saved')
      mutate()
    } catch {
      toast.error('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveSSH = async () => {
    setSaving(true)
    try {
      await apiRequest('/api/v1/settings', {
        method: 'PATCH',
        body: JSON.stringify({
          ssh: {
            timeout_seconds: settings?.ssh.timeoutSeconds ?? 30,
            command_timeout_seconds: settings?.ssh.commandTimeoutSeconds ?? 60,
            strict_host_key_checking: settings?.ssh.strictHostKeyChecking ?? false,
          },
        }),
      })
      toast.success('SSH settings saved')
      mutate()
    } catch {
      toast.error('Failed to save SSH settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Settings</h1>
        <p className="text-sm text-muted-foreground">General, AI, device, SSH, GNS3, Containerlab, security, and notification behavior.</p>
      </div>

      <Tabs defaultValue="ai" className="gap-0">
        <div className="overflow-x-auto rounded-xl border border-border bg-card px-2 shadow-sm [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <TabsList variant="line" className="h-12 min-w-max justify-start gap-2 bg-transparent p-0">
            <TabsTrigger className="h-12 flex-none px-3" value="general">General</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="ai">AI</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="devices">Devices</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="ssh">SSH</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="gns3">GNS3</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="containerlab">Containerlab</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="security">Security</TabsTrigger>
            <TabsTrigger className="h-12 flex-none px-3" value="notifications">Notifications</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="general" className="mt-5">
          <Card>
            <CardHeader><CardTitle>General</CardTitle></CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <Field label="Workspace Name"><Input defaultValue={settings?.general.workspaceName} /></Field>
              <Field label="Timezone"><Input defaultValue={settings?.general.timezone} /></Field>
              <Field label="Default View"><Input defaultValue={settings?.general.defaultView} /></Field>
            </CardContent>
            <div className="px-6 pb-6">
              <Button onClick={handleSaveGeneral} disabled={saving}>
                {saving ? 'Saving...' : 'Save General Settings'}
              </Button>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="mt-5">
          <Card>
            <CardHeader className="border-b"><CardTitle>AI Settings</CardTitle></CardHeader>
            <CardContent className="grid gap-5 py-5">
              <div className="grid gap-4 md:grid-cols-4">
                <Field label="AI Provider">
                  <Select value={aiProvider} onValueChange={(v) => setAiProvider(v ?? '9router')}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="9router">9Router (Free Go/Zen)</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                      <SelectItem value="ollama">Ollama (Local)</SelectItem>
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Model">
                  <Select value={aiModel} onValueChange={(v) => setAiModel(v ?? 'opencode-go')}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {aiProvider === '9router' && (
                        <>
                          <SelectItem value="opencode-cheap">opencode-cheap (Free)</SelectItem>
                          <SelectItem value="opencode-coder">opencode-coder</SelectItem>
                          <SelectItem value="opencode-reasoning">opencode-reasoning</SelectItem>
                        </>
                      )}
                      {aiProvider === 'openai' && (
                        <>
                          <SelectItem value="gpt-4">GPT-4</SelectItem>
                          <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                          <SelectItem value="gpt-5">GPT-5</SelectItem>
                        </>
                      )}
                      {aiProvider === 'anthropic' && (
                        <>
                          <SelectItem value="claude-sonnet-4-20250514">Claude Sonnet</SelectItem>
                          <SelectItem value="claude-opus-4-20250514">Claude Opus</SelectItem>
                        </>
                      )}
                      {aiProvider === 'ollama' && (
                        <>
                          <SelectItem value="llama3">Llama 3</SelectItem>
                          <SelectItem value="codellama">CodeLlama</SelectItem>
                        </>
                      )}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Temperature"><Input type="number" step="0.1" defaultValue={settings?.ai.temperature} /></Field>
                <Field label="Maximum Tokens"><Input type="number" defaultValue={settings?.ai.maximumTokens} /></Field>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <Toggle label="Require approval before config changes" checked={settings?.ai.requireApproval ?? true} />
                <Toggle label="Automatic backup before config" checked={settings?.ai.automaticBackup ?? true} />
                <Toggle label="Post-change validation" checked={settings?.ai.postChangeValidation ?? true} />
                <Toggle label="Automatic rollback on failure" checked={settings?.ai.automaticRollback ?? true} />
                <Toggle label="Allow destructive commands" checked={settings?.ai.allowDestructiveCommands ?? false} destructive />
              </div>

              <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200">
                {aiProvider === '9router' && aiModel.includes('free')
                  ? 'Using free model. For better responses, consider upgrading to opencode-coder or opencode-reasoning.'
                  : 'Destructive commands should stay disabled unless backend policy, approval, audit, and rollback enforcement are active.'}
              </div>
              <Button className="w-fit" onClick={handleSaveAI} disabled={saving}>
                {saving ? 'Saving...' : 'Save AI Settings'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ssh" className="mt-5">
          <Card>
            <CardHeader><CardTitle>SSH</CardTitle></CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <Field label="Connect Timeout"><Input type="number" defaultValue={settings?.ssh.timeoutSeconds} /></Field>
              <Field label="Command Timeout"><Input type="number" defaultValue={settings?.ssh.commandTimeoutSeconds} /></Field>
              <Toggle label="Strict host key checking" checked={settings?.ssh.strictHostKeyChecking ?? true} />
            </CardContent>
            <div className="px-6 pb-6">
              <Button onClick={handleSaveSSH} disabled={saving}>
                {saving ? 'Saving...' : 'Save SSH Settings'}
              </Button>
            </div>
          </Card>
        </TabsContent>

        {['devices', 'gns3', 'containerlab', 'security', 'notifications'].map((tab) => (
          <TabsContent key={tab} value={tab} className="mt-5">
            <Card>
              <CardHeader><CardTitle className="capitalize">{tab}</CardTitle></CardHeader>
              <CardContent className="py-8 text-sm text-muted-foreground">
                Settings schema is prepared for backend integration.
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
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

function Toggle({ label, checked, destructive = false }: { label: string; checked: boolean; destructive?: boolean }) {
  return (
    <div className={destructive ? 'flex items-center justify-between rounded-lg border border-red-500/20 bg-red-500/5 p-3' : 'flex items-center justify-between rounded-lg border border-border p-3'}>
      <Label>{label}</Label>
      <Switch defaultChecked={checked} />
    </div>
  )
}

export default SettingsPage
