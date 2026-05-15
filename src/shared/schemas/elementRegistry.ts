import { z } from "zod";
import {
  ELEMENT_ID_PATTERN,
  PAGE_STATE_ID_PATTERN,
  SchemaVersionSchema
} from "./common.js";

export const SelectorTypeSchema = z.enum([
  "testId",
  "role",
  "label",
  "placeholder",
  "text",
  "css",
  "xpath"
]);
export type SelectorType = z.infer<typeof SelectorTypeSchema>;

export const SelectorCandidateSchema = z
  .object({
    type: SelectorTypeSchema,
    value: z.string().min(1),
    priority: z.number().int().min(1),
    confidence: z.number().min(0).max(1).optional()
  })
  .strict();
export type SelectorCandidate = z.infer<typeof SelectorCandidateSchema>;

export const StableHintsSchema = z
  .object({
    role: z.string().nullable().optional(),
    label: z.string().nullable().optional(),
    text: z.string().nullable().optional(),
    placeholder: z.string().nullable().optional(),
    nearbyText: z.string().nullable().optional(),
    formId: z.string().nullable().optional(),
    region: z.string().nullable().optional()
  })
  .strict();
export type StableHints = z.infer<typeof StableHintsSchema>;

export const ElementRegistryItemSchema = z
  .object({
    elementId: z.string().regex(ELEMENT_ID_PATTERN),
    selectorCandidates: z.array(SelectorCandidateSchema).min(1),
    stableHints: StableHintsSchema.optional(),
    lastKnownBounds: z
      .object({
        x: z.number(),
        y: z.number(),
        width: z.number(),
        height: z.number()
      })
      .strict()
      .optional()
  })
  .strict();
export type ElementRegistryItem = z.infer<typeof ElementRegistryItemSchema>;

export const ElementRegistrySchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    elementRegistryId: z.string().regex(/^REG_[0-9]{3}$/),
    pageStateId: z.string().regex(PAGE_STATE_ID_PATTERN),
    createdAt: z.string().datetime({ offset: true }),
    items: z.array(ElementRegistryItemSchema)
  })
  .strict();
export type ElementRegistry = z.infer<typeof ElementRegistrySchema>;
