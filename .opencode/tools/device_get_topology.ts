
import { tool } from "@opencode-ai/plugin"
import { apiGet } from "../../src/api-client.js"

export const device_get_topology = tool({
  description: "Get LLDP/CDP neighbor information",
  args: {
    deviceId: tool.schema.string().describe("Device ID"),
    protocol: tool.schema.string().optional().describe("Protocol to use (lldp or cdp)"),
  },
  async execute(args) {
    const params = args.protocol ? `?protocol=${args.protocol}` : ""
    const data = await apiGet(`/devices/${args.deviceId}/topology${params}`)
    return JSON.stringify(data)
  },
})
