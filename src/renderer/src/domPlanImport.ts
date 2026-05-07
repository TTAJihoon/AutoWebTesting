import type {
  DomElementRole,
  DomSummary,
  DomSummaryElement,
  ExecutionPlan,
  ExecutionPlanPayload,
  RunnerAction,
  TestCase
} from "../../shared/types";
import { allowedRunnerActions } from "../../shared/constants";

export type ImportResult<T> = {
  payload?: T;
  errors: string[];
  warnings: string[];
};

const elementIdPattern = /^el_[0-9]{4}$/;
const formIdPattern = /^form_[0-9]{4}$/;
const tcIdPattern = /^TC_[0-9]{3}-[0-9]{3}$/;

const domRoles: DomElementRole[] = [
  "textbox",
  "textarea",
  "button",
  "link",
  "select",
  "checkbox",
  "radio",
  "file",
  "table",
  "menuitem",
  "heading",
  "text",
  "dialog",
  "unknown"
];

const planStatuses: ExecutionPlan["status"][] = [
  "READY",
  "NEEDS_MAPPING_REVIEW",
  "NOT_AUTOMATABLE",
  "SKIPPED_RISK"
];

const elementActions: RunnerAction[] = [
  "click",
  "fill",
  "selectOption",
  "check",
  "uncheck",
  "uploadFile",
  "assertElementVisible",
  "assertElementNotVisible",
  "assertValueEquals"
];

export function parseDomSummaryJson(jsonText: string): ImportResult<DomSummary> {
  try {
    return normalizeDomSummary(JSON.parse(jsonText));
  } catch (error) {
    return {
      errors: [`DOM 요약 JSON 파싱에 실패했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`],
      warnings: []
    };
  }
}

export function parseExecutionPlanJson(
  jsonText: string,
  testCases: TestCase[],
  domSummary?: DomSummary
): ImportResult<ExecutionPlanPayload> {
  try {
    return normalizeExecutionPlan(JSON.parse(jsonText), testCases, domSummary);
  } catch (error) {
    return {
      errors: [`실행계획 JSON 파싱에 실패했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`],
      warnings: []
    };
  }
}

function normalizeDomSummary(input: unknown): ImportResult<DomSummary> {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!isRecord(input)) {
    return { errors: ["DOM 요약 JSON의 최상위 값은 객체여야 합니다."], warnings };
  }

  if (input.schemaVersion !== "1.0.0") {
    errors.push("DOM 요약 schemaVersion은 1.0.0이어야 합니다.");
  }

  if (!isRecord(input.page)) {
    errors.push("DOM 요약 page는 객체여야 합니다.");
  }

  const page = isRecord(input.page)
    ? {
        url: readString(input.page, "url", "page", errors),
        title: readString(input.page, "title", "page", errors),
        heading: readOptionalString(input.page, "heading"),
        visibleTextSummary: readOptionalStringArray(input.page, "visibleTextSummary", "page", errors)
      }
    : undefined;

  if (!Array.isArray(input.elements)) {
    errors.push("DOM 요약 elements는 배열이어야 합니다.");
  }

  const elements = Array.isArray(input.elements)
    ? input.elements.flatMap((item, index) => normalizeDomElement(item, index, errors))
    : [];

  const duplicateElementIds = findDuplicates(elements.map((element) => element.elementId));
  duplicateElementIds.forEach((elementId) => errors.push(`중복 elementId가 있습니다: ${elementId}`));

  const elementIds = new Set(elements.map((element) => element.elementId));
  const forms = normalizeForms(input.forms, elementIds, errors, warnings);

  if (elements.length === 0) {
    warnings.push("DOM 요약에 실행 가능한 요소가 없습니다.");
  }

  if (errors.length > 0 || !page?.url || !page.title) {
    return { errors, warnings };
  }

  return {
    payload: {
      schemaVersion: "1.0.0",
      page: {
        url: page.url,
        title: page.title,
        heading: page.heading,
        visibleTextSummary: page.visibleTextSummary
      },
      forms,
      elements
    },
    errors,
    warnings
  };
}

function normalizeDomElement(input: unknown, index: number, errors: string[]): DomSummaryElement[] {
  const label = `elements[${index}]`;

  if (!isRecord(input)) {
    errors.push(`${label}는 객체여야 합니다.`);
    return [];
  }

  const elementId = readString(input, "elementId", label, errors);
  const role = readEnum(input, "role", label, domRoles, errors);
  const tag = readString(input, "tag", label, errors);
  const visible = readBoolean(input, "visible", label, errors);
  const enabled = readBoolean(input, "enabled", label, errors);

  if (elementId && !elementIdPattern.test(elementId)) {
    errors.push(`${label}.elementId 형식은 el_0001이어야 합니다.`);
  }

  if (!elementId || !role || !tag || visible === undefined || enabled === undefined) {
    return [];
  }

  return [
    {
      elementId,
      role,
      tag,
      type: readOptionalString(input, "type"),
      label: readOptionalString(input, "label"),
      text: readOptionalString(input, "text"),
      placeholder: readOptionalString(input, "placeholder"),
      name: readOptionalString(input, "name"),
      required: readOptionalBoolean(input, "required"),
      visible,
      enabled,
      nearbyText: readOptionalStringArray(input, "nearbyText", label, errors),
      formId: readOptionalFormId(input, "formId", label, errors)
    }
  ];
}

function normalizeForms(
  input: unknown,
  elementIds: Set<string>,
  errors: string[],
  warnings: string[]
): DomSummary["forms"] {
  if (input === undefined) {
    return [];
  }

  if (!Array.isArray(input)) {
    errors.push("DOM 요약 forms는 배열이어야 합니다.");
    return [];
  }

  return input.flatMap((form, index) => {
    const label = `forms[${index}]`;
    if (!isRecord(form)) {
      errors.push(`${label}는 객체여야 합니다.`);
      return [];
    }

    const formId = readString(form, "formId", label, errors);
    const formElementIds = readStringArray(form, "elementIds", label, errors);

    if (formId && !formIdPattern.test(formId)) {
      errors.push(`${label}.formId 형식은 form_0001이어야 합니다.`);
    }

    formElementIds
      .filter((elementId) => !elementIds.has(elementId))
      .forEach((elementId) => warnings.push(`${label}에 DOM 요소 목록에 없는 elementId가 있습니다: ${elementId}`));

    if (!formId) {
      return [];
    }

    return [
      {
        formId,
        title: readOptionalString(form, "title"),
        elementIds: formElementIds
      }
    ];
  });
}

function normalizeExecutionPlan(
  input: unknown,
  testCases: TestCase[],
  domSummary?: DomSummary
): ImportResult<ExecutionPlanPayload> {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!isRecord(input)) {
    return { errors: ["실행계획 JSON의 최상위 값은 객체여야 합니다."], warnings };
  }

  if (input.schemaVersion !== "1.0.0") {
    errors.push("실행계획 schemaVersion은 1.0.0이어야 합니다.");
  }

  if (!Array.isArray(input.executionPlans)) {
    errors.push("executionPlans는 배열이어야 합니다.");
  }

  const approvedTcIds = new Set(
    testCases
      .filter((testCase) => testCase.reviewStatus === "APPROVED" && testCase.automationTarget)
      .map((testCase) => testCase.tcId)
  );
  const allTcIds = new Set(testCases.map((testCase) => testCase.tcId));
  const domElementIds = new Set(domSummary?.elements.map((element) => element.elementId) ?? []);

  const executionPlans = Array.isArray(input.executionPlans)
    ? input.executionPlans.flatMap((item, index) =>
        normalizeExecutionPlanItem(item, index, approvedTcIds, allTcIds, domElementIds, errors, warnings)
      )
    : [];

  findDuplicates(executionPlans.map((plan) => plan.tcId)).forEach((tcId) =>
    errors.push(`중복 실행계획 TC_ID가 있습니다: ${tcId}`)
  );

  const missingApprovedPlans = Array.from(approvedTcIds).filter(
    (tcId) => !executionPlans.some((plan) => plan.tcId === tcId)
  );
  missingApprovedPlans.forEach((tcId) => warnings.push(`승인된 자동화 대상 TC에 대한 실행계획이 없습니다: ${tcId}`));

  if (errors.length > 0) {
    return { errors, warnings };
  }

  return {
    payload: {
      schemaVersion: "1.0.0",
      executionPlans
    },
    errors,
    warnings
  };
}

function normalizeExecutionPlanItem(
  input: unknown,
  index: number,
  approvedTcIds: Set<string>,
  allTcIds: Set<string>,
  domElementIds: Set<string>,
  errors: string[],
  warnings: string[]
): ExecutionPlan[] {
  const label = `executionPlans[${index}]`;

  if (!isRecord(input)) {
    errors.push(`${label}는 객체여야 합니다.`);
    return [];
  }

  const tcId = readString(input, "tcId", label, errors);
  const status = readEnum(input, "status", label, planStatuses, errors);
  const confidence = readNumber(input, "confidence", label, errors);

  if (tcId && !tcIdPattern.test(tcId)) {
    errors.push(`${label}.tcId 형식은 TC_001-001이어야 합니다.`);
  }

  if (tcId && !allTcIds.has(tcId)) {
    warnings.push(`${tcId}는 업로드된 TC 목록에 없습니다.`);
  }

  if (tcId && allTcIds.has(tcId) && !approvedTcIds.has(tcId) && status === "READY") {
    warnings.push(`${tcId}는 승인된 자동화 대상이 아닌데 READY 실행계획이 생성되었습니다.`);
  }

  if (confidence !== undefined && (confidence < 0 || confidence > 1)) {
    errors.push(`${label}.confidence는 0 이상 1 이하이어야 합니다.`);
  }

  if (!Array.isArray(input.steps)) {
    errors.push(`${label}.steps는 배열이어야 합니다.`);
  }

  const steps = Array.isArray(input.steps)
    ? input.steps.flatMap((step, stepIndex) => normalizeStep(step, `${label}.steps[${stepIndex}]`, status, domElementIds, errors))
    : [];

  if (status === "READY" && steps.length === 0) {
    errors.push(`${label}은 READY 상태이므로 steps가 1개 이상 필요합니다.`);
  }

  if (!tcId || !status || confidence === undefined) {
    return [];
  }

  return [
    {
      tcId,
      status,
      confidence,
      reason: readOptionalString(input, "reason"),
      steps
    }
  ];
}

function normalizeStep(
  input: unknown,
  label: string,
  planStatus: ExecutionPlan["status"] | undefined,
  domElementIds: Set<string>,
  errors: string[]
) {
  if (!isRecord(input)) {
    errors.push(`${label}는 객체여야 합니다.`);
    return [];
  }

  const action = readEnum(input, "action", label, allowedRunnerActions, errors);
  const elementId = readOptionalElementId(input, "elementId", label, errors);

  if (elementId && domElementIds.size > 0 && !domElementIds.has(elementId)) {
    errors.push(`${label}.elementId가 DOM 요약에 없습니다: ${elementId}`);
  }

  if (action && elementActions.includes(action) && planStatus === "READY" && !elementId) {
    errors.push(`${label}.${action} 액션은 elementId가 필요합니다.`);
  }

  if (action === "goto" && !readOptionalString(input, "url")) {
    errors.push(`${label}.goto 액션은 url이 필요합니다.`);
  }

  if ((action === "waitForText" || action === "assertTextVisible" || action === "assertUrlContains") && !readOptionalString(input, "text")) {
    errors.push(`${label}.${action} 액션은 text가 필요합니다.`);
  }

  if ((action === "fill" || action === "assertValueEquals") && !readOptionalString(input, "valueSource") && !readOptionalString(input, "valueLiteral")) {
    errors.push(`${label}.${action} 액션은 valueSource 또는 valueLiteral이 필요합니다.`);
  }

  if (!action) {
    return [];
  }

  return [
    {
      action,
      elementId,
      url: readOptionalString(input, "url"),
      text: readOptionalString(input, "text"),
      valueSource: readOptionalString(input, "valueSource"),
      valueLiteral: readOptionalString(input, "valueLiteral"),
      optionLabel: readOptionalString(input, "optionLabel"),
      optionValue: readOptionalString(input, "optionValue"),
      timeoutMs: readOptionalNumber(input, "timeoutMs", label, errors),
      note: readOptionalString(input, "note")
    }
  ];
}

function readString(input: Record<string, unknown>, field: string, label: string, errors: string[]): string | undefined {
  const value = input[field];
  if (typeof value !== "string" || value.trim().length === 0) {
    errors.push(`${label}.${field}는 비어 있지 않은 문자열이어야 합니다.`);
    return undefined;
  }
  return value.trim();
}

function readOptionalString(input: Record<string, unknown>, field: string): string | undefined {
  const value = input[field];
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : undefined;
}

function readOptionalStringArray(
  input: Record<string, unknown>,
  field: string,
  label: string,
  errors: string[]
): string[] | undefined {
  const value = input[field];
  if (value === undefined) {
    return undefined;
  }
  return readStringArray(input, field, label, errors);
}

function readStringArray(input: Record<string, unknown>, field: string, label: string, errors: string[]): string[] {
  const value = input[field];
  if (!Array.isArray(value)) {
    errors.push(`${label}.${field}는 문자열 배열이어야 합니다.`);
    return [];
  }

  const invalidIndex = value.findIndex((item) => typeof item !== "string");
  if (invalidIndex >= 0) {
    errors.push(`${label}.${field}[${invalidIndex}]는 문자열이어야 합니다.`);
    return [];
  }

  return value as string[];
}

function readNumber(input: Record<string, unknown>, field: string, label: string, errors: string[]): number | undefined {
  const value = input[field];
  if (typeof value !== "number" || Number.isNaN(value)) {
    errors.push(`${label}.${field}는 숫자여야 합니다.`);
    return undefined;
  }
  return value;
}

function readOptionalNumber(
  input: Record<string, unknown>,
  field: string,
  label: string,
  errors: string[]
): number | undefined {
  const value = input[field];
  if (value === undefined) {
    return undefined;
  }
  if (typeof value !== "number" || !Number.isInteger(value) || value < 100 || value > 120000) {
    errors.push(`${label}.${field}는 100 이상 120000 이하의 정수여야 합니다.`);
    return undefined;
  }
  return value;
}

function readBoolean(input: Record<string, unknown>, field: string, label: string, errors: string[]): boolean | undefined {
  const value = input[field];
  if (typeof value !== "boolean") {
    errors.push(`${label}.${field}는 boolean이어야 합니다.`);
    return undefined;
  }
  return value;
}

function readOptionalBoolean(input: Record<string, unknown>, field: string): boolean | undefined {
  const value = input[field];
  return typeof value === "boolean" ? value : undefined;
}

function readEnum<T extends string>(
  input: Record<string, unknown>,
  field: string,
  label: string,
  values: readonly T[],
  errors: string[]
): T | undefined {
  const value = input[field];
  if (typeof value !== "string" || !values.includes(value as T)) {
    errors.push(`${label}.${field}는 ${values.join(", ")} 중 하나여야 합니다.`);
    return undefined;
  }
  return value as T;
}

function readOptionalElementId(
  input: Record<string, unknown>,
  field: string,
  label: string,
  errors: string[]
): string | undefined {
  const value = readOptionalString(input, field);
  if (value && !elementIdPattern.test(value)) {
    errors.push(`${label}.${field} 형식은 el_0001이어야 합니다.`);
  }
  return value;
}

function readOptionalFormId(
  input: Record<string, unknown>,
  field: string,
  label: string,
  errors: string[]
): string | undefined {
  const value = readOptionalString(input, field);
  if (value && !formIdPattern.test(value)) {
    errors.push(`${label}.${field} 형식은 form_0001이어야 합니다.`);
  }
  return value;
}

function findDuplicates(values: string[]): string[] {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  values.forEach((value) => {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  });

  return Array.from(duplicates);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
