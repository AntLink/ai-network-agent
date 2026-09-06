import { Bell, CheckCircle2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useAlerts } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import { cn } from 'src/lib/utils'
import type { Alert } from 'src/types/network'

const severityClass: Record<Alert['severity'], string> = {
  critical: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
  high: 'border-orange-500/30 bg-orange-500/10 text-orange-700 dark:text-orange-300',
  medium: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  low: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  info: 'border-muted-foreground/30 bg-muted text-muted-foreground',
}

const AlertsPage = () => {
  const { data, error, isLoading, mutate } = useAlerts()
  const [acknowledging, setAcknowledging] = useState<string | null>(null)

  if (isLoading) return <LoadingState rows={6} />
  if (error) return <ErrorState message="Failed to load alerts." />

  const alerts = data?.data ?? []

  const handleAcknowledge = async (alertId: string) => {
    setAcknowledging(alertId)
    try {
      // TODO: Call PATCH /api/v1/alerts/{id} with status: acknowledged
      toast.success('Alert acknowledged')
      mutate()
    } catch {
      toast.error('Failed to acknowledge alert')
    } finally {
      setAcknowledging(null)
    }
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Alerts</h1>
        <p className="text-sm text-muted-foreground">Device, interface, resource, SSH, configuration, and routing health alerts.</p>
      </div>
      <Card>
        <CardHeader className="border-b"><CardTitle>Active Alerts</CardTitle></CardHeader>
        <CardContent className="py-5">
          {alerts.length ? (
            <div className="overflow-x-auto rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Device</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="font-medium"><span className="flex items-center gap-2"><Bell className="size-4" />{alert.type}</span></TableCell>
                      <TableCell><Badge variant="outline" className={cn('capitalize', severityClass[alert.severity])}>{alert.severity}</Badge></TableCell>
                      <TableCell>{alert.device}</TableCell>
                      <TableCell className="min-w-80">{alert.message}</TableCell>
                      <TableCell>{alert.createdAt}</TableCell>
                      <TableCell>{alert.status}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAcknowledge(alert.id)}
                          disabled={acknowledging === alert.id || alert.status === 'acknowledged'}
                        >
                          <CheckCircle2 className="size-4" />
                          {acknowledging === alert.id ? 'Processing...' : 'Acknowledge'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <EmptyState title="No alerts found." />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default AlertsPage
