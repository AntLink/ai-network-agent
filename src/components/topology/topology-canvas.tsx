import { forwardRef, useEffect, useImperativeHandle, useMemo } from 'react'
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  Handle,
  Position,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { cn } from 'src/lib/utils'
import type { Topology, Vendor } from 'src/types/network'
import {
  Router,
  Network,
  Monitor,
  Server,
  Cloud,
  HardDrive,
  type LucideIcon,
} from 'lucide-react'

type TopoNode = Topology['nodes'][number]
type NodePosition = { x: number; y: number }
type DeviceNodeData = {
  hostname: string
  ip: string
  vendor: Vendor
  kind?: Topology['nodes'][number]['kind']
  nodeType?: Topology['nodes'][number]['nodeType']
  status: TopoNode['status']
}
type DeviceFlowNode = Node<DeviceNodeData, 'device'>

export type TopologyCanvasHandle = {
  saveLayout: () => boolean
  exportLayout: () => Record<string, NodePosition>
}

type TopologyCanvasProps = {
  topology: Topology
  builder?: boolean
  storageKey?: string
}

const VENDOR_ICON: Record<Vendor, LucideIcon> = {
  cisco: Router,
  mikrotik: Router,
  aruba: Network,
  linux: Server,
  other: HardDrive,
}

const VENDOR_COLOR: Record<Vendor, string> = {
  cisco: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  mikrotik: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
  aruba: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
  linux: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  other: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
}

const STATUS_STYLES: Record<TopoNode['status'], { border: string; ring: string; badge: string; dot: string }> = {
  online: {
    border: 'border-emerald-400/50',
    ring: 'ring-emerald-500/15',
    badge: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    dot: 'bg-emerald-500',
  },
  warning: {
    border: 'border-amber-400/60',
    ring: 'ring-amber-500/15',
    badge: 'bg-amber-500/10 text-amber-700 dark:text-amber-400',
    dot: 'bg-amber-500',
  },
  offline: {
    border: 'border-rose-400/50',
    ring: 'ring-rose-500/15',
    badge: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
    dot: 'bg-rose-500',
  },
  unknown: {
    border: 'border-slate-400/50',
    ring: 'ring-slate-500/10',
    badge: 'bg-slate-500/10 text-slate-600 dark:text-slate-400',
    dot: 'bg-slate-500',
  },
}

function DeviceIcon({ vendor, hostname }: { vendor: Vendor; hostname: string }) {
  const name = hostname.toLowerCase()

  // Refine by name patterns
  let icon: LucideIcon = VENDOR_ICON[vendor]
  let color = VENDOR_COLOR[vendor]

  if (name.startsWith('pc') || name.startsWith('host')) {
    icon = Monitor
    color = 'bg-sky-500/10 text-sky-600 dark:text-sky-400'
  } else if (name.startsWith('sw') || name.includes('switch')) {
    icon = Network
    color = 'bg-purple-500/10 text-purple-600 dark:text-purple-400'
  } else if (name.startsWith('cloud') || name === 'internet' || name === 'nat') {
    icon = Cloud
    color = 'bg-slate-500/10 text-slate-600 dark:text-slate-400'
  } else if (name.includes('server') || name.includes('vm') || name.includes('telemetry')) {
    icon = Server
    color = 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
  }

  const Icon = icon

  return <Icon className={cn('size-7', color)} />
}

function kindAppearance(kind?: Topology['nodes'][number]['kind'], vendor?: Vendor) {
  switch (kind) {
    case 'router':
      return {
        shell: 'rounded-2xl border-blue-400/50 bg-gradient-to-br from-blue-500/10 via-card to-card',
        iconWrap: 'rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400',
        badge: 'bg-blue-500/10 text-blue-700 dark:text-blue-300',
        label: 'Router',
      }
    case 'switch':
      return {
        shell: 'rounded-xl border-dashed border-purple-400/50 bg-gradient-to-br from-purple-500/10 via-card to-card',
        iconWrap: 'rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400',
        badge: 'bg-purple-500/10 text-purple-700 dark:text-purple-300',
        label: 'Switch',
      }
    case 'host':
      return {
        shell: 'rounded-xl border-emerald-400/50 bg-gradient-to-br from-emerald-500/10 via-card to-card',
        iconWrap: 'rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
        badge: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
        label: 'Host',
      }
    case 'cloud':
      return {
        shell: 'rounded-full border-slate-400/50 bg-gradient-to-br from-slate-500/10 via-card to-card',
        iconWrap: 'rounded-full bg-slate-500/10 text-slate-600 dark:text-slate-400',
        badge: 'bg-slate-500/10 text-slate-700 dark:text-slate-300',
        label: 'Cloud',
      }
    case 'nat':
      return {
        shell: 'rounded-full border-orange-400/50 bg-gradient-to-br from-orange-500/10 via-card to-card',
        iconWrap: 'rounded-full bg-orange-500/10 text-orange-600 dark:text-orange-400',
        badge: 'bg-orange-500/10 text-orange-700 dark:text-orange-300',
        label: 'NAT',
      }
    case 'firewall':
      return {
        shell: 'rounded-2xl border-rose-400/50 bg-gradient-to-br from-rose-500/10 via-card to-card',
        iconWrap: 'rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400',
        badge: 'bg-rose-500/10 text-rose-700 dark:text-rose-300',
        label: 'Firewall',
      }
    case 'loopback':
      return {
        shell: 'rounded-full border-sky-400/50 bg-gradient-to-br from-sky-500/10 via-card to-card',
        iconWrap: 'rounded-full bg-sky-500/10 text-sky-600 dark:text-sky-400',
        badge: 'bg-sky-500/10 text-sky-700 dark:text-sky-300',
        label: 'Loopback',
      }
    default:
      return {
        shell:
          vendor === 'cisco'
            ? 'rounded-2xl border-blue-400/50 bg-gradient-to-br from-blue-500/10 via-card to-card'
            : vendor === 'mikrotik'
              ? 'rounded-[1.5rem] border-cyan-400/50 bg-gradient-to-br from-cyan-500/10 via-card to-card'
              : vendor === 'aruba'
                ? 'rounded-xl border-dashed border-purple-400/50 bg-gradient-to-br from-purple-500/10 via-card to-card'
                : vendor === 'linux'
                  ? 'rounded-lg border-emerald-400/50 bg-gradient-to-br from-emerald-500/10 via-card to-card'
                  : 'rounded-[1.4rem] border-orange-400/50 bg-gradient-to-br from-orange-500/10 via-card to-card',
        iconWrap:
          vendor === 'cisco'
            ? 'rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400'
            : vendor === 'mikrotik'
              ? 'rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-400'
              : vendor === 'aruba'
                ? 'rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400'
                : vendor === 'linux'
                  ? 'rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                  : 'rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400',
        badge:
          vendor === 'cisco'
            ? 'bg-blue-500/10 text-blue-700 dark:text-blue-300'
            : vendor === 'mikrotik'
              ? 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300'
              : vendor === 'aruba'
                ? 'bg-purple-500/10 text-purple-700 dark:text-purple-300'
                : vendor === 'linux'
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
                  : 'bg-orange-500/10 text-orange-700 dark:text-orange-300',
        label: vendor === 'cisco' ? 'Cisco' : vendor === 'mikrotik' ? 'MikroTik' : vendor === 'aruba' ? 'Aruba' : vendor === 'linux' ? 'Linux' : 'Other',
      }
  }
}

function nodeTypeLabel(nodeType?: Topology['nodes'][number]['nodeType']) {
  switch (nodeType) {
    case 'qemu':
      return 'qemu'
    case 'vpcs':
      return 'vpcs'
    case 'dynamips':
      return 'dynamips'
    case 'cloud':
      return 'cloud'
    case 'ethernet_switch':
      return 'ethernet_switch'
    case 'docker':
      return 'docker'
    default:
      return null
  }
}

function DeviceNode({ data, selected }: NodeProps<DeviceFlowNode>) {
  const statusStyle = STATUS_STYLES[data.status]
  const appearance = kindAppearance(data.kind, data.vendor)
  const statusLabel = data.status.charAt(0).toUpperCase() + data.status.slice(1)
  const typeLabel = nodeTypeLabel(data.nodeType)

  return (
    <div
      className={[
        'w-[8.25rem] max-w-[8.25rem] border px-1.5 py-1.5 shadow-sm transition-all',
        appearance.shell,
        selected ? `border-primary/60 shadow-md ring-1 ring-primary/20 ${statusStyle.ring}` : statusStyle.border,
      ].join(' ')}
    >
      <Handle type="target" position={Position.Left} className="!h-2.5 !w-2.5 !border-2 !border-background !bg-primary" />
      <Handle type="source" position={Position.Right} className="!h-2.5 !w-2.5 !border-2 !border-background !bg-primary" />
      <div className="flex items-center gap-2">
        <div className={cn('flex size-12 items-center justify-center border', appearance.iconWrap)}>
          <DeviceIcon vendor={data.vendor} hostname={data.hostname} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12px] font-bold leading-none tracking-tight text-black">{data.hostname}</p>
          <div className="mt-0.5 flex flex-col gap-0.5">
            <span className={cn('inline-flex w-fit items-center rounded-full px-1.5 py-0.5 text-[9px] font-semibold leading-none text-black', appearance.badge)}>
              {appearance.label}
            </span>
            {typeLabel ? (
              <span className="inline-flex w-fit items-center rounded-full bg-muted px-1.5 py-0.5 text-[9px] font-semibold leading-none text-black/90">
                {typeLabel}
              </span>
            ) : null}
            {data.kind ? (
              <span className="inline-flex w-fit items-center rounded-full bg-muted px-1.5 py-0.5 text-[9px] font-semibold leading-none text-black/90">
                {data.kind}
              </span>
            ) : null}
            <span className={cn('inline-flex w-fit items-center gap-1 rounded-full px-1.5 py-0.5 text-[9px] font-semibold leading-none text-black', statusStyle.badge)}>
              <span className={cn('size-1.5 rounded-full', statusStyle.dot)} />
              {statusLabel}
            </span>
          </div>
          {data.ip && data.ip.trim() !== '-' ? (
            <p className="mt-0.5 truncate font-mono text-[9px] font-semibold leading-none text-black">{data.ip}</p>
          ) : null}
        </div>
      </div>
    </div>
  )
}

const NODE_TYPES = {
  device: DeviceNode,
}

function autoLayout(topology: Topology): Record<string, NodePosition> {
  const { nodes, links } = topology
  if (nodes.length === 0) return {}

  const connCount: Record<string, number> = {}
  for (const n of nodes) connCount[n.id] = 0
  for (const l of links) {
    connCount[l.source] = (connCount[l.source] || 0) + 1
    connCount[l.target] = (connCount[l.target] || 0) + 1
  }

  const routers: TopoNode[] = []
  const switches: TopoNode[] = []
  const endpoints: TopoNode[] = []

  for (const n of nodes) {
    const conns = connCount[n.id] || 0
    if ((n.vendor === 'cisco' || n.vendor === 'mikrotik') && conns >= 2) {
      routers.push(n)
    } else if (conns >= 2) {
      switches.push(n)
    } else {
      endpoints.push(n)
    }
  }

  const core = routers.length > 0 ? routers : switches.length > 0 ? switches : nodes.slice(0, Math.ceil(nodes.length / 2))
  const edge = routers.length > 0 || switches.length > 0
    ? nodes.filter(n => !core.find(c => c.id === n.id))
    : nodes.slice(Math.ceil(nodes.length / 2))

  const positions: Record<string, NodePosition> = {}
  const X_GAP = 300
  const Y_GAP = 140

  const coreX = Math.floor(core.length / 2) * X_GAP
  core.forEach((n, i) => {
    positions[n.id] = { x: coreX, y: i * Y_GAP }
  })

  const coreMap = new Map(core.map(c => [c.id, c]))
  const leftEdge: TopoNode[] = []
  const rightEdge: TopoNode[] = []

  for (const n of edge) {
    const linkedCore = links
      .filter(l => l.source === n.id || l.target === n.id)
      .map(l => l.source === n.id ? l.target : l.source)
      .find(id => coreMap.has(id))

    if (linkedCore) {
      if (leftEdge.length <= rightEdge.length) {
        leftEdge.push(n)
      } else {
        rightEdge.push(n)
      }
    } else {
      rightEdge.push(n)
    }
  }

  leftEdge.forEach((n, i) => {
    const linkedCore = links
      .filter(l => l.source === n.id || l.target === n.id)
      .map(l => l.source === n.id ? l.target : l.source)
      .find(id => coreMap.has(id))
    const coreY = linkedCore ? positions[linkedCore]?.y ?? 0 : i * Y_GAP
    positions[n.id] = { x: -X_GAP, y: coreY + (i % 2 === 0 ? 0 : Y_GAP * 0.4) }
  })

  rightEdge.forEach((n, i) => {
    const linkedCore = links
      .filter(l => l.source === n.id || l.target === n.id)
      .map(l => l.source === n.id ? l.target : l.source)
      .find(id => coreMap.has(id))
    const coreY = linkedCore ? positions[linkedCore]?.y ?? 0 : i * Y_GAP
    positions[n.id] = { x: X_GAP, y: coreY + (i % 2 === 0 ? 0 : Y_GAP * 0.4) }
  })

  let fallbackIdx = 0
  for (const n of nodes) {
    if (!positions[n.id]) {
      positions[n.id] = { x: (fallbackIdx % 4) * X_GAP, y: Math.floor(fallbackIdx / 4) * Y_GAP }
      fallbackIdx++
    }
  }

  return positions
}

function readSavedPositions(storageKey?: string): Record<string, NodePosition> | null {
  if (!storageKey || typeof window === 'undefined') return null

  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) return null

    const parsed = JSON.parse(raw) as Record<string, NodePosition>
    return Object.fromEntries(
      Object.entries(parsed).filter(([, position]) => {
        return (
          position !== null &&
          typeof position === 'object' &&
          typeof position.x === 'number' &&
          typeof position.y === 'number'
        )
      })
    )
  } catch {
    return null
  }
}

function savePositions(storageKey: string, positions: Record<string, NodePosition>) {
  if (typeof window === 'undefined') return false

  try {
    window.localStorage.setItem(storageKey, JSON.stringify(positions))
    return true
  } catch {
    return false
  }
}

export const TopologyCanvas = forwardRef<TopologyCanvasHandle, TopologyCanvasProps>(function TopologyCanvas(
  { topology, builder: _builder = false, storageKey },
  ref
) {
  const builder = _builder
  const savedPositions = useMemo(() => readSavedPositions(storageKey), [storageKey])
  const positions = useMemo(() => {
    const base = autoLayout(topology)
    const layoutPositions = topology.layout ?? {}
    const merged = { ...base, ...layoutPositions }
    if (!builder && !savedPositions) return merged

    for (const node of topology.nodes) {
      const saved = savedPositions?.[node.id]
      if (saved) merged[node.id] = saved
    }

    return merged
  }, [builder, savedPositions, topology])

  const initialNodes = useMemo<Node[]>(
    () =>
      topology.nodes.map((node) => ({
        id: node.id,
        position: positions[node.id] ?? { x: 0, y: 0 },
        draggable: builder,
        data: {
          hostname: node.hostname,
          ip: node.ip,
          vendor: node.vendor,
          nodeType: node.nodeType,
          status: node.status,
        },
        type: 'device',
      })),
    [topology.nodes, positions]
  )

  const initialEdges = useMemo<Edge[]>(
    () =>
      topology.links.map((link) => ({
        id: link.id,
        source: link.source,
        target: link.target,
        label: `${link.sourceInterface} / ${link.targetInterface}`,
        animated: link.status === 'up',
        markerEnd: { type: MarkerType.ArrowClosed },
        style: {
          stroke: link.status === 'up' ? 'var(--color-primary)' : 'var(--color-destructive)',
          strokeWidth: 2,
        },
        labelStyle: {
          fill: '#000000',
          fontSize: 11,
          fontWeight: 700,
        },
      })),
    [topology.links]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const persistLayout = () => {
    if (!builder || !storageKey) return false

    const nextPositions = Object.fromEntries(
      nodes.map((node) => [
        node.id,
        {
          x: Math.round(node.position.x),
          y: Math.round(node.position.y),
        },
      ])
    )

    return savePositions(storageKey, nextPositions)
  }

  useImperativeHandle(
  ref,
  () => ({
    saveLayout: persistLayout,
    exportLayout: () =>
      Object.fromEntries(
        nodes.map((node) => [
          node.id,
          {
            x: Math.round(node.position.x),
            y: Math.round(node.position.y),
          },
        ])
      ),
  }),
  [builder, nodes, storageKey]
)

  useEffect(() => {
    setNodes(initialNodes)
  }, [initialNodes, setNodes])

  useEffect(() => {
    setEdges(initialEdges)
  }, [initialEdges, setEdges])

  return (
    <div className="h-[36rem] overflow-hidden rounded-lg border border-border bg-muted/20">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        nodesDraggable={builder}
        nodesConnectable={false}
        elementsSelectable={builder}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
      >
        <Background />
        <Controls />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  )
})
