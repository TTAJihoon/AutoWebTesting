import type { RunnerAction, RiskFlag } from "./types";

export const allowedRunnerActions: RunnerAction[] = [
  "goto",
  "click",
  "fill",
  "selectOption",
  "check",
  "uncheck",
  "uploadFile",
  "waitForText",
  "assertTextVisible",
  "assertUrlContains",
  "assertElementVisible",
  "assertElementNotVisible",
  "assertValueEquals",
  "takeScreenshot"
];

export const riskFlags: RiskFlag[] = [
  "PAYMENT",
  "DELETE_DATA",
  "SEND_EXTERNAL_MESSAGE",
  "SUBMIT_TO_EXTERNAL_SYSTEM",
  "DOWNLOAD_SENSITIVE_DATA",
  "CHANGE_PERMISSION",
  "CHANGE_SECURITY_SETTING",
  "PUBLIC_PUBLISH",
  "IRREVERSIBLE_ACTION",
  "LEGAL_OR_FINANCIAL_ACTION"
];

export const defaultProjectRootName = "AutoWebTesting";
