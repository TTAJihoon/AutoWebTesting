import { z } from "zod";
import { RiskFlagSchema, SchemaVersionSchema } from "./common.js";

export const RiskKeywordsSchema = z
  .object({
    PAYMENT: z.array(z.string()).optional(),
    DELETE_DATA: z.array(z.string()).optional(),
    SEND_EXTERNAL_MESSAGE: z.array(z.string()).optional(),
    SUBMIT_TO_EXTERNAL_SYSTEM: z.array(z.string()).optional(),
    DOWNLOAD_SENSITIVE_DATA: z.array(z.string()).optional(),
    CHANGE_PERMISSION: z.array(z.string()).optional(),
    CHANGE_SECURITY_SETTING: z.array(z.string()).optional(),
    PUBLIC_PUBLISH: z.array(z.string()).optional(),
    IRREVERSIBLE_ACTION: z.array(z.string()).optional(),
    LEGAL_OR_FINANCIAL_ACTION: z.array(z.string()).optional()
  })
  .strict();
export type RiskKeywords = z.infer<typeof RiskKeywordsSchema>;

export const ElevationTriggerSchema = z.enum([
  "ANY_RISK_KEYWORD",
  "HIGH_RISK_KEYWORD",
  "IRREVERSIBLE_KEYWORD",
  "PROHIBITED_KEYWORD"
]);

export const ElevationRuleSchema = z
  .object({
    from: z.enum(["LOW", "MEDIUM", "HIGH"]),
    to: z.enum(["MEDIUM", "HIGH", "PROHIBITED"]),
    trigger: ElevationTriggerSchema,
    description: z.string().optional()
  })
  .strict();

export const RiskPolicyDefaultsSchema = z
  .object({
    lowExecution: z.enum(["AUTO", "WARN_BEFORE"]),
    mediumExecution: z.enum(["AUTO", "WARN_BEFORE"]),
    highExecution: z.enum(["APPROVAL_REQUIRED", "BLOCKED"]),
    prohibitedExecution: z.enum(["BLOCKED"]),
    defaultApprovalScope: z.enum(["PER_ACTION", "PER_TC", "PER_RUN"]).optional()
  })
  .strict();

export const DeletePolicySchema = z
  .object({
    onlyCreatedData: z.boolean().default(true),
    defaultRiskLevel: z.enum(["HIGH", "PROHIBITED"]).default("HIGH")
  })
  .strict();

export const RiskPolicySchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    riskPolicyId: z.string().min(1),
    name: z.string().min(1),
    description: z.string().optional(),
    riskKeywords: RiskKeywordsSchema,
    elevationRules: z.array(ElevationRuleSchema).optional(),
    defaults: RiskPolicyDefaultsSchema,
    deletePolicy: DeletePolicySchema.optional()
  })
  .strict();
export type RiskPolicy = z.infer<typeof RiskPolicySchema>;

// Re-export RiskFlag for convenience
export { RiskFlagSchema };
