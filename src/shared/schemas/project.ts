import { z } from "zod";
import { EnvironmentTypeSchema, SchemaVersionSchema } from "./common.js";

export const ProjectIdSchema = z
  .string()
  .regex(/^PROJECT_[A-Z0-9_]+$/, "projectId 형식: PROJECT_{대문자영숫자언더스코어}");

export const ProjectSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    projectId: ProjectIdSchema,
    name: z.string().min(1),
    folderName: z.string().optional(),
    targetUrl: z.string().url().optional(),
    createdAt: z.string().datetime({ offset: true }),
    lastOpenedAt: z.string().datetime({ offset: true }).optional(),
    testDataProfileId: z.string().optional(),
    riskPolicyId: z.string().optional(),
    appVersion: z.string().optional(),
    environmentType: EnvironmentTypeSchema.optional()
  })
  .strict();
export type Project = z.infer<typeof ProjectSchema>;

export const ProjectListItemSchema = z
  .object({
    projectId: ProjectIdSchema,
    name: z.string().min(1),
    folderName: z.string(),
    folderPath: z.string(),
    createdAt: z.string().datetime({ offset: true }),
    lastOpenedAt: z.string().datetime({ offset: true }).optional()
  })
  .strict();
export type ProjectListItem = z.infer<typeof ProjectListItemSchema>;
