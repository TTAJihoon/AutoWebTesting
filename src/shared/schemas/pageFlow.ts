import { z } from "zod";
import {
  ELEMENT_ID_PATTERN,
  PAGE_STATE_ID_PATTERN,
  SchemaVersionSchema
} from "./common.js";

export const PageFlowTriggerActionSchema = z.enum([
  "click",
  "fill",
  "selectOption",
  "submitForm",
  "clickRowAction",
  "goto",
  "press"
]);

export const PageFlowNavigationTypeSchema = z.enum([
  "NONE",
  "URL_CHANGE",
  "TEXT_APPEAR",
  "ELEMENT_APPEAR",
  "MODAL_OPEN",
  "MODAL_CLOSE",
  "POPUP_OPEN",
  "URL_CHANGE_OR_TEXT_APPEAR",
  "URL_CHANGE_OR_DOM_CHANGE"
]);

export const TransitionSchema = z
  .object({
    transitionId: z.string().regex(/^TR_[0-9]{3}$/),
    fromPageStateId: z.string().regex(PAGE_STATE_ID_PATTERN),
    toPageStateId: z.string().regex(PAGE_STATE_ID_PATTERN),
    trigger: z
      .object({
        action: PageFlowTriggerActionSchema,
        elementId: z.string().regex(ELEMENT_ID_PATTERN).optional(),
        description: z.string().optional()
      })
      .strict(),
    expectedNavigation: z
      .object({
        type: PageFlowNavigationTypeSchema,
        urlPattern: z.string().optional(),
        requiredTexts: z.array(z.string()).optional(),
        timeoutMs: z.number().int().min(100).optional()
      })
      .strict()
      .optional()
  })
  .strict();
export type Transition = z.infer<typeof TransitionSchema>;

export const PageFlowSchema = z
  .object({
    schemaVersion: SchemaVersionSchema,
    flowId: z.string().regex(/^FLOW_[A-Z0-9_]+$/),
    name: z.string().min(1),
    description: z.string().optional(),
    startPageStateId: z.string().regex(PAGE_STATE_ID_PATTERN),
    transitions: z.array(TransitionSchema)
  })
  .strict();
export type PageFlow = z.infer<typeof PageFlowSchema>;
