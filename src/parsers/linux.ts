export interface OsRelease {
  name: string
  version: string
  id: string
  id_like: string
  version_id: string
  pretty_name: string
  home_url: string
  bug_report_url: string
}

export interface UnameInfo {
  kernel: string
  hostname: string
  kernel_release: string
  kernel_version: string
  machine: string
  os: string
}

export interface InterfaceInfo {
  name: string
  index: number
  flags: string[]
  mtu: number
  state: string
  mac: string
  ipv4: { address: string; broadcast: string }[]
  ipv6: { address: string; scope: string }[]
}

export interface RouteInfo {
  destination: string
  gateway: string
  genmask: string
  flags: string
  metric: number
  interface: string
}

export function parseOsRelease(output: string): OsRelease {
  const result: Partial<OsRelease> = {}
  for (const line of output.trim().split("\n")) {
    const eqIdx = line.indexOf("=")
    if (eqIdx > 0) {
      const key = line.substring(0, eqIdx).trim().toLowerCase().replace("-", "_")
      const value = line.substring(eqIdx + 1).trim().replace(/^["']|["']$/g, "")
      ;(result as Record<string, string>)[key] = value
    }
  }
  return result as OsRelease
}

export function parseUname(output: string): UnameInfo {
  const parts = output.trim().split(/\s+/)
  return {
    kernel: parts[0] || "",
    hostname: parts[1] || "",
    kernel_release: parts[2] || "",
    kernel_version: parts.slice(3).join(" "),
    machine: parts[4] || "",
    os: parts.slice(5).join(" ") || "",
  }
}

export function parseInterfacesJson(output: string): InterfaceInfo[] {
  try {
    const data = JSON.parse(output)
    return data.map((iface: Record<string, unknown>) => ({
      name: iface.ifname as string,
      index: iface.ifindex as number,
      flags: iface.flags as string[],
      mtu: iface.mtu as number,
      state: iface.operstate as string,
      mac: iface.address as string,
      ipv4: (iface.addr_info as Record<string, unknown>[])
        ?.filter((a: Record<string, unknown>) => a.family === "inet")
        .map((a: Record<string, unknown>) => ({
          address: `${a.local}/${a.prefixlen}`,
          broadcast: a.broadcast as string,
        })) || [],
      ipv6: (iface.addr_info as Record<string, unknown>[])
        ?.filter((a: Record<string, unknown>) => a.family === "inet6")
        .map((a: Record<string, unknown>) => ({
          address: `${a.local}/${a.prefixlen}`,
          scope: a.scope as string,
        })) || [],
    }))
  } catch {
    return parseInterfacesRaw(output)
  }
}

export function parseInterfacesRaw(output: string): InterfaceInfo[] {
  const interfaces: InterfaceInfo[] = []
  let current: Partial<InterfaceInfo> | null = null

  for (const line of output.trim().split("\n")) {
    const trimmed = line.trim()
    const ifaceMatch = trimmed.match(/^\d+:\s+(\S+?):/)
    if (ifaceMatch) {
      if (current?.name) interfaces.push(current as InterfaceInfo)
      current = {
        name: ifaceMatch[1],
        flags: [],
        ipv4: [],
        ipv6: [],
      }
      if (trimmed.includes("UP")) current.flags?.push("UP")
      if (trimmed.includes("LOWER_UP")) current.flags?.push("LOWER_UP")
      const mtuMatch = trimmed.match(/mtu\s+(\d+)/)
      if (mtuMatch) current.mtu = parseInt(mtuMatch[1])
      const stateMatch = trimmed.match(/state\s+(\S+)/)
      if (stateMatch) current.state = stateMatch[1]
    }
    if (current) {
      const linkMatch = trimmed.match(/link\/ether\s+(\S+)/)
      if (linkMatch) current.mac = linkMatch[1]
      const inetMatch = trimmed.match(/inet\s+(\S+)/)
      if (inetMatch) current.ipv4?.push({ address: inetMatch[1], broadcast: "" })
      const inet6Match = trimmed.match(/inet6\s+(\S+)/)
      if (inet6Match) current.ipv6?.push({ address: inet6Match[1], scope: "" })
    }
  }
  if (current?.name) interfaces.push(current as InterfaceInfo)
  return interfaces
}

export function parseRoutesJson(output: string): RouteInfo[] {
  try {
    const data = JSON.parse(output)
    return data.map((route: Record<string, unknown>) => ({
      destination: route.dst as string || route.dstaddr as string || "",
      gateway: route.gateway as string || "",
      genmask: route.genmask as string || "",
      flags: route.flags as string || "",
      metric: route.metric as number || 0,
      interface: route.dev as string || "",
    }))
  } catch {
    return parseRoutesRaw(output)
  }
}

export function parseRoutesRaw(output: string): RouteInfo[] {
  const routes: RouteInfo[] = []
  for (const line of output.trim().split("\n")) {
    const trimmed = line.trim()
    if (trimmed.startsWith("default")) {
      const parts = trimmed.split(/\s+/)
      routes.push({
        destination: "0.0.0.0/0",
        gateway: parts[1] || "",
        genmask: "",
        flags: "",
        metric: parseInt(parts[3]) || 0,
        interface: parts[4] || "",
      })
    } else {
      const parts = trimmed.split(/\s+/)
      if (parts.length >= 6) {
        routes.push({
          destination: parts[0],
          gateway: parts[1],
          genmask: parts[2],
          flags: parts[3],
          metric: parseInt(parts[4]) || 0,
          interface: parts[5],
        })
      }
    }
  }
  return routes
}

export function identifyVendor(output: string): { vendor: string; platform: string; os_version: string; model: string } | null {
  const lower = output.toLowerCase()
  if (lower.includes("linux") || lower.includes("debian") || lower.includes("ubuntu") || lower.includes("centos") || lower.includes("rhel")) {
    const kv: Record<string, string> = {}
    for (const line of output.split("\n")) {
      const eqIdx = line.indexOf("=")
      if (eqIdx > 0) {
        kv[line.substring(0, eqIdx).trim().toLowerCase()] = line.substring(eqIdx + 1).trim().replace(/^["']|["']$/g, "")
      }
    }
    return {
      vendor: "linux",
      platform: kv["id"] || "linux",
      os_version: kv["version_id"] || kv["version"] || "",
      model: kv["pretty_name"] || "",
    }
  }
  return null
}
