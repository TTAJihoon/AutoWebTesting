import { z } from "zod";
import {
  EXECUTION_PLAN_ID_PATTERN,
  PAGE_STATE_ID_PATTERN,
  RiskCheckResultSchema,
  SchemaVersionSchema,
  SourceModeSchema,
  TC_ID_PATTERN
} from "./common.js";

// === Transition expectation ===

export const TransitionTypeSchema = z.enum([
  "NONE",
  "URL_CHANGE",
  "DOM_CHANGE",
  "TEXT_APPEAR",
  "ELEMENT_APPEAR",
  "MODAL_OPEN",
  "MODAL_CLOSE",
  "POPUP_OPEN",
  "DIALOG_OPEN",
  "TAB_CHANGE",
  "IFRAME_CHANGE",
  "URL_CHANGE_OR_DOM_CHANGE",
  "URL_CHANGE_OR_TEXT_APPEAR"
]);
export type TransitionType = z.infer<typeof TransitionTypeSchema>;

export const TransitionExpectationSchema = z
  .object({
    type: TransitionTypeSchema,
    expectedNextPageStateId: z.string().regex(PAGE_STATE_ID_PATTERN).optional(),
    urlPattern: z.string().optional(),
    requiredTexts: z.array(z.string()).optional(),
    timeoutMs: z.number().int().min(100).optional()
  })
  .strict();
export type TransitionExpectation = z.infer<typeof TransitionExpectationSchema>;

// === Step common fields and onFailure ===

export const OnFailureSchema = z.enum([
  "STOP_TC",
  "CONTINUE",
  "TAKE_SCREENSHOT_AND_STOP",
  "MARK_MANUAL_REQUIRED"
]);
export type OnFailure = z.infer<typeof OnFailureSchema>;

// === ACTION Step ===

export const ActionNameSchema = z.enum([
  "goto",
  "click",
  "fill",
  "selectOption",
  "check",
  "uncheck",
  "uploadFile",
  "press",
  "hover",
  "clear",
  "takeScreenshot",
  "waitForNavigation",
  "waitForLoadState"
]);
export type ActionName = z.infer<typeof ActionNameSchema>;

export const ActionStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.literal("ACTION"),
    pageStateId: z.string().regex(PAGE_STATE_ID_PATTERN).optional(),
    description: z.string().optional(),
    action: ActionNameSchema,
    elementId: z.string().optional(),
    url: z.string().optional(),
    valueSource: z.string().optional(),
    valueLiteral: z.string().optional(),
    optionLabel: z.string().optional(),
    optionValue: z.string().optional(),
    timeoutMs: z.number().int().min(100).optional(),
    onFailure: OnFailureSchema.optional(),
    riskCheck: RiskCheckResultSchema.optional(),
    expectedTransition: TransitionExpectationSchema.optional()
  })
  .strict();
export type ActionStep = z.infer<typeof ActionStepSchema>;

// === ASSERTION Step ===

export const AssertionNameSchema = z.enum([
  "assertTextVisible",
  "assertTextNotVisible",
  "assertElementVisible",
  "assertElementNotVisible",
  "assertValueEquals",
  "assertValueContains",
  "assertUrlContains",
  "assertPageTitleContains",
  "assertRowContains",
  "assertRowNotContains",
  "assertCellEquals",
  "assertToastVisible",
  "assertAlertText",
  "assertEnabled",
  "assertDisabled",
  "assertCountEquals",
  "assertCountGreaterThan",
  "assertDownloadStarted"
]);
export type AssertionName = z.infer<typeof AssertionNameSchema>;

export const AssertionStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.literal("ASSERTION"),
    pageStateId: z.string().regex(PAGE_STATE_ID_PATTERN).optional(),
    description: z.string().optional(),
    assertion: AssertionNameSchema,
    elementId: z.string().optional(),
    tableId: z.string().optional(),
    expectedText: z.string().optional(),
    expectedSubstring: z.string().optional(),
    expectedValueSource: z.string().optional(),
    expectedCount: z.number().int().optional(),
    onFailure: OnFailureSchema.optional()
  })
  .strict();
export type AssertionStep = z.infer<typeof AssertionStepSchema>;

// === WAIT Step ===

export const WaitTypeSchema = z.enum([
  "TEXT_APPEAR",
  "ELEMENT_APPEAR",
  "ELEMENT_DISAPPEAR",
  "URL_MATCH",
  "LOAD_STATE"
]);

export const WaitStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.literal("WAIT"),
    pageStateId: z.string().optional(),
    description: z.string().optional(),
    waitType: WaitTypeSchema,
    expectedText: z.string().optional(),
    elementId: z.string().optional(),
    urlPattern: z.string().optional(),
    timeoutMs: z.number().int().min(100).optional()
  })
  .strict();
export type WaitStep = z.infer<typeof WaitStepSchema>;

// === DIALOG Step ===

export const DialogTypeSchema = z.enum([
  "alert",
  "confirm",
  "prompt",
  "htmlModal",
  "toast",
  "popup"
]);

export const DialogResponseSchema = z.enum([
  "accept",
  "dismiss",
  "fillAndAccept",
  "close",
  "manual"
]);

export const DialogStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.literal("DIALOG"),
    pageStateId: z.string().optional(),
    description: z.string().optional(),
    dialogType: DialogTypeSchema,
    expectedTextContains: z.string().optional(),
    response: DialogResponseSchema,
    promptValueSource: z.string().optional(),
    riskCheck: RiskCheckResultSchema.optional()
  })
  .strict();
export type DialogStep = z.infer<typeof DialogStepSchema>;

// === TABLE_ACTION Step ===

export const RowMatchTypeSchema = z.enum([
  "CONTAINS_VALUE",
  "CELL_EQUALS",
  "CELL_CONTAINS",
  "FIRST_ROW",
  "LAST_ROW"
]);

export const TableActionStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.literal("TABLE_ACTION"),
    pageStateId: z.string().optional(),
    description: z.string().optional(),
    action: z.literal("clickRowAction"),
    tableId: z.string(),
    rowMatch: z
      .object({
        matchType: RowMatchTypeSchema,
        valueSource: z.string().optional(),
        valueLiteral: z.string().optional(),
        column: z.string().optional()
      })
      .strict(),
    actionText: z.string(),
    riskCheck: RiskCheckResultSchema.optional(),
    expectedTransition: TransitionExpectationSchema.optional()
  })
  .strict();
export type TableActionStep = z.infer<typeof TableActionStepSchema>;

// === SCREENSHOT Step ===

export const ScreenshotStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.literal("SCREENSHOT"),
    pageStateId: z.string().optional(),
    description: z.string().optional(),
    fileName: z.string().optional()
  })
  .strict();
export type ScreenshotStep = z.infer<typeof ScreenshotStepSchema>;

// === CLEANUP Step ===

export const CleanupStrategySchema = z.enum([
  "DELETE_CREATED_ROW",
  "DEACTIVATE_CREATED_ITEM",
  "ROLLBACK_BY_UI",
  "MANUAL_CLEANUP",
  "NO_CLEANUP"
]);

export const CleanupPolicySchema = z.enum([
  "NO_CLEANUP",
  "MANUAL_CLEANUP",
  "AUTO_CLEANUP_APPROVAL_REQUIRED",
  "AUTO_CLEANUP_SAFE_ONLY"
]);

export const CleanupItemSchema = z
  .object({
    cleanupId: z.string(),
    entityType: z.string(),
    matchValueSource: z.string(),
    strategy: CleanupStrategySchema,
    requiresApproval: z.boolean().optional(),
    riskCheck: RiskCheckResultSchema.optional()
  })
  .strict();

export const CleanupPlanSchema = z
  .object({
    policy: CleanupPolicySchema,
    items: z.array(CleanupItemSchema)
  })
  .strict();
export type CleanupPlan = z.infer<typeof CleanupPlanSchema>;

export const CleanupStepSchema = z
  .object({
    stepId: z.string(),
    stepType: z.literal("CLEANUP"),
    pageStateId: z.string().optional(),
    description: z.string().optional(),
    cleanupId: z.string()
  })
  .strict();
export type CleanupStep = z.infer<typeof CleanupStepSchema>;

// === Step union ===

export const StepSchema = z.discriminatedUnion("stepType", [
  ActionStepSchema,
  AssertionStepSchema,
  WaitStepSchema,
  DialogStepSchema,
  TableActionStepSchema,
  ScreenshotStepSchema,
  CleanupStepSchema
]);
export type Step = z.infer<typeof StepSchema>;

// === planStatus ===

export const PlanStatusSchema = z.enum([
  "DRAFT",
  "READY",
  "NEEDS_MAPPING_REVIEW",
  "NEEDS_RISK_APPROVAL",
  "MANUAL_REQUIRED",
  "NOT_AUTOMATABLE",
  "REJECTED"
]);
export type PlanStatus = z.infer<typeof PlanStatusSchema>;

// === ExecutionPlan ===

export const ExecutionPlanSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    executionPlanId: z.string().regex(EXECUTION_PLAN_ID_PATTERN),
    tcId: z.string().regex(TC_ID_PATTERN),
    source: z
      .object({
        explorationSessionId: z.string().optional(),
        candidateCrudFlowId: z.string().optional(),
        generatedBy: SourceModeSchema.optional(),
        reviewedByHuman: z.boolean().optional()
      })
      .strict()
      .optional(),
    name: z.string().min(1),
    description: z.string().optional(),
    startPageStateId: z.string().regex(PAGE_STATE_ID_PATTERN),
    requiredPageStateIds: z.array(z.string().regex(PAGE_STATE_ID_PATTERN)).min(1),
    testDataProfileId: z.string(),
    variablesUsed: z.array(z.string()).optional(),
    riskSummary: RiskCheckResultSchema,
    planStatus: PlanStatusSchema,
    steps: z.array(StepSchema).min(1),
    cleanupPlan: CleanupPlanSchema.optional()
  })
  .strict();
export type ExecutionPlan = z.infer<typeof ExecutionPlanSchema>;
