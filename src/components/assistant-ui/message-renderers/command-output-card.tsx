import { Copy } from 'lucide-react'
import { useCallback } from 'react'

export function CommandOutputCard({ text }: { text: string }) {
  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      // clipboard unavailable
    }
  }, [text])

  return (
    <div className="my-2 overflow-hidden rounded-xl border border-border bg-slate-950 text-xs text-slate-100 dark:text-slate-200">
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-1.5">
        <span className="font-mono text-[10px] uppercase text-slate-400">command output</span>
        <button
          type="button"
          onClick={copy}
          className="flex items-center gap-1 rounded-md bg-white/10 px-2 py-0.5 text-[10px] text-slate-300 transition hover:bg-white/20"
          aria-label="Copy output"
        >
          <Copy className="size-3" />
          Copy
        </button>
      </div>
      <pre className="bubble-scrollbar max-h-[30rem] overflow-auto p-3 font-mono leading-5 text-emerald-200/90">{text}</pre>
    </div>
  )
}
