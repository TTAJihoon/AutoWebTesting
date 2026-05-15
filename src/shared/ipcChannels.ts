// Single source of truth for IPC channel names.
// See docs/design/10-ipc-contract.md.
// Legacy channels are kept for backwards compatibility during Phase 0.5.

export const IpcChannel = {
  // === App ===
  AppGetInfo: "app:get-info",

  // === Project (Phase 2) ===
  ProjectCreate: "project:create",
  ProjectList: "project:list",
  ProjectOpen: "project:open",

  // === Test data (Phase 2) ===
  TestDataProfileSave: "test-data-profile:save",
  TestDataProfileLoad: "test-data-profile:load",
  SecretSet: "secret:set",
  SecretClear: "secret:clear",

  // === DOM (existing + Phase 3) ===
  DomCaptureSummary: "dom:capture-summary",
  DomSavePageState: "dom:save-page-state",

  // === Plan import (Phase 4) ===
  PlanImport: "plan:import",
  PlanValidate: "plan:validate",

  // === Run (existing legacy + Phase 6 new) ===
  RunStart: "run:start", // new (Phase 6)
  RunCancel: "run:cancel",
  RunRerunTestcase: "run:rerun-testcase",
  RunExecutePlans: "run:execute-plans", // legacy alias for current src/main/index.ts
  RunSaveArtifacts: "run:save-artifacts",
  RunExportExcel: "run:export-excel",
  RunCreateZip: "run:create-zip",

  // === Failure analysis (Phase 8) ===
  FailureAnalysisImport: "failure-analysis:import",

  // === Exploration (Phase 9, AI Mode) ===
  ExplorationStart: "exploration:start",
  ExplorationNextAction: "exploration:next-action",
  ExplorationApproveAction: "exploration:approve-action",
  ExplorationStop: "exploration:stop"
} as const;

export type IpcChannel = (typeof IpcChannel)[keyof typeof IpcChannel];

// === Event channel names (Main → Renderer) ===

export const IpcEvent = {
  RunStarted: "run:started",
  RunProgress: "run:progress",
  RunTestcaseStarted: "run:testcase-started",
  RunStepStarted: "run:step-started",
  RunStepFinished: "run:step-finished",
  RunTestcaseFinished: "run:testcase-finished",
  RunFailed: "run:failed",
  RunCancelled: "run:cancelled",
  RunFinished: "run:finished",
  ExplorationEvent: "exploration:event"
} as const;

export type IpcEvent = (typeof IpcEvent)[keyof typeof IpcEvent];
