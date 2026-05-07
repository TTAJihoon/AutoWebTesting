import { allowedRunnerActions } from "../shared/constants";
import type { ExecutionPlan } from "../shared/types";

export type PlanPolicyIssue = {
  tcId: string;
  message: string;
};

export function validatePlanActions(plan: ExecutionPlan): PlanPolicyIssue[] {
  return plan.steps.flatMap((step) => {
    if (allowedRunnerActions.includes(step.action)) {
      return [];
    }

    return [
      {
        tcId: plan.tcId,
        message: `Unsupported action: ${step.action}`
      }
    ];
  });
}
