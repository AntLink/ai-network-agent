import {
  Activity,
  Archive,
  Bell,
  Bot,
  Boxes,
  ClipboardList,
  Cloud,
  FileClock,
  FlaskConical,
  KeyRound,
  LayoutDashboard,
  Network,
  Radar,
  ShieldCheck,
  Route,
  Server,
  Settings,
  Sparkles,
  Terminal,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface ChildItem {
  id?: number | string
  name: string
  icon?: LucideIcon
  items?: ChildItem[]
  item?: unknown
  url?: string
  color?: string
  disabled?: boolean
  subtitle?: string
  badge?: boolean
  badgeType?: string
  badgeContent?: string
  isActive?: boolean
  external?: boolean
  isPro?: boolean
}

export interface MenuItem {
  heading?: string
  name?: string
  icon?: LucideIcon
  id?: number | string
  to?: string
  item?: MenuItem[]
  items?: ChildItem[]
  url?: string
  disabled?: boolean
  subtitle?: string
  badgeType?: string
  badge?: boolean
  badgeContent?: string
  isActive?: boolean
  isPro?: boolean
}

const SidebarContent: MenuItem[] = [
  {
    heading: 'Dashboard',
    items: [
      {
        id: 'dashboard',
        name: 'Dashboard',
        icon: LayoutDashboard,
        url: '/dashboard',
      },
    ],
  },
  {
    heading: 'AI',
    items: [
      {
        id: 'ai-assistant',
        name: 'AI Assistant',
        icon: Sparkles,
        url: '/ai-assistant',
      },
      {
        id: 'agent',
        name: 'Agent',
        icon: Bot,
        url: '/agent',
      },
      {
        id: 'tasks',
        name: 'Tasks',
        icon: ClipboardList,
        url: '/tasks',
      },
      {
        id: 'terminal',
        name: 'Terminal',
        icon: Terminal,
        url: '/terminal',
      },
    ],
  },
  {
    heading: 'Network',
    items: [
      {
        id: 'devices',
        name: 'Devices',
        icon: Server,
        url: '/devices',
      },
      {
        id: 'topology',
        name: 'Topology',
        icon: Network,
        url: '/topology',
      },
      {
        id: 'topology-builder',
        name: 'Topology Builder',
        icon: Route,
        url: '/topology-builder',
      },
      {
        id: 'discovery',
        name: 'Discovery',
        icon: Radar,
        url: '/discovery',
      },
      {
        id: 'alerts',
        name: 'Alerts',
        icon: Bell,
        url: '/alerts',
      },
    ],
  },
  {
    heading: 'Labs',
    items: [
      {
        id: 'labs',
        name: 'Labs',
        icon: FlaskConical,
        url: '/labs',
      },
      {
        id: 'gns3',
        name: 'GNS3',
        icon: Cloud,
        url: '/gns3',
      },
      {
        id: 'containerlab',
        name: 'Containerlab',
        icon: Boxes,
        url: '/containerlab',
      },
    ],
  },
  {
    heading: 'Environment',
    items: [
      {
        id: 'environments',
        name: 'Overview',
        icon: FlaskConical,
        url: '/environments',
      },
      {
        id: 'environment-lab',
        name: 'Lab',
        icon: FlaskConical,
        url: '/environments/lab',
      },
      {
        id: 'environment-staging',
        name: 'Staging',
        icon: ShieldCheck,
        url: '/environments/staging',
      },
      {
        id: 'environment-production',
        name: 'Production',
        icon: Server,
        url: '/environments/production',
      },
    ],
  },
  {
    heading: 'Automation',
    items: [
      {
        id: 'configurations',
        name: 'Configurations',
        icon: Activity,
        url: '/configurations',
      },
      {
        id: 'backups',
        name: 'Backups',
        icon: Archive,
        url: '/backups',
      },
      {
        id: 'audit',
        name: 'Audit Logs',
        icon: FileClock,
        url: '/audit',
      },
    ],
  },
  {
    heading: 'System',
    items: [
      {
        id: 'credentials',
        name: 'Credentials',
        icon: KeyRound,
        url: '/settings/credentials',
      },
      {
        id: 'settings',
        name: 'Settings',
        icon: Settings,
        url: '/settings',
      },
    ],
  },
]

export default SidebarContent
