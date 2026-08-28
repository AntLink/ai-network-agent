import type { ReactNode } from 'react'

export function AgentLayout({
  sessions,
  chat,
  context,
  contextCollapsed = false,
}: {
  sessions: ReactNode
  chat: ReactNode
  context: ReactNode
  contextCollapsed?: boolean
}) {
  const gridClassName = contextCollapsed
    ? 'grid gap-4 xl:grid-cols-[12.5rem_minmax(0,1fr)]'
    : 'grid gap-4 xl:grid-cols-[12.5rem_minmax(0,1fr)_18rem] 2xl:grid-cols-[13rem_minmax(0,1fr)_18.5rem]'

  return (
    <div className={gridClassName}>
      {sessions}
      {chat}
      {contextCollapsed ? null : context}
    </div>
  )
}
