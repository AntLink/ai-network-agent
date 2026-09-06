import { tool } from "@opencode-ai/plugin";
import { apiPost } from "../../src/api-client.js";
export const config_plan = tool({
    description: "Generate a configuration change plan for a device",
    args: {
        deviceId: tool.schema.string().describe("Device ID"),
        commands: tool.schema.array(tool.schema.string()).describe("Proposed commands in vendor syntax"),
        description: tool.schema.string().optional().describe("Human-readable description of the change"),
    },
    async execute(args) {
        const data = await apiPost("/config/plan", {
            device_id: args.deviceId,
            commands: args.commands,
            description: args.description || "",
        });
        return JSON.stringify(data);
    },
});
