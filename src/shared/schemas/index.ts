// Single source of truth for runtime validation and TypeScript types.
// See docs/decisions/ADR-006-schema-as-contract-zod-as-runtime.md

export * from "./common.js";
export * from "./project.js";
export * from "./testcase.js";
export * from "./pageState.js";
export * from "./domSummary.js";
export * from "./elementRegistry.js";
export * from "./executionPlan.js";
export * from "./explorationSession.js";
export * from "./observation.js";
export * from "./pageFlow.js";
export * from "./riskPolicy.js";
export * from "./runResult.js";
export * from "./failurePackage.js";
export * from "./testDataProfile.js";

// Convenience map: name → { schema, sampleFile, jsonSchemaFile }
// Used by scripts/validate-schemas.mjs for paired JSON-Schema + Zod + sample validation.
import { ProjectSchema } from "./project.js";
import { TestCasePayloadSchema } from "./testcase.js";
import { PageStateSchema } from "./pageState.js";
import { DomSummarySchema } from "./domSummary.js";
import { ElementRegistrySchema } from "./elementRegistry.js";
import { ExecutionPlanSchema } from "./executionPlan.js";
import { ExplorationSessionSchema } from "./explorationSession.js";
import { ObservationSchema } from "./observation.js";
import { PageFlowSchema } from "./pageFlow.js";
import { RiskPolicySchema } from "./riskPolicy.js";
import { RunResultSchema } from "./runResult.js";
import { FailurePackageSchema } from "./failurePackage.js";
import { TestDataProfileSchema } from "./testDataProfile.js";

export const SCHEMA_REGISTRY = {
  project: ProjectSchema,
  testcase: TestCasePayloadSchema,
  "page-state": PageStateSchema,
  "dom-summary": DomSummarySchema,
  "element-registry": ElementRegistrySchema,
  "execution-plan": ExecutionPlanSchema,
  "exploration-session": ExplorationSessionSchema,
  observation: ObservationSchema,
  "page-flow": PageFlowSchema,
  "risk-policy": RiskPolicySchema,
  "run-result": RunResultSchema,
  "failure-package": FailurePackageSchema,
  "test-data-profile": TestDataProfileSchema
} as const;

export type SchemaName = keyof typeof SCHEMA_REGISTRY;
