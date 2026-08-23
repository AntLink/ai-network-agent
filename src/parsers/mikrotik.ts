export interface ParsedRow {
  [key: string]: string
}

export interface SystemResource {
  uptime: string
  version: string
  build_time: string
  free_memory: string
  total_memory: string
  cpu: string
  cpu_count: string
  cpu_frequency: string
  free_disk: string
  total_disk: string
  board_name: string
  architecture: string
}

export interface SystemIdentity {
  name: string
}

export interface Interface {
  name: string
  type: string
  mtu: string
  mac_address: string
  status: string
  tx_rate: string
  rx_rate: string
  tx_bytes: string
  rx_bytes: string
  tx_packets: string
  rx_packets: string
  tx_errors: string
  rx_errors: string
  tx_drops: string
  rx_drops: string
  last_link_up: string
  last_link_down: string
  speed: string
}

export interface Route {
  dst_address: string
  gateway: string
  distance: string
  pref_src: string
  routing_table: string
  check_gateway: string
  scope: string
  target_scope: string
  bgp_communities: string
  immediate_gw: string
}

export interface Vlan {
  name: string
  vlan_id: string
  interface: string
  mtu: string
  mac_address: string
  tx_bytes: string
  rx_bytes: string
  tx_packets: string
  rx_packets: string
}

export function parseTable(output: string): ParsedRow[] {
  const lines = output.trim().split("\n").filter(l => l.trim())
  if (lines.length < 2) return []

  const rows: ParsedRow[] = []
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith("Columns:") || trimmed.startsWith("#")) continue

    const row: ParsedRow = {}
    const parts = trimmed.split(/\s{2,}/)
    for (const part of parts) {
      const eqIdx = part.indexOf("=")
      if (eqIdx > 0) {
        const key = part.substring(0, eqIdx).trim()
        const value = part.substring(eqIdx + 1).trim()
        row[key] = value
      }
    }
    if (Object.keys(row).length > 0) rows.push(row)
  }
  return rows
}

export function parseKeyValue(output: string): Record<string, string> {
  const result: Record<string, string> = {}
  for (const line of output.trim().split("\n")) {
    const eqIdx = line.indexOf("=")
    if (eqIdx > 0) {
      const key = line.substring(0, eqIdx).trim()
      const value = line.substring(eqIdx + 1).trim()
      result[key] = value
    }
  }
  return result
}

export function parseSystemResource(output: string): SystemResource {
  const kv = parseKeyValue(output)
  return {
    uptime: kv["uptime"] || "",
    version: kv["version"] || "",
    build_time: kv["build-time"] || "",
    free_memory: kv["free-memory"] || "",
    total_memory: kv["total-memory"] || "",
    cpu: kv["cpu"] || "",
    cpu_count: kv["cpu-count"] || "",
    cpu_frequency: kv["cpu-frequency"] || "",
    free_disk: kv["free-disk"] || "",
    total_disk: kv["total-disk"] || "",
    board_name: kv["board-name"] || "",
    architecture: kv["architecture-name"] || "",
  }
}

export function parseSystemIdentity(output: string): SystemIdentity {
  const kv = parseKeyValue(output)
  return { name: kv["name"] || "" }
}

export function parseInterfaces(output: string): Interface[] {
  const lines = output.trim().split("\n").filter(l => l.trim())
  const interfaces: Interface[] = []

  let current: Partial<Interface> | null = null
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith("Flags:") || trimmed.startsWith("Columns:")) continue

    if (trimmed.startsWith("*") || (!trimmed.startsWith(" ") && !trimmed.startsWith("\t"))) {
      if (current?.name) interfaces.push(current as Interface)
      current = {}
      const parts = trimmed.split(/\s+/)
      if (parts.length >= 2) {
        current.name = parts[1] || parts[0].replace("*", "")
      }
    }

    if (current) {
      const kv = parseKeyValue(trimmed)
      Object.assign(current, kv)

      const flagLine = trimmed
      if (flagLine.includes("R ") || flagLine.includes(" running")) current.status = "running"
      if (flagLine.includes("S ") || flagLine.includes(" slave")) current.type = current.type || "slave"
      if (flagLine.includes("switch")) current.type = "switch"
      if (flagLine.includes("wlan")) current.type = "wlan"
      if (flagLine.includes("vlan")) current.type = "vlan"
      if (flagLine.includes("bridge")) current.type = "bridge"
    }
  }
  if (current?.name) interfaces.push(current as Interface)
  return interfaces
}

export function parseRoutes(output: string): Route[] {
  const rows = parseTable(output)
  return rows.map(r => ({
    dst_address: r["DST-ADDRESS"] || r["dst-address"] || "",
    gateway: r["GATEWAY"] || r["gateway"] || "",
    distance: r["DISTANCE"] || r["distance"] || "",
    pref_src: r["Pref.Src"] || r["pref-src"] || "",
    routing_table: r["ROUTING-TABLE"] || r["routing-table"] || "",
    check_gateway: r["CHECK-GATEWAY"] || r["check-gateway"] || "",
    scope: r["SCOPE"] || r["scope"] || "",
    target_scope: r["TARGET-SCOPE"] || r["target-scope"] || "",
    bgp_communities: r["BGP-COMMUNITIES"] || r["bgp-communities"] || "",
    immediate_gw: r["immediate-gw"] || "",
  }))
}

export function parseVlans(output: string): Vlan[] {
  const rows = parseTable(output)
  return rows.map(r => ({
    name: r["NAME"] || r["name"] || "",
    vlan_id: r["VLAN-ID"] || r["vlan-id"] || "",
    interface: r["INTERFACE"] || r["interface"] || "",
    mtu: r["MTU"] || r["mtu"] || "",
    mac_address: r["MAC-ADDRESS"] || r["mac-address"] || "",
    tx_bytes: r["TX-BYTE"] || r["tx-byte"] || "",
    rx_bytes: r["RX-BYTE"] || r["rx-byte"] || "",
    tx_packets: r["TX-PACKET"] || r["tx-packet"] || "",
    rx_packets: r["RX-PACKET"] || r["rx-packet"] || "",
  }))
}

export function parseConfig(output: string): string {
  return output.trim()
}

export function identifyVendor(output: string): { vendor: string; platform: string; os_version: string; model: string } | null {
  const lower = output.toLowerCase()
  if (lower.includes("routeros") || lower.includes("mikrotik") || lower.includes("routerboard")) {
    const kv = parseKeyValue(output)
    return {
      vendor: "mikrotik",
      platform: "routeros",
      os_version: kv["version"] || kv["version-number"] || "",
      model: kv["board-name"] || "",
    }
  }
  return null
}
