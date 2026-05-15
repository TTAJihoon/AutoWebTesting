import { z } from "zod";
import {
  PAGE_STATE_ID_PATTERN,
  RiskFlagSchema,
  RiskLevelSchema,
  SchemaVersionSchema
} from "./common.js";

export const PageStateTypeSchema = z.enum([
  "PAGE",
  "MODAL",
  "POPUP",
  "DIALOG",
  "PARTIAL"
]);
export type PageStateType = z.infer<typeof PageStateTypeSchema>;

export const IdentityHintsSchema = z
  .object({
    requiredTexts: z.array(z.string()).min(1),
    requiredElementIds: z.array(z.string()).optional(),
    optionalTexts: z.array(z.string()).optional()
  })
  .strict();
export type IdentityHints = z.infer<typeof IdentityHintsSchema>;

export const PageStateSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    pageStateId: z.string().regex(PAGE_STATE_ID_PATTERN),
    name: z.string().min(1),
    description: z.string().optional(),
    url: z.string().url().optional(),
    urlPattern: z.string().optional(),
    title: z.string().optional(),
    stateType: PageStateTypeSchema,
    parentPageStateId: z.string().regex(PAGE_STATE_ID_PATTERN).optional(),
    identityHints: IdentityHintsSchema,
    domSummaryId: z.string(),
    elementRegistryId: z.string(),
    riskAssessment: z
      .object({
        riskLevel: RiskLevelSchema,
        riskFlags: z.array(RiskFlagSchema).optional()
      })
      .strict()
      .optional(),
    capturedAt: z.string().datetime({ offset: true })
  })
  .strict();
export type PageState = z.infer<typeof PageStateSchema>;
