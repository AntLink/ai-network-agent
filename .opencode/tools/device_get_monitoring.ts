
import { tool } from "@opencode-ai/plugin"
import { apiGet } from "../../src/api-client.js"

export const device_get_monitoring = tool({
  description: "Get real-time monitoring metrics (CPU, memory, interface stats, temperature)",
  args: {
    deviceId: tool.schema.string().describe("Device ID"),
    metrics: tool.schema.array(tool.schema.string()).optional().describe("List of metrics to collect"),
  },
  async execute(args) {
    const params = args.metrics ? `?metrics=${args.metrics.join(",")}` : ""
    const data = await apiGet(`/devices/${args.deviceId}/monitoring${params}`)
    return JSON.stringify(data)
  },
})
