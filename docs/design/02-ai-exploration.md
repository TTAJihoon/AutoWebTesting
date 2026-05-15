---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 01-mvp-scope.md
  - 04-page-state-dom.md
  - 05-execution-plan.md
  - 06-risk-policy.md
---

# AI 탐색 세션 설계

AutoWebTesting의 핵심 목표는 사용자가 URL, 계정 정보, 시험 방법 설명을 입력하면 AI가 웹 제품을 탐색하고, 실제 제품 형상에 기반하여 테스트케이스와 실행계획 후보를 생성하는 것이다.

## 1. LLM 사용 모드

### 1.1 GPT Web Import Mode

GPT Web Import Mode는 앱이 직접 LLM API를 호출하지 않는 방식이다. 사용자는 제공된 프롬프트 파일을 GPT 웹페이지에 붙여넣고 JSON 결과를 저장한 뒤 앱에 업로드한다.

**장점**

- 외부 API 키가 필요 없다.
- API 비용 구조를 앱이 직접 관리하지 않아도 된다.
- 보안상 민감한 조직에서 도입 부담이 낮다.
- 사용자가 GPT 출력 내용을 직접 확인할 수 있다.

**단점**

- 복사/붙여넣기 과정이 번거롭다.
- 탐색 루프를 자동화하기 어렵다.
- GPT가 JSON 외 설명을 붙일 수 있다.
- 사용자가 잘못된 파일을 업로드할 수 있다.

### 1.2 API Mode

API Mode는 앱이 LLM API를 직접 호출하여 테스트케이스 생성, 실행계획 생성, 실패분석, 탐색 판단을 자동 수행하는 방식이다.

AI 탐색 기반 MVP를 구현하려면 장기적으로 API Mode 또는 로컬 LLM 어댑터가 필요하다. URL만 주고 웹앱을 탐색하려면 다음 루프가 반복되어야 하기 때문이다.

```text
현재 화면 관찰
→ LLM 판단
→ 다음 행동 선택
→ Playwright 실행
→ 새 화면 관찰
→ LLM 판단
→ 반복
```

### 1.3 공통 원칙

GPT Web Import Mode와 API Mode는 입력 방식만 다르다. 내부 데이터 계약은 동일해야 한다.

```text
GPT 웹 결과든 API 결과든
→ 동일한 JSON 스키마 검증
→ 동일한 사람 검토
→ 동일한 리스크 정책
→ 동일한 실행 엔진
```

---

## 2. AI 탐색 모드

사용자는 다음 정보를 입력한다.

- 대상 URL
- 계정 정보
- 시험 방법 설명
- 선택 입력: 기능목록 Excel
- 선택 입력: 제품 매뉴얼
- 선택 입력: 테스트 제외 조건

앱은 다음 과정을 수행한다.

```text
1. 대상 URL 접속
2. 로그인 수행
3. 현재 화면 DOM Summary 생성
4. AI가 화면 목적과 주요 기능 후보 판단
5. AI가 다음 탐색 행동 후보 제안
6. Risk Policy가 위험 행동 차단
7. Playwright가 안전한 행동 실행
8. 새 PageState 캡처
9. PageFlow 후보 생성
10. CRUD 후보 흐름 발견
11. TestCase 후보 생성
12. ExecutionPlan 후보 생성
13. 사람 검토 및 승인
```

### 2.1 AI 탐색 루프 단위

```json
{
  "observation": {
    "pageStateId": "PAGE_001",
    "url": "https://example.com/users",
    "title": "사용자 관리",
    "visibleTexts": ["사용자 목록", "검색", "등록"],
    "elements": []
  },
  "taskContext": {
    "goal": "사용자 관리 기능의 CRUD 흐름을 탐색한다.",
    "allowedRiskLevel": "MEDIUM",
    "forbiddenActions": ["PAYMENT", "SEND_EXTERNAL_MESSAGE"]
  },
  "aiDecision": {
    "intent": "DISCOVER_CREATE_FLOW",
    "action": "click",
    "elementId": "PAGE_001.el_0001",
    "reason": "등록 버튼으로 판단되며 Create 흐름 탐색에 필요합니다.",
    "riskLevel": "LOW",
    "expectedOutcome": "사용자 등록 화면으로 이동"
  }
}
```

### 2.2 탐색 모드와 실행 모드의 분리

| 구분 | 탐색 모드 | 실행 모드 |
|---|---|---|
| 목적 | 기능과 화면 흐름 발견 | 승인된 TC 반복 실행 |
| 판단 주체 | AI + 정책 엔진 + 사람 검토 | Playwright Runner |
| 실행계획 | 생성 중인 후보 | 승인된 계획 |
| 결과 | PageState, PageFlow, TC 후보 | P/F 결과, 증적, 보고서 |
| 위험도 | 상대적으로 높음 | 통제 가능 |
| 재현성 | 낮을 수 있음 | 높아야 함 |

탐색 모드는 유연해야 하지만, 실행 모드는 재현 가능해야 한다.

```text
AI 탐색 모드
→ 후보 생성
→ 사람 검토 및 승인
→ 정식 실행계획 저장
→ 실행 모드에서 반복 실행
```

### 2.3 AI 탐색의 안전장치

탐색 중에도 다음 안전장치를 적용한다.

- 허용 액션 whitelist
- 리스크 키워드 탐지
- HIGH 이상 행동 실행 전 사람 승인
- PROHIBITED 행동 자동 차단
- 비밀번호/토큰 등 secret 값 LLM 전달 금지
- 삭제, 결제, 외부 발송, 권한 변경은 기본 차단
- AI 판단 결과와 실제 실행 결과를 모두 로그로 저장

### 2.4 AI 탐색의 중단 조건

```text
- 최대 탐색 step 수 도달
- 최대 PageState 수 도달
- 동일 화면 반복 감지
- 위험 행동 후보만 남음
- 로그인 실패
- 세션 만료
- 사용자가 중단
- AI가 더 이상 유의미한 후보가 없다고 판단
```

권장 기본값:

| 항목 | 기본값 |
|---|---:|
| 최대 탐색 step | 50 |
| 최대 PageState | 20 |
| 동일 URL 반복 허용 | 3회 |
| 동일 action 반복 허용 | 2회 |
| HIGH 행동 자동 실행 | 금지 |

---

## 3. 핵심 개념

| 개념 | 설명 |
|---|---|
| `ExplorationSession` | 한 번의 AI 탐색 작업 전체 |
| `Observation` | 현재 화면을 AI가 판단할 수 있도록 정리한 관찰 데이터 |
| `AiDecision` | AI가 현재 화면을 보고 다음 행동 또는 판단을 제안한 결과 |
| `ExplorationAction` | AI 결정에 따라 실제로 수행할 탐색 행동 |
| `ExplorationMemory` | 이미 방문한 화면, 시도한 행동, 발견한 기능 후보를 저장하는 탐색 기억 |
| `CandidateFeature` | AI가 발견한 기능 후보 |
| `CandidateCrudFlow` | AI가 발견한 CRUD 흐름 후보 |
| `HumanReviewGate` | 사람 검토 또는 승인이 필요한 지점 |

---

### 3.1 ExplorationSession

`ExplorationSession`은 하나의 URL 또는 하나의 제품을 대상으로 수행한 AI 탐색 작업 전체를 의미한다.

**예시**

```json
{
  "explorationSessionId": "EXP_20260515_001",
  "projectId": "PROJECT_USER_MANAGEMENT",
  "targetUrl": "https://example.com/admin",
  "goal": "사용자 관리 기능의 CRUD 흐름을 탐색하고 테스트케이스 후보를 생성한다.",
  "inputSources": {
    "featureList": true,
    "manual": true,
    "webShape": true
  },
  "mode": "AI_ASSISTED_EXPLORATION",
  "llmMode": "GPT_WEB_IMPORT_OR_API_ADAPTER",
  "environmentType": "staging",
  "riskPolicyId": "RISK_DEFAULT",
  "testDataProfileId": "PROFILE_DEFAULT",
  "status": "IN_PROGRESS",
  "startedAt": "2026-05-15T10:00:00+09:00",
  "endedAt": null,
  "summary": {
    "visitedPageStates": 0,
    "candidateFeatures": 0,
    "candidateCrudFlows": 0,
    "blockedActions": 0,
    "reviewRequiredItems": 0
  }
}
```

---

### 3.2 Observation

`Observation`은 특정 시점의 화면을 AI가 판단할 수 있도록 정리한 관찰 데이터다. DOM Summary, 가시 텍스트, 테이블 정보, 폼 정보, 현재 URL, 이전 행동 결과, 필요 시 스크린샷 정보를 포함한다.

**예시**

```json
{
  "observationId": "OBS_001",
  "explorationSessionId": "EXP_20260515_001",
  "pageStateId": "PAGE_001",
  "url": "https://example.com/admin/users",
  "title": "사용자 관리",
  "observationType": "TEXT_DOM_PRIMARY",
  "pageStateGuess": {
    "name": "사용자 목록 화면",
    "confidence": 0.88,
    "reason": "사용자 목록, 검색, 등록 버튼, 사용자 테이블이 확인됨"
  },
  "domSummaryId": "DOM_001",
  "elementRegistryId": "REG_001",
  "visibleTexts": ["사용자 목록", "검색", "등록", "사용자명", "상태"],
  "forms": [
    { "formId": "FORM_SEARCH", "label": "검색 조건", "fields": ["사용자명", "상태"] }
  ],
  "tables": [
    { "tableId": "TABLE_USERS", "label": "사용자 목록 테이블", "columns": ["사용자명", "아이디", "상태", "관리"] }
  ],
  "screenshot": {
    "available": true,
    "path": "observations/OBS_001.png",
    "sendToLlm": "OPTIONAL_ON_AMBIGUITY"
  },
  "previousActionResult": null,
  "createdAt": "2026-05-15T10:01:00+09:00"
}
```

**Observation 유형**

| 유형 | 설명 |
|---|---|
| `TEXT_DOM_PRIMARY` | DOM Summary와 텍스트 정보 중심 관찰 |
| `TEXT_DOM_WITH_IMAGE` | DOM Summary와 스크린샷을 함께 사용하는 관찰 |
| `IMAGE_ASSISTED_ONLY` | DOM 정보가 부족해 이미지 판단을 보조로 사용하는 관찰 |
| `ERROR_STATE` | 오류 화면 또는 예외 상태 관찰 |
| `UNKNOWN_STATE` | 기존 PageState와 매칭되지 않는 화면 관찰 |

---

### 3.3 AiDecision

`AiDecision`은 AI가 Observation을 보고 내린 판단 결과다. 자유로운 자연어 응답이 아니라 구조화된 JSON이어야 한다.

**예시**

```json
{
  "aiDecisionId": "DEC_001",
  "observationId": "OBS_001",
  "decisionType": "NEXT_ACTION",
  "intent": "DISCOVER_CREATE_FLOW",
  "proposedAction": {
    "action": "click",
    "elementId": "PAGE_001.el_0001",
    "description": "등록 버튼을 클릭하여 사용자 등록 화면을 탐색한다."
  },
  "expectedOutcome": {
    "transitionType": "URL_CHANGE_OR_DOM_CHANGE",
    "expectedTexts": ["사용자 등록", "저장"],
    "expectedPageStateName": "사용자 등록 화면"
  },
  "riskAssessment": {
    "riskLevel": "LOW",
    "riskFlags": [],
    "reason": "등록 화면으로 이동하는 버튼으로 판단되며 실제 데이터 변경은 아직 발생하지 않음"
  },
  "confidence": 0.86,
  "reason": "현재 화면에서 등록 버튼은 Create 흐름을 시작하는 대표적인 요소임",
  "requiresHumanReview": false
}
```

**decisionType**

| 값 | 설명 |
|---|---|
| `CLASSIFY_PAGE` | 현재 화면의 의미를 분류 |
| `DISCOVER_FEATURES` | 기능 후보 추출 |
| `NEXT_ACTION` | 다음 탐색 행동 제안 |
| `CREATE_PAGE_STATE` | 새 PageState 후보 생성 |
| `CREATE_PAGE_FLOW` | 화면 전환 후보 생성 |
| `CREATE_TESTCASE_CANDIDATE` | 테스트케이스 후보 생성 |
| `CREATE_EXECUTION_PLAN_CANDIDATE` | 실행계획 후보 생성 |
| `STOP_EXPLORATION` | 탐색 종료 제안 |

---

### 3.4 ExplorationAction

`ExplorationAction`은 AiDecision을 바탕으로 실제 Playwright가 수행하는 탐색 행동이다. AiDecision이 제안했다고 해서 무조건 실행하지 않는다. 실행 전 Risk Policy Engine이 다시 검사한다.

**예시**

```json
{
  "explorationActionId": "ACT_001",
  "aiDecisionId": "DEC_001",
  "action": "click",
  "pageStateId": "PAGE_001",
  "elementId": "PAGE_001.el_0001",
  "riskCheck": {
    "allowed": true,
    "effectiveRiskLevel": "LOW",
    "matchedRiskKeywords": []
  },
  "status": "EXECUTED",
  "result": {
    "transitionDetected": true,
    "newObservationId": "OBS_002",
    "newPageStateCandidateId": "PAGE_002"
  },
  "executedAt": "2026-05-15T10:02:00+09:00"
}
```

**ExplorationAction 상태**

| 상태 | 설명 |
|---|---|
| `PENDING` | 실행 대기 |
| `EXECUTED` | 실행 완료 |
| `BLOCKED_BY_RISK` | 리스크 정책으로 차단 |
| `REVIEW_REQUIRED` | 사람 승인 필요 |
| `FAILED` | Playwright 실행 실패 |
| `SKIPPED` | 중복 또는 불필요 판단으로 건너뜀 |

---

### 3.5 ExplorationMemory

`ExplorationMemory`는 탐색 중 이미 확인한 화면, 행동, 후보 기능을 기억하는 구조다. AI 탐색에서 가장 흔한 문제는 같은 화면을 반복하거나, 같은 버튼을 계속 누르는 것이다.

**저장 항목**

- 방문한 URL
- 방문한 PageState
- 시도한 elementId/action 조합
- 실패한 action
- 위험 차단된 action
- 발견한 기능 후보
- 발견한 CRUD 흐름 후보
- 이미 생성한 테스트케이스 후보

---

### 3.6 CandidateFeature

`CandidateFeature`는 AI가 탐색 중 발견한 기능 후보이다. 기능목록이나 매뉴얼에 없더라도 실제 웹 형상에서 발견되면 후보로 기록한다.

**featureType 후보**

| 값 | 설명 |
|---|---|
| `CRUD_MANAGEMENT` | 등록/조회/수정/삭제 관리 기능 |
| `SEARCH_FILTER` | 검색/필터 기능 |
| `DETAIL_VIEW` | 상세 조회 기능 |
| `STATUS_CHANGE` | 승인/반려/활성화/비활성화 등 상태 변경 |
| `FILE_UPLOAD` | 파일 업로드 |
| `FILE_DOWNLOAD` | 파일 다운로드 |
| `EXTERNAL_SEND` | SMS, 메일, 푸시 등 외부 발송 |
| `AUTHENTICATION` | 로그인/로그아웃/계정 관련 기능 |
| `AUTHORIZATION` | 권한/역할 관련 기능 |
| `REPORT_DASHBOARD` | 통계/대시보드/리포트 |
| `UNKNOWN` | 분류 불명 |

---

### 3.7 CandidateCrudFlow

`CandidateCrudFlow`는 AI가 발견한 CRUD 흐름 후보이다.

**예시**

```json
{
  "candidateCrudFlowId": "CRUD_001",
  "featureId": "FEAT_001",
  "name": "사용자 기본 CRUD 흐름",
  "entityName": "사용자",
  "supportedOperations": ["CREATE", "READ", "UPDATE", "DELETE"],
  "pageStateIds": ["PAGE_001", "PAGE_002", "PAGE_003", "PAGE_004"],
  "flowSummary": {
    "create": "목록 화면에서 등록 버튼 클릭 후 등록 화면에서 저장",
    "read": "목록 화면에서 검색 후 결과 테이블 확인",
    "update": "목록 행의 수정 버튼 클릭 후 값 변경",
    "delete": "자동 생성한 사용자 행의 삭제 버튼 클릭 후 확인"
  },
  "riskAssessment": {
    "deleteRisk": "HIGH_APPROVAL_REQUIRED",
    "reason": "삭제는 자동 생성한 테스트 데이터에 대해서만 허용"
  },
  "reviewStatus": "DRAFT",
  "confidence": 0.82
}
```

---

### 3.8 HumanReviewGate

`HumanReviewGate`는 사람 검토 또는 승인이 필요한 지점을 의미한다. AutoWebTesting은 대부분의 과정을 자동화하되, 위험하거나 불확실한 판단은 사람에게 넘긴다.

**검토가 필요한 경우**

| 상황 | 처리 |
|---|---|
| HIGH 리스크 행동 | 실행 전 승인 필요 |
| PROHIBITED 후보 | 기본 차단, 예외 승인 불가 또는 관리자 승인 필요 |
| 삭제/발송/결제/권한변경 | 승인 필요 |
| AI confidence 낮음 | 검토 필요 |
| 동일 후보가 여러 개 | 사용자가 선택 |
| 화면 의미 불명확 | PageState 이름 확인 필요 |
| 자동 생성 TC 과다 | 사용자가 실행 대상 선별 |

---

## 4. 이미지/스크린샷 기반 관찰 전략

### 4.1 문제의식

AI 에이전트가 화면을 판단할 때 DOM 텍스트뿐 아니라 스크린샷 또는 시각 정보를 함께 활용할 가능성이 높다.

다만 모든 단계에서 이미지를 LLM에 전달하면 다음 문제가 생긴다.

- 비용 증가
- 처리 속도 저하
- 민감정보 노출 위험 증가
- 이미지 기반 판단의 재현성 저하
- 텍스트 DOM보다 구조화가 어려움

따라서 기본 전략은 **텍스트 DOM 우선, 이미지 선택 보강**으로 한다. 자세한 결정 근거는 [`ADR-002-dom-and-image-observation.md`](../decisions/ADR-002-dom-and-image-observation.md) 참고.

### 4.2 기본 원칙

```text
1. 기본 판단은 DOM Summary, visible text, form/table 구조를 사용한다.
2. 이미지 판단은 DOM만으로 불충분하거나 화면 배치/시각 정보가 중요한 경우에만 사용한다.
3. LLM에 이미지를 전달하기 전 민감정보 마스킹을 우선 적용한다.
4. 이미지 판단 결과도 구조화된 JSON으로 변환하여 저장한다.
5. 반복 실행은 이미지 판단에 의존하지 않고, 가능한 한 DOM/selector 기반으로 수행한다.
```

### 4.3 이미지가 필요한 경우

| 상황 | 이유 |
|---|---|
| 버튼 텍스트가 아이콘만 있는 경우 | DOM 텍스트만으로 의미 파악이 어려움 |
| 화면 레이아웃 이해가 필요한 경우 | 좌측 메뉴, 상단 탭, 모달 위치 등 판단 필요 |
| 테이블 구조가 DOM에서 명확하지 않은 경우 | 시각적으로는 표이지만 DOM이 div 기반일 수 있음 |
| 차트/그래프/대시보드 화면 | 텍스트만으로 화면 목적 파악이 어려움 |
| 캡처된 DOM에 label이 부족한 경우 | 입력칸 주변 배치로 의미 추론 필요 |
| 팝업/모달/토스트 위치 판단 | 화면 위에 겹쳐 표시되는 요소 확인 필요 |
| 디자인 기반 오류 확인 | 깨짐, 겹침, 가려짐 등 시각 결함 판단 |
| OCR이 필요한 이미지 텍스트 | DOM에 없는 텍스트가 화면에 표시될 수 있음 |

### 4.4 이미지 전송 전 마스킹

| 마스킹 대상 | 예시 |
|---|---|
| 비밀번호 입력값 | password field |
| 토큰/인증코드 | 긴 난수 문자열 |
| 주민번호/전화번호/이메일 | 개인정보 패턴 |
| 계정명 | 로그인 ID, 사용자명 |
| 고객명/기관명 | 민감 업무 데이터 |
| 금액/계약번호 | 업무상 민감정보 |

마스킹 전 원본 스크린샷은 로컬 증적용으로만 저장하고, LLM 전달용 이미지는 별도 masked 파일로 만든다.

### 4.5 이미지 사용 수준

| Level | 설명 | MVP 적용 |
|---|---|---|
| Level 0 | 이미지 미사용, DOM Summary만 사용 | 기본값 |
| Level 1 | 필요 시 이미지 보강 (label 부족, 아이콘, 모달 등) | 권장 |
| Level 2 | 모든 Observation에 스크린샷 포함 | 비권장 (비용/보안 부담) |

### 4.6 이미지 기반 판단의 한계

이미지에서 "저장 버튼"을 찾았다고 해도 Playwright가 클릭하려면 결국 DOM 요소나 좌표가 필요하다.

```text
이미지는 이해 보조용으로 사용한다.
실행은 가능한 한 ElementRegistry와 selectorCandidates 기반으로 수행한다.
이미지 기반 좌표 클릭은 최후 수단으로만 사용한다.
```

좌표 클릭은 다음 문제가 있으므로 기본적으로 피한다.

- 화면 해상도에 따라 위치가 달라짐
- 브라우저 줌 비율 영향
- 반응형 레이아웃 영향
- 스크롤 위치 영향
- 재현성 낮음
