
import { tool } from "@opencode-ai/plugin"
import { apiGet } from "../../src/api-client.js"

export const device_identify = tool({
  description: "Identify the vendor, model, and OS version of a device via SSH",
  args: {
    deviceId: tool.schema.string().describe("Device ID or IP address"),
  },
  async execute(args) {
    const data = await apiGet(`/devices/${args.deviceId}/identify`)
    return JSON.stringify(data)
  },
})
