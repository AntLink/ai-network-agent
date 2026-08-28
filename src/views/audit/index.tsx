import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, Loader2, Search, X } from 'lucide-react'
import { useAuditLogs } from 'src/api/network'
import { EmptyState, ErrorState, LoadingState } from 'src/components/network/page-state'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from 'src/components/ui/table'
import type { AuditLogQuery } from 'src/api/network/backend-client'

const PAGE_SIZES = [10, 25, 50, 100]

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

const AuditPage = () => {
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(25)
  const [searchInput, setSearchInput] = useState('')
  const [filterAction, setFilterAction] = useState<string>('')
  const [filterDevice, setFilterDevice] = useState<string>('')
  const [filterResult, setFilterResult] = useState<string>('')
  const [filterSource, setFilterSource] = useState<string>('')

  const debouncedSearch = useDebounce(searchInput, 400)

  const query: AuditLogQuery = {
    page,
    limit,
    search: debouncedSearch || undefined,
    action: filterAction || undefined,
    device: filterDevice || undefined,
    result: filterResult || undefined,
    source: filterSource || undefined,
  }

  const { data, error, isLoading, isValidating } = useAuditLogs(query)

  // Initial load — show full skeleton
  if (isLoading && !data) return <LoadingState rows={6} />
  if (error && !data) return <ErrorState message="Failed to load audit logs." />

  const result = data?.data
  const logs = result?.logs ?? []
  const total = result?.total ?? 0
  const pages = result?.pages ?? 1
  const filters = result?.filters
  const tableLoading = isValidating && !!data

  const hasFilters = debouncedSearch || filterAction || filterDevice || filterResult || filterSource

  const clearFilters = () => {
    setSearchInput('')
    setFilterAction('')
    setFilterDevice('')
    setFilterResult('')
    setFilterSource('')
    setPage(1)
  }

  const handleLimitChange = (value: string | null) => {
    if (value) { setLimit(Number(value)); setPage(1) }
  }

  return (
    <div className="grid gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Audit Logs</h1>
        <p className="text-sm text-muted-foreground">Every user, AI agent, automation, and API action in one immutable trail.</p>
      </div>
      <Card>
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <CardTitle>Activity / Audit Log</CardTitle>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              {tableLoading && <Loader2 className="size-3.5 animate-spin" />}
              <span>{total} events</span>
              <Select value={String(limit)} onValueChange={handleLimitChange}>
                <SelectTrigger className="h-8 w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAGE_SIZES.map((size) => (
                    <SelectItem key={size} value={String(size)}>{size} / page</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="py-5">
          {/* Filters */}
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-lg border border-input bg-transparent px-2.5 h-8 focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50">
              <Search className="size-3.5 shrink-0 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchInput}
                onChange={(e) => { setSearchInput(e.target.value); setPage(1) }}
                className="h-full min-w-0 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
            </div>

            {filters?.actions && filters.actions.length > 0 && (
              <Select value={filterAction} onValueChange={(v) => { setFilterAction(v ?? ''); setPage(1) }}>
                <SelectTrigger className="h-8 w-[130px]"><SelectValue placeholder="Action" /></SelectTrigger>
                <SelectContent>
                  {filters.actions.map((a) => <SelectItem key={a} value={a}>{a}</SelectItem>)}
                </SelectContent>
              </Select>
            )}

            {filters?.devices && filters.devices.length > 0 && (
              <Select value={filterDevice} onValueChange={(v) => { setFilterDevice(v ?? ''); setPage(1) }}>
                <SelectTrigger className="h-8 w-[180px]"><SelectValue placeholder="Device" /></SelectTrigger>
                <SelectContent>
                  {filters.devices.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                </SelectContent>
              </Select>
            )}

            {filters?.results && filters.results.length > 0 && (
              <Select value={filterResult} onValueChange={(v) => { setFilterResult(v ?? ''); setPage(1) }}>
                <SelectTrigger className="h-8 w-[120px]"><SelectValue placeholder="Result" /></SelectTrigger>
                <SelectContent>
                  {filters.results.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                </SelectContent>
              </Select>
            )}

            {filters?.sources && filters.sources.length > 0 && (
              <Select value={filterSource} onValueChange={(v) => { setFilterSource(v ?? ''); setPage(1) }}>
                <SelectTrigger className="h-8 w-[130px]"><SelectValue placeholder="Source" /></SelectTrigger>
                <SelectContent>
                  {filters.sources.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
            )}

            {hasFilters && (
              <Button variant="ghost" size="sm" className="h-8 px-2" onClick={clearFilters}>
                <X className="mr-1 size-3" /> Clear
              </Button>
            )}
          </div>

          {/* Table */}
          <div className="relative">
            {tableLoading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-card/60">
                <Loader2 className="size-5 animate-spin text-muted-foreground" />
              </div>
            )}
            {logs.length ? (
              <>
                <div className="overflow-x-auto rounded-lg border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Time</TableHead>
                        <TableHead>User</TableHead>
                        <TableHead>Action</TableHead>
                        <TableHead>Device</TableHead>
                        <TableHead>Result</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Details</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {logs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell className="whitespace-nowrap text-xs">{log.time}</TableCell>
                          <TableCell>{log.user}</TableCell>
                          <TableCell className="font-medium">{log.action}</TableCell>
                          <TableCell className="font-mono text-xs">{log.device}</TableCell>
                          <TableCell>
                            <Badge variant={log.result === 'success' ? 'default' : log.result === 'failed' ? 'destructive' : 'outline'}>
                              {log.result}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className="capitalize">{log.source}</Badge>
                          </TableCell>
                          <TableCell className="min-w-80 text-muted-foreground">{log.details}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {/* Pagination */}
                <div className="mt-4 flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Page {page} of {pages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
                      <ChevronLeft className="size-4" /> Prev
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(pages, p + 1))} disabled={page >= pages}>
                      Next <ChevronRight className="size-4" />
                    </Button>
                  </div>
                </div>
              </>
            ) : (
              <EmptyState title="No audit logs found." />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AuditPage
