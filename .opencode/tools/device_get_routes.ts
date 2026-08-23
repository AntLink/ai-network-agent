
import { tool } from "@opencode-ai/plugin"
import { apiGet } from "../../src/api-client.js"

export const device_get_routes = tool({
  description: "Get the IPv4/IPv6 routing table",
  args: {
    deviceId: tool.schema.string().describe("Device ID"),
  },
  async execute(args) {
    const data = await apiGet(`/devices/${args.deviceId}/routes`)
    return JSON.stringify(data)
  },
})
