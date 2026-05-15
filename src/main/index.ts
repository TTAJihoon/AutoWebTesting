import { app, BrowserWindow, ipcMain } from "electron";
import { join } from "node:path";
import { electronApp, is, optimizer } from "@electron-toolkit/utils";
import { saveRunArtifacts, type SaveRunArtifactsRequest } from "./runArtifacts";
import { executePlans, type ExecutePlansRequest } from "../runner/executor";
import { captureDomSummary, type CaptureDomSummaryRequest } from "../runner/playwrightDomCapture";
import {
  createProject,
  listProjects,
  openProject,
  type CreateProjectRequest,
  type OpenProjectRequest
} from "./projectStore";
import { IpcChannel } from "../shared/ipcChannels";

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 820,
    minWidth: 960,
    minHeight: 680,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      sandbox: false
    }
  });

  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
  });

  if (is.dev && process.env.ELECTRON_RENDERER_URL) {
    void mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    void mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }
}

app.whenReady().then(() => {
  electronApp.setAppUserModelId("kr.or.tta.autowebtesting");

  app.on("browser-window-created", (_, window) => {
    optimizer.watchWindowShortcuts(window);
  });

  ipcMain.handle(IpcChannel.AppGetInfo, () => ({
    name: "AutoWebTesting",
    version: app.getVersion(),
    platform: process.platform
  }));

  // === Project (Phase 2) ===
  ipcMain.handle(IpcChannel.ProjectCreate, async (_event, request: CreateProjectRequest) => {
    return createProject(request);
  });

  ipcMain.handle(IpcChannel.ProjectList, async () => {
    return listProjects();
  });

  ipcMain.handle(IpcChannel.ProjectOpen, async (_event, request: OpenProjectRequest) => {
    return openProject(request);
  });

  // === DOM (existing) ===
  ipcMain.handle(IpcChannel.DomCaptureSummary, async (_event, request: CaptureDomSummaryRequest) => {
    return captureDomSummary(request);
  });

  // === Run (existing legacy channels) ===
  ipcMain.handle(IpcChannel.RunExecutePlans, async (_event, request: ExecutePlansRequest) => {
    return executePlans(request);
  });

  ipcMain.handle(IpcChannel.RunSaveArtifacts, async (_event, request: SaveRunArtifactsRequest) => {
    return saveRunArtifacts(request);
  });

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
