import { tool } from "@opencode-ai/plugin";
import { apiPost } from "../../src/api-client.js";
export const config_rollback = tool({
    description: "Rollback to a previous configuration backup",
    args: {
        deviceId: tool.schema.string().describe("Device ID"),
        backupId: tool.schema.string().describe("Backup ID from config_backup"),
    },
    async execute(args) {
        const data = await apiPost("/config/rollback", {
            device_id: args.deviceId,
            backup_id: args.backupId,
        });
        return JSON.stringify(data);
    },
});
