---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 08-assertion-policy.md
  - 11-runner-design.md
---

# RunResult, FailurePackage, FailureCause

## 1. ExecutionStatus

다중 화면 CRUD 자동화를 고려한 ExecutionStatus는 다음과 같다.

| 상태 | 설명 |
|---|---|
| `NOT_RUN` | 아직 실행하지 않음 |
| `RUNNING` | 실행 중 |
| `COMPLETED` | 실행과 검증이 완료됨 |
| `BLOCKED` | 사전조건 또는 환경 문제로 실행 불가 |
| `MAPPING_FAILED` | elementId를 실제 요소에 매핑하지 못함 |
| `PAGE_STATE_MISMATCH` | 현재 화면이 기대한 PageState와 다름 |
| `NAVIGATION_FAILED` | 기대한 화면 상태 전환이 발생하지 않음 |
| `DIALOG_UNHANDLED` | 다이얼로그/모달/팝업을 처리하지 못함 |
| `SCRIPT_FAILED` | Playwright 명령 실행 중 예외 발생 |
| `SKIPPED_RISK` | 리스크 정책에 의해 건너뜀 |
| `MANUAL_REQUIRED` | 사람 확인 필요 |
| `CANCELLED` | 사용자가 실행 취소 |

## 2. TestResult

| 결과 | 설명 |
|---|---|
| `P` | Pass |
| `F` | Fail |
| `N/A` | 실행 완료 상태가 아니거나 assertion 없음 |

`testResult`는 `executionStatus = COMPLETED`인 경우에만 `P` 또는 `F`가 될 수 있다.

---

## 3. FailureCause (실패 원인 분류)

### 3.1 기본 원칙

실패 원인은 자유 텍스트만으로 기록하지 않는다. 통계와 개선 우선순위 분석을 위해 enum 값으로 고정한다.

### 3.2 FailureCause 목록

| 값 | 설명 |
|---|---|
| `PRODUCT_DEFECT` | 제품 기능 자체의 결함 가능성 |
| `MAPPING_ERROR` | DOM elementId 또는 selector 매핑 실패 |
| `SCRIPT_ERROR` | 실행계획 또는 Playwright 명령 오류 |
| `TEST_DATA_ERROR` | 입력 데이터, 중복 데이터, 테스트 데이터 문제 |
| `ENVIRONMENT_ERROR` | 서버, 네트워크, 브라우저, 계정 상태 문제 |
| `PRECONDITION_NOT_MET` | 사전조건 미충족 |
| `RISK_BLOCKED` | 리스크 정책에 의해 실행 차단 |
| `MANUAL_REVIEW_REQUIRED` | 자동 판단 불가, 사람 검토 필요 |
| `UNKNOWN` | 원인 불명 |

### 3.3 실패 분석 예시

```json
{
  "tcId": "TC_001-001",
  "executionStatus": "SCRIPT_FAILED",
  "failureCause": "MAPPING_ERROR",
  "summary": "저장 버튼에 해당하는 elementId를 실행 시점에 찾지 못했습니다.",
  "recommendedReview": "DOM을 다시 캡처하거나 저장 버튼의 label/nearbyText를 확인하세요."
}
```

---

## 4. RunResult 구조

RunResult는 실행 완료 후 생성되는 결과 데이터다.

### 4.1 예시

```json
{
  "schemaVersion": "0.3",
  "runId": "RUN_20260515_001",
  "projectId": "PROJECT_USER_MANAGEMENT",
  "executionPlanId": "PLAN_TC_001_001",
  "startedAt": "2026-05-15T11:00:00+09:00",
  "endedAt": "2026-05-15T11:01:20+09:00",
  "environment": {
    "environmentType": "staging",
    "baseUrl": "https://example.com/admin",
    "browser": "chromium",
    "headless": false
  },
  "summary": {
    "totalSteps": 5,
    "passedSteps": 5,
    "failedSteps": 0,
    "executionStatus": "COMPLETED",
    "testResult": "P"
  },
  "stepResults": [],
  "assertionResults": [],
  "createdDataRegistryId": "CDR_001",
  "evidence": {
    "screenshots": [],
    "videos": [],
    "logs": []
  }
}
```

### 4.2 StepResult

```json
{
  "stepId": "STEP_004",
  "status": "PASSED",
  "startedAt": "2026-05-15T11:00:30+09:00",
  "endedAt": "2026-05-15T11:00:35+09:00",
  "message": "저장 버튼 클릭 완료",
  "currentUrl": "https://example.com/admin/users",
  "screenshotPath": "evidence/STEP_004.png"
}
```

### 4.3 StepResult status

| 값 | 설명 |
|---|---|
| `PASSED` | step 성공 |
| `FAILED` | step 실패 |
| `SKIPPED` | 건너뜀 |
| `BLOCKED` | 정책 또는 사전조건으로 차단 |
| `REVIEW_REQUIRED` | 사람 검토 필요 |

---

## 5. FailurePackage 구조

FailurePackage는 실패분석을 위해 LLM 또는 사람이 참고하는 패키지다.

단순 에러 메시지가 아니라 실패 당시의 맥락을 포함해야 한다.

### 5.1 포함 항목

- testcase
- executionPlan
- failedStep
- pageState
- domSummary
- elementRegistry 일부
- testDataSnapshot
- currentUrl
- visibleTexts
- screenshotPath
- consoleErrors
- networkErrors
- riskCheckResult
- previousStepResults

### 5.2 예시

```json
{
  "schemaVersion": "0.3",
  "failurePackageId": "FAIL_001",
  "runId": "RUN_20260515_001",
  "tcId": "TC_001-001",
  "executionPlanId": "PLAN_TC_001_001",
  "failureType": "EXECUTION_FAILURE",
  "executionStatus": "PAGE_STATE_MISMATCH",
  "testResult": null,
  "failedStep": {
    "stepId": "STEP_003",
    "expectedPageStateId": "PAGE_002",
    "actualUrl": "https://example.com/admin/users",
    "message": "사용자 등록 화면에서 입력해야 하지만 현재 사용자 목록 화면으로 판단됨"
  },
  "context": {
    "visibleTexts": ["사용자 목록", "검색", "등록"],
    "screenshotPath": "evidence/FAIL_001.png",
    "consoleErrors": [],
    "networkErrors": []
  },
  "suggestedAnalysisPromptInput": true
}
```

### 5.3 failureType

| 값 | 설명 |
|---|---|
| `TEST_FAILURE` | TC는 실행 완료되었으나 assertion 실패 |
| `EXECUTION_FAILURE` | 자동화 수행 자체 실패 |
| `RISK_BLOCKED` | 리스크 정책으로 실행 차단 |
| `MANUAL_REQUIRED` | 자동 판단 불가, 사람 검토 필요 |

---

## 6. FailureAnalysis (GPT 응답)

failure-package를 입력으로 GPT가 생성하는 분석 결과.

```json
{
  "tcId": "TC_001-001",
  "failureSummary": "사용자 등록 화면으로 이동하지 못해 입력 단계가 실패했습니다.",
  "likelyCauseCategory": "MAPPING_ERROR",
  "recommendedReview": "등록 버튼의 elementId를 다시 확인하세요. data-testid가 변경되었을 가능성이 있습니다.",
  "suggestedNextAction": "DOM 재캡처 후 실행계획 재생성",
  "finalResult": "MANUAL_REVIEW"
}
```

### 6.1 likelyCauseCategory

| 값 | 설명 |
|---|---|
| `APPLICATION_DEFECT` | 제품 결함 가능성 |
| `EXPECTED_RESULT_MISMATCH` | 기대결과 자체가 잘못 작성됨 |
| `MAPPING_ERROR` | 요소 매핑 실패 |
| `SCRIPT_ERROR` | 스크립트 오류 |
| `ENVIRONMENT_ERROR` | 환경 문제 |
| `DATA_ISSUE` | 데이터 문제 |
| `PERMISSION_OR_SESSION` | 권한/세션 문제 |
| `UNKNOWN` | 원인 불명 |

### 6.2 finalResult

| 값 | 설명 |
|---|---|
| `F` | 최종 Fail로 확정 |
| `MANUAL_REVIEW` | 사람 검토 필요 |
| `NOT_A_PRODUCT_FAILURE` | 제품 결함 아님 (자동화/환경 문제) |

---

## 7. 보고서 품질 게이트

- 실행 상태와 P/F 결과 분리
- 실패 원인 enum 표시
- 증적 파일 경로 연결
- 실행 당시 URL, 앱 버전, schemaVersion 기록
- 한글 Windows에서 Excel 깨짐 방지 (UTF-8)
