import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { app } from "electron";
import type { ExecutePlansResponse, PlanExecutionResult } from "../runner/executor";
import type { DomSummary, ExecutionPlan, TestCase } from "../shared/types";

export type SaveRunArtifactsRequest = {
  runResult: ExecutePlansResponse;
  testCases: TestCase[];
  domSummary?: DomSummary;
  executionPlans?: ExecutionPlan[];
};

export type SaveRunArtifactsResponse = {
  runId: string;
  runDir: string;
  files: {
    runResult: string;
    failurePackage: string;
    htmlReport: string;
  };
  failedCaseCount: number;
};

export type FailurePackage = {
  schemaVersion: "1.0.0";
  runId: string;
  generatedAt: string;
  failedTestCases: FailurePackageItem[];
};

type FailurePackageItem = {
  tcId: string;
  scenario: string;
  precondition: string;
  expectedResult: string;
  executionStatus: string;
  testResult: string;
  failedStep?: {
    index: number;
    action: string;
    elementId?: string;
    message?: string;
  };
  actualState: {
    currentUrl?: string;
    pageTitle?: string;
    visibleTexts: string[];
    consoleErrors: string[];
    networkErrors: string[];
  };
  evidence: {
    screenshotPath?: string;
    domSummaryPath?: string;
  };
  rawFailureDetail?: string;
};

export async function saveRunArtifacts(request: SaveRunArtifactsRequest): Promise<SaveRunArtifactsResponse> {
  const runId = createRunId();
  const runDir = join(app.getPath("documents"), "AutoWebTesting", "runs", runId);
  await mkdir(runDir, { recursive: true });

  const runResultPath = join(runDir, "run-result.json");
  const failurePackagePath = join(runDir, "failure-package.json");
  const htmlReportPath = join(runDir, "report.html");

  const failurePackage = createFailurePackage(runId, request);

  await writeJson(runResultPath, {
    schemaVersion: "1.0.0",
    runId,
    savedAt: new Date().toISOString(),
    runResult: request.runResult,
    testCases: request.testCases,
    domSummary: request.domSummary,
    executionPlans: request.executionPlans
  });
  await writeJson(failurePackagePath, failurePackage);
  await writeFile(htmlReportPath, createHtmlReport(runId, request.runResult, failurePackage), "utf8");

  return {
    runId,
    runDir,
    files: {
      runResult: runResultPath,
      failurePackage: failurePackagePath,
      htmlReport: htmlReportPath
    },
    failedCaseCount: failurePackage.failedTestCases.length
  };
}

function createFailurePackage(runId: string, request: SaveRunArtifactsRequest): FailurePackage {
  const testCaseMap = new Map(request.testCases.map((testCase) => [testCase.tcId, testCase]));
  const failedTestCases = request.runResult.results
    .filter((result) => result.testResult === "F" || result.executionStatus !== "COMPLETED")
    .map((result) => createFailurePackageItem(result, testCaseMap.get(result.tcId), request.domSummary));

  return {
    schemaVersion: "1.0.0",
    runId,
    generatedAt: new Date().toISOString(),
    failedTestCases
  };
}

function createFailurePackageItem(
  result: PlanExecutionResult,
  testCase: TestCase | undefined,
  domSummary: DomSummary | undefined
): FailurePackageItem {
  const failedStep = result.steps.find((step) => step.status === "FAILED");

  return {
    tcId: result.tcId,
    scenario: testCase?.scenario ?? "",
    precondition: testCase?.precondition ?? "",
    expectedResult: testCase?.expectedResult ?? "",
    executionStatus: result.executionStatus,
    testResult: result.testResult,
    failedStep: failedStep
      ? {
          index: failedStep.stepIndex,
          action: failedStep.action,
          elementId: failedStep.elementId,
          message: failedStep.message
        }
      : undefined,
    actualState: {
      currentUrl: result.currentUrl,
      pageTitle: domSummary?.page.title,
      visibleTexts: domSummary?.page.visibleTextSummary ?? [],
      consoleErrors: [],
      networkErrors: []
    },
    evidence: {
      domSummaryPath: domSummary ? "run-result.json#/domSummary" : undefined
    },
    rawFailureDetail: result.failureDetail
  };
}

function createHtmlReport(runId: string, runResult: ExecutePlansResponse, failurePackage: FailurePackage): string {
  const total = runResult.results.length;
  const passed = runResult.results.filter((result) => result.testResult === "P").length;
  const failed = runResult.results.filter((result) => result.testResult === "F").length;
  const notExecutable = runResult.results.filter((result) => result.testResult === "N/A").length;

  const rows = runResult.results
    .map(
      (result) => `
        <tr>
          <td>${escapeHtml(result.tcId)}</td>
          <td>${escapeHtml(result.executionStatus)}</td>
          <td>${escapeHtml(result.testResult)}</td>
          <td>${escapeHtml(result.failureDetail ?? "")}</td>
        </tr>`
    )
    .join("");

  return `<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <title>AutoWebTesting Report ${escapeHtml(runId)}</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 32px; color: #172026; }
      h1 { margin: 0 0 12px; }
      .summary { display: flex; gap: 12px; margin: 24px 0; }
      .summary div { border: 1px solid #d4dfdc; border-radius: 8px; padding: 12px 16px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid #e2e8e6; padding: 10px; text-align: left; vertical-align: top; }
      th { background: #f5f8f7; }
    </style>
  </head>
  <body>
    <h1>AutoWebTesting 실행 보고서</h1>
    <p>Run ID: ${escapeHtml(runId)}</p>
    <p>시작: ${escapeHtml(runResult.runStartedAt)} / 종료: ${escapeHtml(runResult.runFinishedAt)}</p>
    <section class="summary">
      <div>전체: <strong>${total}</strong></div>
      <div>P: <strong>${passed}</strong></div>
      <div>F: <strong>${failed}</strong></div>
      <div>실행 불가: <strong>${notExecutable}</strong></div>
      <div>실패 패키지: <strong>${failurePackage.failedTestCases.length}</strong></div>
    </section>
    <table>
      <thead>
        <tr>
          <th>TC_ID</th>
          <th>실행 상태</th>
          <th>결과</th>
          <th>상세</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  </body>
</html>`;
}

function createRunId(): string {
  const now = new Date();
  const timestamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
    "-",
    String(now.getHours()).padStart(2, "0"),
    String(now.getMinutes()).padStart(2, "0"),
    String(now.getSeconds()).padStart(2, "0")
  ].join("");

  return `RUN-${timestamp}`;
}

async function writeJson(path: string, value: unknown): Promise<void> {
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
