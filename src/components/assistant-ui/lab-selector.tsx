import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import type { Lab } from 'src/types/network'

export function LabSelector({
  labs,
  value,
  onValueChange,
}: {
  labs: Lab[]
  value: string
  onValueChange: (value: string) => void
}) {
  const safeValue = value && ['all-labs', ...labs.map((lab) => lab.id)].includes(value) ? value : 'all-labs'

  return (
    <Select value={safeValue} onValueChange={(next) => onValueChange(next ?? 'all-labs')}>
      <SelectTrigger className="w-52">
        <SelectValue placeholder="Select lab" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all-labs">All labs</SelectItem>
        {labs.map((lab) => (
          <SelectItem key={lab.id} value={lab.id}>
            {lab.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
