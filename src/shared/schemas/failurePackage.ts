import { z } from "zod";
import {
  EXECUTION_PLAN_ID_PATTERN,
  SchemaVersionSchema,
  TC_ID_PATTERN,
  TestResultSchema
} from "./common.js";

export const FailureTypeSchema = z.enum([
  "TEST_FAILURE",
  "EXECUTION_FAILURE",
  "RISK_BLOCKED",
  "MANUAL_REQUIRED"
]);
export type FailureType = z.infer<typeof FailureTypeSchema>;

export const FailurePackageExecutionStatusSchema = z.enum([
  "BLOCKED",
  "MAPPING_FAILED",
  "PAGE_STATE_MISMATCH",
  "NAVIGATION_FAILED",
  "DIALOG_UNHANDLED",
  "SCRIPT_FAILED",
  "SKIPPED_RISK",
  "MANUAL_REQUIRED",
  "COMPLETED"
]);

export const FailedStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.string().optional(),
    action: z.string().optional(),
    expectedPageStateId: z.string().optional(),
    actualUrl: z.string().optional(),
    actualPageStateGuess: z.string().optional(),
    message: z.string().optional(),
    playwrightError: z.string().optional()
  })
  .strict();

export const FailureContextSchema = z
  .object({
    currentUrl: z.string().optional(),
    pageTitle: z.string().optional(),
    visibleTexts: z.array(z.string()),
    screenshotPath: z.string().optional(),
    domSummaryPath: z.string().optional(),
    consoleErrors: z.array(z.string()).optional(),
    networkErrors: z.array(z.string()).optional(),
    previousStepResults: z
      .array(
        z
          .object({
            stepId: z.string(),
            status: z.string(),
            message: z.string().optional()
          })
          .strict()
      )
      .optional()
  })
  .strict();

export const FailurePackageSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    failurePackageId: z.string().regex(/^FAIL_[0-9]{3,6}$/),
    runId: z.string(),
    tcId: z.string().regex(TC_ID_PATTERN),
    executionPlanId: z.string().regex(EXECUTION_PLAN_ID_PATTERN),
    failureType: FailureTypeSchema,
    executionStatus: FailurePackageExecutionStatusSchema,
    testResult: TestResultSchema.optional(),
    failedStep: FailedStepSchema,
    context: FailureContextSchema,
    riskCheckResult: z.record(z.string(), z.unknown()).optional(),
    testDataSnapshot: z.record(z.string(), z.unknown()).optional(),
    suggestedAnalysisPromptInput: z.boolean().optional(),
    generatedAt: z.string().datetime({ offset: true }).optional()
  })
  .strict();
export type FailurePackage = z.infer<typeof FailurePackageSchema>;

// === GPT failure analysis output (별도 스키마이지만 같은 파일) ===

export const LikelyCauseCategorySchema = z.enum([
  "APPLICATION_DEFECT",
  "EXPECTED_RESULT_MISMATCH",
  "MAPPING_ERROR",
  "SCRIPT_ERROR",
  "ENVIRONMENT_ERROR",
  "DATA_ISSUE",
  "PERMISSION_OR_SESSION",
  "UNKNOWN"
]);

export const FailureAnalysisFinalResultSchema = z.enum([
  "F",
  "MANUAL_REVIEW",
  "NOT_A_PRODUCT_FAILURE"
]);

export const FailureAnalysisSchema = z
  .object({
    tcId: z.string().regex(TC_ID_PATTERN),
    failureSummary: z.string().min(1),
    likelyCauseCategory: LikelyCauseCategorySchema,
    recommendedReview: z.string().min(1),
    suggestedNextAction: z.string().optional(),
    finalResult: FailureAnalysisFinalResultSchema
  })
  .strict();
export type FailureAnalysis = z.infer<typeof FailureAnalysisSchema>;
