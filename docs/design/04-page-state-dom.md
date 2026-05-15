---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 11-runner-design.md
---

# PageState, DOM Summary, ElementRegistry

CRUD 중심 다중 화면 자동화를 지원하려면 단순 DOM Summary만으로는 부족하다. 화면 상태를 구분하는 `PageState`, 화면 간 이동 관계를 표현하는 `PageFlow`, 실제 실행용 요소 매핑을 보관하는 `ElementRegistry`가 필요하다.

## 1. 설계 목표

1. 여러 화면에 걸친 CRUD 테스트를 표현할 수 있어야 한다.
2. GPT에는 단순하고 안전한 DOM Summary만 제공해야 한다.
3. 실제 Playwright 실행에는 앱 내부의 안정적인 selector 후보를 사용해야 한다.
4. 실행 실패 시 어느 화면, 어느 요소, 어느 selector 후보에서 실패했는지 추적할 수 있어야 한다.
5. 사용자가 수동으로 캡처한 화면과 실행 중 도달한 화면을 비교할 수 있어야 한다.

## 2. 핵심 개념 관계

```text
Project
└── PageState[]
    ├── DOM Summary
    └── Element Registry

TestCase
└── ExecutionPlan
    └── Step[]
        ├── pageStateId
        ├── elementId
        └── action

PageFlow
└── Transition[]
    ├── fromPageStateId
    ├── toPageStateId
    ├── triggerElementId
    └── expectedNavigation
```

| 개념 | 역할 |
|---|---|
| `PageState` | 특정 시점의 화면 상태를 식별한다. |
| `DOM Summary` | GPT에게 전달할 화면 요소 요약본이다. |
| `ElementRegistry` | 앱 내부에서 elementId를 실제 Playwright locator 후보와 연결한다. |
| `PageFlow` | 화면 간 이동 관계와 전환 조건을 표현한다. |
| `ExecutionPlan` | 테스트케이스를 실제 실행 가능한 step과 assertion으로 표현한다. |

---

## 3. PageState

### 3.1 정의

`PageState`는 테스트 자동화에서 구분해야 하는 하나의 화면 상태다.

웹앱에서는 URL이 같아도 상태가 다를 수 있다. 예를 들어 같은 `/users` URL이라도 검색 전 목록, 검색 후 목록, 모달이 열린 상태는 서로 다른 PageState로 볼 수 있다.

### 3.2 예시

```json
{
  "pageStateId": "PAGE_001",
  "name": "사용자 목록 화면",
  "description": "사용자 검색, 등록 버튼, 사용자 목록 테이블이 표시되는 화면",
  "url": "https://example.com/users",
  "urlPattern": "/users",
  "title": "사용자 관리",
  "stateType": "PAGE",
  "identityHints": {
    "requiredTexts": ["사용자 목록", "검색", "등록"],
    "requiredElementIds": ["PAGE_001.el_0001", "PAGE_001.el_0002"],
    "optionalTexts": ["전체", "사용자명"]
  },
  "domSummaryId": "DOM_001",
  "elementRegistryId": "REG_001",
  "capturedAt": "2026-05-14T14:30:22+09:00"
}
```

### 3.3 필드 정의

| 필드 | 필수 | 설명 |
|---|---:|---|
| `pageStateId` | 필수 | 화면 상태 ID. 예: `PAGE_001` |
| `name` | 필수 | 사람이 이해할 수 있는 화면 이름 |
| `description` | 권장 | 화면 역할 설명 |
| `url` | 권장 | 캡처 당시 실제 URL |
| `urlPattern` | 권장 | 화면 식별용 URL 패턴 |
| `title` | 권장 | 브라우저 title 또는 주요 화면 제목 |
| `stateType` | 필수 | `PAGE`, `MODAL`, `POPUP`, `DIALOG`, `PARTIAL` |
| `identityHints` | 필수 | 실행 중 현재 화면이 이 PageState인지 확인하기 위한 단서 |
| `domSummaryId` | 필수 | 연결된 DOM Summary ID |
| `elementRegistryId` | 필수 | 연결된 Element Registry ID |
| `capturedAt` | 필수 | 캡처 시각 |

### 3.4 stateType

| 값 | 설명 |
|---|---|
| `PAGE` | 일반 페이지 화면 |
| `MODAL` | HTML 기반 모달이 열린 상태 |
| `POPUP` | 새 브라우저 창 또는 탭 |
| `DIALOG` | alert, confirm, prompt 등 브라우저 다이얼로그 |
| `PARTIAL` | 페이지 일부 영역만 변경된 상태 |

### 3.5 identityHints

`identityHints`는 실행 중 현재 화면이 기대한 PageState와 일치하는지 확인하는 데 사용한다.

```json
{
  "requiredTexts": ["사용자 목록", "검색", "등록"],
  "requiredElementIds": ["PAGE_001.el_0001"],
  "optionalTexts": ["전체", "사용자명"]
}
```

**판단 방식**

- `requiredTexts` 중 일정 비율 이상이 화면에 보여야 한다.
- `requiredElementIds`는 ElementRegistry를 통해 실제 요소가 확인되어야 한다.
- `urlPattern`이 있으면 현재 URL과 함께 비교한다.
- 일치하지 않으면 `PAGE_STATE_MISMATCH` 또는 `MAPPING_FAILED`로 처리한다.

### 3.6 캡처 방식

MVP에서는 다음 방식을 채택한다.

```text
MVP:
- 사용자가 주요 CRUD 화면을 직접 이동하며 PageState 캡처
- 앱은 DOM Summary와 ElementRegistry 생성
- GPT는 여러 PageState의 DOM Summary를 참고하여 실행계획 생성

후속 Phase:
- 실행 중 예상하지 못한 화면 도달 시 자동 캡처
- PageState 후보 자동 생성
- 사용자 승인 후 저장
```

---

## 4. DOM Summary

### 4.1 목적

DOM Summary는 GPT가 실행계획을 만들 수 있도록 화면 요소를 요약한 JSON이다.

- 전체 HTML을 전달하지 않는다.
- 비밀번호, 토큰, 계정값 등 민감정보를 포함하지 않는다.
- GPT가 elementId를 선택할 수 있을 정도의 정보만 제공한다.
- 실제 Playwright selector는 포함하지 않는다.

### 4.2 예시

```json
{
  "schemaVersion": "0.2",
  "domSummaryId": "DOM_001",
  "pageStateId": "PAGE_001",
  "url": "https://example.com/users",
  "title": "사용자 관리",
  "capturedAt": "2026-05-14T14:30:22+09:00",
  "limits": {
    "maxElements": 250,
    "maxVisibleTexts": 80
  },
  "elements": [
    {
      "elementId": "PAGE_001.el_0001",
      "role": "button",
      "tag": "button",
      "type": null,
      "label": "등록",
      "text": "등록",
      "placeholder": null,
      "name": null,
      "required": false,
      "visible": true,
      "enabled": true,
      "nearbyText": "사용자 목록",
      "formId": null,
      "region": "toolbar"
    },
    {
      "elementId": "PAGE_001.el_0002",
      "role": "textbox",
      "tag": "input",
      "type": "text",
      "label": "사용자명",
      "text": null,
      "placeholder": "사용자명을 입력하세요",
      "name": "username",
      "required": false,
      "visible": true,
      "enabled": true,
      "nearbyText": "검색 조건",
      "formId": "FORM_SEARCH",
      "region": "search"
    }
  ],
  "visibleTexts": ["사용자 목록", "검색", "등록", "사용자명"],
  "forms": [
    {
      "formId": "FORM_SEARCH",
      "name": "검색 조건",
      "elementIds": ["PAGE_001.el_0002", "PAGE_001.el_0003"]
    }
  ],
  "tables": [
    {
      "tableId": "TABLE_USERS",
      "label": "사용자 목록 테이블",
      "elementId": "PAGE_001.el_0020",
      "columns": ["사용자명", "아이디", "상태", "관리"]
    }
  ]
}
```

### 4.3 Element 필드

| 필드 | 설명 |
|---|---|
| `elementId` | GPT와 실행계획에서 참조하는 요소 ID |
| `role` | 접근성 role 또는 추정 역할 |
| `tag` | HTML 태그명 |
| `type` | input type 등 |
| `label` | label, aria-label, nearby label 등에서 추출한 이름 |
| `text` | 요소 자체의 텍스트 |
| `placeholder` | placeholder 값 |
| `name` | name 속성 |
| `required` | 필수 입력 여부 |
| `visible` | 표시 여부 |
| `enabled` | 활성화 여부 |
| `nearbyText` | 주변 텍스트 |
| `formId` | 소속 폼 ID |
| `region` | 화면 내 영역 (`search`, `table`, `form`, `toolbar`, `modal`) |

### 4.4 elementId 형식

다중 페이지를 지원하기 위해 elementId는 PageState를 포함한다.

```text
PAGE_001.el_0001
PAGE_002.el_0001
PAGE_003.el_0001
```

이렇게 해야 서로 다른 화면의 `el_0001`이 충돌하지 않는다.

### 4.5 테이블 정보 필요성

CRUD 테스트에서는 목록 검증이 매우 중요하다. 따라서 DOM Summary에는 테이블 후보 정보를 별도로 포함한다.

**필요 이유**

- 등록 후 목록에 값이 표시되는지 확인
- 수정 후 특정 행 값이 변경되었는지 확인
- 삭제 후 특정 행이 사라졌는지 확인
- 검색 결과 개수를 검증

### 4.6 테이블 행 액션 후보

```json
{
  "tableId": "TABLE_USERS",
  "label": "사용자 목록 테이블",
  "rowActionCandidates": [
    { "actionText": "수정", "column": "관리", "riskLevel": "MEDIUM" },
    { "actionText": "삭제", "column": "관리", "riskLevel": "HIGH", "riskFlags": ["DELETE_DATA"] }
  ]
}
```

---

## 5. ElementRegistry

### 5.1 정의

`ElementRegistry`는 앱 내부에서만 사용하는 실행용 요소 매핑 정보다. GPT에는 전달하지 않는다.

`DOM Summary`가 GPT용 요약이라면, `ElementRegistry`는 Playwright 실행용 실제 locator 후보 목록이다.

### 5.2 예시

```json
{
  "schemaVersion": "0.2",
  "elementRegistryId": "REG_001",
  "pageStateId": "PAGE_001",
  "createdAt": "2026-05-14T14:30:22+09:00",
  "items": [
    {
      "elementId": "PAGE_001.el_0001",
      "selectorCandidates": [
        { "type": "role", "value": "button[name='등록']", "priority": 1, "confidence": 0.95 },
        { "type": "text", "value": "button:has-text('등록')", "priority": 2, "confidence": 0.85 },
        { "type": "css", "value": "[data-testid='create-user']", "priority": 3, "confidence": 0.9 }
      ],
      "stableHints": {
        "role": "button",
        "label": "등록",
        "text": "등록",
        "nearbyText": "사용자 목록",
        "formId": null,
        "region": "toolbar"
      },
      "lastKnownBounds": { "x": 812, "y": 140, "width": 80, "height": 36 }
    }
  ]
}
```

### 5.3 selectorCandidates 우선순위

selector 후보는 안정성이 높은 순서로 사용한다.

| 우선순위 | selector 유형 | 설명 |
|---:|---|---|
| 1 | `testId` | `data-testid`, `data-cy` 등 테스트 전용 속성 |
| 2 | `role` | Playwright getByRole 기반 locator |
| 3 | `label` | getByLabel 기반 locator |
| 4 | `placeholder` | getByPlaceholder 기반 locator |
| 5 | `text` | 텍스트 기반 locator |
| 6 | `css` | CSS selector |
| 7 | `xpath` | 최후 수단 |

### 5.4 selector 후보 생성 규칙

앱은 DOM 캡처 시 다음 정보를 기반으로 selectorCandidates를 생성한다.

- `data-testid`
- `data-cy`
- `aria-label`
- `role`
- label 연결
- placeholder
- button/link text
- name/id 속성
- 주변 텍스트
- form 내부 위치
- table column 정보

### 5.5 실행 시 element resolve 방식

```text
1. 현재 PageState 확인
2. elementId에 해당하는 registry item 조회
3. selectorCandidates를 priority 순서로 시도
4. visible/enabled 조건 확인
5. 후보가 여러 개면 stableHints로 재필터링
6. 하나로 확정되면 실행
7. 실패하면 MAPPING_FAILED 처리
```

### 5.6 매핑 로그 예시

```json
{
  "tcId": "TC_001-001",
  "stepId": "STEP_002",
  "pageStateId": "PAGE_001",
  "elementId": "PAGE_001.el_0001",
  "resolveAttempts": [
    { "selectorType": "role", "selector": "button[name='등록']", "result": "NOT_FOUND" },
    { "selectorType": "text", "selector": "button:has-text('등록')", "result": "MULTIPLE_MATCHES" },
    { "selectorType": "css", "selector": "[data-testid='create-user']", "result": "FOUND" }
  ],
  "finalResult": "FOUND"
}
```

### 5.7 매핑 실패 처리

실행 시점에 `elementId`를 실제 요소로 찾지 못하면 해당 step은 `MAPPING_FAILED`가 된다.

매핑 실패 시 저장해야 할 정보:

- tcId
- stepId
- pageStateId
- elementId
- selectorCandidates 시도 결과
- 현재 URL
- 현재 화면 제목
- 현재 가시 텍스트 요약
- 스크린샷 경로

---

## 6. PageFlow

### 6.1 정의

`PageFlow`는 화면 간 이동 관계를 표현한다. CRUD 테스트에서는 특정 버튼을 클릭하면 다른 화면이나 모달로 이동한다.

### 6.2 예시

```json
{
  "schemaVersion": "0.2",
  "flowId": "FLOW_USER_CRUD",
  "name": "사용자 CRUD 흐름",
  "description": "사용자 등록, 조회, 수정, 삭제 흐름",
  "startPageStateId": "PAGE_001",
  "transitions": [
    {
      "transitionId": "TR_001",
      "fromPageStateId": "PAGE_001",
      "toPageStateId": "PAGE_002",
      "trigger": {
        "action": "click",
        "elementId": "PAGE_001.el_0001",
        "description": "등록 버튼 클릭"
      },
      "expectedNavigation": {
        "type": "URL_CHANGE",
        "urlPattern": "/users/new",
        "requiredTexts": ["사용자 등록", "저장"]
      }
    }
  ]
}
```

### 6.3 expectedNavigation 유형

| 유형 | 설명 |
|---|---|
| `NONE` | 화면 전환 없음 |
| `URL_CHANGE` | URL 변경 기대 |
| `TEXT_APPEAR` | 특정 텍스트 등장 기대 |
| `ELEMENT_APPEAR` | 특정 요소 등장 기대 |
| `MODAL_OPEN` | 모달 열림 기대 |
| `POPUP_OPEN` | 새 창/탭 열림 기대 |
| `URL_CHANGE_OR_TEXT_APPEAR` | URL 변경 또는 텍스트 등장 중 하나 허용 |

### 6.4 PageFlow의 역할

MVP에서는 PageFlow를 "강제 실행 엔진"이 아니라 "검증 및 추적 보조 정보"로 사용한다.

- 실행계획이 올바른 화면 순서를 따르는지 검증
- 예상 화면 전환이 발생했는지 확인
- 실패 시 어느 전환에서 실패했는지 기록
- 향후 자동 PageState 캡처의 기반으로 활용

ExecutionPlan의 step이 실제 실행 순서를 결정하고, PageFlow는 그 순서가 예상 흐름과 맞는지 확인하는 기준이다.

---

## 7. 모달/팝업 처리

CRUD 자동화에서 모달과 팝업은 핵심이다.

### 7.1 모달/팝업 유형

| 유형 | 설명 | 처리 방식 |
|---|---|---|
| HTML Modal | DOM 내부에 표시되는 모달 | `PageState(stateType=MODAL)` |
| Drawer | 좌우측 슬라이드 패널 | `PageState(stateType=PARTIAL)` |
| Toast | 잠시 나타나는 성공/실패 메시지 | `assertToastVisible` |
| Alert | 브라우저 alert | Dialog event |
| Confirm | 브라우저 confirm | 위험도 판단 후 처리 |
| Prompt | 브라우저 prompt | 기본 수동 검토 |
| Popup Window | 새 창/새 탭 | `PageState(stateType=POPUP)` |
| iframe | 내부 프레임 | 제한 지원, 후속 고도화 |

### 7.2 모달 PageState 예시

```json
{
  "pageStateId": "PAGE_005",
  "name": "삭제 확인 모달",
  "stateType": "MODAL",
  "parentPageStateId": "PAGE_001",
  "identityHints": {
    "requiredTexts": ["정말 삭제하시겠습니까?", "확인", "취소"]
  },
  "riskAssessment": {
    "riskLevel": "HIGH",
    "riskFlags": ["DELETE_DATA"]
  }
}
```

### 7.3 Dialog 처리 정책

브라우저 confirm이 나타난 경우 다음 규칙을 적용한다.

```text
LOW 문구 → 자동 확인 가능
DELETE_DATA / PAYMENT / SEND_EXTERNAL_MESSAGE 키워드 포함 → 승인 필요
PROHIBITED 키워드 포함 → 차단
실행계획에 dialog 처리 step이 없음 → DIALOG_UNHANDLED
```

---

## 8. 확정된 결정

| 항목 | 결정 |
|---|---|
| PageState 도입 | 도입 |
| elementId 형식 | `PAGE_001.el_0001` 형식 사용 |
| DOM Summary | GPT 전달용 요약 정보로 사용 |
| ElementRegistry | 앱 내부 실행용 selector 후보 저장 |
| selectorCandidates GPT 전달 여부 | 전달하지 않음 |
| PageFlow | 실행 검증 및 추적 보조 정보로 사용 |
| PageState 캡처 방식 | MVP는 수동 캡처, 후속 자동 캡처 |
| PageState 확인 | step 실행 전후로 확인 |
