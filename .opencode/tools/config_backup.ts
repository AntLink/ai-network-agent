
import { tool } from "@opencode-ai/plugin"
import { apiPost } from "../../src/api-client.js"

export const config_backup = tool({
  description: "Create a backup of the current device configuration",
  args: {
    deviceId: tool.schema.string().describe("Device ID"),
    label: tool.schema.string().optional().describe("Optional backup label (e.g., before-change)"),
  },
  async execute(args) {
    const data = await apiPost("/config/backup", {
      device_id: args.deviceId,
      label: args.label || "",
    })
    return JSON.stringify(data)
  },
})
