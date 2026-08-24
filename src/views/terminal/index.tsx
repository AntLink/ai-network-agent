import { useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, Bot, Clipboard, Expand, PlugZap, RotateCw, Save, Trash2 } from 'lucide-react'
import {
  closeTerminalSession,
  createTerminalSession,
  executeTerminalSessionCommand,
  runTerminalCommand,
  suggestTerminalCommand,
  useDevices,
} from 'src/api/network'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from 'src/components/ui/alert-dialog'
import { Badge } from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { Input } from 'src/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Switch } from 'src/components/ui/switch'
import { cn } from 'src/lib/utils'
import type { TerminalLiveSession, TerminalSuggestion, Vendor } from 'src/types/network'

type RiskLevel = 'read-only' | 'low' | 'medium' | 'high' | 'critical'
type SuggestionItem = TerminalSuggestion & { source: 'device' }

const riskClass: Record<RiskLevel, string> = {
  'read-only': 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  low: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  medium: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  high: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
  critical: 'border-red-700/50 bg-red-700/20 text-red-800 dark:text-red-200',
}

const connectionClass: Record<'disconnected' | 'connecting' | 'connected' | 'error', string> = {
  connected: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  connecting: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  disconnected: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300',
  error: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
}

const TerminalPage = () => {
  const devices = useDevices()
  const [command, setCommand] = useState('')
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>()
  const [rawMode, setRawMode] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [localOutput, setLocalOutput] = useState<string[]>([])
  const [localHistory, setLocalHistory] = useState<string[]>([])
  const [commandStatus, setCommandStatus] = useState<'idle' | 'running' | 'error'>('idle')
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [commandError, setCommandError] = useState<string>()
  const [pendingCommand, setPendingCommand] = useState<string>()
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(0)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [liveSession, setLiveSession] = useState<TerminalLiveSession>()
  const [deviceSuggestions, setDeviceSuggestions] = useState<TerminalSuggestion[]>([])
  const [suggestionStatus, setSuggestionStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const suggestionRequestRef = useRef(0)
  const liveSessionRef = useRef<TerminalLiveSession | undefined>(undefined)
  const suggestionsViewportRef = useRef<HTMLDivElement | null>(null)
  const suggestionItemRefs = useRef<Array<HTMLButtonElement | null>>([])
  const terminalOutputRef = useRef<HTMLDivElement | null>(null)

  const selectedDevice = useMemo(() => {
    const deviceId = selectedDeviceId
    return devices.data?.data.find((device) => device.id === deviceId) ?? devices.data?.data[0]
  }, [devices.data?.data, selectedDeviceId])

  const output = localOutput
  const prompt = liveSession?.prompt || (selectedDevice ? makeLocalPrompt(selectedDevice.vendor, selectedDevice.hostname) : undefined)
  const risk = useMemo(() => classifyCommandRisk(command, selectedDevice?.vendor ?? 'other'), [command, selectedDevice?.vendor])
  const suggestionQuery = useMemo(() => parseSuggestionQuery(command), [command])
  const suggestions = useMemo<SuggestionItem[]>(() => {
    const filter = suggestionQuery?.filter.toLowerCase() ?? ''
    return deviceSuggestions
      .filter((item) => !filter || item.value.toLowerCase().startsWith(filter))
      .map((item) => ({ ...item, source: 'device' }))
  }, [deviceSuggestions, suggestionQuery?.filter])
  const shouldRequestSuggestions = Boolean(suggestionQuery)

  useEffect(() => {
    if (!selectedDeviceId && devices.data?.data[0]) {
      setSelectedDeviceId(devices.data.data[0].id)
    }
  }, [devices.data?.data, selectedDeviceId])

  useEffect(() => {
    setActiveSuggestionIndex(0)
  }, [command, selectedDevice?.vendor, deviceSuggestions])

  useEffect(() => {
    if (!showSuggestions) return
    const item = suggestionItemRefs.current[activeSuggestionIndex]
    const viewport = suggestionsViewportRef.current
    if (!item || !viewport) return
    item.scrollIntoView({ block: 'nearest' })
  }, [activeSuggestionIndex, showSuggestions, suggestions.length])

  useEffect(() => {
    const terminal = terminalOutputRef.current
    if (!terminal) return
    terminal.scrollTop = terminal.scrollHeight
  }, [output.length, commandStatus])

  useEffect(() => {
    liveSessionRef.current = liveSession
  }, [liveSession])

  useEffect(() => () => {
    const current = liveSessionRef.current
    if (current) void closeTerminalSession(current.sessionId)
  }, [])

  useEffect(() => {
    if (!shouldRequestSuggestions) {
      setDeviceSuggestions([])
      setSuggestionStatus('idle')
      setShowSuggestions(false)
      return
    }

    if (!liveSession) {
      setDeviceSuggestions([])
      setSuggestionStatus('error')
      setShowSuggestions(true)
      return
    }

    const requestId = suggestionRequestRef.current + 1
    suggestionRequestRef.current = requestId
    setSuggestionStatus('loading')

    const timeout = window.setTimeout(() => {
      suggestTerminalCommand(liveSession.sessionId, suggestionQuery?.request ?? command)
        .then((items) => {
          if (suggestionRequestRef.current !== requestId) return
          setDeviceSuggestions(items)
          setSuggestionStatus('idle')
        })
        .catch(() => {
          if (suggestionRequestRef.current !== requestId) return
          setDeviceSuggestions([])
          setSuggestionStatus('error')
        })
    }, 350)

    return () => window.clearTimeout(timeout)
  }, [command, liveSession, shouldRequestSuggestions, suggestionQuery?.request])

  const connectSession = async () => {
    if (!selectedDevice || connectionStatus === 'connecting') return
    setConnectionStatus('connecting')
    setCommandError(undefined)
    setDeviceSuggestions([])

    try {
      if (liveSession) await closeTerminalSession(liveSession.sessionId)
      const nextSession = await createTerminalSession(selectedDevice.id)
      setLiveSession(nextSession)
      setConnectionStatus('connected')
      setLocalOutput((current) => [
        ...current,
        `Connected to ${nextSession.hostname} (${nextSession.managementAddress}) via backend SSH session.`,
        nextSession.prompt || makeLocalPrompt(selectedDevice.vendor, selectedDevice.hostname),
      ])
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create terminal session'
      setCommandError(message)
      setConnectionStatus('error')
      setLocalOutput((current) => [...current, `ERROR: ${message}`])
    }
  }

  const disconnectSession = async () => {
    if (!liveSession) {
      setConnectionStatus('disconnected')
      return
    }
    const closing = liveSession
    setLiveSession(undefined)
    setConnectionStatus('disconnected')
    setDeviceSuggestions([])
    await closeTerminalSession(closing.sessionId).catch(() => undefined)
    setLocalOutput((current) => [...current, `Disconnected from ${closing.hostname}.`])
  }

  const reconnectSession = async () => {
    await disconnectSession()
    await connectSession()
  }

  const switchDevice = async (deviceId: string) => {
    if (liveSession) await disconnectSession()
    setSelectedDeviceId(deviceId)
    setCommandError(undefined)
    setDeviceSuggestions([])
  }

  const runCommand = async (commandOverride?: string, confirmed = false) => {
    const text = (commandOverride ?? command).trim()
    if (!text || !selectedDevice || commandStatus === 'running') return
    const commandRisk = classifyCommandRisk(text, selectedDevice.vendor)

    if (commandRisk.level === 'critical') {
      const message = `CRITICAL command blocked in terminal: ${commandRisk.reasons.join(', ')}`
      setCommandError(message)
      setCommandStatus('error')
      setLocalOutput((current) => [
        ...current,
        `${prompt ?? selectedDevice.hostname + '#'} ${text}`,
        `BLOCKED: ${message}`,
        'Use the configuration workflow with explicit plan, approval, backup, and rollback.',
        prompt ?? selectedDevice.hostname + '#',
      ])
      return
    }

    if (commandRisk.level !== 'read-only' && !confirmed) {
      setPendingCommand(text)
      return
    }

    setCommandStatus('running')
    setCommandError(undefined)

    try {
      const result = liveSession && liveSession.deviceId === selectedDevice.id
        ? await executeTerminalSessionCommand(liveSession, text)
        : await runTerminalCommand(selectedDevice, text)
      setLocalOutput((current) => [...current, ...result.output])
      if (commandRisk.level !== 'read-only') {
        setLocalOutput((current) => [
          ...current,
          `WARNING ACCEPTED: ${commandRisk.level.toUpperCase()} risk command executed after operator confirmation.`,
        ])
      }
      setLocalHistory((current) => [text, ...current.filter((item) => item !== text)].slice(0, 12))
      setCommand('')
      setShowSuggestions(false)
      setPendingCommand(undefined)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Command execution failed'
      setCommandError(message)
      setCommandStatus('error')
      setLocalOutput((current) => [
        ...current,
        `${prompt ?? selectedDevice.hostname + '#'} ${text}`,
        `ERROR: ${message}`,
        prompt ?? selectedDevice.hostname + '#',
      ])
      return
    }

    setCommandStatus('idle')
  }

  const applySuggestion = (suggestion?: SuggestionItem) => {
    if (!suggestion) return
    setCommand(completeSuggestion(command, suggestion))
    setShowSuggestions(false)
  }

  if (devices.isLoading) {
    return <LoadingState rows={6} />
  }

  if (devices.error) {
    return <ErrorState message="Failed to load terminal session." />
  }

  return (
    <div className={fullscreen ? 'fixed inset-0 z-50 overflow-auto bg-background p-4' : 'grid gap-4'}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Command Terminal</h1>
          <p className="text-sm text-muted-foreground">Command execution through backend-managed SSH sessions. Browser never opens SSH directly.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            className="border-sky-500/30 text-sky-700 hover:bg-sky-500/10 dark:text-sky-300"
            disabled={!selectedDevice || connectionStatus === 'connecting'}
            onClick={reconnectSession}
          >
            <RotateCw className="size-4" /> Reconnect
          </Button>
          <Button variant="destructive" onClick={() => setLocalOutput([])}><Trash2 className="size-4" /> Clear</Button>
          <Button
            variant="outline"
            className="border-indigo-500/30 text-indigo-700 hover:bg-indigo-500/10 dark:text-indigo-300"
          >
            <Clipboard className="size-4" /> Copy Output
          </Button>
          <Button
            variant="outline"
            className="border-emerald-500/30 text-emerald-700 hover:bg-emerald-500/10 dark:text-emerald-300"
          >
            <Save className="size-4" /> Save Output
          </Button>
          <Button className="bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-950 dark:hover:bg-zinc-200" onClick={() => setFullscreen((current) => !current)}>
            <Expand className="size-4" /> Fullscreen
          </Button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(20rem,0.6fr)]">
        <Card>
          <CardHeader className="border-b">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle>SSH Session</CardTitle>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline" className={cn('uppercase', connectionClass[commandStatus === 'error' ? 'error' : connectionStatus])}>
                  <PlugZap className="size-3" />
                  {commandStatus === 'running' ? 'running via session' : commandStatus === 'error' ? 'error' : connectionStatus}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 py-5">
            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(12rem,0.35fr)]">
              <Select value={selectedDevice?.id} onValueChange={(value) => {
                if (value) void switchDevice(value)
              }}>
                <SelectTrigger><SelectValue placeholder="Select device" /></SelectTrigger>
                <SelectContent>
                  {(devices.data?.data ?? []).map((device) => (
                    <SelectItem key={device.id} value={device.id}>
                      {device.hostname} - {device.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className={cn(
                'rounded-lg border px-3 py-2 text-sm font-medium',
                liveSession ? connectionClass.connected : connectionClass.disconnected,
              )}>
                SSH / {selectedDevice?.managementIp ?? '-'} / {liveSession ? 'interactive session' : 'not connected'}
              </div>
            </div>

            {commandError && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300">
                {commandError}
              </div>
            )}

            <div ref={terminalOutputRef} className="h-[32rem] overflow-y-auto overflow-x-auto rounded-lg border border-border bg-zinc-950 p-4 font-mono text-xs leading-6 text-zinc-100 scrollbar-thin scrollbar-track-zinc-900 scrollbar-thumb-zinc-700">
              {output.map((line, index) => (
                <div
                  key={`${line}-${index}`}
                  className={
                    line.startsWith('ERROR') || line.startsWith('BLOCKED')
                      ? 'text-red-300'
                      : line.endsWith('#') || line.endsWith('>')
                        ? 'text-emerald-300'
                        : undefined
                  }
                >
                  {rawMode ? line : line.replace(/\s+/g, ' ')}
                </div>
              ))}
              {commandStatus === 'running' && <div className="text-cyan-300">Executing command through FastAPI backend...</div>}
            </div>

            <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_auto_auto]">
              <div className="relative grid gap-2">
                <div className="flex items-stretch gap-2">
                  <Input
                    value={command}
                    onChange={(event) => {
                      const value = event.target.value
                      setCommand(value)
                      setShowSuggestions(Boolean(parseSuggestionQuery(value)))
                    }}
                    onBlur={() => {
                      window.setTimeout(() => setShowSuggestions(false), 120)
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Tab' && showSuggestions && suggestions.length) {
                        event.preventDefault()
                        applySuggestion(suggestions[activeSuggestionIndex] ?? suggestions[0])
                      }
                      if (event.key === 'ArrowDown' && showSuggestions && suggestions.length) {
                        event.preventDefault()
                        setActiveSuggestionIndex((current) => (current + 1) % suggestions.length)
                      }
                      if (event.key === 'ArrowUp' && showSuggestions && suggestions.length) {
                        event.preventDefault()
                        setActiveSuggestionIndex((current) => (current - 1 + suggestions.length) % suggestions.length)
                      }
                      if (event.key === 'Escape') {
                        setShowSuggestions(false)
                      }
                      if (event.key === 'Enter' && showSuggestions && suggestions.length) {
                        event.preventDefault()
                        applySuggestion(suggestions[activeSuggestionIndex] ?? suggestions[0])
                      } else if (event.key === 'Enter' && !parseSuggestionQuery(command)) {
                        runCommand()
                      }
                    }}
                    className="font-mono"
                    placeholder={selectedDevice?.vendor === 'mikrotik' ? 'Ketik perintah MikroTik...' : 'Ketik perintah...'}
                  />
                  <span
                    className={cn(
                      'flex h-8 w-28 shrink-0 items-center justify-center rounded-md border px-3 font-mono text-xs font-semibold uppercase leading-none',
                      riskClass[risk.level],
                    )}
                  >
                    {risk.level}
                  </span>
                </div>
                {showSuggestions && (suggestions.length > 0 || suggestionStatus !== 'idle') && (
                  <div className="absolute bottom-full left-0 right-0 z-20 mb-2 overflow-hidden rounded-lg border border-border bg-popover shadow-lg">
                    <div className="border-b bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
                      {suggestionStatus === 'loading'
                        ? 'Loading suggestions from device...'
                        : suggestionStatus === 'error'
                          ? liveSession ? 'Device suggestion failed.' : 'Connect SSH first to load suggestions from device.'
                          : 'Device command helper'}
                    </div>
                    <div ref={suggestionsViewportRef} className="max-h-60 overflow-auto p-1">
                      {suggestions.map((suggestion, index) => (
                        <button
                          key={`${suggestion.source}-${suggestion.value}`}
                          ref={(element) => {
                            suggestionItemRefs.current[index] = element
                          }}
                          className={cn(
                            'flex w-full items-center justify-between rounded-md px-3 py-2 text-left font-mono text-xs hover:bg-muted',
                            index === activeSuggestionIndex && 'bg-muted',
                          )}
                          onMouseDown={(event) => {
                            event.preventDefault()
                            applySuggestion(suggestion)
                          }}
                        >
                          <span>{suggestion.value}</span>
                          <span className="text-[10px] uppercase text-muted-foreground">
                            {suggestion.description || classifyCommandRisk(completeSuggestion(command, suggestion), selectedDevice?.vendor ?? 'other').level}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <Button variant="outline" disabled={commandStatus === 'running'} onClick={() => runCommand()}>
                {commandStatus === 'running' ? 'Running...' : 'Run Command'}
              </Button>
              <Button><Bot className="size-4" /> Explain with AI</Button>
            </div>
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-200">
              Live SSH session lewat backend. Ketik ? di akhir command untuk mengambil helper langsung dari device.
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 content-start">
          <Card>
            <CardHeader><CardTitle>Session Controls</CardTitle></CardHeader>
            <CardContent className="grid gap-4">
              <div className="flex items-center justify-between gap-3 rounded-lg border border-border p-3">
                <div>
                  <p className="text-sm font-medium">Raw mode</p>
                  <p className="text-xs text-muted-foreground">Preserve command spacing and terminal formatting.</p>
                </div>
                <Switch checked={rawMode} onCheckedChange={(value) => setRawMode(Boolean(value))} />
              </div>
              <div className="rounded-lg border border-border p-3">
                <p className="text-sm font-medium">Prompt</p>
                <p className="mt-1 font-mono text-sm text-muted-foreground">{prompt}</p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <Button
                  className="bg-emerald-600 text-white hover:bg-emerald-700"
                  disabled={!selectedDevice || connectionStatus === 'connecting' || connectionStatus === 'connected'}
                  onClick={connectSession}
                >
                  {connectionStatus === 'connecting' ? 'Connecting...' : 'Connect SSH'}
                </Button>
                <Button
                  variant="outline"
                  className="border-red-500/30 text-red-700 hover:bg-red-500/10 dark:text-red-300"
                  disabled={!liveSession}
                  onClick={disconnectSession}
                >
                  Disconnect
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Command Helper</CardTitle></CardHeader>
            <CardContent className="grid gap-3 text-sm">
              <div className="rounded-lg border border-border p-3">
                <p className="font-medium">Keyboard</p>
                <p className="mt-1 text-xs text-muted-foreground">Ketik ? untuk helper, Arrow Up/Down pilih suggestion, Enter pilih suggestion, Esc tutup helper.</p>
              </div>
              <div className="rounded-lg border border-border p-3">
                <p className="font-medium">Risk Guard</p>
                <p className="mt-1 text-xs text-muted-foreground">Read-only langsung jalan. Low/Medium/High minta confirmation. Critical diblokir dari terminal.</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Command History</CardTitle></CardHeader>
            <CardContent className="grid gap-2">
              {Array.from(new Set(localHistory)).map((item) => (
                <button key={item} className="rounded-lg border border-border px-3 py-2 text-left font-mono text-xs hover:bg-muted" onClick={() => {
                  setCommand(item)
                  setShowSuggestions(false)
                }}>
                  {item}
                </button>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      <AlertDialog open={Boolean(pendingCommand)} onOpenChange={(open) => {
        if (!open) setPendingCommand(undefined)
      }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-amber-500/10 text-amber-700 dark:text-amber-300">
              <AlertTriangle className="size-5" />
            </AlertDialogMedia>
            <AlertDialogTitle>Run risky command?</AlertDialogTitle>
            <AlertDialogDescription>
              Command ini tidak diklasifikasikan read-only. Pastikan ini memang lab/development dan siap menerima dampaknya.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="grid gap-3 rounded-lg border border-border bg-muted/30 p-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Device</span>
              <span className="font-medium">{selectedDevice?.hostname ?? '-'}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Risk</span>
              <Badge variant="outline" className={cn('uppercase', riskClass[classifyCommandRisk(pendingCommand ?? '', selectedDevice?.vendor ?? 'other').level])}>
                {classifyCommandRisk(pendingCommand ?? '', selectedDevice?.vendor ?? 'other').level}
              </Badge>
            </div>
            <pre className="overflow-auto rounded-md bg-zinc-950 p-3 font-mono text-xs text-zinc-100">{pendingCommand}</pre>
            <ul className="grid gap-1 text-xs text-muted-foreground">
              {classifyCommandRisk(pendingCommand ?? '', selectedDevice?.vendor ?? 'other').reasons.map((reason) => (
                <li key={reason}>- {reason}</li>
              ))}
            </ul>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => runCommand(pendingCommand, true)}>Run Anyway</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

function makeLocalPrompt(vendor: Vendor, hostname: string) {
  return vendor === 'mikrotik' ? `[admin@${hostname}] >` : `${hostname}#`
}

function parseSuggestionQuery(command: string) {
  const questionIndex = command.lastIndexOf('?')
  if (questionIndex < 0) return null

  return {
    request: command.slice(0, questionIndex + 1),
    filter: command.slice(questionIndex + 1).trim().toLowerCase(),
    base: command.slice(0, questionIndex),
  }
}

function completeSuggestion(command: string, suggestion: SuggestionItem) {
  const query = parseSuggestionQuery(command)
  const current = query ? query.base : command
  const trailingSpace = /\s$/.test(current)
  const parts = current.trimEnd().split(/\s+/)
  const base = trailingSpace ? current : parts.slice(0, -1).join(' ')
  const separator = base && !base.endsWith(' ') ? ' ' : ''

  const completed = `${base}${separator}${suggestion.value}`.trimStart()
  return completed
}

function classifyCommandRisk(command: string, vendor: Vendor): { level: RiskLevel; reasons: string[] } {
  const value = command.trim().toLowerCase()
  if (!value) return { level: 'read-only', reasons: ['No command entered.'] }

  const criticalPatterns = [
    /write erase/,
    /erase startup-config/,
    /erase nvram/,
    /delete\s+flash:/,
    /format\s+/,
    /\breload\b/,
    /factory-reset/,
    /system reset/,
    /\/system reset-configuration/,
    /\/system shutdown/,
    /\/system reboot/,
  ]
  if (criticalPatterns.some((pattern) => pattern.test(value))) {
    return { level: 'critical', reasons: ['May erase, reboot, reset, or destroy device state.'] }
  }

  const readOnlyPrefixes = vendor === 'mikrotik'
    ? ['/interface print', '/ip address print', '/ip route print', '/ip firewall filter print', '/ip firewall nat print', '/routing', '/system identity print', '/system resource print', '/log print', '/tool ping', '/tool traceroute']
    : ['show ', 'ping ', 'traceroute ', 'dir', 'terminal length']

  if (readOnlyPrefixes.some((prefix) => value.startsWith(prefix))) {
    return { level: 'read-only', reasons: ['Read-only inspection command.'] }
  }

  const highPatterns = [
    /configure terminal/,
    /^conf t$/,
    /^interface\s+/,
    /\bshutdown\b/,
    /\bno shutdown\b/,
    /\bip address\b/,
    /\bip route\b/,
    /\brouter ospf\b/,
    /\brouter bgp\b/,
    /\baccess-list\b/,
    /\bip access-group\b/,
    /\busername\b/,
    /\bsecret\b/,
    /\bpassword\b/,
    /\/ip address (add|remove|set)/,
    /\/interface (disable|enable|set)/,
    /\/ip firewall/,
    /\/routing/,
    /\/user/,
  ]
  if (highPatterns.some((pattern) => pattern.test(value))) {
    return { level: 'high', reasons: ['Command can change configuration, routing, interface state, users, or firewall policy.'] }
  }

  const mediumPatterns = [
    /copy running-config startup-config/,
    /write memory/,
    /^wr$/,
    /\bset\b/,
    /\badd\b/,
    /\bremove\b/,
    /\bdelete\b/,
    /\/.*\s(add|remove|set|enable|disable)\b/,
  ]
  if (mediumPatterns.some((pattern) => pattern.test(value))) {
    return { level: 'medium', reasons: ['Command may persist or alter operational state.'] }
  }

  return { level: 'low', reasons: ['Unknown command pattern. Review before running.'] }
}

export default TerminalPage
