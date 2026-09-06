import { tool } from "@opencode-ai/plugin";
import { apiPost } from "../../src/api-client.js";
export const config_validate = tool({
    description: "Validate a configuration plan without applying it (dry-run)",
    args: {
        planId: tool.schema.string().describe("Plan ID from config_plan"),
    },
    async execute(args) {
        const data = await apiPost("/config/validate", {
            plan_id: args.planId,
        });
        return JSON.stringify(data);
    },
});
