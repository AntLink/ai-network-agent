
import { tool } from "@opencode-ai/plugin"
import { apiPost } from "../../src/api-client.js"

export const policy_check = tool({
  description: "Check if an operation is allowed by policy (authorization, risk, approval)",
  args: {
    deviceId: tool.schema.string().describe("Device ID"),
    operation: tool.schema.string().describe("Operation to check (e.g., 'apply', 'rollback')"),
    riskLevel: tool.schema.string().describe("Risk level: LOW, MEDIUM, HIGH, CRITICAL"),
    planId: tool.schema.string().optional().describe("Plan ID if available"),
  },
  async execute(args) {
    const data = await apiPost("/policy/check", {
      device_id: args.deviceId,
      operation: args.operation,
      risk_level: args.riskLevel,
      plan_id: args.planId,
    })
    return JSON.stringify(data)
  },
})
