import { SendHorizontal } from 'lucide-react'
import { ComposerPrimitive, useAuiState } from '@assistant-ui/react'

export function AgentComposer() {
  const running = useAuiState((state) => state.thread.isRunning)

  return (
    <ComposerPrimitive.Root className="border-t border-border bg-background/90 p-4 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <ComposerPrimitive.Input
          placeholder="Konfigurasi perangkat, buat tools, atau jalankan diagnostik..."
          disabled={running}
          className="min-h-12 flex-1 resize-none rounded-3xl border border-border bg-background px-4 py-3 text-sm shadow-sm outline-none transition placeholder:text-muted-foreground focus:border-primary/50 focus:ring-2 focus:ring-primary/10"
        />
        <ComposerPrimitive.Send
          disabled={running}
          className="flex size-12 shrink-0 items-center justify-center rounded-2xl border border-border bg-foreground text-background shadow-sm transition hover:opacity-90 disabled:opacity-50"
        >
          <SendHorizontal className="size-5" />
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  )
}
