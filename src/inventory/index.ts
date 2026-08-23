import { promises as fs } from "node:fs"
export async function loadInventory(file="inventory/devices.json") { return JSON.parse(await fs.readFile(file,"utf8")) }
