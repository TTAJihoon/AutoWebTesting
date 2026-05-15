import { z } from "zod";
import {
  EXPLORATION_SESSION_ID_PATTERN,
  SchemaVersionSchema
} from "./common.js";

export const ObservationTypeSchema = z.enum([
  "TEXT_DOM_PRIMARY",
  "TEXT_DOM_WITH_IMAGE",
  "IMAGE_ASSISTED_ONLY",
  "ERROR_STATE",
  "UNKNOWN_STATE"
]);
export type ObservationType = z.infer<typeof ObservationTypeSchema>;

export const MaskingRuleSchema = z.enum([
  "passwordFields",
  "secretVariables",
  "emailLikeTexts",
  "phoneLikeTexts",
  "rrnLikeTexts",
  "tokenLikeTexts",
  "amountLikeTexts"
]);

export const ScreenshotSendModeSchema = z.union([
  z.boolean(),
  z.enum(["OPTIONAL_ON_AMBIGUITY", "FORCE_SEND", "NEVER"])
]);

export const ObservationScreenshotSchema = z
  .object({
    available: z.boolean().optional(),
    path: z.string().optional(),
    originalPath: z.string().optional(),
    sendToLlm: ScreenshotSendModeSchema.optional(),
    maskingApplied: z.boolean().optional(),
    maskingRules: z.array(MaskingRuleSchema).optional(),
    reason: z.string().optional()
  })
  .strict();

export const PageStateGuessSchema = z
  .object({
    name: z.string().optional(),
    confidence: z.number().min(0).max(1).optional(),
    reason: z.string().optional()
  })
  .strict();

export const ObservationSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    observationId: z.string().regex(/^OBS_[0-9]{3,6}$/),
    explorationSessionId: z.string().regex(EXPLORATION_SESSION_ID_PATTERN),
    pageStateId: z.string().nullable().optional(),
    url: z.string().url(),
    title: z.string(),
    observationType: ObservationTypeSchema,
    pageStateGuess: PageStateGuessSchema.optional(),
    domSummaryId: z.string(),
    elementRegistryId: z.string(),
    visibleTexts: z.array(z.string()).optional(),
    forms: z
      .array(
        z
          .object({
            formId: z.string(),
            label: z.string().optional(),
            fields: z.array(z.string()).optional()
          })
          .strict()
      )
      .optional(),
    tables: z
      .array(
        z
          .object({
            tableId: z.string(),
            label: z.string().optional(),
            columns: z.array(z.string()).optional()
          })
          .strict()
      )
      .optional(),
    screenshot: ObservationScreenshotSchema.optional(),
    previousActionResult: z
      .object({
        previousActionId: z.string().optional(),
        transitionDetected: z.boolean().optional(),
        summary: z.string().optional()
      })
      .strict()
      .nullable()
      .optional(),
    createdAt: z.string().datetime({ offset: true })
  })
  .strict();
export type Observation = z.infer<typeof ObservationSchema>;
