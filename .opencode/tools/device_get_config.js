import { tool } from "@opencode-ai/plugin";
import { apiGet } from "../../src/api-client.js";
export const device_get_config = tool({
    description: "Get the running configuration of a device",
    args: {
        deviceId: tool.schema.string().describe("Device ID"),
        section: tool.schema.string().optional().describe("Optional config section (e.g., 'interface', 'vlan')"),
    },
    async execute(args) {
        const params = args.section ? `?section=${args.section}` : "";
        const data = await apiGet(`/devices/${args.deviceId}/config${params}`);
        return JSON.stringify(data);
    },
});
