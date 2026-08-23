import { promises as fs } from "node:fs"
export async function appendAudit(event: unknown) { await fs.mkdir("logs",{recursive:true}); await fs.appendFile("logs/audit.log", JSON.stringify(event)+"\n") }
