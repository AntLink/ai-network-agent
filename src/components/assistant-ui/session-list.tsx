import { useState } from 'react'
import { Archive, EllipsisVertical, Pin, Pencil, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import type { AgentSession } from 'src/types/agent'
import { cn } from 'src/lib/utils'
import { Button } from 'src/components/ui/button'
import { Input } from 'src/components/ui/input'
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from 'src/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'src/components/ui/dropdown-menu'
import { ScrollArea } from 'src/components/ui/scroll-area'

/**
 * Session/sidebar list for the AI Network Copilot chat.
 */
export function AgentSessionList({
  sessions,
  loading,
  activeSessionId,
  onSelectSession,
  onDeleteSession,
  onRenameSession,
}: {
  sessions: AgentSession[]
  loading: boolean
  activeSessionId?: string
  onSelectSession: (session: AgentSession) => void
  onDeleteSession: (session: AgentSession) => Promise<void> | void
  onRenameSession: (session: AgentSession, title: string) => Promise<void> | void
}) {
  const [renameOpen, setRenameOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [activeSession, setActiveSession] = useState<AgentSession | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [busyAction, setBusyAction] = useState<'rename' | 'delete' | null>(null)

  const openRename = (session: AgentSession) => {
    setActiveSession(session)
    setRenameValue(session.title)
    setRenameOpen(true)
  }

  const openDelete = (session: AgentSession) => {
    setActiveSession(session)
    setDeleteOpen(true)
  }

  const handleRename = async () => {
    if (!activeSession) return
    const nextTitle = renameValue.trim()
    if (!nextTitle || nextTitle === activeSession.title) {
      setRenameOpen(false)
      return
    }

    setBusyAction('rename')
    try {
      await Promise.resolve(onRenameSession(activeSession, nextTitle))
      toast.success('Chat renamed')
      setRenameOpen(false)
    } catch {
      toast.error('Failed to rename chat')
    } finally {
      setBusyAction(null)
    }
  }

  const handleDelete = async () => {
    if (!activeSession) return

    setBusyAction('delete')
    try {
      await Promise.resolve(onDeleteSession(activeSession))
      toast.success('Chat deleted')
      setDeleteOpen(false)
    } catch {
      toast.error('Failed to delete chat')
    } finally {
      setBusyAction(null)
    }
  }

  return (
    <>
      <ScrollArea className="bubble-scrollbar relative flex h-full min-h-0 flex-1 overflow-hidden rounded-xl border border-border/40 bg-background/20">
        <div className="relative flex min-h-full flex-col gap-0.5 p-1">
          {loading ? (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">Loading sessions...</p>
          ) : sessions.length === 0 ? (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">No sessions yet. Start a new chat.</p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  'group flex min-w-0 items-center gap-1.5 rounded-lg border border-transparent px-2.5 py-1.5 text-[13px] transition hover:border-border hover:bg-muted/60',
                  activeSessionId === session.id && 'border-border bg-muted text-foreground',
                )}
              >
                <button
                  type="button"
                  className="flex min-w-0 flex-1 items-center overflow-hidden text-left"
                  onClick={() => onSelectSession(session)}
                >
                  <span className="min-w-0 flex-1 truncate text-left text-[13px] font-medium leading-5">{session.title}</span>
                </button>
                <DropdownMenu>
                  <DropdownMenuTrigger
                    className="inline-flex size-7 shrink-0 items-center justify-center rounded-md border border-border/60 bg-background text-muted-foreground opacity-0 transition-opacity hover:bg-muted hover:text-foreground group-hover:opacity-100 group-data-[state=open]:opacity-100"
                    aria-label="Session actions"
                    title="Session actions"
                  >
                    <EllipsisVertical className="size-3.5" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-44">
                    <DropdownMenuItem
                      className="flex items-center gap-2"
                      onClick={() => {
                        openRename(session)
                      }}
                    >
                      <Pencil className="size-3.5" />
                      Rename chat
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="flex items-center gap-2"
                      onSelect={() => {
                        toast.info(`Pin chat: ${session.title}`)
                      }}
                    >
                      <Pin className="size-3.5" />
                      Pin chat
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="flex items-center gap-2"
                      onSelect={() => {
                        toast.info(`Archive chat: ${session.title}`)
                      }}
                    >
                      <Archive className="size-3.5" />
                      Archive
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      variant="destructive"
                      className="flex items-center gap-2"
                      onClick={() => {
                        openDelete(session)
                      }}
                    >
                      <Trash2 className="size-3.5" />
                      Delete chat
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      <Dialog
        open={renameOpen}
        onOpenChange={(open) => {
          setRenameOpen(open)
          if (!open) {
            setActiveSession(null)
            setRenameValue('')
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rename chat</DialogTitle>
            <DialogDescription>Change the session title for easier tracking in history.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-2">
            <Input value={renameValue} onChange={(event) => setRenameValue(event.target.value)} placeholder="Chat title" autoFocus />
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setRenameOpen(false)}
              disabled={busyAction === 'rename'}
            >
              Cancel
            </Button>
            <Button type="button" onClick={() => void handleRename()} disabled={busyAction === 'rename'}>
              {busyAction === 'rename' ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={deleteOpen}
        onOpenChange={(open) => {
          setDeleteOpen(open)
          if (!open) {
            setActiveSession(null)
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-red-500/10 text-red-600">
              <Trash2 className="size-5" />
            </AlertDialogMedia>
            <AlertDialogTitle>Delete chat?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove {activeSession?.title ?? 'the selected chat'} from history.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={busyAction === 'delete'}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => void handleDelete()}
              disabled={busyAction === 'delete'}
            >
              {busyAction === 'delete' ? 'Deleting...' : 'Delete chat'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
