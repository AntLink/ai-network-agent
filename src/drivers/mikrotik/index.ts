import { runSshCommand, SshTarget } from "../../transports/ssh.js"
import {
  parseSystemResource,
  parseSystemIdentity,
  parseInterfaces,
  parseRoutes,
  parseVlans,
  parseConfig,
  identifyVendor,
} from "../../parsers/mikrotik.js"

export interface MikroTikDevice {
  id: string
  hostname: string
  management_address: string
  vendor: string
  platform: string
  transport: string
  credential_ref: string
}

function resolveCredentials(device: MikroTikDevice): SshTarget {
  const prefix = device.id.toUpperCase().replace(/-/g, "_")
  const username = process.env[`${prefix}_USERNAME`] || process.env.NETWORK_USERNAME || "admin"
  const password = process.env[`${prefix}_PASSWORD`] || process.env.NETWORK_PASSWORD

  return {
    host: device.management_address,
    port: 22,
    username,
    password,
  }
}

export async function identify(device: MikroTikDevice) {
  const target = resolveCredentials(device)
  const resource = await runSshCommand(target, "/system resource print")
  const identity = await runSshCommand(target, "/system identity print")
  const detected = identifyVendor(resource + "\n" + identity)
  return {
    vendor: detected?.vendor || "unknown",
    platform: detected?.platform || "unknown",
    os_version: detected?.os_version || "",
    model: detected?.model || "",
    identity: parseSystemIdentity(identity),
    resource: parseSystemResource(resource),
  }
}

export async function getFacts(device: MikroTikDevice) {
  const target = resolveCredentials(device)
  const resource = await runSshCommand(target, "/system resource print")
  const identity = await runSshCommand(target, "/system identity print")
  return {
    identity: parseSystemIdentity(identity),
    resource: parseSystemResource(resource),
  }
}

export async function getInterfaces(device: MikroTikDevice) {
  const target = resolveCredentials(device)
  const output = await runSshCommand(target, "/interface print detail without-paging")
  return parseInterfaces(output)
}

export async function getRoutes(device: MikroTikDevice) {
  const target = resolveCredentials(device)
  const output = await runSshCommand(target, "/ip route print detail without-paging")
  return parseRoutes(output)
}

export async function getVlans(device: MikroTikDevice) {
  const target = resolveCredentials(device)
  const output = await runSshCommand(target, "/interface vlan print detail without-paging")
  return parseVlans(output)
}

export async function getConfig(device: MikroTikDevice) {
  const target = resolveCredentials(device)
  const output = await runSshCommand(target, "/export terse")
  return parseConfig(output)
}

export async function backup(device: MikroTikDevice) {
  const target = resolveCredentials(device)
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
  const backupName = `backup-${timestamp}`
  await runSshCommand(target, `/export file=${backupName}`)
  return { backup_name: backupName }
}

export async function applyCommands(device: MikroTikDevice, commands: string[]) {
  const target = resolveCredentials(device)
  const outputs: string[] = []
  for (const command of commands) {
    const output = await runSshCommand(target, command)
    outputs.push(output)
  }
  return { success: true, outputs }
}

export const mikrotikDriver = {
  vendor: "mikrotik",
  platform: "routeros",
  identify,
  getFacts,
  getInterfaces,
  getRoutes,
  getVlans,
  getConfig,
  backup,
  applyCommands,
}
