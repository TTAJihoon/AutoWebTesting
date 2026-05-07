import type { GenerationLevel, LlmMode, ReviewStatus, RiskFlag, RiskLevel, TestCase } from "../../shared/types";

export type TestcaseImportPayload = {
  schemaVersion: "1.0.0";
  sourceMode: LlmMode;
  generationLevel: GenerationLevel;
  testCases: TestCase[];
};

export type TestcaseImportResult = {
  payload?: TestcaseImportPayload;
  errors: string[];
  warnings: string[];
};

const reviewStatuses: ReviewStatus[] = [
  "DRAFT",
  "APPROVED",
  "NEEDS_REVISION",
  "REJECTED",
  "EXCLUDED",
  "DEPRECATED"
];

const riskLevels: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "PROHIBITED"];

const riskFlags: RiskFlag[] = [
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

const tcIdPattern = /^TC_[0-9]{3}-[0-9]{3}$/;

export function parseTestcaseJson(jsonText: string): TestcaseImportResult {
  try {
    return normalizeTestcasePayload(JSON.parse(jsonText));
  } catch (error) {
    return {
      errors: [`JSON 파싱에 실패했습니다: ${error instanceof Error ? error.message : "알 수 없는 오류"}`],
      warnings: []
    };
  }
}

function normalizeTestcasePayload(input: unknown): TestcaseImportResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!isRecord(input)) {
    return { errors: ["최상위 JSON은 객체여야 합니다."], warnings };
  }

  if (input.schemaVersion !== "1.0.0") {
    errors.push("schemaVersion은 1.0.0이어야 합니다.");
  }

  if (input.sourceMode !== "API" && input.sourceMode !== "GPT_WEB_IMPORT") {
    errors.push("sourceMode는 API 또는 GPT_WEB_IMPORT여야 합니다.");
  }

  if (input.generationLevel !== "STANDARD" && input.generationLevel !== "DETAILED") {
    errors.push("generationLevel은 STANDARD 또는 DETAILED여야 합니다.");
  }

  if (!Array.isArray(input.testCases) || input.testCases.length === 0) {
    errors.push("testCases는 1개 이상의 항목을 가진 배열이어야 합니다.");
  }

  const testCases = Array.isArray(input.testCases)
    ? input.testCases.flatMap((item, index) => normalizeTestCase(item, index, errors, warnings))
    : [];

  if (errors.length > 0) {
    return { errors, warnings };
  }

  const duplicateIds = findDuplicates(testCases.map((testCase) => testCase.tcId));
  duplicateIds.forEach((tcId) => errors.push(`중복 TC_ID가 있습니다: ${tcId}`));

  return {
    payload: {
      schemaVersion: "1.0.0",
      sourceMode: input.sourceMode as LlmMode,
      generationLevel: input.generationLevel as GenerationLevel,
      testCases
    },
    errors,
    warnings
  };
}

function normalizeTestCase(
  input: unknown,
  index: number,
  errors: string[],
  warnings: string[]
): TestCase[] {
  const label = `testCases[${index}]`;

  if (!isRecord(input)) {
    errors.push(`${label}는 객체여야 합니다.`);
    return [];
  }

  const tcId = readString(input, "tcId", label, errors);
  const minorCategoryNo = readNumber(input, "minorCategoryNo", label, errors);
  const tcSeqNo = readNumber(input, "tcSeqNo", label, errors);
  const majorCategory = readString(input, "majorCategory", label, errors);
  const middleCategory = readString(input, "middleCategory", label, errors);
  const minorCategory = readString(input, "minorCategory", label, errors);
  const scenario = readString(input, "scenario", label, errors);
  const precondition = readString(input, "precondition", label, errors);
  const expectedResult = readString(input, "expectedResult", label, errors);
  const reviewStatus = readEnum(input, "reviewStatus", label, reviewStatuses, errors);
  const riskLevel = readEnum(input, "riskLevel", label, riskLevels, errors);
  const automationTarget = readBoolean(input, "automationTarget", label, errors);
  const riskFlagValues = readStringArray(input, "riskFlags", label, errors);
  const invalidRiskFlags = riskFlagValues.filter((flag) => !riskFlags.includes(flag as RiskFlag));

  if (tcId && !tcIdPattern.test(tcId)) {
    errors.push(`${label}.tcId 형식은 TC_001-001이어야 합니다.`);
  }

  if (minorCategoryNo !== undefined && minorCategoryNo < 1) {
    errors.push(`${label}.minorCategoryNo는 1 이상이어야 합니다.`);
  }

  if (tcSeqNo !== undefined && tcSeqNo < 1) {
    errors.push(`${label}.tcSeqNo는 1 이상이어야 합니다.`);
  }

  invalidRiskFlags.forEach((flag) => errors.push(`${label}.riskFlags에 지원하지 않는 값이 있습니다: ${flag}`));

  if (riskLevel === "HIGH" && automationTarget) {
    warnings.push(`${tcId || label}은 HIGH 위험도이므로 실행 전 별도 확인이 필요합니다.`);
  }

  if (riskLevel === "PROHIBITED" && automationTarget) {
    warnings.push(`${tcId || label}은 PROHIBITED 위험도이므로 자동화 대상에서 제외하는 것이 좋습니다.`);
  }

  if (
    !tcId ||
    minorCategoryNo === undefined ||
    tcSeqNo === undefined ||
    !majorCategory ||
    !middleCategory ||
    !minorCategory ||
    !scenario ||
    !precondition ||
    !expectedResult ||
    !reviewStatus ||
    !riskLevel ||
    automationTarget === undefined ||
    invalidRiskFlags.length > 0
  ) {
    return [];
  }

  return [
    {
      tcId,
      minorCategoryNo,
      tcSeqNo,
      majorCategory,
      middleCategory,
      minorCategory,
      scenario,
      precondition,
      expectedResult,
      reviewStatus,
      automationTarget,
      automationReason: readOptionalString(input, "automationReason"),
      riskLevel,
      riskFlags: riskFlagValues as RiskFlag[],
      riskReason: readOptionalString(input, "riskReason"),
      generationReason: readOptionalString(input, "generationReason")
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

function readNumber(input: Record<string, unknown>, field: string, label: string, errors: string[]): number | undefined {
  const value = input[field];
  if (typeof value !== "number" || !Number.isInteger(value)) {
    errors.push(`${label}.${field}는 정수여야 합니다.`);
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

function readEnum<T extends string>(
  input: Record<string, unknown>,
  field: string,
  label: string,
  values: T[],
  errors: string[]
): T | undefined {
  const value = input[field];
  if (typeof value !== "string" || !values.includes(value as T)) {
    errors.push(`${label}.${field}는 ${values.join(", ")} 중 하나여야 합니다.`);
    return undefined;
  }
  return value as T;
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
