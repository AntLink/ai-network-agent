import { useEffect, useLayoutEffect, useMemo, useRef, useState, type ChangeEvent, type ClipboardEvent, type KeyboardEvent as ReactKeyboardEvent } from 'react'
import { Bot, Clipboard, Expand, PlugZap, RotateCw, Save, Trash2, Wifi } from 'lucide-react'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import {
  closeTerminalSession,
  createTerminalSession,
  executeTerminalSessionCommand,
  getApiBaseUrl,
  runTerminalCommand,
  suggestTerminalCommand,
  useDevices,
} from 'src/api/network'
import { ApiClientError } from 'src/api/network/backend-client'
import { ErrorState, LoadingState } from 'src/components/network/page-state'
import {
  Badge,
} from 'src/components/ui/badge'
import { Button } from 'src/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from 'src/components/ui/card'
import { ScrollArea } from 'src/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from 'src/components/ui/select'
import { Switch } from 'src/components/ui/switch'
import { cn } from 'src/lib/utils'
import type { TerminalLiveSession, TerminalSuggestion, Vendor } from 'src/types/network'

type SuggestionItem = TerminalSuggestion & { source: 'device' }
type PersistedTerminalState = {
  command: string
  selectedDeviceId?: string
  rawMode: boolean
  localOutput: string[]
  localHistory: string[]
}
type TerminalProfile = {
  label: string
  badgeClass: string
  promptColor: string
  accentColor: string
  introLines: (device?: { hostname: string; platform: string; model: string; managementIp: string }, session?: TerminalLiveSession) => string[]
  helperNote: string
}

const TERMINAL_STATE_STORAGE_KEY = 'ai-network-agent-terminal-state'

const connectionClass: Record<'disconnected' | 'connecting' | 'connected' | 'error', string> = {
  connected: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  connecting: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  disconnected: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300',
  error: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300',
}

const terminalProfiles: Record<Vendor, TerminalProfile> = {
  cisco: {
    label: 'Cisco IOS / IOSv',
    badgeClass: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300',
    promptColor: '\x1b[38;5;75m',
    accentColor: '\x1b[38;5;39m',
    introLines: (device, session) => {
      const hostname = device?.hostname ?? session?.hostname ?? 'device'
      const platform = device?.platform || 'Cisco IOS'
      return [
        `${platform} console ready`,
        `${hostname} | SSH backend session active`,
        `Use "?" for context help and "show ?" for command-tree discovery.`,
      ]
    },
    helperNote: 'Cisco-native helpers appear after typing `?`, `show ?`, or `show running-config ?`.',
  },
  mikrotik: {
    label: 'MikroTik RouterOS',
    badgeClass: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
    promptColor: '\x1b[38;5;82m',
    accentColor: '\x1b[38;5;46m',
    introLines: (device, session) => {
      const hostname = device?.hostname ?? session?.hostname ?? 'device'
      const platform = device?.platform || 'RouterOS'
      return [
        `${platform} console ready`,
        `[admin@${hostname}] > interactive backend session`,
        `Use "?" or "ip ?" to expose RouterOS command hierarchy.`,
      ]
    },
    helperNote: 'MikroTik helpers follow the native RouterOS pattern: `?`, `ip ?`, `interface ?`.',
  },
  aruba: {
    label: 'Aruba AOS-CX',
    badgeClass: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
    promptColor: '\x1b[38;5;214m',
    accentColor: '\x1b[38;5;208m',
    introLines: (device, session) => {
      const hostname = device?.hostname ?? session?.hostname ?? 'device'
      const platform = device?.platform || 'AOS-CX'
      return [
        `${platform} console ready`,
        `${hostname} | structured CLI session active`,
        `Use "?" after a keyword to load Aruba context help.`,
      ]
    },
    helperNote: 'Aruba helpers are loaded from the device when you type `?` at the end of a command.',
  },
  linux: {
    label: 'Linux Shell',
    badgeClass: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300',
    promptColor: '\x1b[38;5;250m',
    accentColor: '\x1b[38;5;246m',
    introLines: (device, session) => {
      const hostname = device?.hostname ?? session?.hostname ?? 'device'
      const platform = device?.platform || 'Linux'
      return [
        `${platform} shell ready`,
        `${hostname} | backend-managed interactive session`,
        `Use tab completion or shell-native help when available.`,
      ]
    },
    helperNote: 'Linux behaves like a normal shell session with backend-managed command execution.',
  },
  other: {
    label: 'Generic CLI',
    badgeClass: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300',
    promptColor: '\x1b[38;5;246m',
    accentColor: '\x1b[38;5;244m',
    introLines: (device, session) => {
      const hostname = device?.hostname ?? session?.hostname ?? 'device'
      const platform = device?.platform || 'CLI'
      return [
        `${platform} console ready`,
        `${hostname} | backend-managed session active`,
        `Use "?" to query device-native helpers when supported.`,
      ]
    },
    helperNote: 'Generic devices still pull command helpers from the backend session.',
  },
}

const TerminalPage = () => {
  const devices = useDevices()
  const [command, setCommand] = useState(() => loadPersistedTerminalState().command)
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | undefined>(() => loadPersistedTerminalState().selectedDeviceId)
  const [rawMode, setRawMode] = useState(() => loadPersistedTerminalState().rawMode)
  const [fullscreen, setFullscreen] = useState(false)
  const [localOutput, setLocalOutput] = useState<string[]>(() => loadPersistedTerminalState().localOutput)
  const [localHistory, setLocalHistory] = useState<string[]>(() => loadPersistedTerminalState().localHistory)
  const [commandStatus, setCommandStatus] = useState<'idle' | 'running' | 'error'>('idle')
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [commandError, setCommandError] = useState<string>()
  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(0)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [liveSession, setLiveSession] = useState<TerminalLiveSession>()
  const [deviceSuggestions, setDeviceSuggestions] = useState<TerminalSuggestion[]>([])
  const [suggestionStatus, setSuggestionStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const [wsConnected, setWsConnected] = useState(false)
  const suggestionRequestRef = useRef(0)
  const liveSessionRef = useRef<TerminalLiveSession | undefined>(undefined)
  const wsRef = useRef<WebSocket | null>(null)
  const suggestionsViewportRef = useRef<HTMLDivElement | null>(null)
  const suggestionItemRefs = useRef<Array<HTMLButtonElement | null>>([])
  const terminalHostRef = useRef<HTMLDivElement | null>(null)
  const terminalRef = useRef<XTerm | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)
  const commandRef = useRef('')
  const promptRef = useRef<string | undefined>(undefined)
  const showSuggestionsRef = useRef(false)
  const suggestionsRef = useRef<SuggestionItem[]>([])
  const activeSuggestionIndexRef = useRef(0)
  const suggestionStatusRef = useRef<'idle' | 'loading' | 'error'>('idle')
  const historyBrowseIndexRef = useRef<number | null>(null)

  const selectedDevice = useMemo(() => {
    const deviceId = selectedDeviceId
    return devices.data?.data.find((device) => device.id === deviceId) ?? devices.data?.data[0]
  }, [devices.data?.data, selectedDeviceId])
  const terminalProfile = useMemo(
    () => terminalProfiles[selectedDevice?.vendor ?? 'other'],
    [selectedDevice?.vendor],
  )

  const output = localOutput
  const prompt = liveSession?.prompt || (selectedDevice ? makeLocalPrompt(selectedDevice.vendor, selectedDevice.hostname) : undefined)
  const suggestionQuery = useMemo(() => parseSuggestionQuery(command), [command])
  const suggestions = useMemo<SuggestionItem[]>(() => {
    const filter = suggestionQuery?.filter.toLowerCase() ?? ''
    return deviceSuggestions
      .filter((item) => !filter || item.value.toLowerCase().startsWith(filter))
      .map((item) => ({ ...item, source: 'device' }))
  }, [deviceSuggestions, suggestionQuery?.filter])
  const shouldRequestSuggestions = Boolean(suggestionQuery)

  useEffect(() => {
    commandRef.current = command
  }, [command])

  useEffect(() => {
    promptRef.current = prompt
  }, [prompt])

  useEffect(() => {
    showSuggestionsRef.current = showSuggestions
  }, [showSuggestions])

  useEffect(() => {
    suggestionsRef.current = suggestions
  }, [suggestions])

  useEffect(() => {
    activeSuggestionIndexRef.current = activeSuggestionIndex
  }, [activeSuggestionIndex])

  useEffect(() => {
    suggestionStatusRef.current = suggestionStatus
  }, [suggestionStatus])

  useEffect(() => {
    persistTerminalState({
      command,
      selectedDeviceId,
      rawMode,
      localOutput,
      localHistory,
    })
  }, [command, selectedDeviceId, rawMode, localOutput, localHistory, liveSession])

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

  useLayoutEffect(() => {
    const terminal = terminalRef.current
    if (!terminal) return

    renderTerminalFrame(terminal)
  }, [output, prompt, rawMode, command, connectionStatus])

  useEffect(() => {
    const host = terminalHostRef.current
    if (!host || terminalRef.current) return

    const terminal = new XTerm({
      cursorBlink: true,
      convertEol: true,
      scrollback: 5000,
      fontFamily: 'JetBrains Mono, Menlo, Consolas, monospace',
      fontSize: 12,
      lineHeight: 1.25,
      theme: {
        background: '#09090b',
        foreground: '#e4e4e7',
        cursor: '#22c55e',
        selectionBackground: '#3f3f46',
        black: '#09090b',
        red: '#ef4444',
        green: '#22c55e',
        yellow: '#f59e0b',
        blue: '#3b82f6',
        magenta: '#a855f7',
        cyan: '#06b6d4',
        white: '#e4e4e7',
        brightBlack: '#52525b',
        brightRed: '#f87171',
        brightGreen: '#4ade80',
        brightYellow: '#fbbf24',
        brightBlue: '#60a5fa',
        brightMagenta: '#c084fc',
        brightCyan: '#22d3ee',
        brightWhite: '#fafafa',
      },
    })
    const fitAddon = new FitAddon()
    terminal.loadAddon(fitAddon)
    terminal.open(host)
    fitAddon.fit()

    terminal.writeln('\x1b[38;5;244mTerminal initialized. Connect to a device to begin.\x1b[0m')
    writePromptLine(terminal)

    terminalRef.current = terminal
    fitAddonRef.current = fitAddon

    const handleResize = () => fitAddon.fit()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      terminal.dispose()
      terminalRef.current = null
      fitAddonRef.current = null
    }
  }, [])

  useEffect(() => {
    liveSessionRef.current = liveSession
  }, [liveSession])

  useEffect(() => () => {
    disconnectWebSocket()
    const current = liveSessionRef.current
    if (current) void closeTerminalSession(current.sessionId)
  }, [])

  useEffect(() => {
    if (!terminalRef.current) return
    writePromptLine()
  }, [prompt])

  useEffect(() => {
    if (connectionStatus !== 'connected') return
    const timeout = window.setTimeout(() => {
      inputRef.current?.focus()
    }, 0)
    return () => window.clearTimeout(timeout)
  }, [connectionStatus])

  useEffect(() => {
    if (!liveSession || connectionStatus !== 'connected' || wsRef.current) return
    const timeout = window.setTimeout(() => {
      connectWebSocket()
    }, 150)
    return () => window.clearTimeout(timeout)
  }, [liveSession, connectionStatus])

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
      if (liveSession) await closeTerminalSession(liveSession.sessionId).catch(() => undefined)
      disconnectWebSocket()
      const nextSession = await createTerminalSession(selectedDevice.id)
      const nextPrompt = nextSession.prompt || makeLocalPrompt(selectedDevice.vendor, selectedDevice.hostname)
      setLiveSession(nextSession)
      setConnectionStatus('connected')
      setLocalOutput((current) => [
        ...current,
        ...buildTerminalIntroLines(selectedDevice, nextSession),
      ])
      promptRef.current = nextPrompt
      commandRef.current = ''
      setCommand('')
      window.setTimeout(() => {
        terminalHostRef.current?.focus()
        inputRef.current?.focus()
      }, 0)
      setTimeout(connectWebSocket, 100)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create terminal session'
      setCommandError(message)
      setConnectionStatus('error')
      setLocalOutput((current) => [...current, `ERROR: ${message}`])
    }
  }

  const disconnectSession = async () => {
    disconnectWebSocket()
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

  const connectWebSocket = () => {
    if (!liveSession || wsRef.current) return

    const wsUrl = getApiBaseUrl().replace('http', 'ws')
    const ws = new WebSocket(`${wsUrl}/api/v1/terminal/sessions/${liveSession.sessionId}/stream`)

    ws.onopen = () => {
      setWsConnected(true)
      setLocalOutput((current) => [...current, 'WebSocket stream connected.'])
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'command_output' && data.data?.output) {
          const lines = Array.isArray(data.data.output) ? data.data.output : [String(data.data.output)]
          setLocalOutput((current) => [...current, ...lines])
        } else if (data.type === 'error') {
          setCommandError(data.message)
          setLocalOutput((current) => [...current, `WS ERROR: ${data.message}`])
        } else if (data.type === 'connected') {
          setLocalOutput((current) => [...current, `Stream session ${data.session_id} ready.`])
        }
      } catch {
        setLocalOutput((current) => [...current, event.data])
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
      wsRef.current = null
    }

    ws.onerror = () => {
      setWsConnected(false)
      wsRef.current = null
    }

    wsRef.current = ws
  }

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      setWsConnected(false)
    }
  }

  const switchDevice = async (deviceId: string) => {
    if (liveSession) await disconnectSession()
    setSelectedDeviceId(deviceId)
    setCommandError(undefined)
    setDeviceSuggestions([])
  }

  const runCommand = async (commandOverride?: string) => {
    const text = (commandOverride ?? command).trim()
    if (!text || !selectedDevice || commandStatus === 'running') return

    setCommandStatus('running')
    setCommandError(undefined)

    try {
      const result = liveSession && liveSession.deviceId === selectedDevice.id
        ? await executeTerminalSessionCommand(liveSession, text)
        : await runTerminalCommand(selectedDevice, text)
      setLocalOutput((current) => [...current, ...result.output])
      setLocalHistory((current) => [text, ...current.filter((item) => item !== text)].slice(0, 12))
      setCommand('')
      setShowSuggestions(false)
    } catch (error) {
      const isMissingSession = error instanceof ApiClientError
        && (error.status === 404 || /not found/i.test(error.message))
      const message = error instanceof Error ? error.message : 'Command execution failed'

      setCommandError(message)
      setCommandStatus('error')
      setLocalOutput((current) => [
        ...current,
        `${prompt ?? selectedDevice.hostname + '#'} ${text}`,
        `ERROR: ${message}`,
        prompt ?? selectedDevice.hostname + '#',
      ])
      if (isMissingSession) {
        disconnectWebSocket()
        setLiveSession(undefined)
        setConnectionStatus('disconnected')
        setLocalOutput((current) => [
          ...current,
          'Terminal session expired. Reconnect to start a new SSH session.',
        ])
      }
      return
    }

    setCommandStatus('idle')
  }

  const applySuggestion = (suggestion?: SuggestionItem) => {
    if (!suggestion) return
    const nextCommand = completeSuggestion(commandRef.current, suggestion)
    commandRef.current = nextCommand
    setCommand(nextCommand)
    setShowSuggestions(false)
    historyBrowseIndexRef.current = null
    renderTerminalFrame()
  }

  function writePromptLine(targetTerminal = terminalRef.current) {
    const terminal = targetTerminal
    if (!terminal) return

    const currentPrompt = promptRef.current || ''
    terminal.write(`\r\x1b[2K${terminalProfile.promptColor}\x1b[1m${currentPrompt}\x1b[0m${commandRef.current}`)
    fitAddonRef.current?.fit()
  }

  function resetTerminalOutput() {
    const terminal = terminalRef.current
    if (!terminal) return

    terminal.clear()
    terminal.writeln(`${terminalProfile.accentColor}Terminal initialized for ${terminalProfile.label}.\x1b[0m`)
    terminal.writeln('\x1b[38;5;244mConnect to a device to begin.\x1b[0m')
    commandRef.current = ''
    setCommand('')
    setShowSuggestions(false)
    historyBrowseIndexRef.current = null
    writePromptLine(terminal)
  }

  function selectHistoryCommand(direction: 'up' | 'down') {
    if (localHistory.length === 0) return

    const currentIndex = historyBrowseIndexRef.current
    const nextIndex =
      currentIndex === null
        ? 0
        : direction === 'up'
          ? Math.min(currentIndex + 1, localHistory.length - 1)
          : Math.max(currentIndex - 1, 0)
    historyBrowseIndexRef.current = nextIndex
    syncTerminalInput(localHistory[nextIndex] ?? '')
    setShowSuggestions(false)
  }

  function syncTerminalInput(nextCommand: string) {
    commandRef.current = nextCommand
    setCommand(nextCommand)
    setShowSuggestions(Boolean(parseSuggestionQuery(nextCommand)))
    historyBrowseIndexRef.current = null
    renderTerminalFrame()
  }

  function renderTerminalFrame(targetTerminal = terminalRef.current) {
    const terminal = targetTerminal
    if (!terminal) return

    terminal.clear()

    if (localOutput.length === 0) {
      terminal.writeln(`${terminalProfile.accentColor}Terminal initialized for ${terminalProfile.label}.\x1b[0m`)
      terminal.writeln('\x1b[38;5;244mConnect to a device to begin.\x1b[0m')
    } else {
      localOutput.forEach((line) => {
        terminal.writeln(formatTerminalLine(line, rawMode))
      })
    }

    terminal.write(`\r\x1b[2K${promptRef.current || ''}${commandRef.current}`)
    fitAddonRef.current?.fit()
  }

  function handleTerminalInput(data: string) {
    if (data === '\u0003') {
      commandRef.current = ''
      setCommand('')
      setShowSuggestions(false)
      historyBrowseIndexRef.current = null
      const terminal = terminalRef.current
      if (terminal) {
        terminal.write('^C\r\n')
      }
      renderTerminalFrame()
      return
    }

    if (data === '\r') {
      const text = commandRef.current.trim()
      const hasSuggestions = showSuggestionsRef.current && suggestionsRef.current.length > 0
      const query = parseSuggestionQuery(commandRef.current)
      historyBrowseIndexRef.current = null

      if (hasSuggestions && query) {
        applySuggestion(suggestionsRef.current[activeSuggestionIndexRef.current] ?? suggestionsRef.current[0])
        return
      }

      const terminal = terminalRef.current
      if (terminal) {
        terminal.write('\r\n')
      }
      if (!text) {
        commandRef.current = ''
        setCommand('')
        setShowSuggestions(false)
        renderTerminalFrame()
        return
      }

      void runCommand(text)
      return
    }

    if (data === '\u007F') {
      const nextCommand = commandRef.current.slice(0, -1)
      commandRef.current = nextCommand
      setCommand(nextCommand)
      setShowSuggestions(Boolean(parseSuggestionQuery(nextCommand)))
      historyBrowseIndexRef.current = null
      renderTerminalFrame()
      return
    }

    if (data === '\t') {
      if (showSuggestionsRef.current && suggestionsRef.current.length > 0) {
        applySuggestion(suggestionsRef.current[activeSuggestionIndexRef.current] ?? suggestionsRef.current[0])
      }
      return
    }

    if (data === '\u001b[A') {
      if (showSuggestionsRef.current && suggestionsRef.current.length > 0) {
        setActiveSuggestionIndex((current) => (current - 1 + suggestionsRef.current.length) % suggestionsRef.current.length)
        return
      }
      selectHistoryCommand('up')
      return
    }

    if (data === '\u001b[B') {
      if (showSuggestionsRef.current && suggestionsRef.current.length > 0) {
        setActiveSuggestionIndex((current) => (current + 1) % suggestionsRef.current.length)
        return
      }
      selectHistoryCommand('down')
      return
    }

    if (data === '\u001b[C' || data === '\u001b[D' || data.startsWith('\u001b[')) {
      return
    }

    commandRef.current += data
    setCommand(commandRef.current)
    setShowSuggestions(Boolean(parseSuggestionQuery(commandRef.current)))
    historyBrowseIndexRef.current = null
    renderTerminalFrame()
  }

  function handleInputChange(event: ChangeEvent<HTMLTextAreaElement>) {
    const nextValue = event.target.value
    if (nextValue === commandRef.current) return
    syncTerminalInput(nextValue)
  }

  function handleInputKeyDown(event: ReactKeyboardEvent<HTMLTextAreaElement>) {
    const data = mapKeyboardEventToTerminalInput(event.nativeEvent)
    if (data === null) return
    event.preventDefault()
    event.stopPropagation()

    if (data === '\r') {
      handleTerminalInput(data)
      return
    }

    if (data === '\u007F') {
      syncTerminalInput(commandRef.current.slice(0, -1))
      return
    }

    if (data === '\t') {
      handleTerminalInput(data)
      return
    }

    if (data === '\u001b[A' || data === '\u001b[B' || data === '\u001b[C' || data === '\u001b[D' || data === '\u001b') {
      handleTerminalInput(data)
      return
    }

    if (data === '\u0003') {
      handleTerminalInput(data)
      return
    }

    if (data.length === 1) {
      syncTerminalInput(`${commandRef.current}${data}`)
    }
  }

  function handleInputPaste(event: ClipboardEvent<HTMLTextAreaElement>) {
    const text = event.clipboardData.getData('text')
    if (!text) return
    event.preventDefault()
    event.stopPropagation()
    syncTerminalInput(`${commandRef.current}${text}`)
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
          <Button
            variant="destructive"
            onClick={() => {
              setLocalOutput([])
              resetTerminalOutput()
            }}
          >
            <Trash2 className="size-4" /> Clear
          </Button>
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
                <Badge variant="outline" className={cn('uppercase', terminalProfile.badgeClass)}>
                  {terminalProfile.label}
                </Badge>
                <Badge variant="outline" className={cn('uppercase', connectionClass[commandStatus === 'error' ? 'error' : connectionStatus])}>
                  <PlugZap className="size-3" />
                  {commandStatus === 'running' ? 'running via session' : commandStatus === 'error' ? 'error' : connectionStatus}
                </Badge>
                {liveSession && (
                  <Badge variant="outline" className={wsConnected ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300' : 'border-zinc-500/30 bg-zinc-500/10 text-zinc-700 dark:text-zinc-300'}>
                    <Wifi className="size-3" />
                    {wsConnected ? 'stream active' : 'stream off'}
                  </Badge>
                )}
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
                {terminalProfile.label} / {selectedDevice?.managementIp ?? '-'} / {liveSession ? 'interactive session' : 'not connected'}
              </div>
            </div>

            {commandError && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300">
                {commandError}
              </div>
            )}

            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_auto]">
              <div className="relative rounded-lg border border-border bg-zinc-950 p-0 shadow-inner">
                <div
                  ref={terminalHostRef}
                  className="relative h-[32rem] overflow-hidden rounded-lg"
                  role="application"
                  aria-label="Terminal session"
                  onMouseDown={() => {
                    inputRef.current?.focus()
                  }}
                  onClick={() => {
                    inputRef.current?.focus()
                  }}
                />
                <textarea
                  ref={inputRef}
                  value={command}
                  onChange={handleInputChange}
                  onKeyDown={handleInputKeyDown}
                  onPaste={handleInputPaste}
                  autoCapitalize="off"
                  autoComplete="off"
                  autoCorrect="off"
                  spellCheck={false}
                  aria-label="Terminal input"
                  className="absolute inset-0 z-10 h-full w-full resize-none border-0 bg-transparent p-0 opacity-0 outline-none"
                  style={{ caretColor: 'transparent' }}
                />
                {showSuggestions && (suggestions.length > 0 || suggestionStatus !== 'idle') && (
                  <div className="absolute inset-x-4 bottom-16 z-20 overflow-hidden rounded-lg border border-border bg-popover shadow-lg">
                    <div className="border-b bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
                      {suggestionStatus === 'loading'
                        ? 'Loading suggestions from device...'
                        : suggestionStatus === 'error'
                          ? liveSession ? 'Device suggestion failed.' : 'Connect SSH first to load suggestions from device.'
                          : 'Device command helper'}
                    </div>
                    <ScrollArea className="max-h-60">
                      <div ref={suggestionsViewportRef} className="p-1">
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
                              {suggestion.description || 'device'}
                            </span>
                          </button>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}
                <div className="border-t border-white/10 px-3 py-2 text-[11px] text-zinc-400">
                  Type directly in the terminal. Enter runs the command, `?` loads helpers, Tab accepts helper, and Arrow Up/Down browses history.
                </div>
              </div>
              <Button variant="outline" disabled={commandStatus === 'running'} onClick={() => runCommand(commandRef.current)}>
                {commandStatus === 'running' ? 'Running...' : 'Run Command'}
              </Button>
              <Button><Bot className="size-4" /> Explain with AI</Button>
            </div>
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-200">
              Live SSH session lewat backend. Ketik ? di akhir command untuk mengambil helper langsung dari device.
            </div>
            <div className="rounded-lg border border-border bg-muted/20 p-3 text-xs text-muted-foreground">
              {terminalProfile.helperNote}
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
                <p className="mt-1 font-mono text-sm text-foreground">{prompt}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {selectedDevice?.vendor === 'mikrotik'
                    ? 'Gunakan `?`, `ip ?`, atau `interface ?` agar helper mengikuti RouterOS asli.'
                    : selectedDevice?.vendor === 'cisco'
                      ? 'Gunakan `?` atau `show ?` untuk melihat tree command ala Cisco IOS.'
                      : 'Helper akan menyesuaikan vendor dan state device yang aktif.'}
                </p>
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Command History</CardTitle></CardHeader>
            <CardContent className="p-2">
              <ScrollArea className="h-48 rounded-lg border border-border bg-muted/10">
                <div className="grid gap-1 p-2">
                  {Array.from(new Set(localHistory)).map((item) => (
                    <button key={item} className="rounded-lg border border-border px-3 py-2 text-left font-mono text-xs hover:bg-muted" onClick={() => {
                      setCommand(item)
                      setShowSuggestions(false)
                    }}>
                      {item}
                    </button>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>

    </div>
  )
}

function makeLocalPrompt(vendor: Vendor, hostname: string) {
  return vendor === 'mikrotik' ? `[admin@${hostname}] >` : `${hostname}#`
}

function buildTerminalIntroLines(
  device: { hostname: string; platform: string; model: string; managementIp: string; vendor: Vendor },
  session: TerminalLiveSession,
) {
  return terminalProfiles[device.vendor].introLines(device, session)
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

function mapKeyboardEventToTerminalInput(event: globalThis.KeyboardEvent) {
  if (event.ctrlKey && event.key.toLowerCase() === 'c') return '\u0003'
  if (event.key === 'Enter') return '\r'
  if (event.key === 'Backspace') return '\u007F'
  if (event.key === 'Tab') return '\t'
  if (event.key === 'ArrowUp') return '\u001b[A'
  if (event.key === 'ArrowDown') return '\u001b[B'
  if (event.key === 'ArrowRight') return '\u001b[C'
  if (event.key === 'ArrowLeft') return '\u001b[D'
  if (event.key === 'Escape') return '\u001b'

  if (event.metaKey || event.ctrlKey || event.altKey) return null
  if (event.key.length === 1) return event.key
  return null
}

function formatTerminalLine(line: string, rawMode: boolean) {
  const text = rawMode ? line : line.replace(/\s+/g, ' ')
  if (!text) return ''
  if (text.startsWith('ERROR') || text.startsWith('BLOCKED') || text.startsWith('WS ERROR')) {
    return `\x1b[38;5;203m${text}\x1b[0m`
  }
  if (text.startsWith('WARNING')) {
    return `\x1b[38;5;214m${text}\x1b[0m`
  }
  if (text.startsWith('Connected') || text.startsWith('Disconnected') || text.startsWith('Stream session')) {
    return `\x1b[38;5;81m${text}\x1b[0m`
  }
  if (text.endsWith('#') || text.endsWith('>')) {
    return `\x1b[38;5;120m${text}\x1b[0m`
  }
  return text
}

function loadPersistedTerminalState(): PersistedTerminalState {
  if (typeof window === 'undefined') {
    return {
      command: '',
      rawMode: false,
      localOutput: [],
      localHistory: [],
    }
  }

  try {
    const raw = window.sessionStorage.getItem(TERMINAL_STATE_STORAGE_KEY)
    if (!raw) {
      return {
        command: '',
        rawMode: false,
        localOutput: [],
        localHistory: [],
      }
    }

    const parsed = JSON.parse(raw) as Partial<PersistedTerminalState>
    return {
      command: typeof parsed.command === 'string' ? parsed.command : '',
      selectedDeviceId: typeof parsed.selectedDeviceId === 'string' ? parsed.selectedDeviceId : undefined,
      rawMode: Boolean(parsed.rawMode),
      localOutput: Array.isArray(parsed.localOutput) ? parsed.localOutput.map(String) : [],
      localHistory: Array.isArray(parsed.localHistory) ? parsed.localHistory.map(String) : [],
    }
  } catch {
    return {
      command: '',
      rawMode: false,
      localOutput: [],
      localHistory: [],
    }
  }
}

function persistTerminalState(state: PersistedTerminalState) {
  if (typeof window === 'undefined') return

  try {
    window.sessionStorage.setItem(TERMINAL_STATE_STORAGE_KEY, JSON.stringify(state))
  } catch {
    // Ignore storage quota / privacy mode failures.
  }
}

export default TerminalPage
