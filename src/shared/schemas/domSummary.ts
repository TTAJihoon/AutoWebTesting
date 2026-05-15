import { z } from "zod";
import {
  ELEMENT_ID_PATTERN,
  PAGE_STATE_ID_PATTERN,
  RiskFlagSchema,
  RiskLevelSchema,
  SchemaVersionSchema
} from "./common.js";

export const DomElementRoleSchema = z.enum([
  "textbox",
  "textarea",
  "button",
  "link",
  "select",
  "checkbox",
  "radio",
  "file",
  "table",
  "menuitem",
  "heading",
  "text",
  "dialog",
  "unknown"
]);
export type DomElementRole = z.infer<typeof DomElementRoleSchema>;

export const DomElementRegionSchema = z
  .enum(["search", "table", "form", "toolbar", "modal", "header", "footer", "sidebar", "content"])
  .nullable();
export type DomElementRegion = z.infer<typeof DomElementRegionSchema>;

export const DomElementSchema = z
  .object({
    elementId: z.string().regex(ELEMENT_ID_PATTERN),
    role: DomElementRoleSchema,
    tag: z.string(),
    type: z.string().nullable().optional(),
    label: z.string().nullable().optional(),
    text: z.string().nullable().optional(),
    placeholder: z.string().nullable().optional(),
    name: z.string().nullable().optional(),
    required: z.boolean().optional(),
    visible: z.boolean(),
    enabled: z.boolean(),
    nearbyText: z.string().nullable().optional(),
    formId: z.string().nullable().optional(),
    region: DomElementRegionSchema.optional()
  })
  .strict();
export type DomElement = z.infer<typeof DomElementSchema>;

export const DomFormSchema = z
  .object({
    formId: z.string(),
    name: z.string().optional(),
    elementIds: z.array(z.string())
  })
  .strict();
export type DomForm = z.infer<typeof DomFormSchema>;

export const DomTableRowActionSchema = z
  .object({
    actionText: z.string(),
    column: z.string().optional(),
    riskLevel: RiskLevelSchema.optional(),
    riskFlags: z.array(RiskFlagSchema).optional()
  })
  .strict();

export const DomTableSchema = z
  .object({
    tableId: z.string(),
    label: z.string().optional(),
    elementId: z.string(),
    columns: z.array(z.string()),
    rowActionCandidates: z.array(DomTableRowActionSchema).optional()
  })
  .strict();
export type DomTable = z.infer<typeof DomTableSchema>;

export const DomSummarySchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    domSummaryId: z.string().regex(/^DOM_[0-9]{3}$/),
    pageStateId: z.string().regex(PAGE_STATE_ID_PATTERN),
    url: z.string().url(),
    title: z.string(),
    capturedAt: z.string().datetime({ offset: true }),
    limits: z
      .object({
        maxElements: z.number().int().optional(),
        maxVisibleTexts: z.number().int().optional()
      })
      .strict()
      .optional(),
    elements: z.array(DomElementSchema).max(250),
    visibleTexts: z.array(z.string()).max(80).optional(),
    forms: z.array(DomFormSchema).optional(),
    tables: z.array(DomTableSchema).optional()
  })
  .strict();
export type DomSummary = z.infer<typeof DomSummarySchema>;
