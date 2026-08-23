
import { tool } from "@opencode-ai/plugin"
import { apiGet } from "../../src/api-client.js"

export const device_get_vlans = tool({
  description: "Get VLAN database and port memberships",
  args: {
    deviceId: tool.schema.string().describe("Device ID"),
  },
  async execute(args) {
    const data = await apiGet(`/devices/${args.deviceId}/vlans`)
    return JSON.stringify(data)
  },
})
