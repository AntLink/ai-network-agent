
import { tool } from "@opencode-ai/plugin"
import { apiGet } from "../../src/api-client.js"

export const device_get_facts = tool({
  description: "Get device facts (model, version, uptime, resources)",
  args: {
    deviceId: tool.schema.string().describe("Device ID"),
  },
  async execute(args) {
    const data = await apiGet(`/devices/${args.deviceId}/facts`)
    return JSON.stringify(data)
  },
})
