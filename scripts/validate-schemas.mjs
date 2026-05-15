// Validates docs/schemas/*.schema.json + docs/examples/*.sample.json + src/shared/schemas/*.ts (Zod)
// per ADR-006: JSON Schema is human contract, Zod is runtime/TS source.
// Both must accept the same sample JSONs.

import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join, basename, extname } from "node:path";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const __filename = fileURLToPath(import.meta.url);
const projectRoot = dirname(dirname(__filename));
const docsSchemaDir = join(projectRoot, "docs", "schemas");
const docsExampleDir = join(projectRoot, "docs", "examples");

let errors = 0;
const log = (ok, msg) => {
  if (ok) {
    console.log(`  ok    ${msg}`);
  } else {
    console.error(`  FAIL  ${msg}`);
    errors += 1;
  }
};

// === Step 1: parse all JSON Schema files ===
console.log("\n[1] docs/schemas/*.schema.json — JSON Schema parse + ajv compile");
const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);

const schemaFiles = (await readdir(docsSchemaDir)).filter((f) => f.endsWith(".schema.json"));
const compiledByName = new Map();

for (const file of schemaFiles) {
  try {
    const body = await readFile(join(docsSchemaDir, file), "utf8");
    const json = JSON.parse(body);
    const validate = ajv.compile(json);
    const name = basename(file, ".schema.json");
    compiledByName.set(name, validate);
    log(true, file);
  } catch (e) {
    log(false, `${file} — ${e.message}`);
  }
}

// === Step 2: validate examples against JSON Schema ===
console.log("\n[2] docs/examples/*.sample.json — JSON Schema validation");
const exampleFiles = (await readdir(docsExampleDir)).filter((f) => f.endsWith(".sample.json"));

if (exampleFiles.length === 0) {
  console.warn("  (no examples found)");
}

for (const file of exampleFiles) {
  const name = basename(file, ".sample.json");
  const validate = compiledByName.get(name);
  if (!validate) {
    log(false, `${file} — no matching schema (${name}.schema.json)`);
    continue;
  }
  const body = await readFile(join(docsExampleDir, file), "utf8");
  const data = JSON.parse(body);
  const ok = validate(data);
  if (ok) {
    log(true, `${file} ↔ JSON Schema`);
  } else {
    log(false, `${file} — ${JSON.stringify(validate.errors?.slice(0, 3), null, 2)}`);
  }
}

// === Step 3: validate examples against Zod ===
console.log("\n[3] docs/examples/*.sample.json — Zod (src/shared/schemas) validation");

let SCHEMA_REGISTRY;
try {
  const zodMod = await import(
    new URL("../src/shared/schemas/index.ts", import.meta.url).href
  );
  SCHEMA_REGISTRY = zodMod.SCHEMA_REGISTRY;
} catch (e) {
  // Fallback: tsc may not have run yet. Try to import compiled dist if available.
  try {
    const zodMod = await import(
      new URL("../out/main/shared/schemas/index.js", import.meta.url).href
    );
    SCHEMA_REGISTRY = zodMod.SCHEMA_REGISTRY;
  } catch (e2) {
    console.warn(
      "  (skipped) cannot import src/shared/schemas/index.ts directly.\n" +
        "  To enable Zod check, run `npm run build` first or use tsx:\n" +
        "    npx tsx scripts/validate-schemas.mjs"
    );
    SCHEMA_REGISTRY = null;
  }
}

if (SCHEMA_REGISTRY) {
  for (const file of exampleFiles) {
    const name = basename(file, ".sample.json");
    const schema = SCHEMA_REGISTRY[name];
    if (!schema) {
      log(false, `${file} — no matching Zod schema for "${name}"`);
      continue;
    }
    const body = await readFile(join(docsExampleDir, file), "utf8");
    const data = JSON.parse(body);
    const result = schema.safeParse(data);
    if (result.success) {
      log(true, `${file} ↔ Zod`);
    } else {
      log(
        false,
        `${file} — Zod issues: ${JSON.stringify(
          result.error.issues.slice(0, 3),
          null,
          2
        )}`
      );
    }
  }
}

// === Final report ===
console.log("");
if (errors > 0) {
  console.error(`✗ schema:check FAILED — ${errors} issue(s)`);
  process.exit(1);
} else {
  console.log("✓ schema:check passed");
}
