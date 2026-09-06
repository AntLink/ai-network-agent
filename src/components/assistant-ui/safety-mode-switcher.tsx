import { ShieldCheck } from 'lucide-react'
import { Badge } from 'src/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'

export function SafetyModeSwitcher({
  value,
  onValueChange,
}: {
  value: string
  onValueChange: (value: string) => void
}) {
  const safeValue = ['guarded', 'read-only', 'lab-only'].includes(value) ? value : 'guarded'

  return (
    <div className="flex items-center gap-2">
      <Select value={safeValue} onValueChange={(next) => onValueChange(next ?? 'guarded')}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Mode" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="guarded">Guarded</SelectItem>
          <SelectItem value="read-only">Read only</SelectItem>
          <SelectItem value="lab-only">Lab only</SelectItem>
        </SelectContent>
      </Select>
      <Badge variant="secondary" className="h-8 px-3">
        <ShieldCheck className="size-3" />
        No direct SSH
      </Badge>
    </div>
  )
}
