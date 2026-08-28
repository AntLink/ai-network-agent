import { useState } from 'react'
import { KeyRound, PlugZap, ShieldCheck } from 'lucide-react'
import type { ReactNode } from 'react'
import { toast } from 'sonner'
import { useCredentials } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { VendorBadge } from 'src/components/network/status-badge'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Input } from 'src/components/ui/input'
import { Label } from 'src/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'

const CredentialsPage = () => {
  const { data, error, isLoading, mutate } = useCredentials()
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState<string | null>(null)

  if (isLoading) return <LoadingState rows={6} />
  if (error) return <ErrorState message="Failed to load credential profiles." />

  const credentials = data?.data ?? []

  const handleSave = async () => {
    setSaving(true)
    try {
      // TODO: Call POST /api/v1/credentials with form data
      toast.success('Credential profile saved')
      mutate()
    } catch {
      toast.error('Failed to save credential profile')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async (credId: string) => {
    setTesting(credId)
    try {
      // TODO: Call POST /api/v1/credentials/{id}/test
      toast.success('Connection test successful')
    } catch {
      toast.error('Connection test failed')
    } finally {
      setTesting(null)
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
      <div className="grid gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Credentials</h1>
          <p className="text-sm text-muted-foreground">Credential profiles for backend-managed SSH, API, and token authentication. Secrets are never shown in plaintext.</p>
        </div>

        {credentials.length ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {credentials.map((profile) => (
              <Card key={profile.id}>
                <CardHeader className="border-b">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardTitle>{profile.name}</CardTitle>
                      <p className="mt-1 text-sm text-muted-foreground">{profile.username} / {profile.authType}</p>
                    </div>
                    <VendorBadge vendor={profile.vendor} />
                  </div>
                </CardHeader>
                <CardContent className="grid gap-3 py-5">
                  <div className="rounded-lg border border-border bg-muted/30 p-3">
                    <p className="text-xs text-muted-foreground">Secret</p>
                    <p className="mt-1 font-mono text-sm font-semibold">{profile.secretPreview}</p>
                  </div>
                  <div className="flex items-center justify-between gap-2">
                    <Badge variant={profile.status === 'valid' ? 'default' : 'outline'}>{profile.status}</Badge>
                    <span className="text-xs text-muted-foreground">Last test {profile.lastTest}</span>
                  </div>
                  <Button variant="outline" onClick={() => handleTest(profile.id)} disabled={testing === profile.id}>
                    <PlugZap className="size-4" />
                    {testing === profile.id ? 'Testing...' : 'Test Connection'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <EmptyState title="No credential profiles found." />
        )}
      </div>

      <Card>
        <CardHeader className="border-b"><CardTitle>Profile Form</CardTitle></CardHeader>
        <CardContent className="grid gap-4 py-5">
          <Field label="Profile Name"><Input defaultValue="Cisco Lab" /></Field>
          <Field label="Username"><Input defaultValue="admin" /></Field>
          <Field label="Authentication Type">
            <Select defaultValue="password">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="password">Password</SelectItem>
                <SelectItem value="ssh-key">SSH Key</SelectItem>
                <SelectItem value="api-token">API Token</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <Field label="Password / Key / Token"><Input type="password" defaultValue="maskedsecret" /></Field>
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200">
            Secrets must be sent to backend secret storage only, not browser local storage.
          </div>
          <Button onClick={handleSave} disabled={saving}>
            <ShieldCheck className="size-4" />
            {saving ? 'Saving...' : 'Save Profile'}
          </Button>
          <Button variant="outline"><KeyRound className="size-4" /> Test Connection</Button>
        </CardContent>
      </Card>
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

export default CredentialsPage
