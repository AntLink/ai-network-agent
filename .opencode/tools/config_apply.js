import { tool } from "@opencode-ai/plugin";
import { apiPost } from "../../src/api-client.js";
export const config_apply = tool({
    description: "Apply a configuration plan after approval and policy check",
    args: {
        planId: tool.schema.string().describe("Plan ID from config_plan"),
        approvedBy: tool.schema.string().describe("User who approved the change"),
    },
    async execute(args) {
        const data = await apiPost("/config/apply", {
            plan_id: args.planId,
            approved_by: args.approvedBy,
        });
        return JSON.stringify(data);
    },
});
