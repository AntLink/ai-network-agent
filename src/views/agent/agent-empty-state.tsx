import { Bot } from 'lucide-react'

const SUGGESTIONS = [
  'Kenapa R1 tidak bisa ping R2?',
  'Cek interface dan status device R1',
  'Tampilkan routing table R1 dan R2',
  'Buat rencana konfigurasi VLAN 10',
]

export function AgentEmptyState() {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <span className="flex size-14 items-center justify-center rounded-3xl bg-gradient-to-br from-cyan-500 to-emerald-500 text-white shadow-lg shadow-cyan-950/20">
        <Bot className="size-7" />
      </span>
      <h3 className="text-lg font-semibold">Network Copilot</h3>
      <p className="max-w-sm text-sm text-muted-foreground">
        Ask about device health, interfaces, routing, ping tests, or configuration plans.
      </p>
      <div className="mt-2 flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((suggestion) => (
          <span
            key={suggestion}
            className="rounded-full border border-border bg-background/70 px-3 py-1.5 text-xs text-muted-foreground"
          >
            {suggestion}
          </span>
        ))}
      </div>
    </div>
  )
}

