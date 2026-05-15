import { z } from "zod";
import {
  EXPLORATION_SESSION_ID_PATTERN,
  EnvironmentTypeSchema,
  SchemaVersionSchema
} from "./common.js";

export const ExplorationModeSchema = z.enum([
  "AI_ASSISTED_EXPLORATION",
  "MANUAL_GUIDED"
]);
export type ExplorationMode = z.infer<typeof ExplorationModeSchema>;

export const LlmModeSchema = z.enum([
  "GPT_WEB_IMPORT",
  "API_MODE",
  "AI_EXPLORATION",
  "MANUAL",
  "GPT_WEB_IMPORT_OR_API_ADAPTER"
]);
export type LlmMode = z.infer<typeof LlmModeSchema>;

// EnvironmentTypeSchema re-exported via common.ts (single definition).
export { EnvironmentTypeSchema };
export type { EnvironmentType } from "./common.js";

export const ExplorationSessionStatusSchema = z.enum([
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
  "FAILED",
  "PAUSED"
]);

export const ExplorationStopReasonSchema = z.enum([
  "MAX_STEPS_REACHED",
  "MAX_PAGE_STATES_REACHED",
  "REPEATED_SCREEN",
  "ONLY_RISKY_CANDIDATES",
  "LOGIN_FAILED",
  "SESSION_EXPIRED",
  "USER_CANCELLED",
  "AI_NO_MORE_CANDIDATES",
  "FATAL_ERROR"
]);

export const ExplorationLimitsSchema = z
  .object({
    maxSteps: z.number().int().min(1).default(50),
    maxPageStates: z.number().int().min(1).default(20),
    maxSameUrlVisits: z.number().int().min(1).default(3),
    maxSameActionRepeats: z.number().int().min(1).default(2),
    allowAutoExecuteHigh: z.boolean().default(false)
  })
  .strict();

export const ExplorationSummarySchema = z
  .object({
    visitedPageStates: z.number().int().min(0),
    candidateFeatures: z.number().int().min(0),
    candidateCrudFlows: z.number().int().min(0),
    blockedActions: z.number().int().min(0),
    reviewRequiredItems: z.number().int().min(0),
    totalActionsExecuted: z.number().int().min(0).optional(),
    totalObservations: z.number().int().min(0).optional()
  })
  .strict();

export const ExplorationSessionSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    explorationSessionId: z.string().regex(EXPLORATION_SESSION_ID_PATTERN),
    projectId: z.string().min(1),
    targetUrl: z.string().url(),
    goal: z.string().min(1),
    inputSources: z
      .object({
        featureList: z.boolean().optional(),
        manual: z.boolean().optional(),
        webShape: z.boolean().optional()
      })
      .strict()
      .optional(),
    mode: ExplorationModeSchema,
    llmMode: LlmModeSchema,
    environmentType: EnvironmentTypeSchema,
    riskPolicyId: z.string().optional(),
    testDataProfileId: z.string().optional(),
    status: ExplorationSessionStatusSchema,
    stopReason: ExplorationStopReasonSchema.optional(),
    limits: ExplorationLimitsSchema.optional(),
    startedAt: z.string().datetime({ offset: true }),
    endedAt: z.string().datetime({ offset: true }).nullable().optional(),
    summary: ExplorationSummarySchema.optional()
  })
  .strict();
export type ExplorationSession = z.infer<typeof ExplorationSessionSchema>;
