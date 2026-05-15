---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 04-page-state-dom.md
  - 06-risk-policy.md
  - 07-test-data.md
  - 08-assertion-policy.md
  - 11-runner-design.md
---

# ExecutionPlan 설계

## 1. ExecutionPlan의 목적

ExecutionPlan은 AI 탐색 결과와 사람 검토를 거쳐 실제 Playwright Runner가 실행할 수 있도록 확정된 테스트 실행계획이다.

ExecutionPlan은 단순한 클릭 순서가 아니다. 다음 정보를 함께 포함해야 한다.

- 어떤 테스트케이스를 실행하는지
- 어떤 PageState에서 시작하는지
- 어떤 테스트 데이터를 사용하는지
- 어떤 step을 수행하는지
- 어떤 화면 상태 전환을 기대하는지
- 어떤 assertion으로 P/F를 판단하는지
- 어떤 리스크 검사를 통과했는지
- 어떤 다이얼로그/모달을 처리해야 하는지
- 실행 후 어떤 데이터를 정리해야 하는지

실행계획은 GPT가 생성할 수 있지만, 앱은 이를 비신뢰 입력으로 취급한다.

---

## 2. CRUD 자동화 목표

MVP는 최소한 일반적인 CRUD 업무 흐름을 지원해야 한다.

| 유형 | 목표 |
|---|---|
| Create | 등록 화면 이동, 필수값 입력, 저장, 성공 여부 확인 |
| Read | 목록 조회, 검색, 상세 조회, 결과 표시 확인 |
| Update | 기존 항목 선택, 수정, 저장, 변경 결과 확인 |
| Delete | 삭제 또는 비활성화 요청, 확인 메시지 처리, 목록 반영 확인 |

CRUD는 단일 화면이 아니라 여러 PageState로 구성한다.

```text
PAGE_001: 목록 화면
PAGE_002: 등록 화면
PAGE_003: 상세 화면
PAGE_004: 수정 화면
PAGE_005: 삭제 확인 모달
```

---

## 3. ExecutionPlan 전체 예시

```json
{
  "schemaVersion": "0.3",
  "executionPlanId": "PLAN_TC_001_001",
  "tcId": "TC_001-001",
  "source": {
    "explorationSessionId": "EXP_20260515_001",
    "candidateCrudFlowId": "CRUD_001",
    "generatedBy": "AI_EXPLORATION",
    "reviewedByHuman": true
  },
  "name": "사용자 등록 후 목록 표시 확인",
  "description": "사용자 목록 화면에서 신규 사용자를 등록하고 목록 테이블에 표시되는지 확인한다.",
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
  "steps": [
    {
      "stepId": "STEP_001",
      "stepType": "ACTION",
      "pageStateId": "PAGE_001",
      "action": "click",
      "elementId": "PAGE_001.el_0001",
      "description": "등록 버튼 클릭",
      "expectedTransition": {
        "type": "URL_CHANGE_OR_DOM_CHANGE",
        "expectedNextPageStateId": "PAGE_002",
        "urlPattern": "/users/new",
        "requiredTexts": ["사용자 등록", "저장"]
      },
      "riskCheck": {
        "riskLevel": "LOW",
        "riskFlags": [],
        "requiresApproval": false
      }
    },
    {
      "stepId": "STEP_002",
      "stepType": "ACTION",
      "pageStateId": "PAGE_002",
      "action": "fill",
      "elementId": "PAGE_002.el_0010",
      "valueSource": "UNIQUE_USER_ID",
      "description": "사용자 ID 입력"
    },
    {
      "stepId": "STEP_003",
      "stepType": "ACTION",
      "pageStateId": "PAGE_002",
      "action": "fill",
      "elementId": "PAGE_002.el_0011",
      "valueSource": "USER_NAME",
      "description": "사용자명 입력"
    },
    {
      "stepId": "STEP_004",
      "stepType": "ACTION",
      "pageStateId": "PAGE_002",
      "action": "click",
      "elementId": "PAGE_002.el_0020",
      "description": "저장 버튼 클릭",
      "expectedTransition": {
        "type": "URL_CHANGE_OR_TEXT_APPEAR",
        "expectedNextPageStateId": "PAGE_001",
        "urlPattern": "/users",
        "requiredTexts": ["저장되었습니다"]
      },
      "riskCheck": {
        "riskLevel": "MEDIUM",
        "riskFlags": [],
        "requiresApproval": false
      }
    },
    {
      "stepId": "ASSERT_001",
      "stepType": "ASSERTION",
      "pageStateId": "PAGE_001",
      "assertion": "assertRowContains",
      "tableId": "TABLE_USERS",
      "expectedValueSource": "USER_NAME",
      "description": "사용자 목록 테이블에 신규 사용자명이 표시되는지 확인"
    }
  ],
  "cleanupPlan": {
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
}
```

---

## 4. ExecutionPlan 상위 필드

| 필드 | 필수 | 설명 |
|---|---:|---|
| `schemaVersion` | 필수 | 실행계획 스키마 버전 |
| `executionPlanId` | 필수 | 실행계획 ID |
| `tcId` | 필수 | 연결된 테스트케이스 ID |
| `source` | 필수 | AI 탐색 세션, 후보 흐름, 생성 방식 정보 |
| `name` | 필수 | 실행계획 이름 |
| `description` | 권장 | 실행 목적 설명 |
| `startPageStateId` | 필수 | 실행 시작 화면 상태 |
| `requiredPageStateIds` | 필수 | 실행 중 필요한 PageState 목록 |
| `testDataProfileId` | 필수 | 사용할 테스트 데이터 프로필 |
| `variablesUsed` | 권장 | 실행 중 참조하는 변수 목록 |
| `riskSummary` | 필수 | 실행계획 전체 리스크 요약 |
| `planStatus` | 필수 | 실행계획 상태 |
| `steps` | 필수 | 실행 step 목록 |
| `cleanupPlan` | 선택 | 실행 후 데이터 정리 계획 |

### 4.1 planStatus

| 상태 | 설명 |
|---|---|
| `DRAFT` | AI가 생성했으나 검토 전 |
| `READY` | 실행 가능 |
| `NEEDS_MAPPING_REVIEW` | elementId 또는 PageState 매핑 검토 필요 |
| `NEEDS_RISK_APPROVAL` | HIGH 리스크 승인 필요 |
| `MANUAL_REQUIRED` | 자동 실행 부적합, 수동 확인 필요 |
| `NOT_AUTOMATABLE` | 현재 자동화 불가 |
| `REJECTED` | 사용자가 실행계획을 거부 |

---

## 5. ExecutionStep 구조

Step은 크게 다음으로 나눈다.

| stepType | 설명 |
|---|---|
| `ACTION` | 클릭, 입력, 선택 등 실제 조작 |
| `ASSERTION` | P/F 판단을 위한 검증 |
| `WAIT` | 화면 전환, 텍스트, 로딩 대기 |
| `DIALOG` | alert, confirm, prompt 처리 |
| `TABLE_ACTION` | 테이블 행 기준 액션 |
| `SCREENSHOT` | 증적 캡처 |
| `CLEANUP` | 테스트 데이터 정리 |

### 5.1 공통 필드

```json
{
  "stepId": "STEP_001",
  "stepType": "ACTION",
  "pageStateId": "PAGE_001",
  "description": "등록 버튼 클릭",
  "onFailure": "STOP_TC"
}
```

| 필드 | 필수 | 설명 |
|---|---:|---|
| `stepId` | 필수 | step ID |
| `stepType` | 필수 | step 유형 |
| `pageStateId` | 권장 | 해당 step이 실행될 화면 상태 |
| `description` | 권장 | 사람이 이해할 수 있는 설명 |
| `onFailure` | 선택 | 실패 시 처리 방식 |

### 5.2 onFailure

| 값 | 설명 |
|---|---|
| `STOP_TC` | 해당 TC 실행 중단 |
| `CONTINUE` | 실패를 기록하고 다음 step 진행 |
| `TAKE_SCREENSHOT_AND_STOP` | 스크린샷 저장 후 중단 |
| `MARK_MANUAL_REQUIRED` | 수동 확인 대상으로 표시 |

기본값은 `TAKE_SCREENSHOT_AND_STOP`이다.

---

## 6. ACTION Step

ACTION Step은 Playwright가 실제 UI 조작을 수행하는 단계다.

### 6.1 허용 ACTION 목록

| action | 설명 |
|---|---|
| `goto` | URL 이동 |
| `click` | 요소 클릭 |
| `fill` | 입력값 입력 |
| `selectOption` | select 선택 |
| `check` | 체크박스 선택 |
| `uncheck` | 체크박스 해제 |
| `uploadFile` | 파일 업로드 |
| `press` | 키 입력 |
| `hover` | 마우스 오버 |
| `clear` | 입력값 삭제 |
| `takeScreenshot` | 스크린샷 저장 |
| `waitForNavigation` | 화면 이동 대기 |
| `waitForLoadState` | 네트워크/DOM 안정화 대기 |

### 6.2 값 입력 방식

값은 직접 넣지 않고 가능한 한 `valueSource`를 사용한다.

```json
{
  "action": "fill",
  "elementId": "PAGE_002.el_0010",
  "valueSource": "UNIQUE_USER_ID"
}
```

직접 값 입력(`valueLiteral`)은 민감정보가 아니고 재현성에 문제가 없는 경우에만 허용한다.

---

## 7. ASSERTION Step

자세한 내용은 [`08-assertion-policy.md`](08-assertion-policy.md) 참고.

```json
{
  "stepId": "ASSERT_001",
  "stepType": "ASSERTION",
  "pageStateId": "PAGE_001",
  "assertion": "assertRowContains",
  "tableId": "TABLE_USERS",
  "expectedValueSource": "USER_NAME",
  "description": "사용자 목록에 등록한 사용자명이 표시되는지 확인"
}
```

---

## 8. WAIT Step

화면 전환, 텍스트 등장, 로딩 안정화를 명시적으로 대기한다.

```json
{
  "stepId": "WAIT_001",
  "stepType": "WAIT",
  "waitType": "TEXT_APPEAR",
  "expectedText": "저장되었습니다",
  "timeoutMs": 5000
}
```

| waitType | 설명 |
|---|---|
| `TEXT_APPEAR` | 특정 텍스트 등장 대기 |
| `ELEMENT_APPEAR` | 특정 요소 등장 대기 |
| `ELEMENT_DISAPPEAR` | 특정 요소 사라짐 대기 |
| `URL_MATCH` | URL이 패턴과 일치할 때까지 대기 |
| `LOAD_STATE` | 네트워크/DOM 안정화 대기 |

---

## 9. DIALOG Step

alert, confirm, prompt 또는 HTML 모달을 처리한다.

```json
{
  "stepId": "DIALOG_001",
  "stepType": "DIALOG",
  "dialogType": "confirm",
  "expectedTextContains": "정말 삭제하시겠습니까?",
  "response": "accept",
  "riskCheck": {
    "riskLevel": "HIGH",
    "riskFlags": ["DELETE_DATA"],
    "requiresApproval": true,
    "approvalScope": "PER_RUN",
    "reason": "삭제 확인창 승인"
  },
  "description": "삭제 확인창에서 확인 선택"
}
```

### 9.1 dialogType

| 값 | 설명 |
|---|---|
| `alert` | 브라우저 alert |
| `confirm` | 브라우저 confirm |
| `prompt` | 브라우저 prompt |
| `htmlModal` | DOM 기반 모달 |
| `toast` | 토스트 메시지 |
| `popup` | 새 창/새 탭 |

### 9.2 response

| 값 | 설명 |
|---|---|
| `accept` | 확인 |
| `dismiss` | 취소 |
| `fillAndAccept` | prompt 입력 후 확인 |
| `close` | HTML 모달 또는 popup 닫기 |
| `manual` | 사람 처리 필요 |

---

## 10. TABLE_ACTION Step

CRUD에서 수정/삭제는 대부분 특정 행 내부의 버튼을 눌러야 하므로 일반 click만으로는 부족하다.

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
  "expectedTransition": {
    "type": "URL_CHANGE_OR_DOM_CHANGE",
    "expectedNextPageStateId": "PAGE_004",
    "requiredTexts": ["사용자 수정", "저장"]
  },
  "description": "등록한 사용자 행의 수정 버튼 클릭"
}
```

### 10.1 rowMatch

| matchType | 설명 |
|---|---|
| `CONTAINS_VALUE` | 행 전체 텍스트에 특정 값 포함 |
| `CELL_EQUALS` | 특정 컬럼 값이 기대값과 같음 |
| `CELL_CONTAINS` | 특정 컬럼 값이 특정 문자열 포함 |
| `FIRST_ROW` | 첫 번째 행 선택 |
| `LAST_ROW` | 마지막 행 선택 |

MVP에서는 `CONTAINS_VALUE`를 기본으로 한다.

---

## 11. TransitionExpectation

TransitionExpectation은 어떤 step 이후 기대되는 화면 상태 변화를 정의한다.

```json
{
  "type": "MODAL_OPEN",
  "expectedNextPageStateId": "PAGE_005",
  "requiredTexts": ["정말 삭제하시겠습니까?", "확인", "취소"],
  "timeoutMs": 5000
}
```

### 11.1 전환 유형

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

### 11.2 전환 실패 처리

| 상황 | 처리 |
|---|---|
| URL 변경 기대했으나 변경 없음 | `NAVIGATION_FAILED` |
| 텍스트 등장 기대했으나 없음 | `NAVIGATION_FAILED` |
| 다음 PageState가 다름 | `PAGE_STATE_MISMATCH` |
| 모달이 떠야 하는데 안 뜸 | `NAVIGATION_FAILED` |
| 예상하지 못한 confirm 발생 | `DIALOG_UNHANDLED` |

---

## 12. CLEANUP Step과 CleanupPlan

자세한 내용은 [`07-test-data.md`](07-test-data.md) 참고.

```json
{
  "policy": "AUTO_CLEANUP_APPROVAL_REQUIRED",
  "items": [
    {
      "cleanupId": "CLEANUP_001",
      "entityType": "USER",
      "matchValueSource": "UNIQUE_USER_ID",
      "strategy": "DELETE_CREATED_ROW",
      "requiresApproval": true,
      "riskCheck": {
        "riskLevel": "HIGH",
        "riskFlags": ["DELETE_DATA"],
        "requiresApproval": true,
        "approvalScope": "PER_RUN"
      }
    }
  ]
}
```

---

## 13. ExecutionPlan과 PageState 연결

ExecutionPlan의 각 step은 자신이 실행되어야 할 PageState를 명시한다. Runner는 step 실행 전후로 PageState를 확인한다.

```text
step 실행 전:
- 현재 화면이 step.pageStateId와 맞는지 확인
- 맞지 않으면 PAGE_STATE_MISMATCH

step 실행 후:
- expectedNextPageStateId가 있으면 화면 전환 확인
- expectedNavigation 조건 확인
- 실패 시 NAVIGATION_FAILED 또는 PAGE_STATE_MISMATCH
```

---

## 14. 확정된 결정

| 항목 | 결정 |
|---|---|
| ExecutionPlan | TC 단위 실행계획으로 관리 |
| Step 유형 | ACTION, ASSERTION, WAIT, DIALOG, TABLE_ACTION, SCREENSHOT, CLEANUP |
| 화면 전환 | expectedTransition으로 표현 |
| 페이지 이동 표현 | URL 변경이 아니라 화면 상태 전환으로 일반화 |
| 리스크 검사 | step 단위 riskCheck 포함 |
| 테이블 행 액션 | clickRowAction 도입 |
| Cleanup | CleanupPlan 도입 |
