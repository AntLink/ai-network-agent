import { Link } from 'react-router'
import { Network } from 'lucide-react'

const FullLogo = () => {
  return (
    <Link to="/dashboard" className="flex max-w-[190px] items-center gap-2 overflow-hidden">
      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Network className="size-4" />
      </span>
      <span className="hidden text-sm font-semibold leading-tight lg:block">
        AI Network
        <span className="block text-xs font-medium text-muted-foreground">Agent NOC</span>
      </span>
    </Link>
  )
}

export default FullLogo
