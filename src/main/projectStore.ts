import { mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { app } from "electron";
import {
  ProjectSchema,
  type Project,
  type ProjectListItem,
  SCHEMA_VERSION
} from "../shared/schemas/index.js";

const PROJECTS_DIR_NAME = "projects";

function getProjectsRoot(): string {
  return join(app.getPath("documents"), "AutoWebTesting", PROJECTS_DIR_NAME);
}

// Convert a user-provided Korean name into a Windows-safe folder name.
// Strips reserved chars and trims. Keeps Korean/letters/digits/dash/underscore.
function sanitizeFolderName(name: string): string {
  const stripped = name
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "")
    .replace(/\s+/g, "-")
    .trim();
  return stripped.length > 0 ? stripped : "untitled";
}

function deriveProjectId(folderName: string): string {
  const safe = folderName
    .toUpperCase()
    .replace(/[^A-Z0-9_]/g, "_")
    .replace(/^_+|_+$/g, "")
    .replace(/_+/g, "_");
  const base = safe.length > 0 ? safe : "PROJECT";
  return base.startsWith("PROJECT_") ? base : `PROJECT_${base}`;
}

async function ensureProjectsRoot(): Promise<string> {
  const root = getProjectsRoot();
  await mkdir(root, { recursive: true });
  return root;
}

const PROJECT_SUBDIRS = [
  "inputs",
  "imports",
  "testcases",
  "dom",
  "execution-plans",
  "runs",
  "reports",
  "logs"
] as const;

async function scaffoldProjectFolders(folderPath: string): Promise<void> {
  for (const sub of PROJECT_SUBDIRS) {
    await mkdir(join(folderPath, sub), { recursive: true });
  }
}

export type CreateProjectRequest = {
  name: string;
  targetUrl?: string;
  environmentType?: Project["environmentType"];
};

export async function createProject(
  request: CreateProjectRequest
): Promise<Project> {
  if (!request.name || request.name.trim().length === 0) {
    throw new Error("프로젝트명을 입력하세요.");
  }
  const root = await ensureProjectsRoot();
  const folderName = sanitizeFolderName(request.name);
  const folderPath = join(root, folderName);

  if (existsSync(folderPath)) {
    throw new Error(`이미 같은 이름의 프로젝트가 존재합니다: ${folderName}`);
  }

  await mkdir(folderPath, { recursive: true });
  await scaffoldProjectFolders(folderPath);

  const project: Project = {
    schemaVersion: SCHEMA_VERSION,
    projectId: deriveProjectId(folderName),
    name: request.name.trim(),
    folderName,
    targetUrl: request.targetUrl,
    createdAt: new Date().toISOString(),
    appVersion: app.getVersion(),
    environmentType: request.environmentType
  };

  // Validate via Zod before writing
  const parsed = ProjectSchema.parse(project);

  await writeFile(
    join(folderPath, "project.json"),
    JSON.stringify(parsed, null, 2),
    "utf8"
  );

  return parsed;
}

export async function listProjects(): Promise<ProjectListItem[]> {
  const root = getProjectsRoot();
  if (!existsSync(root)) {
    return [];
  }
  const entries = await readdir(root, { withFileTypes: true });
  const items: ProjectListItem[] = [];
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const folderPath = join(root, entry.name);
    const projectJsonPath = join(folderPath, "project.json");
    if (!existsSync(projectJsonPath)) continue;
    try {
      const body = await readFile(projectJsonPath, "utf8");
      const project = ProjectSchema.parse(JSON.parse(body));
      items.push({
        projectId: project.projectId,
        name: project.name,
        folderName: project.folderName ?? entry.name,
        folderPath,
        createdAt: project.createdAt,
        lastOpenedAt: project.lastOpenedAt
      });
    } catch {
      // Skip invalid project folder. (TODO: surface as warning)
    }
  }
  // Sort by lastOpenedAt desc, fallback createdAt desc
  items.sort((a, b) => {
    const ta = a.lastOpenedAt ?? a.createdAt;
    const tb = b.lastOpenedAt ?? b.createdAt;
    return tb.localeCompare(ta);
  });
  return items;
}

export type OpenProjectRequest = {
  folderName: string;
};

export async function openProject(
  request: OpenProjectRequest
): Promise<Project> {
  const root = getProjectsRoot();
  const folderPath = join(root, request.folderName);
  const projectJsonPath = join(folderPath, "project.json");
  if (!existsSync(projectJsonPath)) {
    throw new Error(`프로젝트를 찾을 수 없습니다: ${request.folderName}`);
  }
  const body = await readFile(projectJsonPath, "utf8");
  const project = ProjectSchema.parse(JSON.parse(body));

  // Touch lastOpenedAt
  const updated: Project = {
    ...project,
    lastOpenedAt: new Date().toISOString()
  };
  const validated = ProjectSchema.parse(updated);
  await writeFile(projectJsonPath, JSON.stringify(validated, null, 2), "utf8");
  return validated;
}

export function getProjectFolderPath(folderName: string): string {
  return join(getProjectsRoot(), folderName);
}

// Re-exported for the IPC layer (so existing code keeps using a single import surface)
export { getProjectsRoot };
