
import { tool } from "@opencode-ai/plugin"
import { apiPost } from "../../src/api-client.js"

export const config_verify = tool({
  description: "Verify that a change was applied correctly",
  args: {
    planId: tool.schema.string().describe("Plan ID to verify"),
  },
  async execute(args) {
    const data = await apiPost("/config/verify", {
      plan_id: args.planId,
    })
    return JSON.stringify(data)
  },
})
