import { z } from "zod";

// === Common enums shared across schemas ===

export const RiskFlagSchema = z.enum([
  "PAYMENT",
  "DELETE_DATA",
  "SEND_EXTERNAL_MESSAGE",
  "SUBMIT_TO_EXTERNAL_SYSTEM",
  "DOWNLOAD_SENSITIVE_DATA",
  "CHANGE_PERMISSION",
  "CHANGE_SECURITY_SETTING",
  "PUBLIC_PUBLISH",
  "IRREVERSIBLE_ACTION",
  "LEGAL_OR_FINANCIAL_ACTION"
]);
export type RiskFlag = z.infer<typeof RiskFlagSchema>;

export const RiskLevelSchema = z.enum(["LOW", "MEDIUM", "HIGH", "PROHIBITED"]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const ReviewStatusSchema = z.enum([
  "DRAFT",
  "APPROVED",
  "NEEDS_REVISION",
  "REJECTED",
  "EXCLUDED",
  "DEPRECATED"
]);
export type ReviewStatus = z.infer<typeof ReviewStatusSchema>;

export const ExecutionStatusSchema = z.enum([
  "NOT_RUN",
  "RUNNING",
  "COMPLETED",
  "BLOCKED",
  "MAPPING_FAILED",
  "PAGE_STATE_MISMATCH",
  "NAVIGATION_FAILED",
  "DIALOG_UNHANDLED",
  "SCRIPT_FAILED",
  "SKIPPED_RISK",
  "MANUAL_REQUIRED",
  "CANCELLED"
]);
export type ExecutionStatus = z.infer<typeof ExecutionStatusSchema>;

export const TestResultSchema = z.enum(["P", "F", "N/A"]).nullable();
export type TestResult = z.infer<typeof TestResultSchema>;

export const SourceModeSchema = z.enum([
  "GPT_WEB_IMPORT",
  "API_MODE",
  "AI_EXPLORATION",
  "MANUAL"
]);
export type SourceMode = z.infer<typeof SourceModeSchema>;

// === Identifier regex patterns (mirror JSON Schema) ===

export const TC_ID_PATTERN = /^TC_[0-9]{3}-[0-9]{3}$/;
export const PAGE_STATE_ID_PATTERN = /^PAGE_[0-9]{3}$/;
export const ELEMENT_ID_PATTERN = /^PAGE_[0-9]{3}\.el_[0-9]{4}$/;
export const RUN_ID_PATTERN = /^RUN[-_][0-9]{8}[-_][0-9]{6}$/;
export const EXPLORATION_SESSION_ID_PATTERN = /^EXP_[0-9]{8}_[0-9]{3}$/;
export const EXECUTION_PLAN_ID_PATTERN = /^PLAN_TC_[0-9]{3}_[0-9]{3}$/;

// === RiskCheckResult (shared by execution-plan, run-result, etc.) ===

export const RiskCheckResultSchema = z
  .object({
    riskLevel: RiskLevelSchema,
    maxRiskLevel: RiskLevelSchema.optional(),
    riskFlags: z.array(RiskFlagSchema),
    matchedRiskKeywords: z.array(z.string()).optional(),
    requiresApproval: z.boolean().optional(),
    approvalScope: z
      .enum(["NONE", "PER_ACTION", "PER_TC", "PER_RUN", "FORBIDDEN"])
      .optional(),
    reason: z.string().optional()
  })
  .strict();
export type RiskCheckResult = z.infer<typeof RiskCheckResultSchema>;

// === Schema version constant ===

export const SCHEMA_VERSION = "0.3" as const;
export const SchemaVersionSchema = z.literal(SCHEMA_VERSION);
