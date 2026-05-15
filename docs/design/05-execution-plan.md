---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 04-page-state-dom.md
  - 06-risk-policy.md
  - 08-assertion-policy.md
  - 09-run-result-failure.md
---

# 05. ExecutionPlan 설계

## 목적

`ExecutionPlan`은 AI 탐색 결과와 사람 검토를 거쳐 실제 Playwright Runner가 실행할 수 있도록 확정된 테스트 실행계획이다.

ExecutionPlan은 단순한 클릭 순서가 아니라 다음을 포함한다.

- 연결된 테스트케이스
- 시작 PageState
- 테스트 데이터
- 실행 step
- 화면 상태 전환 기대값
- assertion
- step 단위 riskCheck
- dialog/modal 처리
- table row action
- cleanupPlan

## ExecutionPlan 예시

```json
{
  "schemaVersion": "0.3",
  "executionPlanId": "PLAN_TC_001_001",
  "tcId": "TC_001-001",
  "name": "사용자 등록 후 목록 표시 확인",
  "startPageStateId": "PAGE_001",
  "requiredPageStateIds": ["PAGE_001", "PAGE_002"],
  "testDataProfileId": "PROFILE_DEFAULT",
  "variablesUsed": ["UNIQUE_USER_ID", "USER_NAME"],
  "riskSummary": {
    "maxRiskLevel": "MEDIUM",
    "riskFlags": [],
    "requiresApproval": false
  },
  "planStatus": "READY",
  "steps": [],
  "cleanupPlan": {
    "policy": "AUTO_CLEANUP_APPROVAL_REQUIRED",
    "items": []
  }
}
```

## planStatus

| 상태 | 설명 |
|---|---|
| `DRAFT` | AI가 생성했으나 검토 전 |
| `READY` | 실행 가능 |
| `NEEDS_MAPPING_REVIEW` | elementId 또는 PageState 매핑 검토 필요 |
| `NEEDS_RISK_APPROVAL` | HIGH 리스크 승인 필요 |
| `MANUAL_REQUIRED` | 자동 실행 부적합, 수동 확인 필요 |
| `NOT_AUTOMATABLE` | 현재 자동화 불가 |
| `REJECTED` | 사용자가 실행계획을 거부 |

## Step 유형

| stepType | 설명 |
|---|---|
| `ACTION` | 클릭, 입력, 선택 등 실제 조작 |
| `ASSERTION` | P/F 판단을 위한 검증 |
| `WAIT` | 화면 전환, 텍스트, 로딩 대기 |
| `DIALOG` | alert, confirm, prompt 처리 |
| `TABLE_ACTION` | 테이블 행 기준 액션 |
| `SCREENSHOT` | 증적 캡처 |
| `CLEANUP` | 테스트 데이터 정리 |

## ACTION Step

```json
{
  "stepId": "STEP_002",
  "stepType": "ACTION",
  "pageStateId": "PAGE_002",
  "action": "fill",
  "elementId": "PAGE_002.el_0010",
  "valueSource": "USER_NAME",
  "description": "사용자명 입력",
  "riskCheck": {
    "riskLevel": "LOW",
    "riskFlags": [],
    "requiresApproval": false
  }
}
```

## TABLE_ACTION Step

```json
{
  "stepId": "STEP_010",
  "stepType": "TABLE_ACTION",
  "pageStateId": "PAGE_001",
  "action": "clickRowAction",
  "tableId": "TABLE_USERS",
  "rowMatch": {
    "matchType": "CONTAINS_VALUE",
    "valueSource": "UNIQUE_USER_ID"
  },
  "actionText": "수정",
  "description": "등록한 사용자 행의 수정 버튼 클릭"
}
```

## TransitionExpectation

화면 이동은 URL 변경만 의미하지 않는다. 모달, DOM 변경, 탭 전환, 팝업도 모두 화면 상태 전환으로 본다.

| type | 설명 |
|---|---|
| `NONE` | 화면 변화 없음 |
| `URL_CHANGE` | URL 변경 기대 |
| `DOM_CHANGE` | URL은 그대로지만 DOM 변경 기대 |
| `TEXT_APPEAR` | 특정 텍스트 등장 기대 |
| `ELEMENT_APPEAR` | 특정 요소 등장 기대 |
| `MODAL_OPEN` | 모달 열림 기대 |
| `MODAL_CLOSE` | 모달 닫힘 기대 |
| `POPUP_OPEN` | 새 창/탭 열림 기대 |
| `DIALOG_OPEN` | alert/confirm/prompt 열림 기대 |
| `TAB_CHANGE` | 화면 내 탭 전환 기대 |
| `IFRAME_CHANGE` | iframe 내부 변경 기대 |
| `URL_CHANGE_OR_DOM_CHANGE` | URL 변경 또는 DOM 변경 중 하나 허용 |
| `URL_CHANGE_OR_TEXT_APPEAR` | URL 변경 또는 텍스트 등장 중 하나 허용 |

## CleanupPlan

```json
{
  "policy": "AUTO_CLEANUP_APPROVAL_REQUIRED",
  "items": [
    {
      "cleanupId": "CLEANUP_001",
      "entityType": "USER",
      "matchValueSource": "UNIQUE_USER_ID",
      "strategy": "DELETE_CREATED_ROW",
      "requiresApproval": true
    }
  ]
}
```

## 핵심 원칙

- `testResult`는 `executionStatus = COMPLETED`인 경우에만 부여한다.
- 각 step은 실행 전 riskCheck를 가져야 한다.
- 값 입력은 가능한 한 `valueSource`를 사용한다.
- row 기반 수정/삭제는 `TABLE_ACTION`을 사용한다.
- cleanup은 AutoWebTesting이 생성하고 추적한 데이터만 대상으로 한다.
