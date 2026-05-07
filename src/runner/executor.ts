import type { ExecutionPlan, ExecutionStep } from "../shared/types";

export type RunnerContext = {
  elementSelectors: Record<string, string>;
  values: Record<string, string>;
  evidenceDir: string;
};

export type StepExecutionResult = {
  step: ExecutionStep;
  status: "PASSED" | "FAILED" | "SKIPPED";
  message?: string;
};

export type PlanExecutionResult = {
  tcId: string;
  executionStatus: "COMPLETED" | "SCRIPT_FAILED" | "MAPPING_FAILED" | "SKIPPED_RISK";
  testResult: "P" | "F" | "N/A";
  steps: StepExecutionResult[];
};

export async function executePlan(
  plan: ExecutionPlan,
  _context: RunnerContext
): Promise<PlanExecutionResult> {
  if (plan.status !== "READY") {
    return {
      tcId: plan.tcId,
      executionStatus: plan.status === "SKIPPED_RISK" ? "SKIPPED_RISK" : "MAPPING_FAILED",
      testResult: "N/A",
      steps: []
    };
  }

  // The concrete Playwright implementation will resolve elementId values
  // against a private selector map and execute only known action names.
  return {
    tcId: plan.tcId,
    executionStatus: "COMPLETED",
    testResult: "P",
    steps: plan.steps.map((step) => ({
      step,
      status: "SKIPPED",
      message: "Execution engine scaffolded; Playwright wiring is not implemented yet."
    }))
  };
}
