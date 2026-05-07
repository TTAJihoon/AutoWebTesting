import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const schemaDir = fileURLToPath(new URL("../schemas/", import.meta.url));
const files = (await readdir(schemaDir)).filter((file) => file.endsWith(".json"));

for (const file of files) {
  const body = await readFile(join(schemaDir, file), "utf8");
  JSON.parse(body);
  console.log(`ok ${file}`);
}
