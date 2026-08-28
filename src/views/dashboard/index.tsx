import { useDashboardSummary, useDevices } from 'src/api/network'
import { DeviceStatusTable } from 'src/components/network/device-status-table'
import { NetworkHealthChart } from 'src/components/network/network-health-chart'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import { SummaryCards } from 'src/components/network/summary-cards'

const DashboardPage = () => {
  const summary = useDashboardSummary()
  const devices = useDevices()

  if (summary.isLoading || devices.isLoading) {
    return <LoadingState rows={6} />
  }

  if (summary.error || devices.error) {
    return <ErrorState message="Failed to load Network Operations Overview." />
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Network Operations Overview</h1>
        <p className="text-sm text-muted-foreground">AI-powered visibility across devices, labs, configuration changes, and validation signals.</p>
      </div>

      {summary.data?.data && <SummaryCards summary={summary.data.data} />}
      <NetworkHealthChart />
      {devices.data?.data && <DeviceStatusTable devices={devices.data.data} compact />}
    </div>
  )
}

export default DashboardPage
