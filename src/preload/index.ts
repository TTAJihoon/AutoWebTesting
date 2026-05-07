import { contextBridge, ipcRenderer } from "electron";

const api = {
  getAppInfo: () => ipcRenderer.invoke("app:get-info"),
  captureDomSummary: (request: { url: string; showBrowser?: boolean }) =>
    ipcRenderer.invoke("dom:capture-summary", request)
};

contextBridge.exposeInMainWorld("autoWebTesting", api);
