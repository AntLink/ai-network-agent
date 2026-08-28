import { parseJsonBlock } from './utils'

export function PlanCard({ text }: { text: string }) {
  const data = parseJsonBlock(text)
  if (!data) {
    return (
      <pre className="bubble-scrollbar my-2 max-h-64 overflow-auto rounded-xl border border-border bg-slate-950 p-3 text-xs text-slate-100 dark:text-slate-200">
        {text}
      </pre>
    )
  }

  const steps = Array.isArray(data.steps)
    ? data.steps
    : Array.isArray(data.planned_actions)
      ? data.planned_actions
      : null

  return (
    <div className="my-2 max-w-full overflow-hidden rounded-xl border border-border">
      <div className="flex items-center justify-between border-b border-border bg-muted/40 px-3 py-1.5">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Execution Plan</span>
        {data.risk ? (
          <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-300">
            {String(data.risk)}
          </span>
        ) : null}
      </div>
      <div className="grid gap-1.5 p-3">
        {Array.isArray(steps) &&
          steps.map((step, index) => (
            <div key={index} className="flex items-start gap-2 text-xs">
              <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
                {index + 1}
              </span>
              <span className="min-w-0 break-words leading-5">
                {typeof step === 'string' ? step : JSON.stringify(step)}
              </span>
            </div>
          ))}
      </div>
    </div>
  )
}
