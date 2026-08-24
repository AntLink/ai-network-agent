import { tool } from "@opencode-ai/plugin";
import { apiGet } from "../../src/api-client.js";
export const device_get_interfaces = tool({
    description: "Get interface status, IPs, and statistics",
    args: {
        deviceId: tool.schema.string().describe("Device ID"),
    },
    async execute(args) {
        const data = await apiGet(`/devices/${args.deviceId}/interfaces`);
        return JSON.stringify(data);
    },
});
