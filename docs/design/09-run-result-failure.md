---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 08-assertion-policy.md
---

# 09. RunResult / FailurePackage 설계

## 실패 구분

Failure는 두 가지로 구분한다.

| 구분 | 의미 | P/F 여부 |
|---|---|---|
| `TEST_FAILURE` | TC는 실행 완료되었으나 assertion 실패 | `F` |
| `EXECUTION_FAILURE` | 자동화 수행 자체가 중단되거나 불완전 | 없음 |

## ExecutionStatus

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

## FailureCause

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

## RunResult 예시

```json
{
  "schemaVersion": "0.3",
  "runId": "RUN_20260515_001",
  "projectId": "PROJECT_USER_MANAGEMENT",
  "executionPlanId": "PLAN_TC_001_001",
  "summary": {
    "totalSteps": 5,
    "passedSteps": 5,
    "failedSteps": 0,
    "executionStatus": "COMPLETED",
    "testResult": "P"
  },
  "stepResults": [],
  "assertionResults": [],
  "evidence": {
    "screenshots": [],
    "videos": [],
    "logs": []
  }
}
```

## FailurePackage 포함 항목

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
