import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from 'src/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from 'src/components/ui/dialog'

interface DestructiveConfirmDialogProps {
  title: string
  description: string
  confirmLabel?: string
  onConfirm: () => void | Promise<void>
  triggerLabel?: string
}

export function DestructiveConfirmDialog({
  title,
  description,
  confirmLabel = 'Confirm',
  onConfirm,
  triggerLabel = 'Delete',
}: DestructiveConfirmDialogProps) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)

  const handleConfirm = async () => {
    setBusy(true)
    try {
      await onConfirm()
      setOpen(false)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Button variant="destructive" onClick={() => setOpen(true)}>
        <AlertTriangle className="size-4" />
        {triggerLabel}
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} disabled={busy}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirm} disabled={busy}>
              {busy ? 'Working...' : confirmLabel}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

