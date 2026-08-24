import { runSshCommand } from "../../transports/ssh.js";
import { parseOsRelease, parseUname, parseInterfacesJson, parseRoutesJson, identifyVendor, } from "../../parsers/linux.js";
function resolveCredentials(device) {
    const prefix = device.id.toUpperCase().replace(/-/g, "_");
    const username = process.env[`${prefix}_USERNAME`] || process.env.NETWORK_USERNAME || "root";
    const password = process.env[`${prefix}_PASSWORD`] || process.env.NETWORK_PASSWORD;
    const port = parseInt(process.env[`${prefix}_SSH_PORT`] || "22");
    return {
        host: device.management_address,
        port,
        username,
        password,
    };
}
export async function identify(device) {
    const target = resolveCredentials(device);
    const osRelease = await runSshCommand(target, "cat /etc/os-release");
    const uname = await runSshCommand(target, "uname -a");
    const detected = identifyVendor(osRelease + "\n" + uname);
    return {
        vendor: detected?.vendor || "unknown",
        platform: detected?.platform || "unknown",
        os_version: detected?.os_version || "",
        model: detected?.model || "",
        os_release: parseOsRelease(osRelease),
        uname: parseUname(uname),
    };
}
export async function getFacts(device) {
    const target = resolveCredentials(device);
    const osRelease = await runSshCommand(target, "cat /etc/os-release");
    const uname = await runSshCommand(target, "uname -a");
    const uptime = await runSshCommand(target, "uptime");
    const hostname = await runSshCommand(target, "hostname");
    return {
        os_release: parseOsRelease(osRelease),
        uname: parseUname(uname),
        uptime,
        hostname,
    };
}
export async function getInterfaces(device) {
    const target = resolveCredentials(device);
    const output = await runSshCommand(target, "ip -json addr show");
    return parseInterfacesJson(output);
}
export async function getRoutes(device) {
    const target = resolveCredentials(device);
    const output = await runSshCommand(target, "ip -json route show");
    return parseRoutesJson(output);
}
export async function getConfig(device) {
    const target = resolveCredentials(device);
    const configs = {};
    try {
        configs.interfaces = await runSshCommand(target, "cat /etc/network/interfaces 2>/dev/null || echo 'not found'");
    }
    catch {
        configs.interfaces = "not available";
    }
    try {
        configs.sshd_config = await runSshCommand(target, "cat /etc/ssh/sshd_config 2>/dev/null | head -50 || echo 'not found'");
    }
    catch {
        configs.sshd_config = "not available";
    }
    return configs;
}
export async function applyCommands(device, commands) {
    const target = resolveCredentials(device);
    const outputs = [];
    for (const command of commands) {
        const output = await runSshCommand(target, command);
        outputs.push(output);
    }
    return { success: true, outputs };
}
export const linuxDriver = {
    vendor: "linux",
    platform: "linux",
    identify,
    getFacts,
    getInterfaces,
    getRoutes,
    getConfig,
    applyCommands,
};
