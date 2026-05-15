import { contextBridge, ipcRenderer } from "electron";
import { IpcChannel } from "../shared/ipcChannels";

const api = {
  getAppInfo: () => ipcRenderer.invoke(IpcChannel.AppGetInfo),

  // === Project (Phase 2) ===
  createProject: (request: { name: string; targetUrl?: string; environmentType?: string }) =>
    ipcRenderer.invoke(IpcChannel.ProjectCreate, request),
  listProjects: () => ipcRenderer.invoke(IpcChannel.ProjectList),
  openProject: (request: { folderName: string }) =>
    ipcRenderer.invoke(IpcChannel.ProjectOpen, request),

  // === DOM (existing) ===
  captureDomSummary: (request: { url: string; showBrowser?: boolean }) =>
    ipcRenderer.invoke(IpcChannel.DomCaptureSummary, request),

  // === Run (existing legacy channels) ===
  executePlans: (request: {
    plans: unknown[];
    domSummary: unknown;
    values: Record<string, string>;
    showBrowser?: boolean;
  }) => ipcRenderer.invoke(IpcChannel.RunExecutePlans, request),
  saveRunArtifacts: (request: {
    runResult: unknown;
    testCases: unknown[];
    domSummary?: unknown;
    executionPlans?: unknown[];
  }) => ipcRenderer.invoke(IpcChannel.RunSaveArtifacts, request)
};

contextBridge.exposeInMainWorld("autoWebTesting", api);
