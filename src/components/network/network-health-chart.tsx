import { useState } from 'react'
import { Area, AreaChart, CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts'
import { useNetworkHealth } from 'src/api/network'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from 'src/components/ui/chart'
import { ErrorState, LoadingState } from 'src/components/network/page-state'

const ranges = ['1H', '6H', '24H', '7D', '30D']

export function NetworkHealthChart() {
  const [range, setRange] = useState('24H')
  const { data, error, isLoading } = useNetworkHealth(range)

  return (
    <Card>
      <CardHeader className="gap-3 border-b">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Network Health</CardTitle>
            <p className="text-sm text-muted-foreground">Devices online/offline, latency, packet loss, and config failures.</p>
          </div>
          <div className="flex flex-wrap gap-1 rounded-lg bg-muted p-1">
            {ranges.map((item) => (
              <Button
                key={item}
                size="sm"
                variant={item === range ? 'default' : 'ghost'}
                className="h-7"
                onClick={() => setRange(item)}
              >
                {item}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="py-5">
        {isLoading && <LoadingState rows={3} />}
        {error && <ErrorState message="Failed to load health telemetry." />}
        {data?.data && (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
            <ChartContainer
              config={{
                online: { label: 'Online', color: 'var(--chart-2)' },
                offline: { label: 'Offline', color: 'var(--destructive)' },
              }}
              className="h-72"
            >
              <AreaChart data={data.data}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="time" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area dataKey="online" type="monotone" fill="var(--color-online)" fillOpacity={0.22} stroke="var(--color-online)" />
                <Area dataKey="offline" type="monotone" fill="var(--color-offline)" fillOpacity={0.12} stroke="var(--color-offline)" />
              </AreaChart>
            </ChartContainer>

            <ChartContainer
              config={{
                latency: { label: 'Latency', color: 'var(--chart-1)' },
                packetLoss: { label: 'Packet loss', color: 'var(--chart-4)' },
                configFailures: { label: 'Config failures', color: 'var(--chart-5)' },
              }}
              className="h-72"
            >
              <LineChart data={data.data}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="time" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line dataKey="latency" type="monotone" stroke="var(--color-latency)" strokeWidth={2} dot={false} />
                <Line dataKey="packetLoss" type="monotone" stroke="var(--color-packetLoss)" strokeWidth={2} dot={false} />
                <Line dataKey="configFailures" type="monotone" stroke="var(--color-configFailures)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
