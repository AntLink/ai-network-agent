export function parseOsRelease(output) {
    const result = {};
    for (const line of output.trim().split("\n")) {
        const eqIdx = line.indexOf("=");
        if (eqIdx > 0) {
            const key = line.substring(0, eqIdx).trim().toLowerCase().replace("-", "_");
            const value = line.substring(eqIdx + 1).trim().replace(/^["']|["']$/g, "");
            result[key] = value;
        }
    }
    return result;
}
export function parseUname(output) {
    const parts = output.trim().split(/\s+/);
    return {
        kernel: parts[0] || "",
        hostname: parts[1] || "",
        kernel_release: parts[2] || "",
        kernel_version: parts.slice(3).join(" "),
        machine: parts[4] || "",
        os: parts.slice(5).join(" ") || "",
    };
}
export function parseInterfacesJson(output) {
    try {
        const data = JSON.parse(output);
        return data.map((iface) => ({
            name: iface.ifname,
            index: iface.ifindex,
            flags: iface.flags,
            mtu: iface.mtu,
            state: iface.operstate,
            mac: iface.address,
            ipv4: iface.addr_info
                ?.filter((a) => a.family === "inet")
                .map((a) => ({
                address: `${a.local}/${a.prefixlen}`,
                broadcast: a.broadcast,
            })) || [],
            ipv6: iface.addr_info
                ?.filter((a) => a.family === "inet6")
                .map((a) => ({
                address: `${a.local}/${a.prefixlen}`,
                scope: a.scope,
            })) || [],
        }));
    }
    catch {
        return parseInterfacesRaw(output);
    }
}
export function parseInterfacesRaw(output) {
    const interfaces = [];
    let current = null;
    for (const line of output.trim().split("\n")) {
        const trimmed = line.trim();
        const ifaceMatch = trimmed.match(/^\d+:\s+(\S+?):/);
        if (ifaceMatch) {
            if (current?.name)
                interfaces.push(current);
            current = {
                name: ifaceMatch[1],
                flags: [],
                ipv4: [],
                ipv6: [],
            };
            if (trimmed.includes("UP"))
                current.flags?.push("UP");
            if (trimmed.includes("LOWER_UP"))
                current.flags?.push("LOWER_UP");
            const mtuMatch = trimmed.match(/mtu\s+(\d+)/);
            if (mtuMatch)
                current.mtu = parseInt(mtuMatch[1]);
            const stateMatch = trimmed.match(/state\s+(\S+)/);
            if (stateMatch)
                current.state = stateMatch[1];
        }
        if (current) {
            const linkMatch = trimmed.match(/link\/ether\s+(\S+)/);
            if (linkMatch)
                current.mac = linkMatch[1];
            const inetMatch = trimmed.match(/inet\s+(\S+)/);
            if (inetMatch)
                current.ipv4?.push({ address: inetMatch[1], broadcast: "" });
            const inet6Match = trimmed.match(/inet6\s+(\S+)/);
            if (inet6Match)
                current.ipv6?.push({ address: inet6Match[1], scope: "" });
        }
    }
    if (current?.name)
        interfaces.push(current);
    return interfaces;
}
export function parseRoutesJson(output) {
    try {
        const data = JSON.parse(output);
        return data.map((route) => ({
            destination: route.dst || route.dstaddr || "",
            gateway: route.gateway || "",
            genmask: route.genmask || "",
            flags: route.flags || "",
            metric: route.metric || 0,
            interface: route.dev || "",
        }));
    }
    catch {
        return parseRoutesRaw(output);
    }
}
export function parseRoutesRaw(output) {
    const routes = [];
    for (const line of output.trim().split("\n")) {
        const trimmed = line.trim();
        if (trimmed.startsWith("default")) {
            const parts = trimmed.split(/\s+/);
            routes.push({
                destination: "0.0.0.0/0",
                gateway: parts[1] || "",
                genmask: "",
                flags: "",
                metric: parseInt(parts[3]) || 0,
                interface: parts[4] || "",
            });
        }
        else {
            const parts = trimmed.split(/\s+/);
            if (parts.length >= 6) {
                routes.push({
                    destination: parts[0],
                    gateway: parts[1],
                    genmask: parts[2],
                    flags: parts[3],
                    metric: parseInt(parts[4]) || 0,
                    interface: parts[5],
                });
            }
        }
    }
    return routes;
}
export function identifyVendor(output) {
    const lower = output.toLowerCase();
    if (lower.includes("linux") || lower.includes("debian") || lower.includes("ubuntu") || lower.includes("centos") || lower.includes("rhel")) {
        const kv = {};
        for (const line of output.split("\n")) {
            const eqIdx = line.indexOf("=");
            if (eqIdx > 0) {
                kv[line.substring(0, eqIdx).trim().toLowerCase()] = line.substring(eqIdx + 1).trim().replace(/^["']|["']$/g, "");
            }
        }
        return {
            vendor: "linux",
            platform: kv["id"] || "linux",
            os_version: kv["version_id"] || kv["version"] || "",
            model: kv["pretty_name"] || "",
        };
    }
    return null;
}
