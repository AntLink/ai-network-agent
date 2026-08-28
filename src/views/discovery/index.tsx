import { useState } from 'react'
import { Plus, Radar } from 'lucide-react'
import type { ReactNode } from 'react'
import { toast } from 'sonner'
import { useDiscoveryResults } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { VendorBadge } from 'src/components/network/status-badge'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Input } from 'src/components/ui/input'
import { Label } from 'src/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'

const DiscoveryPage = () => {
  const { data, error, isLoading, mutate } = useDiscoveryResults()
  const [scanning, setScanning] = useState(false)
  const [subnet, setSubnet] = useState('192.168.1.0/24')

  if (isLoading) return <LoadingState rows={6} />
  if (error) return <ErrorState message="Failed to load discovery results." />

  const results = data?.data ?? []

  const handleStartScan = async () => {
    if (!subnet.trim()) {
      toast.error('Please enter a subnet')
      return
    }
    setScanning(true)
    try {
      // TODO: Call POST /api/v1/discovery/scan with subnet
      toast.success(`Discovery scan started for ${subnet}`)
      mutate()
    } catch {
      toast.error('Failed to start discovery scan')
    } finally {
      setScanning(false)
    }
  }

  const handleAddDevice = async (_deviceId: string) => {
    try {
      // TODO: Call POST /api/v1/discovery/add with device_id
      toast.success('Device added to inventory')
      mutate()
    } catch {
      toast.error('Failed to add device')
    }
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Network Discovery</h1>
        <p className="text-sm text-muted-foreground">Discover devices by subnet using ICMP, SSH, SNMP, and credential profiles.</p>
      </div>

      <Card>
        <CardHeader className="border-b"><CardTitle>Discovery Job</CardTitle></CardHeader>
        <CardContent className="grid gap-4 py-5 md:grid-cols-4">
          <Field label="Subnet">
            <Input value={subnet} onChange={(e) => setSubnet(e.target.value)} placeholder="192.168.1.0/24" />
          </Field>
          <Field label="Method">
            <Select defaultValue="ssh">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="icmp">ICMP</SelectItem>
                <SelectItem value="ssh">SSH</SelectItem>
                <SelectItem value="snmp">SNMP</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <Field label="Credentials">
            <Select defaultValue="cred-cisco-lab">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="cred-cisco-lab">Cisco Lab</SelectItem>
                <SelectItem value="cred-mikrotik-lab">MikroTik Lab</SelectItem>
                <SelectItem value="cred-aruba-lab">Aruba Lab</SelectItem>
              </SelectContent>
            </Select>
          </Field>
          <div className="flex items-end">
            <Button className="w-full" onClick={handleStartScan} disabled={scanning}>
              <Radar className="size-4" />
              {scanning ? 'Scanning...' : 'Start Discovery'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="border-b"><CardTitle>Results</CardTitle></CardHeader>
        <CardContent className="py-5">
          {results.length ? (
            <div className="overflow-x-auto rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>IP</TableHead>
                    <TableHead>Hostname</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Platform</TableHead>
                    <TableHead>SSH</TableHead>
                    <TableHead>SNMP</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Add</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((result) => (
                    <TableRow key={result.id}>
                      <TableCell className="font-mono text-xs">{result.ip}</TableCell>
                      <TableCell className="font-medium">{result.hostname}</TableCell>
                      <TableCell><VendorBadge vendor={result.vendor} /></TableCell>
                      <TableCell>{result.platform}</TableCell>
                      <TableCell>{result.ssh}</TableCell>
                      <TableCell>{result.snmp}</TableCell>
                      <TableCell><Badge variant="outline">{result.status}</Badge></TableCell>
                      <TableCell className="text-right">
                        <Button size="sm" variant="outline" onClick={() => handleAddDevice(result.id)}>
                          <Plus className="size-4" /> Add
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <EmptyState title="No discovery results yet." />
          )}
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

export default DiscoveryPage
