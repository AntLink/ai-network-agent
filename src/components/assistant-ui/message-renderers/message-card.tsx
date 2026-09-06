import { Bot, Copy, Loader2, RefreshCw } from 'lucide-react'
import { MessagePrimitive, ThreadPrimitive, useAui, useAuiState } from '@assistant-ui/react'
import { useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { CommandOutputCard } from './command-output-card'
import { DeviceStateCard } from './device-state-card'
import { PlanCard } from './plan-card'
import { StreamEventTimeline } from './stream-event-timeline'
import { WorkflowInline } from '../workflow-state'
import type { AgentStreamEvent, AgentWorkflowSnapshot } from 'src/types/agent'
import { normalizeMarkdownTables } from './utils'

function CopyButton({ text }: { text: string }) {
  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      // clipboard unavailable
    }
  }, [text])

  return (
    <button
      type="button"
      onClick={copy}
      className="flex items-center gap-1 rounded-lg border border-border bg-background/70 px-2 py-1 text-xs text-muted-foreground transition hover:text-foreground"
      aria-label="Copy"
    >
      <Copy className="size-3" />
      Copy
    </button>
  )
}

function CodeBlock({ text, language }: { text: string; language?: string }) {
  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      // clipboard unavailable
    }
  }, [text])

  return (
    <div className="my-2 max-w-full overflow-hidden rounded-xl border border-border bg-slate-950 text-xs text-slate-100 dark:text-slate-200">
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-1.5">
        <span className="font-mono text-[10px] uppercase text-slate-400">{language || 'code'}</span>
        <button
          type="button"
          onClick={copy}
          className="flex items-center gap-1 rounded-md bg-white/10 px-2 py-0.5 text-[10px] text-slate-300 transition hover:bg-white/20"
          aria-label="Copy code"
        >
          <Copy className="size-3" />
          Copy
        </button>
      </div>
      <pre className="bubble-scrollbar max-h-[28rem] overflow-auto p-3 leading-5">
        <code className="block min-w-0 whitespace-pre font-mono break-words">{text}</code>
      </pre>
    </div>
  )
}

function StructuredCodeBlock({ text, language }: { text: string; language?: string }) {
  if (language === 'device_state') return <DeviceStateCard text={text} />
  if (language === 'plan') return <PlanCard text={text} />
  if (language === 'command_output' || language === 'output' || language === 'terminal') {
    return <CommandOutputCard text={text} />
  }
  return <CodeBlock text={text} language={language} />
}

function MarkdownText({ text }: { text: string }) {
  const normalizedText = normalizeMarkdownTables(text)
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        table: ({ children }) => (
          <div className="bubble-scrollbar my-2 max-w-full overflow-x-auto rounded-xl border border-border bg-background/80">
            <table className="min-w-full border-collapse text-[13px]">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-muted/50 text-left text-muted-foreground">{children}</thead>,
        tbody: ({ children }) => <tbody className="divide-y divide-border">{children}</tbody>,
        tr: ({ children }) => <tr className="align-top">{children}</tr>,
        th: ({ children }) => (
          <th className="whitespace-nowrap border-b border-border px-3 py-2 text-left font-medium uppercase tracking-wide">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="max-w-[18rem] border-b border-border/60 px-3 py-2 align-top leading-5 text-foreground">
            <span className="block break-words">{children}</span>
          </td>
        ),
        p: ({ children }) => <p className="my-0.5 break-words first:mt-0 last:mb-0 leading-5">{children}</p>,
        ul: ({ children }) => <ul className="my-0.5 list-disc space-y-0.5 pl-5">{children}</ul>,
        ol: ({ children }) => <ol className="my-0.5 list-decimal space-y-0.5 pl-5">{children}</ol>,
        li: ({ children }) => <li className="my-0 leading-5">{children}</li>,
        h1: ({ children }) => <h1 className="my-0.5 text-sm font-semibold leading-5">{children}</h1>,
        h2: ({ children }) => <h2 className="my-0.5 text-sm font-semibold leading-5">{children}</h2>,
        h3: ({ children }) => <h3 className="my-0.5 text-sm font-semibold leading-5">{children}</h3>,
        h4: ({ children }) => <h4 className="my-0.5 text-sm font-semibold leading-5">{children}</h4>,
        h5: ({ children }) => <h5 className="my-0.5 text-sm font-semibold leading-5">{children}</h5>,
        h6: ({ children }) => <h6 className="my-0.5 text-sm font-semibold leading-5">{children}</h6>,
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        a: ({ children, href }) => (
          <a href={href} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-2">
            {children}
          </a>
        ),
        code: (props) => {
          const { children, className } = props
          const inline = !className && !String(children).includes('\n')
          if (inline) {
            return <code className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[0.9em]">{children}</code>
          }
          const language = className?.replace(/^language-/, '')
          return <StructuredCodeBlock text={String(children).replace(/\n$/, '')} language={language} />
        },
      }}
      >
      {normalizedText}
    </ReactMarkdown>
  )
}

function AssistantActions({ text }: { text: string }) {
  return <CopyButton text={text} />
}

function RetryButton() {
  const aui = useAui()
  const messages = useAuiState((state) => state.thread.messages)
  const lastUser = [...messages].reverse().find((message) => message.role === 'user')

  return (
    <button
      type="button"
      onClick={() => {
        if (lastUser) aui.thread.startRun({ parentId: lastUser.id })
      }}
      className="flex items-center gap-1 rounded-lg border border-border bg-background px-2 py-1 text-xs font-medium transition hover:bg-muted"
      aria-label="Retry"
    >
      <RefreshCw className="size-3" />
      Retry
    </button>
  )
}

export function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end py-3">
      <div className="max-w-[85%] rounded-xl bg-muted/70 px-4 py-2.5 text-sm leading-6 text-foreground">
        <MessagePrimitive.Content
          components={{
            Text: ({ text }: { text: string }) => <p className="whitespace-pre-wrap">{text}</p>,
          }}
        />
      </div>
    </MessagePrimitive.Root>
  )
}

export function AssistantMessage({
  streamText,
  fallbackText,
  streamEvents,
  workflowSnapshot,
}: {
  streamText?: string
  fallbackText?: string
  streamEvents?: AgentStreamEvent[]
  workflowSnapshot?: AgentWorkflowSnapshot
}) {
  const running = useAuiState((state) => state.thread.isRunning)
  const last = useAuiState((state) => state.message.isLast)
  const hasStreamText = last && typeof streamText === 'string' && streamText.length > 0
  const showLoading = last && running && !hasStreamText
  const displayText = normalizeMarkdownTables((hasStreamText ? streamText : fallbackText)?.trim() ?? '')
  const showProcess = last && Boolean(workflowSnapshot) && ((streamEvents?.length ?? 0) > 0 || running)

  return (
    <MessagePrimitive.Root className="group py-2">
      <div className="w-full">
        <div className="w-full text-sm leading-6">
          {hasStreamText ? (
            <div className="space-y-1">
              <div className="prose prose-sm max-w-none break-words whitespace-pre-wrap leading-5 dark:prose-invert prose-p:my-0.5 prose-p:leading-5 prose-ul:my-0.5 prose-ol:my-0.5 prose-li:my-0 prose-headings:my-0.5 prose-headings:leading-5 prose-h1:my-0.5 prose-h2:my-0.5 prose-h3:my-0.5 prose-h4:my-0.5 prose-h5:my-0.5 prose-h6:my-0.5 prose-pre:my-0.5 prose-pre:overflow-x-auto prose-pre:scroll-smooth">
                <MarkdownText text={streamText} />
              </div>
            </div>
          ) : showLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Thinking…
            </div>
          ) : displayText ? (
            <div className="prose prose-sm max-w-none break-words whitespace-pre-wrap leading-5 dark:prose-invert prose-p:my-0.5 prose-p:leading-5 prose-ul:my-0.5 prose-ol:my-0.5 prose-li:my-0 prose-headings:my-0.5 prose-headings:leading-5 prose-h1:my-0.5 prose-h2:my-0.5 prose-h3:my-0.5 prose-h4:my-0.5 prose-h5:my-0.5 prose-h6:my-0.5 prose-pre:my-0.5 prose-pre:overflow-x-auto prose-pre:scroll-smooth">
              <MarkdownText text={displayText} />
            </div>
          ) : (
            <MessagePrimitive.Content
              components={{
                Text: ({ text }: { text: string }) => (
                  <div className="prose prose-sm max-w-none break-words whitespace-pre-wrap leading-5 dark:prose-invert prose-p:my-0.5 prose-p:leading-5 prose-ul:my-0.5 prose-ol:my-0.5 prose-li:my-0 prose-headings:my-0.5 prose-headings:leading-5 prose-h1:my-0.5 prose-h2:my-0.5 prose-h3:my-0.5 prose-h4:my-0.5 prose-h5:my-0.5 prose-h6:my-0.5 prose-pre:my-0.5 prose-pre:overflow-x-auto prose-pre:scroll-smooth">
                    <MarkdownText text={text} />
                  </div>
                ),
              }}
            />
          )}
          {showProcess ? (
            <div className="mt-2 grid gap-2">
              <WorkflowInline snapshot={workflowSnapshot as AgentWorkflowSnapshot} visible={(streamEvents?.length ?? 0) > 0 || running} />
              <StreamEventTimeline events={streamEvents ?? []} />
            </div>
          ) : null}
        </div>
        <MessagePrimitive.Error>
          <div className="mt-1.5 flex flex-wrap items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/5 px-3 py-2 text-sm text-red-700 dark:text-red-300">
            <span>This message failed. Retry to generate a new response.</span>
            <RetryButton />
          </div>
        </MessagePrimitive.Error>
        {!running && last && (
          <div className="mt-1 flex items-center gap-1 opacity-0 transition group-hover:opacity-100">
            <AssistantActions text={streamText?.trim() || fallbackText?.trim() || ''} />
          </div>
        )}
      </div>
    </MessagePrimitive.Root>
  )
}

export function AgentEmptyThreadState() {
  const aui = useAui()

  return (
    <ThreadPrimitive.Empty>
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <span className="flex size-14 items-center justify-center rounded-3xl border border-border bg-background text-foreground shadow-sm">
          <Bot className="size-7" />
        </span>
        <h3 className="text-lg font-semibold">Network Copilot</h3>
        <p className="max-w-sm text-sm text-muted-foreground">
          Ask about device health, interfaces, routing, ping tests, or configuration plans.
        </p>
        <div className="mt-2 flex flex-wrap justify-center gap-2">
          {[
            'Kenapa R1 tidak bisa ping R2?',
            'Cek interface dan status device R1',
            'Tampilkan routing table R1 dan R2',
            'Buat rencana konfigurasi VLAN 10',
          ].map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => aui.composer.setText(suggestion)}
              className="rounded-full border border-border bg-background/70 px-3 py-1.5 text-xs text-muted-foreground transition hover:border-primary/40 hover:text-foreground"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </ThreadPrimitive.Empty>
  )
}
