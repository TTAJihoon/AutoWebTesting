import { contextBridge, ipcRenderer } from "electron";

const api = {
  getAppInfo: () => ipcRenderer.invoke("app:get-info"),
  captureDomSummary: (request: { url: string; showBrowser?: boolean }) =>
    ipcRenderer.invoke("dom:capture-summary", request),
  executePlans: (request: {
    plans: unknown[];
    domSummary: unknown;
    values: Record<string, string>;
    showBrowser?: boolean;
  }) => ipcRenderer.invoke("run:execute-plans", request),
  saveRunArtifacts: (request: {
    runResult: unknown;
    testCases: unknown[];
    domSummary?: unknown;
    executionPlans?: unknown[];
  }) => ipcRenderer.invoke("run:save-artifacts", request)
};

contextBridge.exposeInMainWorld("autoWebTesting", api);
