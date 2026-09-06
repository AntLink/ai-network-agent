import { CheckCircle2, FlaskConical, ShieldCheck } from 'lucide-react'
import { Button } from 'src/components/ui/button'
import { Badge } from 'src/components/ui/badge'
import { cn } from 'src/lib/utils'
import type { EnvironmentProfile, EnvironmentType } from 'src/types/environment'

interface EnvironmentSwitcherProps {
  profiles: EnvironmentProfile[]
  value: EnvironmentType
  onChange: (environment: EnvironmentType) => void
}

const iconMap = {
  lab: FlaskConical,
  staging: ShieldCheck,
  production: CheckCircle2,
}

export function EnvironmentSwitcher({ profiles, value, onChange }: EnvironmentSwitcherProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {profiles.map((profile) => {
        const Icon = iconMap[profile.id]
        const active = profile.id === value
        return (
          <Button
            key={profile.id}
            type="button"
            variant={active ? 'default' : 'outline'}
            onClick={() => onChange(profile.id)}
            className={cn('gap-2', active ? 'shadow-sm' : '')}
          >
            <Icon className="size-4" />
            {profile.name}
            <Badge variant="outline" className={cn('ml-1 border-current/20', profile.badge)}>
              {profile.engine ? profile.engine.toUpperCase() : profile.id.toUpperCase()}
            </Badge>
          </Button>
        )
      })}
    </div>
  )
}
