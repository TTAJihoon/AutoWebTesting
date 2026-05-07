import { mkdir, mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { chromium, type Locator, type Page } from "playwright";
import type { DomSummary, DomSummaryElement, ExecutionPlan, ExecutionStep, ExecutionStatus, TestResult } from "../shared/types";

export type RunnerContext = {
  domSummary: DomSummary;
  values: Record<string, string>;
  showBrowser?: boolean;
  screenshotDir: string;
};

export type StepExecutionResult = {
  stepIndex: number;
  action: ExecutionStep["action"];
  elementId?: string;
  status: "PASSED" | "FAILED" | "SKIPPED";
  message?: string;
};

export type PlanExecutionResult = {
  tcId: string;
  executionStatus: ExecutionStatus;
  testResult: TestResult;
  currentUrl?: string;
  failureDetail?: string;
  evidence?: {
    screenshotPath?: string;
  };
  steps: StepExecutionResult[];
};

export type ExecutePlansRequest = {
  plans: ExecutionPlan[];
  domSummary: DomSummary;
  values: Record<string, string>;
  showBrowser?: boolean;
};

export type ExecutePlansResponse = {
  runStartedAt: string;
  runFinishedAt: string;
  results: PlanExecutionResult[];
};

class RunnerError extends Error {
  constructor(
    message: string,
    public readonly executionStatus: ExecutionStatus,
    public readonly testResult: TestResult = "N/A"
  ) {
    super(message);
  }
}

export async function executePlans(request: ExecutePlansRequest): Promise<ExecutePlansResponse> {
  const browser = await chromium.launch({ headless: request.showBrowser !== true });
  const runStartedAt = new Date().toISOString();
  const screenshotDir = await createTempScreenshotDir();

  try {
    const results: PlanExecutionResult[] = [];

    for (const plan of request.plans) {
      const page = await browser.newPage();
      try {
        results.push(
          await executePlanOnPage(page, plan, {
            ...request,
            screenshotDir
          })
        );
      } finally {
        await page.close().catch(() => undefined);
      }
    }

    return {
      runStartedAt,
      runFinishedAt: new Date().toISOString(),
      results
    };
  } finally {
    await browser.close();
  }
}

async function executePlanOnPage(
  page: Page,
  plan: ExecutionPlan,
  context: RunnerContext
): Promise<PlanExecutionResult> {
  if (plan.status !== "READY") {
    return createSkippedResult(plan);
  }

  const steps: StepExecutionResult[] = [];

  try {
    if (!plan.steps.some((step) => step.action === "goto")) {
      await page.goto(context.domSummary.page.url, { waitUntil: "domcontentloaded", timeout: 30000 });
    }

    for (const [index, step] of plan.steps.entries()) {
      await executeStep(page, step, context);
      steps.push({
        stepIndex: index + 1,
        action: step.action,
        elementId: step.elementId,
        status: "PASSED"
      });
    }

    return {
      tcId: plan.tcId,
      executionStatus: "COMPLETED",
      testResult: "P",
      currentUrl: page.url(),
      steps
    };
  } catch (error) {
    const runnerError =
      error instanceof RunnerError
        ? error
        : new RunnerError(error instanceof Error ? error.message : "알 수 없는 실행 오류", "SCRIPT_FAILED");

    const failedStep = plan.steps[steps.length];
    const screenshotPath = await captureFailureScreenshot(page, context.screenshotDir, plan.tcId).catch(() => undefined);

    steps.push({
      stepIndex: steps.length + 1,
      action: failedStep?.action ?? "takeScreenshot",
      elementId: failedStep?.elementId,
      status: "FAILED",
      message: runnerError.message
    });

    return {
      tcId: plan.tcId,
      executionStatus: runnerError.executionStatus,
      testResult: runnerError.testResult,
      currentUrl: page.url(),
      failureDetail: runnerError.message,
      evidence: {
        screenshotPath
      },
      steps
    };
  }
}

function createSkippedResult(plan: ExecutionPlan): PlanExecutionResult {
  if (plan.status === "SKIPPED_RISK") {
    return {
      tcId: plan.tcId,
      executionStatus: "SKIPPED_RISK",
      testResult: "N/A",
      failureDetail: plan.reason ?? "위험 정책으로 자동 실행에서 제외되었습니다.",
      steps: []
    };
  }

  if (plan.status === "NOT_AUTOMATABLE") {
    return {
      tcId: plan.tcId,
      executionStatus: "MANUAL_REQUIRED",
      testResult: "N/A",
      failureDetail: plan.reason ?? "자동화가 어려워 수동 확인이 필요합니다.",
      steps: []
    };
  }

  return {
    tcId: plan.tcId,
    executionStatus: "MAPPING_FAILED",
    testResult: "N/A",
    failureDetail: plan.reason ?? "DOM 매핑 검토가 필요합니다.",
    steps: []
  };
}

async function executeStep(page: Page, step: ExecutionStep, context: RunnerContext): Promise<void> {
  const timeout = step.timeoutMs ?? 10000;

  switch (step.action) {
    case "goto":
      if (!step.url) {
        throw new RunnerError("goto 액션에 url이 없습니다.", "SCRIPT_FAILED");
      }
      await page.goto(step.url, { waitUntil: "domcontentloaded", timeout });
      return;

    case "click":
      await (await resolveElementLocator(page, step, context)).click({ timeout });
      return;

    case "fill":
      await (await resolveElementLocator(page, step, context)).fill(resolveValue(step, context), { timeout });
      return;

    case "selectOption":
      await (await resolveElementLocator(page, step, context)).selectOption(resolveOption(step), { timeout });
      return;

    case "check":
      await (await resolveElementLocator(page, step, context)).check({ timeout });
      return;

    case "uncheck":
      await (await resolveElementLocator(page, step, context)).uncheck({ timeout });
      return;

    case "uploadFile":
      await (await resolveElementLocator(page, step, context)).setInputFiles(resolveValue(step, context), { timeout });
      return;

    case "waitForText":
      await waitForText(page, step.text, timeout);
      return;

    case "assertTextVisible":
      await assertTextVisible(page, step.text, timeout);
      return;

    case "assertUrlContains":
      if (!step.text) {
        throw new RunnerError("assertUrlContains 액션에 text가 없습니다.", "SCRIPT_FAILED");
      }
      if (!page.url().includes(step.text)) {
        throw new RunnerError(`현재 URL에 기대 문자열이 없습니다: ${step.text}`, "COMPLETED", "F");
      }
      return;

    case "assertElementVisible":
      await assertElementVisible(page, step, context, timeout, true);
      return;

    case "assertElementNotVisible":
      await assertElementVisible(page, step, context, timeout, false);
      return;

    case "assertValueEquals": {
      const locator = await resolveElementLocator(page, step, context);
      const actualValue = await locator.inputValue({ timeout }).catch(() => "");
      const expectedValue = resolveValue(step, context);
      if (actualValue !== expectedValue) {
        throw new RunnerError(`입력값이 기대값과 다릅니다. 기대값: ${expectedValue}, 실제값: ${actualValue}`, "COMPLETED", "F");
      }
      return;
    }

    case "takeScreenshot":
      await page.screenshot({ fullPage: true });
      return;
  }
}

async function resolveElementLocator(page: Page, step: ExecutionStep, context: RunnerContext): Promise<Locator> {
  if (!step.elementId) {
    throw new RunnerError(`${step.action} 액션에 elementId가 없습니다.`, "MAPPING_FAILED");
  }

  const element = context.domSummary.elements.find((item) => item.elementId === step.elementId);
  if (!element) {
    throw new RunnerError(`DOM 요약에서 elementId를 찾지 못했습니다: ${step.elementId}`, "MAPPING_FAILED");
  }

  const locator = await firstAvailableLocator(page, createLocatorCandidates(page, element));
  if (!locator) {
    throw new RunnerError(`화면에서 요소를 찾지 못했습니다: ${step.elementId}`, "MAPPING_FAILED");
  }

  return locator;
}

function createLocatorCandidates(page: Page, element: DomSummaryElement): Locator[] {
  const candidates: Locator[] = [];
  const accessibleName = element.label || element.text || element.placeholder;

  if (element.label) {
    candidates.push(page.getByLabel(element.label).first());
  }

  if (element.placeholder) {
    candidates.push(page.getByPlaceholder(element.placeholder).first());
  }

  if (accessibleName && (element.role === "button" || element.role === "link" || element.role === "checkbox" || element.role === "radio")) {
    candidates.push(page.getByRole(element.role, { name: accessibleName }).first());
  }

  if (element.text && element.role !== "textbox" && element.role !== "textarea") {
    candidates.push(page.getByText(element.text, { exact: false }).first());
  }

  if (element.name) {
    candidates.push(page.locator(`${element.tag}[name="${escapeCssAttribute(element.name)}"]`).first());
  }

  if (element.type) {
    candidates.push(page.locator(`${element.tag}[type="${escapeCssAttribute(element.type)}"]`).first());
  }

  candidates.push(page.locator(element.tag).nth(Number(element.elementId.replace("el_", "")) - 1));
  return candidates;
}

async function firstAvailableLocator(page: Page, candidates: Locator[]): Promise<Locator | undefined> {
  for (const candidate of candidates) {
    try {
      if ((await candidate.count()) === 0) {
        continue;
      }
      await candidate.waitFor({ state: "attached", timeout: 1200 });
      return candidate;
    } catch {
      continue;
    }
  }

  return undefined;
}

function resolveValue(step: ExecutionStep, context: RunnerContext): string {
  if (step.valueLiteral !== undefined) {
    return step.valueLiteral;
  }

  if (!step.valueSource) {
    throw new RunnerError(`${step.action} 액션에 valueSource 또는 valueLiteral이 없습니다.`, "SCRIPT_FAILED");
  }

  const value = context.values[step.valueSource];
  if (value === undefined) {
    throw new RunnerError(`입력 데이터가 없습니다: ${step.valueSource}`, "BLOCKED");
  }

  return value;
}

function resolveOption(step: ExecutionStep): { label?: string; value?: string } {
  if (!step.optionLabel && !step.optionValue) {
    throw new RunnerError("selectOption 액션에 optionLabel 또는 optionValue가 없습니다.", "SCRIPT_FAILED");
  }

  return {
    label: step.optionLabel,
    value: step.optionValue
  };
}

async function waitForText(page: Page, text: string | undefined, timeout: number): Promise<void> {
  if (!text) {
    throw new RunnerError("텍스트 확인 액션에 text가 없습니다.", "SCRIPT_FAILED");
  }

  try {
    await page.getByText(text, { exact: false }).first().waitFor({ state: "visible", timeout });
  } catch {
    throw new RunnerError(`기대 텍스트가 표시되지 않았습니다: ${text}`, "COMPLETED", "F");
  }
}

async function assertTextVisible(page: Page, text: string | undefined, timeout: number): Promise<void> {
  await waitForText(page, text, timeout);
}

async function assertElementVisible(
  page: Page,
  step: ExecutionStep,
  context: RunnerContext,
  timeout: number,
  expectedVisible: boolean
): Promise<void> {
  const locator = await resolveElementLocator(page, step, context);
  const visible = await locator.isVisible({ timeout });

  if (visible !== expectedVisible) {
    throw new RunnerError(
      expectedVisible ? `요소가 표시되지 않았습니다: ${step.elementId}` : `요소가 표시되면 안 되지만 표시되었습니다: ${step.elementId}`,
      "COMPLETED",
      "F"
    );
  }
}

function escapeCssAttribute(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

async function createTempScreenshotDir(): Promise<string> {
  const dir = await mkdtemp(join(tmpdir(), "autowebtesting-"));
  const screenshotDir = join(dir, "screenshots");
  await mkdir(screenshotDir, { recursive: true });
  return screenshotDir;
}

async function captureFailureScreenshot(page: Page, screenshotDir: string, tcId: string): Promise<string> {
  const screenshotPath = join(screenshotDir, `${sanitizeFileName(tcId)}_fail.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  return screenshotPath;
}

function sanitizeFileName(value: string): string {
  return value.replace(/[^a-zA-Z0-9_-]/g, "_");
}
