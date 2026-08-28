import type { Device } from 'src/types/network'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'

export function DeviceSelector({
  devices,
  value,
  onValueChange,
}: {
  devices: Device[]
  value: string
  onValueChange: (value: string) => void
}) {
  const safeValue = value && ['all-devices', ...devices.map((device) => device.id)].includes(value) ? value : 'all-devices'

  return (
    <Select value={safeValue} onValueChange={(next) => onValueChange(next ?? 'all-devices')}>
      <SelectTrigger className="w-52">
        <SelectValue placeholder="Select device" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all-devices">All devices</SelectItem>
        {devices.map((device) => (
          <SelectItem key={device.id} value={device.id}>
            {device.hostname} - {device.model}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
