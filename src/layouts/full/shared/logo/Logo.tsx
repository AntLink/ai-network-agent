import { Link } from 'react-router'
import { Network } from 'lucide-react'
import { SidebarMenuButton } from 'src/components/ui/sidebar'

const Logo = () => {
  return (
    <Link to="/dashboard">
      <SidebarMenuButton
        size="lg"
        className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
      >
        <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Network className="size-4" />
        </span>
        <span className="hide-menu text-sm font-semibold">AI Network Agent</span>
      </SidebarMenuButton>
    </Link>
  )
}

export default Logo
