import { z } from "zod";
import {
  EXECUTION_PLAN_ID_PATTERN,
  ExecutionStatusSchema,
  RUN_ID_PATTERN,
  SchemaVersionSchema,
  TC_ID_PATTERN,
  TestResultSchema
} from "./common.js";

export const StepResultStatusSchema = z.enum([
  "PASSED",
  "FAILED",
  "SKIPPED",
  "BLOCKED",
  "REVIEW_REQUIRED"
]);
export type StepResultStatus = z.infer<typeof StepResultStatusSchema>;

export const ResolveAttemptResultSchema = z.enum([
  "FOUND",
  "NOT_FOUND",
  "MULTIPLE_MATCHES",
  "TIMEOUT",
  "ERROR"
]);

export const ResolveAttemptSchema = z
  .object({
    selectorType: z.string(),
    selector: z.string(),
    result: ResolveAttemptResultSchema
  })
  .strict();

export const StepResultSchema = z
  .object({
    stepId: z.string(),
    status: StepResultStatusSchema,
    startedAt: z.string().datetime({ offset: true }),
    endedAt: z.string().datetime({ offset: true }),
    message: z.string().optional(),
    currentUrl: z.string().optional(),
    pageStateId: z.string().optional(),
    screenshotPath: z.string().optional(),
    resolveAttempts: z.array(ResolveAttemptSchema).optional()
  })
  .strict();
export type StepResult = z.infer<typeof StepResultSchema>;

export const AssertionResultSchema = z
  .object({
    stepId: z.string(),
    assertion: z.string(),
    passed: z.boolean(),
    expected: z.string().optional(),
    actual: z.string().optional(),
    message: z.string().optional()
  })
  .strict();
export type AssertionResult = z.infer<typeof AssertionResultSchema>;

export const RunEnvironmentSchema = z
  .object({
    environmentType: z.enum(["local", "dev", "staging", "production"]),
    baseUrl: z.string().url(),
    browser: z.enum(["chromium", "firefox", "webkit"]),
    headless: z.boolean().optional(),
    appVersion: z.string().optional()
  })
  .strict();

export const RunSummarySchema = z
  .object({
    totalSteps: z.number().int().min(0),
    passedSteps: z.number().int().min(0),
    failedSteps: z.number().int().min(0),
    skippedSteps: z.number().int().min(0).optional(),
    executionStatus: ExecutionStatusSchema,
    testResult: TestResultSchema.optional(),
    durationMs: z.number().int().min(0).optional()
  })
  .strict();

export const RunEvidenceSchema = z
  .object({
    screenshots: z.array(z.string()).optional(),
    videos: z.array(z.string()).optional(),
    logs: z.array(z.string()).optional()
  })
  .strict();

export const RunResultSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    runId: z.string().regex(RUN_ID_PATTERN),
    projectId: z.string().min(1),
    executionPlanId: z.string().regex(EXECUTION_PLAN_ID_PATTERN),
    tcId: z.string().regex(TC_ID_PATTERN),
    startedAt: z.string().datetime({ offset: true }),
    endedAt: z.string().datetime({ offset: true }),
    environment: RunEnvironmentSchema,
    summary: RunSummarySchema,
    stepResults: z.array(StepResultSchema),
    assertionResults: z.array(AssertionResultSchema).optional(),
    createdDataRegistryId: z.string().nullable().optional(),
    evidence: RunEvidenceSchema.optional(),
    testDataSnapshotId: z.string().nullable().optional()
  })
  .strict();
export type RunResult = z.infer<typeof RunResultSchema>;
