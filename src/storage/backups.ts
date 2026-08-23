import { promises as fs } from "node:fs"
import path from "node:path"
export async function saveBackup(name: string, content: string) {
  const dir = path.resolve("backups"); await fs.mkdir(dir,{recursive:true});
  const file = path.join(dir, name); await fs.writeFile(file, content, "utf8"); return file;
}
