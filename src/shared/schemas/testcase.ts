import { z } from "zod";
import {
  RiskFlagSchema,
  RiskLevelSchema,
  ReviewStatusSchema,
  SchemaVersionSchema,
  SourceModeSchema,
  TC_ID_PATTERN
} from "./common.js";

export const TestCaseSchema = z
  .object({
    tcId: z.string().regex(TC_ID_PATTERN, "TC_ID 형식: TC_NNN-NNN"),
    minorCategoryNo: z.number().int().min(1).optional(),
    tcSeqNo: z.number().int().min(1).optional(),
    majorCategory: z.string().min(1),
    middleCategory: z.string().min(1),
    minorCategory: z.string().min(1),
    scenario: z.string().min(1),
    precondition: z.string(),
    expectedResult: z.string().min(1),
    reviewStatus: ReviewStatusSchema,
    automationTarget: z.boolean(),
    automationReason: z.string().optional(),
    riskLevel: RiskLevelSchema,
    riskFlags: z.array(RiskFlagSchema),
    riskReason: z.string().optional(),
    generationReason: z.string().optional(),
    testDataRefs: z.array(z.string()).optional(),
    assertionRefs: z.array(z.string()).optional(),
    createdAt: z.string().datetime({ offset: true }).optional(),
    updatedAt: z.string().datetime({ offset: true }).optional()
  })
  .strict();
export type TestCase = z.infer<typeof TestCaseSchema>;

export const TestCasePayloadSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    generatedAt: z.string().datetime({ offset: true }).optional(),
    sourceMode: SourceModeSchema.optional(),
    testCases: z.array(TestCaseSchema)
  })
  .strict();
export type TestCasePayload = z.infer<typeof TestCasePayloadSchema>;
