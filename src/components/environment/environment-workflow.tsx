import { CheckCircle2, Circle, Loader2, LucideIcon } from 'lucide-react'
import { Badge } from 'src/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Separator } from 'src/components/ui/separator'
import type { EnvironmentPolicy, EnvironmentProfile, EnvironmentWorkflowStep } from 'src/types/environment'

const stepIcon: Record<EnvironmentWorkflowStep['status'], LucideIcon> = {
  pending: Circle,
  running: Loader2,
  success: CheckCircle2,
  failed: CheckCircle2,
}

interface EnvironmentWorkflowProps {
  profile: EnvironmentProfile
  steps: EnvironmentWorkflowStep[]
}

export function EnvironmentWorkflow({ profile, steps }: EnvironmentWorkflowProps) {
  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center justify-between gap-3">
          <span>{profile.name} workflow</span>
          <Badge variant="outline" className={profile.badge}>
            {profile.id.toUpperCase()}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 py-5">
        <div className="grid gap-3">
          {steps.map((step, index) => {
            const Icon = stepIcon[step.status]
            return (
              <div key={step.key} className="flex items-start gap-3">
                <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full border bg-muted/40">
                  <Icon className={step.status === 'running' ? 'size-4 animate-spin text-primary' : 'size-4 text-muted-foreground'} />
                </div>
                <div className="grid gap-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{index + 1}. {step.title}</p>
                    <Badge variant={step.status === 'success' ? 'default' : step.status === 'running' ? 'secondary' : 'outline'}>
                      {step.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                </div>
              </div>
            )
          })}
        </div>

        <Separator />

        <PolicySummary policy={profile.policy} />
      </CardContent>
    </Card>
  )
}

function PolicySummary({ policy }: { policy: EnvironmentPolicy }) {
  const rows = [
    ['Approval', policy.approvalRequired ? 'Required' : 'Optional'],
    ['Backup', policy.backupRequired ? 'Required' : 'Optional'],
    ['Rollback', policy.rollbackEnabled ? 'Enabled' : 'Disabled'],
    ['Destructive', policy.destructiveCommandsAllowed ? 'Allowed' : 'Blocked'],
    ['Validation', policy.postChangeValidation ? 'On' : 'Off'],
  ] as const

  return (
    <div className="grid gap-2 text-sm">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-center justify-between gap-3">
          <span className="text-muted-foreground">{label}</span>
          <span className="font-medium">{value}</span>
        </div>
      ))}
    </div>
  )
}

