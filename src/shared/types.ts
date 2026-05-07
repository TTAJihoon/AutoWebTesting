export type LlmMode = "API" | "GPT_WEB_IMPORT";

export type GenerationLevel = "STANDARD" | "DETAILED";

export type ReviewStatus =
  | "DRAFT"
  | "APPROVED"
  | "NEEDS_REVISION"
  | "REJECTED"
  | "EXCLUDED"
  | "DEPRECATED";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "PROHIBITED";

export type RiskFlag =
  | "PAYMENT"
  | "DELETE_DATA"
  | "SEND_EXTERNAL_MESSAGE"
  | "SUBMIT_TO_EXTERNAL_SYSTEM"
  | "DOWNLOAD_SENSITIVE_DATA"
  | "CHANGE_PERMISSION"
  | "CHANGE_SECURITY_SETTING"
  | "PUBLIC_PUBLISH"
  | "IRREVERSIBLE_ACTION"
  | "LEGAL_OR_FINANCIAL_ACTION";

export type ExecutionStatus =
  | "NOT_RUN"
  | "COMPLETED"
  | "BLOCKED"
  | "MAPPING_FAILED"
  | "SCRIPT_FAILED"
  | "SKIPPED_RISK"
  | "MANUAL_REQUIRED"
  | "CANCELLED";

export type TestResult = "P" | "F" | "N/A";

export type TestCase = {
  tcId: string;
  minorCategoryNo: number;
  tcSeqNo: number;
  majorCategory: string;
  middleCategory: string;
  minorCategory: string;
  scenario: string;
  precondition: string;
  expectedResult: string;
  reviewStatus: ReviewStatus;
  automationTarget: boolean;
  automationReason?: string;
  riskLevel: RiskLevel;
  riskFlags: RiskFlag[];
  riskReason?: string;
  generationReason?: string;
};

export type RunnerAction =
  | "goto"
  | "click"
  | "fill"
  | "selectOption"
  | "check"
  | "uncheck"
  | "uploadFile"
  | "waitForText"
  | "assertTextVisible"
  | "assertUrlContains"
  | "assertElementVisible"
  | "assertElementNotVisible"
  | "assertValueEquals"
  | "takeScreenshot";

export type ExecutionStep = {
  action: RunnerAction;
  elementId?: string;
  url?: string;
  text?: string;
  valueSource?: string;
  valueLiteral?: string;
  optionLabel?: string;
  optionValue?: string;
  timeoutMs?: number;
  note?: string;
};

export type ExecutionPlan = {
  tcId: string;
  status: "READY" | "NEEDS_MAPPING_REVIEW" | "NOT_AUTOMATABLE" | "SKIPPED_RISK";
  confidence: number;
  reason?: string;
  steps: ExecutionStep[];
};
