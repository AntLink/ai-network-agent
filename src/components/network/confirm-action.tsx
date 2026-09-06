import { AlertTriangle } from 'lucide-react'
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
  AlertDialogTrigger,
} from 'src/components/ui/alert-dialog'
import { Button } from 'src/components/ui/button'

type ConfirmActionProps = {
  label: string
  title: string
  description: string
  variant?: 'default' | 'destructive' | 'outline'
  disabled?: boolean
  onConfirm?: () => void
}

export function ConfirmAction({ label, title, description, variant = 'outline', disabled = false, onConfirm }: ConfirmActionProps) {
  return (
    <AlertDialog>
      <AlertDialogTrigger render={<Button variant={variant} disabled={disabled} />}>{label}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogMedia className="bg-amber-500/10 text-amber-700 dark:text-amber-300">
            <AlertTriangle className="size-5" />
          </AlertDialogMedia>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction variant={variant === 'destructive' ? 'destructive' : 'default'} onClick={onConfirm}>
            Confirm
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
