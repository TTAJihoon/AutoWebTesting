# AutoWebTesting 한글 통합 설계문서 v0.2

> 본 문서는 기존 `DESIGN.md`, `product-requirements.md`, `architecture.md`, `data-schema.md`, `gpt-web-workflow.md`, `prompt-specs.md`, `risk-policy.md`의 내용을 한글 기준으로 통합하고, 실무 적용 가능성을 높이기 위한 개선사항을 반영한 설계문서 초안이다.
>
> 본 문서는 개발 전 과정에서 참조하는 기준 문서로 사용한다.

---

## 1. 제품 개요

### 1.1 제품명

**AutoWebTesting**

### 1.2 제품 목적

AutoWebTesting은 비개발자 테스터, QA 담당자, 시험 담당자가 GPT의 도움을 받아 웹 기반 제품의 테스트케이스를 만들고, 실행계획을 검토한 뒤, Playwright를 통해 자동 실행하고, 결과 보고서와 증적을 생성할 수 있도록 지원하는 **Windows 11 데스크톱 앱**이다.

이 제품은 단순한 Playwright 코드 생성기가 아니다. 핵심은 다음 업무 흐름을 하나의 로컬 앱에서 관리하는 것이다.

```text
기능목록/매뉴얼 입력
→ GPT 기반 테스트케이스 생성
→ 사람 검토
→ 대상 웹 화면 분석
→ GPT 기반 실행계획 생성
→ 사람 검토
→ 안전 정책 검증
→ Playwright 실행
→ 결과/증적/보고서 생성
```

### 1.3 핵심 사용자

- 소프트웨어 시험 담당자
- QA 담당자
- 웹 서비스 검수 담당자
- 개발 지식은 많지 않지만 테스트 시나리오와 업무 흐름을 이해하는 실무자

### 1.4 핵심 원칙

| 원칙 | 설명 |
|---|---|
| 로컬 우선 | 기본 실행은 사용자의 PC에서 수행한다. |
| GPT 웹 임포트 우선 | MVP에서는 앱이 LLM API를 직접 호출하지 않고, 사용자가 GPT 웹에서 JSON을 생성해 앱에 업로드한다. |
| 안전 실행 | 리스크 정책을 통과한 실행계획만 Playwright로 실행한다. |
| 사람 검토 | GPT가 생성한 테스트케이스와 실행계획은 반드시 사람이 검토할 수 있어야 한다. |
| 제한된 자동화 | GPT가 만든 임의 코드를 실행하지 않고, 허용된 액션만 실행한다. |
| 추적 가능성 | 제외, 거부, 실패, 수동처리 대상도 이력으로 보존한다. |
| 실무 재현성 | 실행 당시의 DOM, 실행계획, 테스트 데이터, 로그, 증적을 함께 보존한다. |

---

## 2. MVP 범위

### 2.1 MVP 방향 재정의

기존의 “사용자가 주요 화면을 수동으로 캡처하고, GPT가 실행계획을 생성하는 방식”은 안전하고 구현 난이도는 낮지만, AutoWebTesting이 지향하는 제품 가치와는 충분히 맞지 않는다.

AutoWebTesting의 핵심 차별점은 기존 자동화 시험 도구처럼 사람이 테스트케이스를 만들고 화면 요소를 매핑한 뒤 자동 실행만 하는 것이 아니다.

본 제품의 MVP는 다음 방향을 목표로 한다.

```text
URL + 계정 정보 + 시험 방법 설명
→ AI가 웹앱을 탐색
→ 주요 기능과 CRUD 흐름 후보 발견
→ PageState / PageFlow / TestCase / ExecutionPlan 자동 생성
→ 사람이 검토 및 승인
→ Playwright가 반복 실행
→ 증적과 보고서 생성
```

즉, MVP부터 **AI 탐색 기반 자동 테스트 설계**를 포함한다.

사람은 모든 화면을 직접 캡처하거나 모든 테스트케이스를 수동으로 작성하는 역할이 아니라, AI가 생성한 후보를 검토하고 승인하는 역할을 담당한다.

### 2.2 MVP의 핵심 목표

MVP는 “단일 화면 자동화”가 아니라 **URL 기반 반자율 CRUD 테스트 자동화**를 목표로 한다.

여기서 “반자율”이란 다음 의미다.

- AI가 대상 웹앱을 직접 탐색한다.
- AI가 화면 상태, 기능 후보, CRUD 흐름, 테스트케이스, 실행계획을 제안한다.
- 앱은 위험 행위와 불확실한 판단을 차단하거나 사람 검토로 보낸다.
- 사람은 최종 실행 전 핵심 후보를 승인한다.
- 승인 이후에는 동일한 실행계획으로 반복 실행할 수 있어야 한다.

### 2.3 MVP 최종 범위

MVP는 다음 범위를 포함한다.

| 구분 | 포함 여부 | 설명 |
|---|---:|---|
| Windows 11 데스크톱 앱 | 포함 | Electron + React + TypeScript 기반 |
| GPT Web Import Mode | 포함 | 사용자가 GPT 웹에서 JSON 생성 후 앱에 업로드 |
| AI 탐색 모드 | 포함 | URL을 기준으로 화면을 관찰하며 PageState/PageFlow 후보 생성 |
| API Mode | 후순위 | 앱이 LLM API를 직접 호출하는 기능은 향후 확장 |
| 기능목록 Excel 입력 | 선택 | 있으면 테스트 범위 보강에 사용, 없어도 URL 탐색 가능해야 함 |
| 제품 매뉴얼 입력 | 선택 | 있으면 기능 이해 보강에 사용, 없어도 기본 탐색 가능해야 함 |
| URL 기반 웹앱 탐색 | 포함 | 로그인 후 메뉴, 목록, 등록, 상세, 수정, 삭제/비활성화 후보 탐색 |
| 테스트케이스 자동 생성 | 포함 | 탐색 결과 기반 TC 후보 생성 |
| 테스트케이스 검토 | 포함 | 승인, 제외, 수정필요 등 상태 관리 |
| 로그인 처리 | 제한 포함 | 일반 ID/PW 로그인은 지원, CAPTCHA/2FA/인증서는 제외 |
| 다중 PageState DOM 캡처 | 포함 | AI 탐색 중 자동 캡처 |
| PageFlow 후보 생성 | 포함 | 화면 이동 관계 자동 추론 |
| 실행계획 자동 생성 | 포함 | 승인된 테스트케이스와 탐색 결과 기반 생성 |
| 실행계획 검토 | 포함 | 매핑 불확실, 리스크, 수동 필요 여부 확인 |
| Playwright 실행 | 포함 | 허용된 액션만 실행 |
| CRUD 자동화 | 포함 | 등록, 조회, 수정, 삭제/비활성화 계열 업무 흐름 지원 |
| 실행 이벤트 스트림 | 포함 | 실행 중 진행률과 단계별 상태 표시 |
| 실패 스크린샷 | 포함 | 실패 단계 증적 저장 |
| HTML 보고서 | 포함 | 기본 실행 결과 요약 |
| Excel 보고서 | 포함 | TC 목록 및 실행결과 내보내기 |
| Evidence ZIP | 포함 | 증적 파일 패키징 |
| SQLite 프로젝트 이력 | 후순위 | 구조는 고려하되, 완성은 후속 Phase |

### 2.4 MVP에서 제외하는 항목

다음 항목은 MVP에서 제외하거나 수동 확인 대상으로 처리한다.

| 제외 항목 | 처리 방식 |
|---|---|
| CAPTCHA | 자동화 제외 |
| 2단계 인증 | 자동화 제외 또는 사전 로그인 세션 사용 |
| 공동인증서/보안모듈 | 자동화 제외 |
| 실제 결제 | 기본 차단 |
| 실제 외부 SMS/메일/푸시 발송 | 기본 차단 또는 명시 승인 |
| 외부기관 제출 | 기본 차단 |
| 권한/보안설정 변경 | HIGH 또는 PROHIBITED |
| 운영 데이터 직접 삭제 | 기본 차단 |
| 복잡한 이미지/그래프 의미 검증 | 수동 확인 |
| 다운로드 파일 내부 내용 정밀 검증 | 후속 Phase |
| 병렬 브라우저 대량 실행 | 후속 Phase |

### 2.5 API Mode의 의미

API Mode란 사용자가 GPT 웹페이지를 직접 열어 복사/붙여넣기 하지 않고, 앱이 OpenAI, Claude, Gemini 등 외부 LLM API를 직접 호출하여 다음 작업을 수행하는 방식을 의미한다.

```text
앱 내부에서 LLM API 직접 호출
→ 탐색 판단
→ 테스트케이스 생성
→ 실행계획 생성
→ 실패분석 생성
→ 앱 내부로 결과 자동 반영
```

다만 MVP에서 “AI 탐색”을 목표로 삼는다면 GPT Web Import Mode만으로는 상호작용이 번거로울 수 있다. 따라서 MVP 구현 방식은 두 단계로 나눈다.

```text
MVP-A:
- GPT Web Import Mode 기반
- 탐색 중 필요한 판단을 JSON 작업 단위로 내보내고 사용자가 GPT 웹에서 처리
- 구현 가능하지만 사용자 조작이 많음

MVP-B:
- 제한적 API Mode 또는 로컬 LLM 어댑터 도입
- AI 탐색 루프를 앱 내부에서 자동 수행
- 제품 목표에는 더 적합함
```

제품 방향상 최종 목표는 MVP-B에 가깝다. 다만 보안과 비용을 고려하여 API 호출 부분은 어댑터 구조로 분리한다.

---

## 3. 전체 아키텍처

### 3.1 런타임 구조

```text
Renderer UI
→ IPC Bridge
→ Electron Main Process
→ Project Store
→ DOM Capture
→ Element Registry
→ Execution Plan Importer
→ Risk Policy Engine
→ Playwright Runner
→ Evidence Collector
→ Report Generator
```

### 3.2 프로세스 책임

| 레이어 | 위치 | 책임 |
|---|---|---|
| Renderer | `src/renderer/` | UI, 상태 표시, 사용자 검토, 입력 폼 |
| Preload | `src/preload/` | `contextBridge` 기반 IPC API 노출 |
| Main Process | `src/main/` | IPC 핸들러, 파일 I/O, 프로젝트 저장소, 보고서 생성 |
| Runner | `src/runner/` | DOM 캡처, Element Registry 생성, Playwright 실행, 리스크 정책 적용 |
| Shared | `src/shared/` | 공통 타입, 상수, 스키마 버전 |
| Schemas | `schemas/` | JSON 계약 정의 |

### 3.3 기본 실행 흐름

```text
1. 프로젝트 생성
2. 기능목록/매뉴얼 준비
3. GPT 웹에서 테스트케이스 JSON 생성
4. 앱에 테스트케이스 JSON 업로드
5. 사람이 테스트케이스 검토
6. 대상 URL 및 계정 정보 입력
7. 앱이 로그인 및 업무 흐름 탐색/캡처 수행
8. 여러 PageState와 DOM Summary 생성
9. GPT 웹에서 실행계획 JSON 생성
10. 앱에 실행계획 JSON 업로드
11. 실행계획 스키마 검증
12. elementId 매핑 검증
13. 리스크 정책 검증
14. 사람이 실행계획 최종 검토
15. Playwright 실행
16. 실행 이벤트 실시간 표시
17. 실패 시 스크린샷과 로그 저장
18. 결과 보고서와 증적 생성
```

---

## 4. LLM 사용 모드와 AI 탐색 구조

### 4.1 GPT Web Import Mode

GPT Web Import Mode는 앱이 직접 LLM API를 호출하지 않는 방식이다. 사용자는 제공된 프롬프트 파일을 GPT 웹페이지에 붙여넣고 JSON 결과를 저장한 뒤 앱에 업로드한다.

#### 장점

- 외부 API 키가 필요 없다.
- API 비용 구조를 앱이 직접 관리하지 않아도 된다.
- 보안상 민감한 조직에서 도입 부담이 낮다.
- 사용자가 GPT 출력 내용을 직접 확인할 수 있다.

#### 단점

- 복사/붙여넣기 과정이 번거롭다.
- 탐색 루프를 자동화하기 어렵다.
- GPT가 JSON 외 설명을 붙일 수 있다.
- 사용자가 잘못된 파일을 업로드할 수 있다.

### 4.2 API Mode

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

이 루프를 GPT Web Import Mode만으로 처리하면 사용자가 매 단계마다 JSON을 복사/붙여넣기 해야 하므로 제품 경험이 나빠진다.

따라서 제품의 목표가 “URL만 주면 AI가 대부분 알아서 테스트 흐름을 구성하는 도구”라면, API Mode는 단순 후순위 부가기능이 아니라 **AI 탐색 모드의 핵심 구현 수단**으로 봐야 한다.

### 4.3 AI 탐색 모드

AI 탐색 모드는 AutoWebTesting의 핵심 차별화 기능이다.

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

### 4.4 AI 탐색 루프

AI 탐색 루프는 다음 단위로 동작한다.

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

### 4.5 탐색 모드와 실행 모드의 분리

AI가 URL을 보고 탐색하는 과정과, 승인된 계획을 반복 실행하는 과정은 분리해야 한다.

| 구분 | 탐색 모드 | 실행 모드 |
|---|---|---|
| 목적 | 기능과 화면 흐름 발견 | 승인된 TC 반복 실행 |
| 판단 주체 | AI + 정책 엔진 + 사람 검토 | Playwright Runner |
| 실행계획 | 생성 중인 후보 | 승인된 계획 |
| 결과 | PageState, PageFlow, TC 후보 | P/F 결과, 증적, 보고서 |
| 위험도 | 상대적으로 높음 | 통제 가능 |
| 재현성 | 낮을 수 있음 | 높아야 함 |

탐색 모드는 유연해야 하지만, 실행 모드는 재현 가능해야 한다.

따라서 AutoWebTesting은 다음 구조를 따른다.

```text
AI 탐색 모드
→ 후보 생성
→ 사람 검토 및 승인
→ 정식 실행계획 저장
→ 실행 모드에서 반복 실행
```

### 4.6 AI 탐색의 안전장치

AI가 화면을 탐색할 때도 모든 행동을 허용해서는 안 된다.

탐색 중에도 다음 안전장치를 적용한다.

- 허용 액션 whitelist
- 리스크 키워드 탐지
- HIGH 이상 행동 실행 전 사람 승인
- PROHIBITED 행동 자동 차단
- 비밀번호/토큰 등 secret 값 LLM 전달 금지
- 삭제, 결제, 외부 발송, 권한 변경은 기본 차단
- AI 판단 결과와 실제 실행 결과를 모두 로그로 저장

### 4.7 AI 탐색의 중단 조건

무한 탐색을 방지하기 위해 중단 조건을 둔다.

예시:

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

### 4.8 공통 원칙

GPT Web Import Mode와 API Mode는 입력 방식만 다르다. 내부 데이터 계약은 동일해야 한다.

```text
GPT 웹 결과든 API 결과든
→ 동일한 JSON 스키마 검증
→ 동일한 사람 검토
→ 동일한 리스크 정책
→ 동일한 실행 엔진
```

다만 AI 탐색 모드는 반복 판단이 필요하므로, 제품 목표상 API Mode 또는 로컬 LLM 어댑터를 우선 고려해야 한다.

---

## 5. 테스트케이스 설계

### 5.1 테스트케이스 입력 자료

테스트케이스 생성에는 다음 자료를 사용한다.

| 입력 | 설명 |
|---|---|
| 기능목록 Excel | 고정 양식의 기능 목록 |
| 제품 매뉴얼 | 기능 설명, 화면 흐름, 제약 조건 |
| 시험 관점 | 정상/오류/경계/권한/데이터 검증 등 |
| 자동화 제외 기준 | CAPTCHA, 실제 결제, 외부 발송 등 |

### 5.2 기능목록 Excel 기본 양식

| 컬럼 | 필수 | 설명 |
|---|---:|---|
| 대분류 | 필수 | 상위 기능 그룹 |
| 중분류 | 필수 | 중간 기능 그룹 |
| 소분류 | 필수 | TC_ID 번호 부여 기준 |
| 기능설명 | 필수 | 자연어 기능 설명 |

### 5.3 테스트케이스 ID 규칙

```text
TC_{소분류번호}-{테스트케이스순번}
```

예:

```text
TC_001-001
TC_001-002
TC_002-001
```

소분류번호는 기능목록의 소분류 순서에 따라 부여한다. 테스트케이스 순번은 소분류별로 `001`부터 시작한다.

### 5.4 테스트케이스 상태

| 상태 | 설명 |
|---|---|
| `DRAFT` | GPT가 생성했으나 아직 검토 전 |
| `APPROVED` | 실행계획 생성 대상으로 승인됨 |
| `NEEDS_REVISION` | 내용 수정 필요 |
| `REJECTED` | 유효한 테스트케이스로 보기 어려움 |
| `EXCLUDED` | 유효하지만 이번 실행에서 제외 |
| `DEPRECATED` | 과거 이력 보존용, 현재 미사용 |

### 5.5 실행계획 생성 대상 조건

다음 조건을 모두 만족해야 실행계획 생성 대상이 된다.

```text
reviewStatus = APPROVED
automationTarget = true
riskLevel이 정책상 허용됨
```

### 5.6 테스트케이스 필드

#### 사용자 표시 필드

- 대분류
- 중분류
- 소분류
- TC_ID
- 테스트 시나리오
- 입력/사전조건
- 기대 출력/사후조건
- 자동화 가능 여부
- 리스크 수준
- 테스트 결과
- 실패 상세 결과

#### 내부 관리 필드

- reviewStatus
- automationTarget
- riskLevel
- riskFlags
- automationReason
- sourceMode
- testDataRefs
- assertionRefs
- createdAt
- updatedAt

---

## 6. CRUD 중심 MVP 기능 범위

### 6.1 CRUD 자동화 목표

MVP는 최소한 일반적인 CRUD 업무 흐름을 지원해야 한다.

| 유형 | 목표 |
|---|---|
| Create | 등록 화면 이동, 필수값 입력, 저장, 성공 여부 확인 |
| Read | 목록 조회, 검색, 상세 조회, 결과 표시 확인 |
| Update | 기존 항목 선택, 수정, 저장, 변경 결과 확인 |
| Delete | 삭제 또는 비활성화 요청, 확인 메시지 처리, 목록 반영 확인 |

### 6.2 CRUD 흐름의 화면 단위

CRUD는 단일 화면이 아니라 여러 PageState로 구성한다.

예:

```text
PAGE_001: 목록 화면
PAGE_002: 등록 화면
PAGE_003: 상세 화면
PAGE_004: 수정 화면
PAGE_005: 삭제 확인 모달
```

### 6.3 CRUD 지원을 위한 PageState 개념

`PageState`는 특정 시점의 화면 상태를 의미한다.

```json
{
  "pageStateId": "PAGE_001",
  "name": "사용자 목록 화면",
  "urlPattern": "/users",
  "description": "사용자 목록, 검색, 등록 버튼이 표시되는 화면",
  "domSummaryId": "DOM_001",
  "elementRegistryId": "REG_001"
}
```

### 6.4 PageFlow 개념

`PageFlow`는 PageState 사이의 이동 관계를 표현한다.

```json
{
  "flowId": "FLOW_USER_CREATE",
  "name": "사용자 등록 흐름",
  "startPageStateId": "PAGE_001",
  "transitions": [
    {
      "from": "PAGE_001",
      "to": "PAGE_002",
      "triggerElementId": "PAGE_001.el_0005",
      "action": "click",
      "description": "등록 버튼 클릭"
    },
    {
      "from": "PAGE_002",
      "to": "PAGE_003",
      "triggerElementId": "PAGE_002.el_0018",
      "action": "click",
      "description": "저장 버튼 클릭 후 상세 화면 이동"
    }
  ]
}
```

### 6.5 MVP에서 허용하는 다중 화면 자동화 수준

MVP는 완전 자율 탐색이 아니라 **사용자가 제공한 업무 흐름 또는 GPT가 생성한 실행계획을 검토 후 실행하는 방식**이다.

즉, 앱이 아무 정보 없이 사이트 전체를 크롤링하지 않는다.

```text
허용:
- URL과 계정 정보 입력
- 로그인
- 지정된 시작 URL 접속
- 실행계획에 정의된 순서에 따라 화면 이동
- 필요한 시점에 PageState 검증
- DOM 재캡처 또는 사전 캡처된 DOM 참조

비허용:
- 사이트 전체 자동 크롤링
- 임의 메뉴 전체 탐색
- GPT가 만든 raw Playwright 코드 실행
- 위험 버튼 무검토 클릭
```

---

## 7. DOM Summary와 Element Registry

### 7.1 기본 원칙

`elementId`는 GPT와 사람이 참조하기 위한 ID다. 실제 Playwright 실행에 직접 사용하는 selector가 아니다.

앱은 `elementId`와 실제 selector 후보를 연결하는 내부 `ElementRegistry`를 별도로 관리한다.

### 7.2 DOM Summary

GPT에 전달하는 요약 정보다.

```json
{
  "pageStateId": "PAGE_001",
  "domSummaryId": "DOM_001",
  "url": "https://example.com/users",
  "title": "사용자 관리",
  "elements": [
    {
      "elementId": "PAGE_001.el_0001",
      "role": "button",
      "tag": "button",
      "text": "등록",
      "label": "등록",
      "visible": true,
      "enabled": true,
      "nearbyText": "사용자 목록",
      "formId": null
    }
  ]
}
```

### 7.3 Element Registry

앱 내부에서만 사용하는 실행용 매핑 정보다.

```json
{
  "elementRegistryId": "REG_001",
  "pageStateId": "PAGE_001",
  "items": [
    {
      "elementId": "PAGE_001.el_0001",
      "selectorCandidates": [
        {
          "type": "role",
          "value": "button[name='등록']",
          "priority": 1
        },
        {
          "type": "text",
          "value": "button:has-text('등록')",
          "priority": 2
        },
        {
          "type": "css",
          "value": "[data-testid='create-user']",
          "priority": 3
        }
      ],
      "stableHints": {
        "role": "button",
        "label": "등록",
        "nearbyText": "사용자 목록"
      }
    }
  ]
}
```

### 7.4 elementId 형식

다중 페이지를 지원하기 위해 elementId는 PageState를 포함한다.

```text
PAGE_001.el_0001
PAGE_002.el_0001
PAGE_003.el_0001
```

이렇게 해야 서로 다른 화면의 `el_0001`이 충돌하지 않는다.

### 7.5 매핑 실패 처리

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

## 8. 테스트 데이터 관리

### 8.1 기본 원칙

테스트 데이터는 계정 정보, 일반 입력값, 실행 시 생성값, 파일 입력값을 구분한다.

LLM에는 비밀번호, 토큰, 실제 계정정보 등 민감정보를 전달하지 않는다.

### 8.2 변수 유형

| 유형 | 설명 | LLM 전달 |
|---|---|---:|
| `secret` | ID, 비밀번호, 토큰 등 민감정보 | 금지 |
| `testData` | 이름, 검색어, 일반 입력값 | 가능 |
| `generated` | 실행 시점에 생성되는 고유값 | 가능 |
| `file` | 업로드 테스트용 파일 경로 | 파일명 정도만 가능 |

### 8.3 TestDataProfile 예시

```json
{
  "testDataProfileId": "PROFILE_DEFAULT",
  "name": "기본 테스트 데이터",
  "variables": [
    {
      "name": "LOGIN_ID",
      "type": "secret",
      "valueSource": "localCredentialStore",
      "sendToLlm": false
    },
    {
      "name": "LOGIN_PASSWORD",
      "type": "secret",
      "valueSource": "localCredentialStore",
      "sendToLlm": false
    },
    {
      "name": "UNIQUE_USER_ID",
      "type": "generated",
      "pattern": "autotest_${yyyyMMddHHmmss}",
      "sendToLlm": true
    },
    {
      "name": "USER_NAME",
      "type": "testData",
      "value": "자동테스트사용자",
      "sendToLlm": true
    }
  ]
}
```

### 8.4 실행계획에서 변수 사용

실행계획은 실제 값을 직접 담지 않고 `valueSource`를 사용한다.

```json
{
  "stepId": "STEP_001",
  "action": "fill",
  "elementId": "PAGE_002.el_0010",
  "valueSource": "USER_NAME"
}
```

### 8.5 고유값 생성

등록 테스트는 반복 실행 가능해야 한다. 따라서 ID, 제목, 코드 등 중복 위험이 있는 값은 `generated` 변수를 사용한다.

예:

```text
AUTO_USER_${yyyyMMddHHmmss}
AUTO_TITLE_${timestamp}
AUTO_CODE_${random6}
```

---

## 9. 실행계획 설계

### 9.1 실행계획의 목적

Execution Plan은 승인된 테스트케이스를 Playwright가 실행 가능한 제한된 액션 목록으로 변환한 JSON이다.

실행계획은 GPT가 생성할 수 있지만, 앱은 이를 비신뢰 입력으로 취급한다.

### 9.2 허용 액션

초기 허용 액션은 다음과 같다.

| 액션 | 설명 |
|---|---|
| `goto` | URL 이동 |
| `click` | 요소 클릭 |
| `fill` | 입력칸 값 입력 |
| `selectOption` | 셀렉트 박스 선택 |
| `check` | 체크박스 선택 |
| `uncheck` | 체크박스 해제 |
| `uploadFile` | 파일 업로드 |
| `waitForText` | 특정 텍스트 대기 |
| `assertTextVisible` | 텍스트 표시 검증 |
| `assertUrlContains` | URL 일부 포함 검증 |
| `assertElementVisible` | 요소 표시 검증 |
| `assertElementNotVisible` | 요소 미표시 검증 |
| `assertValueEquals` | 입력값 일치 검증 |
| `takeScreenshot` | 스크린샷 저장 |

### 9.3 추가 권장 액션

CRUD와 다중 화면 테스트를 위해 다음 액션을 추가 검토한다.

| 액션 | 필요성 |
|---|---|
| `waitForNavigation` | 화면 이동 대기 |
| `waitForLoadState` | 네트워크/DOM 안정화 대기 |
| `assertRowContains` | 목록/테이블 행 검증 |
| `assertToastVisible` | 저장 성공 메시지 검증 |
| `confirmDialog` | 삭제 확인/저장 확인 처리 |
| `dismissDialog` | 확인창 취소 처리 |
| `switchToPopup` | 새 창/팝업 대응 |
| `closePopup` | 팝업 닫기 |

MVP에서는 `waitForNavigation`, `assertRowContains`, `assertToastVisible`, `confirmDialog` 정도는 포함하는 것을 권장한다.

---

## 10. Assertion 구조화

### 10.1 기본 원칙

자연어 기대결과만으로 P/F를 판단하지 않는다.

자동 P/F 판정은 구조화된 assertion을 기준으로 한다.

### 10.2 Assertion 분류

실제로 필요한 assertion 분류는 다음 수준까지 두는 것을 권장한다.

| 대분류 | Assertion Type | 설명 |
|---|---|---|
| 텍스트 검증 | `assertTextVisible` | 특정 텍스트가 보이는지 확인 |
| 텍스트 검증 | `assertTextNotVisible` | 특정 텍스트가 보이지 않는지 확인 |
| 요소 검증 | `assertElementVisible` | 특정 요소가 보이는지 확인 |
| 요소 검증 | `assertElementNotVisible` | 특정 요소가 보이지 않는지 확인 |
| 값 검증 | `assertValueEquals` | 입력값 또는 표시값이 기대값과 같은지 확인 |
| 값 검증 | `assertValueContains` | 값이 특정 문자열을 포함하는지 확인 |
| URL 검증 | `assertUrlContains` | URL에 특정 경로/문자열 포함 여부 확인 |
| 페이지 검증 | `assertPageTitleContains` | 페이지 제목 확인 |
| 테이블 검증 | `assertRowContains` | 목록/테이블 행에 특정 값이 포함되는지 확인 |
| 테이블 검증 | `assertRowNotContains` | 목록/테이블 행에 특정 값이 사라졌는지 확인 |
| 메시지 검증 | `assertToastVisible` | 저장/수정/삭제 성공 메시지 확인 |
| 메시지 검증 | `assertAlertText` | alert/dialog 문구 확인 |
| 상태 검증 | `assertEnabled` | 버튼/입력 요소 활성화 여부 확인 |
| 상태 검증 | `assertDisabled` | 버튼/입력 요소 비활성화 여부 확인 |
| 개수 검증 | `assertCountEquals` | 검색 결과나 목록 개수 확인 |
| 파일 검증 | `assertDownloadStarted` | 다운로드 발생 여부 확인 |

### 10.3 Assertion 필수 여부

실행 가능한 테스트케이스는 최소 1개 이상의 assertion을 가져야 한다.

단, 로그인, 메뉴 이동, 사전 준비 단계 같은 보조 흐름은 assertion 없이도 step으로 포함될 수 있다.

### 10.4 Assertion 예시

```json
{
  "assertionId": "ASSERT_001",
  "type": "assertRowContains",
  "pageStateId": "PAGE_001",
  "targetElementId": "PAGE_001.el_0020",
  "expectedValueSource": "USER_NAME",
  "description": "사용자 목록 테이블에 등록한 사용자명이 표시되는지 확인"
}
```

### 10.5 Assertion 실패와 실행 실패 구분

| 상황 | executionStatus | testResult | 의미 |
|---|---|---|---|
| 모든 step과 assertion 성공 | `COMPLETED` | `P` | 테스트 통과 |
| step은 성공했지만 assertion 실패 | `COMPLETED` | `F` | 제품 기능 실패 가능성 |
| 요소를 찾지 못함 | `MAPPING_FAILED` | 없음 | 자동화 매핑 실패 |
| Playwright 명령 실패 | `SCRIPT_FAILED` | 없음 | 스크립트 실행 실패 |
| 사전조건 미충족 | `BLOCKED` | 없음 | 테스트 수행 불가 |
| 위험 정책 차단 | `SKIPPED_RISK` | 없음 | 안전상 실행 제외 |

---

## 11. 실행 상태와 결과 정책

### 11.1 ExecutionStatus

| 상태 | 설명 |
|---|---|
| `NOT_RUN` | 아직 실행하지 않음 |
| `RUNNING` | 실행 중 |
| `COMPLETED` | 실행과 검증이 완료됨 |
| `BLOCKED` | 사전조건 또는 환경 문제로 실행 불가 |
| `MAPPING_FAILED` | elementId를 실제 요소에 매핑하지 못함 |
| `SCRIPT_FAILED` | 실행계획은 있으나 Playwright 실행 실패 |
| `SKIPPED_RISK` | 리스크 정책에 의해 건너뜀 |
| `MANUAL_REQUIRED` | 사람 확인 필요 |
| `CANCELLED` | 사용자가 실행 취소 |

### 11.2 TestResult

| 결과 | 설명 |
|---|---|
| `P` | Pass |
| `F` | Fail |
| 없음 | 실행 완료 상태가 아니므로 P/F 판단 불가 |

`testResult`는 `executionStatus = COMPLETED`일 때만 `P` 또는 `F`가 될 수 있다.

---

## 12. 실행 이벤트 스트림

### 12.1 필요성

테스트 실행은 시간이 걸리며, 중간 단계에서 실패할 수 있다. 사용자는 현재 어떤 TC와 어떤 step이 실행 중인지 실시간으로 확인해야 한다.

### 12.2 IPC Command

| 채널 | 설명 |
|---|---|
| `run:start` | 실행 시작 |
| `run:cancel` | 실행 취소 |
| `run:rerun-testcase` | 특정 TC 재실행 |
| `run:save-artifacts` | 결과 저장 |

### 12.3 IPC Event

| 이벤트 | 설명 |
|---|---|
| `run:started` | 실행 시작됨 |
| `run:progress` | 전체 진행률 갱신 |
| `run:testcase-started` | 특정 TC 시작 |
| `run:step-started` | 특정 step 시작 |
| `run:step-finished` | 특정 step 종료 |
| `run:testcase-finished` | 특정 TC 종료 |
| `run:failed` | 실행 중 치명 오류 발생 |
| `run:cancelled` | 사용자 취소 완료 |
| `run:finished` | 전체 실행 완료 |

### 12.4 이벤트 예시

```json
{
  "event": "run:step-finished",
  "runId": "RUN-20260514-143022",
  "tcId": "TC_001-001",
  "stepId": "STEP_003",
  "status": "PASSED",
  "message": "저장 버튼 클릭 완료"
}
```

---

## 13. 리스크 정책

### 13.1 리스크 수준

| 수준 | 의미 | 기본 처리 |
|---|---|---|
| `LOW` | 읽기 또는 되돌리기 쉬운 동작 | 승인된 TC는 자동 실행 가능 |
| `MEDIUM` | 제한적 상태 변경 | 실행 전 경고 권장 |
| `HIGH` | 민감하거나 영향이 큰 동작 | 실행마다 명시 승인 필요 |
| `PROHIBITED` | 자동화 금지 | 자동 실행 차단 |

### 13.2 리스크 플래그

| 플래그 | 의미 |
|---|---|
| `PAYMENT` | 실제 결제, 카드 승인, 유료 주문 확정 |
| `DELETE_DATA` | 운영 또는 중요 데이터 삭제 |
| `SEND_EXTERNAL_MESSAGE` | SMS, 이메일, 푸시, 메신저 발송 |
| `SUBMIT_TO_EXTERNAL_SYSTEM` | 외부기관 또는 외부 API 제출 |
| `DOWNLOAD_SENSITIVE_DATA` | 개인정보, 고객정보, 대량 민감정보 다운로드 |
| `CHANGE_PERMISSION` | 사용자, 역할, 관리자 권한 변경 |
| `CHANGE_SECURITY_SETTING` | 비밀번호 정책, MFA, 접근제어 변경 |
| `PUBLIC_PUBLISH` | 외부 공개 게시 |
| `IRREVERSIBLE_ACTION` | 되돌리기 어려운 작업 |
| `LEGAL_OR_FINANCIAL_ACTION` | 계약, 청구, 정산, 세금계산서, 법적 약정 |

### 13.3 위험 키워드 탐지

GPT가 리스크 플래그를 누락하더라도 앱은 위험 키워드를 탐지해야 한다.

예시 키워드:

```json
{
  "DELETE_DATA": ["삭제", "영구삭제", "제거", "탈퇴", "초기화", "폐기"],
  "PAYMENT": ["결제", "주문확정", "카드승인", "청구", "입금", "정산"],
  "SEND_EXTERNAL_MESSAGE": ["발송", "문자", "SMS", "메일", "이메일", "알림톡", "푸시"],
  "CHANGE_PERMISSION": ["권한", "관리자", "역할 변경", "승인자 변경"],
  "CHANGE_SECURITY_SETTING": ["비밀번호 정책", "MFA", "2단계 인증", "접근제어", "보안설정"],
  "PUBLIC_PUBLISH": ["게시", "공개", "배포", "발행"]
}
```

### 13.4 키워드 탐지 대상

- 테스트 시나리오
- 사전조건
- 기대결과
- 실행 step 설명
- action
- element text
- button label
- nearbyText

### 13.5 리스크 보정 규칙

```text
LOW + 위험 키워드 → MEDIUM 이상으로 상향
MEDIUM + 고위험 키워드 → HIGH로 상향
HIGH + 되돌리기 어려운 행위 → PROHIBITED 후보
PROHIBITED 키워드 → 자동 실행 차단
```

---

## 14. 실패 원인 분류

### 14.1 기본 원칙

실패 원인은 자유 텍스트만으로 기록하지 않는다. 통계와 개선 우선순위 분석을 위해 enum 값으로 고정한다.

### 14.2 FailureCause

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

### 14.3 실패 분석 예시

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

## 15. GPT Web Import Workflow

### 15.1 Step 1 — 테스트케이스 생성

사용자 작업:

1. `prompts/testcase-generation.prompt.md`를 연다.
2. 기능목록과 매뉴얼 내용을 GPT에 입력한다.
3. GPT에 JSON만 출력하도록 요청한다.
4. 결과를 `testcases.json`으로 저장한다.
5. 앱에 업로드한다.

앱 작업:

- JSON 파싱
- 스키마 검증
- TC_ID 형식 검사
- TC_ID 중복 검사
- 필수 필드 검사
- 리스크 수준 표시
- 검토 테이블 표시

### 15.2 Step 2 — DOM 캡처 및 실행계획 생성

사용자 작업:

1. 대상 URL과 계정 정보를 앱에 입력한다.
2. 앱이 로그인하고 시작 화면으로 이동한다.
3. 앱이 필요한 PageState의 DOM Summary와 Element Registry를 생성한다.
4. 승인된 TC JSON과 DOM Summary JSON을 내보낸다.
5. `prompts/dom-mapping.prompt.md`를 연다.
6. 승인된 TC JSON, DOM Summary JSON, 테스트 데이터 변수 목록, 리스크 정책을 GPT에 입력한다.
7. GPT가 반환한 실행계획 JSON을 저장한다.
8. 앱에 실행계획 JSON을 업로드한다.

앱 작업:

- 실행계획 JSON 파싱
- 스키마 검증
- action 이름 검증
- elementId 존재 여부 검증
- PageState 존재 여부 검증
- 리스크 정책 적용
- 실행계획 검토 화면 표시

### 15.3 Step 3 — 실행 및 실패분석

사용자 작업:

1. 실행 가능한 TC를 선택한다.
2. HIGH 리스크 항목이 있으면 명시 승인한다.
3. 실행을 시작한다.
4. 실패 또는 차단 케이스가 있으면 failure package JSON을 내보낸다.
5. GPT 웹에서 실패분석 프롬프트를 실행한다.
6. 실패분석 JSON을 앱에 업로드한다.

앱 작업:

- 실행 이벤트 표시
- 스크린샷 저장
- 로그 저장
- 실패 패키지 생성
- 실패분석 JSON 검증
- 결과 보고서 반영

### 15.4 GPT 출력 보정 정책

원칙적으로 GPT 출력은 JSON만 허용한다.

다만 GPT 웹 사용 과정에서 흔히 발생하는 형식 오류를 줄이기 위해 다음 보정은 허용한다.

- Markdown 코드펜스 제거
- 첫 번째 `{` 또는 `[` 앞의 텍스트 제거
- 마지막 `}` 또는 `]` 뒤의 텍스트 제거
- UTF-8 BOM 제거
- 보정 적용 시 사용자에게 경고 표시

앱은 필드 값 자체를 조용히 변경해서는 안 된다.

---

## 16. 프로젝트 저장 구조

### 16.1 기본 저장 루트

```text
Documents/AutoWebTesting/projects/{projectName}/
```

### 16.2 권장 폴더 구조

```text
Documents/AutoWebTesting/projects/{projectName}/
├── project.json
├── inputs/
│   ├── feature-list.xlsx
│   └── manuals/
├── imports/
│   ├── testcases.import.json
│   ├── execution-plan.import.json
│   └── failure-analysis.import.json
├── testcases/
│   ├── testcases.reviewed.json
│   └── testcases.xlsx
├── dom/
│   ├── page-states.json
│   ├── dom-summary.PAGE_001.json
│   ├── element-registry.PAGE_001.json
│   ├── dom-summary.PAGE_002.json
│   └── element-registry.PAGE_002.json
├── execution-plans/
│   └── execution-plan.reviewed.json
├── runs/
│   └── RUN-20260514-143022/
│       ├── run-result.json
│       ├── failure-package.json
│       ├── report.html
│       └── evidence/
├── reports/
│   ├── execution-result.xlsx
│   └── evidence.zip
└── logs/
    └── app.log
```

### 16.3 저장 원칙

- 실행 결과는 프로젝트 하위에 저장한다.
- runId는 타임스탬프 기반으로 생성한다.
- DOM Summary와 Element Registry는 실행계획과 함께 추적 가능해야 한다.
- 실패 재현을 위해 실행 당시의 테스트 데이터 snapshot을 저장한다.

---

## 17. UI 설계

### 17.1 주요 화면

| 화면 | 목적 |
|---|---|
| 프로젝트 설정 | 프로젝트 생성, 대상 URL, LLM 모드 선택 |
| 테스트케이스 임포트 | GPT 생성 TC JSON 업로드 |
| 테스트케이스 검토 | TC 승인, 제외, 수정필요 처리 |
| 테스트 데이터 설정 | 계정 변수, 테스트 데이터 변수 설정 |
| DOM 캡처 | 로그인, PageState 캡처, DOM Summary 생성 |
| 실행계획 임포트 | GPT 생성 실행계획 JSON 업로드 |
| 실행계획 검토 | 매핑, 리스크, assertion 검토 |
| 실행 모니터 | 실시간 실행 상태 표시 |
| 결과 요약 | P/F, 실패 원인, 증적 확인 |
| 보고서 내보내기 | Excel, HTML, ZIP 생성 |

### 17.2 실행 모니터 표시 항목

- 전체 진행률
- 현재 TC_ID
- 현재 stepId
- 현재 action
- 현재 PageState
- 성공/실패 상태
- 실패 메시지
- 스크린샷 미리보기
- 실행 취소 버튼
- 개별 TC 재실행 버튼

---

## 18. 개발 Phase 재정의

### Phase 0 — Foundation

- Electron + React + TypeScript 설정
- IPC Bridge 구성
- TypeScript strict 설정
- 공통 타입과 스키마 기본 구성

### Phase 1 — 테스트케이스 임포트 및 검토

- 테스트케이스 JSON 업로드
- Zod/JSON Schema 검증
- TC_ID 형식/중복 검사
- 검토 상태 변경 UI

### Phase 2 — 테스트 데이터 및 프로젝트 구조

- 프로젝트 저장 구조 적용
- TestDataProfile 정의
- secret/testData/generated/file 변수 구분
- 테스트 데이터 snapshot 저장

### Phase 3 — 다중 PageState DOM 캡처

- 로그인 처리
- 시작 URL 접속
- PageState 캡처
- DOM Summary 생성
- Element Registry 생성
- PageFlow 기본 구조 저장

### Phase 4 — 실행계획 임포트 및 검토

- 실행계획 JSON 업로드
- PageState/elementId 검증
- action whitelist 검증
- assertion 구조 검증
- 리스크 정책 검증

### Phase 5 — Playwright 실행 엔진

- 허용 액션 실행
- selectorCandidates 기반 element resolve
- CRUD 흐름 실행
- 다중 PageState 전환 처리
- 실행 이벤트 스트림
- 취소/재실행 처리

### Phase 6 — 결과 저장 및 보고서

- run-result.json 저장
- failure-package.json 저장
- HTML 보고서 생성
- Excel 보고서 생성
- Evidence ZIP 생성

### Phase 7 — 실패분석 반영

- 실패분석 JSON 업로드
- FailureCause enum 매핑
- 실패 상세 보고서 반영
- 개선 제안 표시

### Phase 8 — 프로젝트 이력 및 SQLite

- 프로젝트 목록
- 런 이력 조회
- 이전 결과 재조회
- TC 검토 상태 영속화

### Phase 9 — API Mode

- API 키 입력
- safeStorage 또는 OS 키체인 저장
- LLM API 직접 호출
- GPT Web Import Mode와 동일 스키마 검증

---

## 19. 품질 게이트

### 19.1 공통 품질 게이트

- TypeScript 빌드 오류 0건
- `any` 타입 사용 금지
- 스키마 검증 통과
- 샘플 JSON 검증 통과
- UI 오류 메시지는 한국어
- 코드 주석은 영어
- GPT 출력은 항상 비신뢰 입력으로 처리

### 19.2 DOM/매핑 품질 게이트

- elementId 중복 없음
- PageState별 elementId namespace 분리
- Element Registry 생성 성공
- selectorCandidates 최소 1개 이상
- 매핑 실패 시 원인 로그 저장

### 19.3 실행 품질 게이트

- PROHIBITED 자동 실행 차단
- HIGH 실행 전 명시 승인
- 알 수 없는 action 거부
- 알 수 없는 elementId는 `MAPPING_FAILED`
- assertion 없는 TC는 자동 P/F 판단 금지
- 실패 시 스크린샷 저장

### 19.4 보고서 품질 게이트

- 실행 상태와 P/F 결과 분리
- 실패 원인 enum 표시
- 증적 파일 경로 연결
- 실행 당시 URL, 앱 버전, schemaVersion 기록
- 한글 Windows에서 Excel 깨짐 방지

---

## 20. AI 탐색 세션 설계

AutoWebTesting의 핵심 목표는 사용자가 URL, 계정 정보, 시험 방법 설명을 입력하면 AI가 웹 제품을 탐색하고, 실제 제품 형상에 기반하여 테스트케이스와 실행계획 후보를 생성하는 것이다.

이를 위해 다음 개념을 도입한다.

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

### 20.1 ExplorationSession

`ExplorationSession`은 하나의 URL 또는 하나의 제품을 대상으로 수행한 AI 탐색 작업 전체를 의미한다.

#### 목적

- 탐색 목표와 제약 조건을 저장한다.
- AI가 어떤 화면을 보고 어떤 판단을 했는지 추적한다.
- 탐색 결과로 생성된 PageState, PageFlow, CandidateFeature, CandidateCrudFlow를 연결한다.
- 이후 테스트케이스 생성과 실행계획 생성의 근거 자료로 사용한다.

#### 예시

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

#### 주요 필드

| 필드 | 설명 |
|---|---|
| `explorationSessionId` | 탐색 세션 ID |
| `projectId` | 연결된 프로젝트 ID |
| `targetUrl` | 탐색 시작 URL |
| `goal` | 사용자가 입력한 시험 목적 |
| `inputSources` | 기능목록, 매뉴얼, 웹 형상 사용 여부 |
| `mode` | 탐색 모드 |
| `llmMode` | GPT 웹 임포트, API, 내부 AI 서버 등 |
| `environmentType` | local/dev/staging/production |
| `riskPolicyId` | 적용할 리스크 정책 |
| `testDataProfileId` | 사용할 테스트 데이터 프로필 |
| `status` | 탐색 상태 |
| `summary` | 탐색 결과 요약 |

---

### 20.2 Observation

`Observation`은 특정 시점의 화면을 AI가 판단할 수 있도록 정리한 관찰 데이터다.

Observation은 단순 DOM Summary가 아니다. DOM Summary, 가시 텍스트, 테이블 정보, 폼 정보, 현재 URL, 이전 행동 결과, 필요 시 스크린샷 정보를 포함한다.

#### 예시

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
  "visibleTexts": [
    "사용자 목록",
    "검색",
    "등록",
    "사용자명",
    "상태"
  ],
  "forms": [
    {
      "formId": "FORM_SEARCH",
      "label": "검색 조건",
      "fields": ["사용자명", "상태"]
    }
  ],
  "tables": [
    {
      "tableId": "TABLE_USERS",
      "label": "사용자 목록 테이블",
      "columns": ["사용자명", "아이디", "상태", "관리"]
    }
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

#### Observation 유형

| 유형 | 설명 |
|---|---|
| `TEXT_DOM_PRIMARY` | DOM Summary와 텍스트 정보 중심 관찰 |
| `TEXT_DOM_WITH_IMAGE` | DOM Summary와 스크린샷을 함께 사용하는 관찰 |
| `IMAGE_ASSISTED_ONLY` | DOM 정보가 부족해 이미지 판단을 보조로 사용하는 관찰 |
| `ERROR_STATE` | 오류 화면 또는 예외 상태 관찰 |
| `UNKNOWN_STATE` | 기존 PageState와 매칭되지 않는 화면 관찰 |

---

### 20.3 AiDecision

`AiDecision`은 AI가 Observation을 보고 내린 판단 결과다.

AiDecision은 자유로운 자연어 응답이 아니라 구조화된 JSON이어야 한다.

#### 예시

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

#### decisionType

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

### 20.4 ExplorationAction

`ExplorationAction`은 AiDecision을 바탕으로 실제 Playwright가 수행하는 탐색 행동이다.

AiDecision이 제안했다고 해서 무조건 실행하지 않는다. 실행 전 Risk Policy Engine이 다시 검사한다.

#### 예시

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

#### ExplorationAction 상태

| 상태 | 설명 |
|---|---|
| `PENDING` | 실행 대기 |
| `EXECUTED` | 실행 완료 |
| `BLOCKED_BY_RISK` | 리스크 정책으로 차단 |
| `REVIEW_REQUIRED` | 사람 승인 필요 |
| `FAILED` | Playwright 실행 실패 |
| `SKIPPED` | 중복 또는 불필요 판단으로 건너뜀 |

---

### 20.5 ExplorationMemory

`ExplorationMemory`는 탐색 중 이미 확인한 화면, 행동, 후보 기능을 기억하는 구조다.

AI 탐색에서 가장 흔한 문제는 같은 화면을 반복하거나, 같은 버튼을 계속 누르는 것이다. 이를 방지하기 위해 탐색 메모리가 필요하다.

#### 저장 항목

- 방문한 URL
- 방문한 PageState
- 시도한 elementId/action 조합
- 실패한 action
- 위험 차단된 action
- 발견한 기능 후보
- 발견한 CRUD 흐름 후보
- 이미 생성한 테스트케이스 후보

#### 예시

```json
{
  "explorationMemoryId": "MEM_001",
  "explorationSessionId": "EXP_20260515_001",
  "visitedPageStates": ["PAGE_001", "PAGE_002"],
  "visitedUrls": [
    "https://example.com/admin/users",
    "https://example.com/admin/users/new"
  ],
  "attemptedActions": [
    {
      "pageStateId": "PAGE_001",
      "elementId": "PAGE_001.el_0001",
      "action": "click",
      "result": "SUCCESS"
    }
  ],
  "blockedActions": [],
  "candidateFeatureIds": ["FEAT_001"],
  "candidateCrudFlowIds": ["CRUD_001"]
}
```

---

### 20.6 CandidateFeature

`CandidateFeature`는 AI가 탐색 중 발견한 기능 후보이다.

기능목록이나 매뉴얼에 없더라도 실제 웹 형상에서 발견되면 후보로 기록한다.

#### 예시

```json
{
  "candidateFeatureId": "FEAT_001",
  "explorationSessionId": "EXP_20260515_001",
  "name": "사용자 관리",
  "featureType": "CRUD_MANAGEMENT",
  "source": "WEB_SHAPE",
  "relatedPageStateIds": ["PAGE_001", "PAGE_002", "PAGE_003"],
  "evidence": {
    "texts": ["사용자 목록", "등록", "수정", "삭제"],
    "elementIds": ["PAGE_001.el_0001", "PAGE_001.el_0020"]
  },
  "confidence": 0.9,
  "riskFlags": [],
  "reviewStatus": "DRAFT"
}
```

#### featureType 후보

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

### 20.7 CandidateCrudFlow

`CandidateCrudFlow`는 AI가 발견한 CRUD 흐름 후보이다.

#### 예시

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

### 20.8 HumanReviewGate

`HumanReviewGate`는 사람 검토 또는 승인이 필요한 지점을 의미한다.

AutoWebTesting은 대부분의 과정을 자동화하되, 위험하거나 불확실한 판단은 사람에게 넘겨야 한다.

#### 검토가 필요한 경우

| 상황 | 처리 |
|---|---|
| HIGH 리스크 행동 | 실행 전 승인 필요 |
| PROHIBITED 후보 | 기본 차단, 예외 승인 불가 또는 관리자 승인 필요 |
| 삭제/발송/결제/권한변경 | 승인 필요 |
| AI confidence 낮음 | 검토 필요 |
| 동일 후보가 여러 개 | 사용자가 선택 |
| 화면 의미 불명확 | PageState 이름 확인 필요 |
| 자동 생성 TC 과다 | 사용자가 실행 대상 선별 |

#### 예시

```json
{
  "reviewGateId": "RG_001",
  "type": "HIGH_RISK_ACTION_APPROVAL",
  "targetType": "ExplorationAction",
  "targetId": "ACT_010",
  "message": "삭제 버튼 클릭이 감지되었습니다. 이 삭제는 AutoWebTesting이 생성한 테스트 데이터에 대해서만 실행할 수 있습니다.",
  "options": ["APPROVE_ONCE", "SKIP", "MARK_MANUAL_REQUIRED"],
  "defaultOption": "SKIP",
  "status": "PENDING"
}
```

---

## 21. 이미지/스크린샷 기반 관찰 전략

### 21.1 문제의식

Claude Code와 같은 에이전트는 화면을 판단할 때 DOM 텍스트뿐 아니라 스크린샷 또는 시각 정보를 함께 활용할 가능성이 높다.

AutoWebTesting도 웹 제품의 실제 형상을 더 잘 이해하려면 이미지 기반 관찰을 고려해야 한다.

다만 모든 단계에서 이미지를 LLM에 전달하면 다음 문제가 생긴다.

- 비용 증가
- 처리 속도 저하
- 민감정보 노출 위험 증가
- 이미지 기반 판단의 재현성 저하
- 텍스트 DOM보다 구조화가 어려움

따라서 기본 전략은 **텍스트 DOM 우선, 이미지 선택 보강**으로 한다.

---

### 21.2 기본 원칙

```text
1. 기본 판단은 DOM Summary, visible text, form/table 구조를 사용한다.
2. 이미지 판단은 DOM만으로 불충분하거나 화면 배치/시각 정보가 중요한 경우에만 사용한다.
3. LLM에 이미지를 전달하기 전 민감정보 마스킹을 우선 적용한다.
4. 이미지 판단 결과도 구조화된 JSON으로 변환하여 저장한다.
5. 반복 실행은 이미지 판단에 의존하지 않고, 가능한 한 DOM/selector 기반으로 수행한다.
```

---

### 21.3 이미지가 필요한 경우

다음 상황에서는 스크린샷을 LLM에 함께 전달하는 것을 권장한다.

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

---

### 21.4 이미지가 필요하지 않은 경우

다음 경우에는 이미지를 보내지 않고 텍스트/DOM 기반으로 처리한다.

| 상황 | 이유 |
|---|---|
| 일반 버튼/입력/링크가 DOM에서 명확함 | DOM Summary로 충분 |
| CRUD 폼 입력과 저장 | selector 기반 실행이 더 안정적 |
| 단순 텍스트 검증 | visible text로 충분 |
| URL/상태/값 검증 | 구조화 assertion이 더 적합 |
| 민감정보가 많은 화면 | 이미지 전달 위험 증가 |

---

### 21.5 Observation의 이미지 필드

Observation에는 이미지 정보를 선택적으로 포함한다.

```json
{
  "observationId": "OBS_001",
  "observationType": "TEXT_DOM_WITH_IMAGE",
  "screenshot": {
    "available": true,
    "path": "observations/OBS_001.masked.png",
    "originalPath": "observations/OBS_001.original.png",
    "sendToLlm": true,
    "maskingApplied": true,
    "maskingRules": [
      "passwordFields",
      "secretVariables",
      "emailLikeTexts",
      "phoneLikeTexts"
    ],
    "reason": "아이콘 버튼과 모달 구조를 DOM만으로 판단하기 어려움"
  }
}
```

---

### 21.6 이미지 전송 전 마스킹

이미지를 LLM에 전달하기 전 다음 정보를 마스킹한다.

| 마스킹 대상 | 예시 |
|---|---|
| 비밀번호 입력값 | password field |
| 토큰/인증코드 | 긴 난수 문자열 |
| 주민번호/전화번호/이메일 | 개인정보 패턴 |
| 계정명 | 로그인 ID, 사용자명 |
| 고객명/기관명 | 민감 업무 데이터 |
| 금액/계약번호 | 업무상 민감정보 |

마스킹 전 원본 스크린샷은 로컬 증적용으로만 저장하고, LLM 전달용 이미지는 별도 masked 파일로 만든다.

---

### 21.7 이미지 사용 방식

이미지는 세 가지 수준으로 사용할 수 있다.

#### Level 0 — 이미지 미사용

DOM Summary만 사용한다.

기본값이다.

#### Level 1 — 필요 시 이미지 보강

AI가 DOM Summary만으로 판단이 어렵다고 표시하거나, 앱이 label 부족/아이콘 버튼/모달 감지 등의 조건을 만나면 스크린샷을 추가한다.

MVP 권장 방식이다.

#### Level 2 — 멀티모달 기본 사용

모든 Observation에 스크린샷을 포함한다.

판단력은 좋아질 수 있으나 비용, 보안, 속도 부담이 크므로 MVP 기본값으로는 권장하지 않는다.

---

### 21.8 이미지 기반 판단의 한계

이미지는 화면 이해에 도움이 되지만, 실제 실행의 기준으로 삼기에는 부족하다.

예를 들어 이미지에서 “저장 버튼”을 찾았다고 해도 Playwright가 클릭하려면 결국 DOM 요소나 좌표가 필요하다.

따라서 AutoWebTesting은 다음 원칙을 따른다.

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

---

### 21.9 추천 결정

MVP에서는 다음 전략을 채택한다.

```text
텍스트 DOM 우선 + 선택적 이미지 보강
```

구체적으로는 다음과 같다.

1. 모든 화면에서 DOM Summary와 ElementRegistry를 생성한다.
2. 기본 AI 판단은 DOM Summary 기반으로 수행한다.
3. 다음 조건에서만 masked screenshot을 LLM에 추가 전달한다.
   - 아이콘 버튼이 많음
   - label이 부족함
   - 모달/팝업 구조가 불명확함
   - div 기반 테이블로 구조 추출이 어려움
   - 대시보드/그래프/시각 정보가 핵심임
4. LLM이 이미지 기반으로 판단한 내용도 반드시 elementId 또는 PageState 후보와 연결한다.
5. 반복 실행은 이미지가 아니라 selectorCandidates 기반으로 수행한다.

---

## 22. 모달/팝업 처리 설계

CRUD 자동화에서 모달과 팝업은 핵심이다. 등록 폼, 삭제 확인, 저장 성공 메시지, 주소 검색, 미리보기 등이 모두 모달 또는 팝업으로 나타날 수 있다.

### 22.1 모달/팝업 유형

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

### 22.2 모달 PageState 예시

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

### 22.3 Dialog 처리 정책

브라우저 confirm이 나타난 경우 다음 규칙을 적용한다.

```text
LOW 문구 → 자동 확인 가능
DELETE_DATA / PAYMENT / SEND_EXTERNAL_MESSAGE 키워드 포함 → 승인 필요
PROHIBITED 키워드 포함 → 차단
실행계획에 dialog 처리 step이 없음 → DIALOG_UNHANDLED
```

---

## 23. 테이블/목록 인식 설계

CRUD 테스트에서 목록과 테이블 검증은 매우 중요하다.

### 23.1 테이블 정보 추출

DOM Summary는 일반 elements 외에 tables 정보를 별도로 가진다.

```json
{
  "tableId": "TABLE_USERS",
  "label": "사용자 목록 테이블",
  "pageStateId": "PAGE_001",
  "elementId": "PAGE_001.el_0020",
  "columns": ["사용자명", "아이디", "상태", "관리"],
  "rowActionCandidates": [
    {
      "actionText": "수정",
      "column": "관리",
      "riskLevel": "MEDIUM"
    },
    {
      "actionText": "삭제",
      "column": "관리",
      "riskLevel": "HIGH",
      "riskFlags": ["DELETE_DATA"]
    }
  ]
}
```

### 23.2 행 기준 액션

테이블 행 내부 버튼을 클릭하려면 row-scoped action이 필요하다.

```json
{
  "action": "clickRowAction",
  "tableId": "TABLE_USERS",
  "rowMatch": {
    "valueSource": "USER_NAME"
  },
  "actionText": "수정",
  "description": "등록한 사용자 행의 수정 버튼 클릭"
}
```

### 23.3 테이블 Assertion

| Assertion | 설명 |
|---|---|
| `assertRowContains` | 특정 값을 포함한 행이 존재하는지 확인 |
| `assertRowNotContains` | 특정 값을 포함한 행이 없는지 확인 |
| `assertCellEquals` | 특정 행/열 값이 기대값과 같은지 확인 |
| `assertCountEquals` | 행 개수가 기대값과 같은지 확인 |
| `assertCountGreaterThan` | 행 개수가 특정 수보다 큰지 확인 |

---

## 24. 테스트 데이터 정리 전략

자동화 테스트는 데이터를 생성한다. 데이터 정리 전략이 없으면 테스트 데이터가 계속 누적되거나, 반대로 기존 데이터를 잘못 삭제할 위험이 있다.

### 24.1 기본 원칙

```text
AutoWebTesting이 생성한 데이터만 자동 정리 대상으로 삼는다.
기존 데이터 삭제는 기본적으로 차단한다.
```

### 24.2 CreatedDataRegistry

```json
{
  "createdDataRegistryId": "CDR_001",
  "runId": "RUN_20260515_001",
  "items": [
    {
      "createdDataId": "DATA_001",
      "entityType": "USER",
      "displayName": "자동테스트사용자",
      "uniqueKey": "AUTO_USER_20260515103000",
      "createdByTcId": "TC_001-001",
      "createdAt": "2026-05-15T10:30:00+09:00",
      "cleanupStatus": "PENDING"
    }
  ]
}
```

### 24.3 Cleanup 정책

| 정책 | 설명 |
|---|---|
| `NO_CLEANUP` | 정리하지 않음 |
| `MANUAL_CLEANUP` | 보고서에 정리 대상 표시 |
| `AUTO_CLEANUP_APPROVAL_REQUIRED` | 사용자 승인 후 자동 삭제 |
| `AUTO_CLEANUP_SAFE_ONLY` | 자동 생성 데이터에 한해 자동 삭제 |

MVP 기본값은 `AUTO_CLEANUP_APPROVAL_REQUIRED`로 한다.

---

## 25. ExecutionPlan 최종 구조

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

---

### 25.1 ExecutionPlan 전체 예시

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
      "description": "사용자 ID 입력",
      "riskCheck": {
        "riskLevel": "LOW",
        "riskFlags": [],
        "requiresApproval": false
      }
    },
    {
      "stepId": "STEP_003",
      "stepType": "ACTION",
      "pageStateId": "PAGE_002",
      "action": "fill",
      "elementId": "PAGE_002.el_0011",
      "valueSource": "USER_NAME",
      "description": "사용자명 입력",
      "riskCheck": {
        "riskLevel": "LOW",
        "riskFlags": [],
        "requiresApproval": false
      }
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

### 25.2 ExecutionPlan 상위 필드

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

---

### 25.3 planStatus

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

## 26. ExecutionStep 구조

ExecutionStep은 실행계획 안의 개별 단계다.

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

---

### 26.1 공통 필드

모든 step은 다음 공통 필드를 가진다.

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

### 26.2 onFailure

| 값 | 설명 |
|---|---|
| `STOP_TC` | 해당 TC 실행 중단 |
| `CONTINUE` | 실패를 기록하고 다음 step 진행 |
| `TAKE_SCREENSHOT_AND_STOP` | 스크린샷 저장 후 중단 |
| `MARK_MANUAL_REQUIRED` | 수동 확인 대상으로 표시 |

기본값은 `TAKE_SCREENSHOT_AND_STOP`이다.

---

## 27. ACTION Step

ACTION Step은 Playwright가 실제 UI 조작을 수행하는 단계다.

### 27.1 기본 ACTION 예시

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

### 27.2 허용 ACTION 목록

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

### 27.3 값 입력 방식

값은 직접 넣지 않고 가능한 한 `valueSource`를 사용한다.

```json
{
  "action": "fill",
  "elementId": "PAGE_002.el_0010",
  "valueSource": "UNIQUE_USER_ID"
}
```

직접 값 입력은 민감정보가 아니고 재현성에 문제가 없는 경우에만 허용한다.

---

## 28. ASSERTION Step

Assertion Step은 자동 P/F 판단의 기준이다.

자연어 기대결과는 사람이 이해하기 위한 설명이고, 실제 자동 판정은 Assertion Step으로 수행한다.

### 28.1 Assertion 예시

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

### 28.2 Assertion 목록

| assertion | 설명 |
|---|---|
| `assertTextVisible` | 특정 텍스트가 보이는지 확인 |
| `assertTextNotVisible` | 특정 텍스트가 보이지 않는지 확인 |
| `assertElementVisible` | 특정 요소가 보이는지 확인 |
| `assertElementNotVisible` | 특정 요소가 보이지 않는지 확인 |
| `assertValueEquals` | 입력값 또는 표시값이 기대값과 같은지 확인 |
| `assertValueContains` | 값이 특정 문자열을 포함하는지 확인 |
| `assertUrlContains` | 현재 URL에 특정 문자열 포함 여부 확인 |
| `assertPageTitleContains` | 페이지 제목 확인 |
| `assertToastVisible` | 토스트 메시지 표시 확인 |
| `assertAlertText` | alert/dialog 문구 확인 |
| `assertRowContains` | 테이블에 특정 값을 포함한 행이 있는지 확인 |
| `assertRowNotContains` | 테이블에 특정 값을 포함한 행이 없는지 확인 |
| `assertCellEquals` | 특정 행/열의 셀 값이 기대값과 같은지 확인 |
| `assertCountEquals` | 행 개수 또는 요소 개수 확인 |
| `assertDownloadStarted` | 다운로드 발생 여부 확인 |

### 28.3 Assertion 결과와 testResult

| Assertion 결과 | executionStatus | testResult |
|---|---|---|
| 모든 assertion 성공 | `COMPLETED` | `P` |
| 하나 이상의 assertion 실패 | `COMPLETED` | `F` |
| assertion 수행 전 실행 실패 | 실패 유형에 따름 | 없음 |

---

## 29. TransitionExpectation 구조

TransitionExpectation은 어떤 step 이후 기대되는 화면 상태 변화를 정의한다.

기존의 “페이지 이동”이라는 표현은 URL 변경만 연상시키므로, 설계에서는 “화면 상태 전환”이라는 개념을 사용한다.

### 29.1 TransitionExpectation 예시

```json
{
  "type": "MODAL_OPEN",
  "expectedNextPageStateId": "PAGE_005",
  "requiredTexts": ["정말 삭제하시겠습니까?", "확인", "취소"],
  "timeoutMs": 5000
}
```

### 29.2 전환 유형

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

### 29.3 전환 실패 처리

기대 전환이 발생하지 않으면 `NAVIGATION_FAILED` 또는 `PAGE_STATE_MISMATCH`로 처리한다.

| 상황 | 처리 |
|---|---|
| URL 변경 기대했으나 변경 없음 | `NAVIGATION_FAILED` |
| 텍스트 등장 기대했으나 없음 | `NAVIGATION_FAILED` |
| 다음 PageState가 다름 | `PAGE_STATE_MISMATCH` |
| 모달이 떠야 하는데 안 뜸 | `NAVIGATION_FAILED` |
| 예상하지 못한 confirm 발생 | `DIALOG_UNHANDLED` |

---

## 30. RiskCheckResult 구조

리스크 검사는 TC 생성 전, 실행계획 생성 후, 실제 실행 직전 세 단계에서 수행한다.

ExecutionPlan에는 각 step의 리스크 판단 결과가 포함되어야 한다.

### 30.1 RiskCheckResult 예시

```json
{
  "riskLevel": "HIGH",
  "riskFlags": ["DELETE_DATA"],
  "matchedRiskKeywords": ["삭제"],
  "requiresApproval": true,
  "approvalScope": "PER_RUN",
  "reason": "삭제 버튼 클릭이며 데이터 삭제 가능성이 있음"
}
```

### 30.2 필드 정의

| 필드 | 설명 |
|---|---|
| `riskLevel` | LOW, MEDIUM, HIGH, PROHIBITED |
| `riskFlags` | 위험 플래그 목록 |
| `matchedRiskKeywords` | 탐지된 위험 키워드 |
| `requiresApproval` | 사람 승인 필요 여부 |
| `approvalScope` | 승인 범위 |
| `reason` | 판단 이유 |

### 30.3 approvalScope

| 값 | 설명 |
|---|---|
| `NONE` | 승인 불필요 |
| `PER_ACTION` | 해당 action마다 승인 |
| `PER_TC` | 해당 TC 실행 단위 승인 |
| `PER_RUN` | 해당 run에서 한 번 승인 |
| `FORBIDDEN` | 승인 불가, 실행 차단 |

---

## 31. DIALOG Step

DIALOG Step은 alert, confirm, prompt 또는 HTML 모달을 처리하는 단계다.

### 31.1 confirm 처리 예시

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

### 31.2 dialogType

| 값 | 설명 |
|---|---|
| `alert` | 브라우저 alert |
| `confirm` | 브라우저 confirm |
| `prompt` | 브라우저 prompt |
| `htmlModal` | DOM 기반 모달 |
| `toast` | 토스트 메시지 |
| `popup` | 새 창/새 탭 |

### 31.3 response

| 값 | 설명 |
|---|---|
| `accept` | 확인 |
| `dismiss` | 취소 |
| `fillAndAccept` | prompt 입력 후 확인 |
| `close` | HTML 모달 또는 popup 닫기 |
| `manual` | 사람 처리 필요 |

---

## 32. TABLE_ACTION Step

TABLE_ACTION Step은 목록/테이블 행 기준 조작을 표현한다.

CRUD에서 수정/삭제는 대부분 특정 행 내부의 버튼을 눌러야 하므로 일반 click만으로는 부족하다.

### 32.1 clickRowAction 예시

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

### 32.2 rowMatch

| matchType | 설명 |
|---|---|
| `CONTAINS_VALUE` | 행 전체 텍스트에 특정 값 포함 |
| `CELL_EQUALS` | 특정 컬럼 값이 기대값과 같음 |
| `CELL_CONTAINS` | 특정 컬럼 값이 특정 문자열 포함 |
| `FIRST_ROW` | 첫 번째 행 선택 |
| `LAST_ROW` | 마지막 행 선택 |

MVP에서는 `CONTAINS_VALUE`를 기본으로 한다.

---

## 33. CLEANUP Step과 CleanupPlan

테스트 자동화가 생성한 데이터는 정리 전략이 필요하다.

### 33.1 CleanupPlan 예시

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

### 33.2 cleanup strategy

| strategy | 설명 |
|---|---|
| `DELETE_CREATED_ROW` | 생성한 데이터 행 삭제 |
| `DEACTIVATE_CREATED_ITEM` | 삭제 대신 비활성화 |
| `ROLLBACK_BY_UI` | UI를 통해 원복 |
| `MANUAL_CLEANUP` | 수동 정리 필요 |
| `NO_CLEANUP` | 정리하지 않음 |

### 33.3 기본 원칙

```text
기존 데이터는 자동 cleanup 대상이 아니다.
AutoWebTesting이 생성하고 추적한 데이터만 cleanup 대상으로 삼는다.
```

---

## 34. RunResult 구조

RunResult는 실행 완료 후 생성되는 결과 데이터다.

### 34.1 RunResult 예시

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

### 34.2 StepResult

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

### 34.3 StepResult status

| 값 | 설명 |
|---|---|
| `PASSED` | step 성공 |
| `FAILED` | step 실패 |
| `SKIPPED` | 건너뜀 |
| `BLOCKED` | 정책 또는 사전조건으로 차단 |
| `REVIEW_REQUIRED` | 사람 검토 필요 |

---

## 35. FailurePackage 구조

FailurePackage는 실패분석을 위해 LLM 또는 사람이 참고하는 패키지다.

FailurePackage는 단순 에러 메시지가 아니라 실패 당시의 맥락을 포함해야 한다.

### 35.1 포함 항목

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

### 35.2 FailurePackage 예시

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

### 35.3 failureType

| 값 | 설명 |
|---|---|
| `TEST_FAILURE` | TC는 실행 완료되었으나 assertion 실패 |
| `EXECUTION_FAILURE` | 자동화 수행 자체 실패 |
| `RISK_BLOCKED` | 리스크 정책으로 실행 차단 |
| `MANUAL_REQUIRED` | 자동 판단 불가, 사람 검토 필요 |

---

## 36. ExecutionStatus 최종 후보

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

`testResult`는 `executionStatus = COMPLETED`인 경우에만 `P` 또는 `F`를 가진다.

---

## 37. 이번 단계 확정 권장안

| 항목 | 추천 결정 |
|---|---|
| ExecutionPlan | TC 단위 실행계획으로 관리 |
| Step 유형 | ACTION, ASSERTION, WAIT, DIALOG, TABLE_ACTION, SCREENSHOT, CLEANUP |
| 화면 전환 | expectedTransition으로 표현 |
| 페이지 이동 표현 | URL 변경이 아니라 화면 상태 전환으로 일반화 |
| 리스크 검사 | step 단위 riskCheck 포함 |
| 테이블 행 액션 | clickRowAction 도입 |
| Cleanup | CleanupPlan 도입 |
| 결과 | RunResult와 FailurePackage 분리 |
| 실패 | TEST_FAILURE와 EXECUTION_FAILURE 구분 |
| P/F 부여 | COMPLETED 상태에서만 허용 |

---

## 38. 다음 단계 검토 안건

다음 단계에서는 실제 구현을 위해 아래 항목을 확정한다.

1. JSON Schema 파일 구성
2. TypeScript 타입 구조
3. IPC 계약 재정리
4. Runner 실행 흐름
5. AI 탐색 루프와 ExecutionPlan 생성 프롬프트 구조
6. 샘플 JSON 세트
7. Phase별 구현 순서 재정의

## 39. 현재 확정된 설계 결정

| 번호 | 결정 | 상태 |
|---:|---|---|
| 1 | MVP는 단일 화면이 아니라 CRUD 중심 다중 화면 흐름을 지원한다. | 확정 |
| 2 | API Mode는 후순위이며, MVP는 GPT Web Import Mode 중심이다. | 확정 |
| 3 | `elementId`는 GPT 참조용 ID이고 실제 실행은 내부 selectorCandidates로 수행한다. | 확정 |
| 4 | 테스트 데이터는 `secret`, `testData`, `generated`, `file`로 구분한다. | 확정 |
| 5 | 자동 P/F 판정은 구조화된 assertion을 기준으로 한다. | 확정 |
| 6 | 실행 이벤트 스트림을 도입한다. | 확정 |
| 7 | 리스크 키워드 탐지를 적용한다. | 확정 |
| 8 | 실패 원인은 enum으로 고정한다. | 확정 |
| 9 | 저장 구조는 프로젝트 기준으로 통일한다. | 확정 |
| 10 | GPT Web Import 결과는 안전한 범위에서 보정한다. | 확정 |

---

## 22. 다음 단계 검토: PageState / PageFlow / ElementRegistry 세부 설계

CRUD 중심 다중 화면 자동화를 지원하려면 단순 DOM Summary만으로는 부족하다. 웹 업무 흐름은 여러 화면과 상태를 오가며 진행되므로, 화면 상태를 구분하는 `PageState`, 화면 간 이동 관계를 표현하는 `PageFlow`, 실제 실행용 요소 매핑을 보관하는 `ElementRegistry`가 필요하다.

---

### 22.1 설계 목표

이 단계의 설계 목표는 다음과 같다.

1. 여러 화면에 걸친 CRUD 테스트를 표현할 수 있어야 한다.
2. GPT에는 단순하고 안전한 DOM Summary만 제공해야 한다.
3. 실제 Playwright 실행에는 앱 내부의 안정적인 selector 후보를 사용해야 한다.
4. 실행 실패 시 어느 화면, 어느 요소, 어느 selector 후보에서 실패했는지 추적할 수 있어야 한다.
5. 사용자가 수동으로 캡처한 화면과 실행 중 도달한 화면을 비교할 수 있어야 한다.

---

### 22.2 핵심 개념 관계

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

각 개념의 역할은 다음과 같다.

| 개념 | 역할 |
|---|---|
| `PageState` | 특정 시점의 화면 상태를 식별한다. 예: 목록 화면, 등록 화면, 수정 화면, 삭제 확인 모달 |
| `DOM Summary` | GPT에게 전달할 화면 요소 요약본이다. |
| `ElementRegistry` | 앱 내부에서 elementId를 실제 Playwright locator 후보와 연결한다. |
| `PageFlow` | 화면 간 이동 관계와 전환 조건을 표현한다. |
| `ExecutionPlan` | 테스트케이스를 실제 실행 가능한 step과 assertion으로 표현한다. |

---

## 23. PageState 설계

### 23.1 PageState 정의

`PageState`는 테스트 자동화에서 구분해야 하는 하나의 화면 상태다.

웹앱에서는 URL이 같아도 상태가 다를 수 있다. 예를 들어 같은 `/users` URL이라도 검색 전 목록, 검색 후 목록, 모달이 열린 상태는 서로 다른 PageState로 볼 수 있다.

따라서 PageState는 단순 URL이 아니라 다음 정보를 함께 가진다.

- 화면 이름
- URL 또는 URL 패턴
- 화면 식별용 텍스트
- 해당 화면의 DOM Summary
- 해당 화면의 Element Registry
- 모달/팝업 여부
- 캡처 시각

### 23.2 PageState 예시

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

### 23.3 PageState 필드 정의

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

### 23.4 stateType

| 값 | 설명 |
|---|---|
| `PAGE` | 일반 페이지 화면 |
| `MODAL` | HTML 기반 모달이 열린 상태 |
| `POPUP` | 새 브라우저 창 또는 탭 |
| `DIALOG` | alert, confirm, prompt 등 브라우저 다이얼로그 |
| `PARTIAL` | 페이지 일부 영역만 변경된 상태. 예: 검색 결과 갱신 |

### 23.5 identityHints

`identityHints`는 실행 중 현재 화면이 기대한 PageState와 일치하는지 확인하는 데 사용한다.

```json
{
  "requiredTexts": ["사용자 목록", "검색", "등록"],
  "requiredElementIds": ["PAGE_001.el_0001"],
  "optionalTexts": ["전체", "사용자명"]
}
```

#### 판단 방식

- `requiredTexts` 중 일정 비율 이상이 화면에 보여야 한다.
- `requiredElementIds`는 ElementRegistry를 통해 실제 요소가 확인되어야 한다.
- `urlPattern`이 있으면 현재 URL과 함께 비교한다.
- 일치하지 않으면 `PAGE_STATE_MISMATCH` 또는 `MAPPING_FAILED`로 처리한다.

### 23.6 추천 결정

MVP에서는 PageState를 반드시 도입한다.

다만 앱이 사이트를 자동 탐색해 PageState를 만드는 방식은 후순위로 둔다. MVP에서는 사용자가 주요 화면으로 이동한 뒤 캡처하거나, 실행계획에 따라 이동한 후 필요한 화면을 캡처하는 방식으로 시작한다.

---

## 24. DOM Summary 설계

### 24.1 DOM Summary 목적

DOM Summary는 GPT가 실행계획을 만들 수 있도록 화면 요소를 요약한 JSON이다.

DOM Summary는 다음 원칙을 따른다.

- 전체 HTML을 전달하지 않는다.
- 비밀번호, 토큰, 계정값 등 민감정보를 포함하지 않는다.
- GPT가 elementId를 선택할 수 있을 정도의 정보만 제공한다.
- 실제 Playwright selector는 포함하지 않는다.

### 24.2 DOM Summary 예시

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
  "visibleTexts": [
    "사용자 목록",
    "검색",
    "등록",
    "사용자명"
  ],
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

### 24.3 DOM Element 필드 정의

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
| `region` | 화면 내 영역. 예: `search`, `table`, `form`, `toolbar`, `modal` |

### 24.4 tables 정보의 필요성

CRUD 테스트에서는 목록 검증이 매우 중요하다. 따라서 DOM Summary에는 테이블 후보 정보를 별도로 포함하는 것이 좋다.

필요 이유:

- 등록 후 목록에 값이 표시되는지 확인
- 수정 후 특정 행 값이 변경되었는지 확인
- 삭제 후 특정 행이 사라졌는지 확인
- 검색 결과 개수를 검증

---

## 25. ElementRegistry 설계

### 25.1 ElementRegistry 정의

`ElementRegistry`는 앱 내부에서만 사용하는 실행용 요소 매핑 정보다.

GPT에는 전달하지 않는다.

`DOM Summary`가 GPT용 요약이라면, `ElementRegistry`는 Playwright 실행용 실제 locator 후보 목록이다.

### 25.2 ElementRegistry 예시

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
        {
          "type": "role",
          "value": "button[name='등록']",
          "priority": 1,
          "confidence": 0.95
        },
        {
          "type": "text",
          "value": "button:has-text('등록')",
          "priority": 2,
          "confidence": 0.85
        },
        {
          "type": "css",
          "value": "[data-testid='create-user']",
          "priority": 3,
          "confidence": 0.9
        }
      ],
      "stableHints": {
        "role": "button",
        "label": "등록",
        "text": "등록",
        "nearbyText": "사용자 목록",
        "formId": null,
        "region": "toolbar"
      },
      "lastKnownBounds": {
        "x": 812,
        "y": 140,
        "width": 80,
        "height": 36
      }
    }
  ]
}
```

### 25.3 selectorCandidates 우선순위

selector 후보는 안정성이 높은 순서로 사용한다.

권장 우선순위:

| 우선순위 | selector 유형 | 설명 |
|---:|---|---|
| 1 | `testId` | `data-testid`, `data-cy` 등 테스트 전용 속성 |
| 2 | `role` | Playwright getByRole 기반 locator |
| 3 | `label` | getByLabel 기반 locator |
| 4 | `placeholder` | getByPlaceholder 기반 locator |
| 5 | `text` | 텍스트 기반 locator |
| 6 | `css` | CSS selector |
| 7 | `xpath` | 최후 수단 |

### 25.4 selector 후보 생성 규칙

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

### 25.5 실행 시 element resolve 방식

실행 시 Runner는 다음 순서로 요소를 찾는다.

```text
1. 현재 PageState 확인
2. elementId에 해당하는 registry item 조회
3. selectorCandidates를 priority 순서로 시도
4. visible/enabled 조건 확인
5. 후보가 여러 개면 stableHints로 재필터링
6. 하나로 확정되면 실행
7. 실패하면 MAPPING_FAILED 처리
```

### 25.6 매핑 로그 예시

```json
{
  "tcId": "TC_001-001",
  "stepId": "STEP_002",
  "pageStateId": "PAGE_001",
  "elementId": "PAGE_001.el_0001",
  "resolveAttempts": [
    {
      "selectorType": "role",
      "selector": "button[name='등록']",
      "result": "NOT_FOUND"
    },
    {
      "selectorType": "text",
      "selector": "button:has-text('등록')",
      "result": "MULTIPLE_MATCHES"
    },
    {
      "selectorType": "css",
      "selector": "[data-testid='create-user']",
      "result": "FOUND"
    }
  ],
  "finalResult": "FOUND"
}
```

---

## 26. PageFlow 설계

### 26.1 PageFlow 정의

`PageFlow`는 화면 간 이동 관계를 표현한다.

CRUD 테스트에서는 특정 버튼을 클릭하면 다른 화면이나 모달로 이동한다. 이 관계를 명시적으로 관리해야 실행계획 검증과 실패 분석이 쉬워진다.

### 26.2 PageFlow 예시

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
    },
    {
      "transitionId": "TR_002",
      "fromPageStateId": "PAGE_002",
      "toPageStateId": "PAGE_003",
      "trigger": {
        "action": "click",
        "elementId": "PAGE_002.el_0018",
        "description": "저장 버튼 클릭"
      },
      "expectedNavigation": {
        "type": "URL_CHANGE_OR_TEXT_APPEAR",
        "urlPattern": "/users/",
        "requiredTexts": ["저장되었습니다"]
      }
    }
  ]
}
```

### 26.3 expectedNavigation 유형

| 유형 | 설명 |
|---|---|
| `NONE` | 화면 전환 없음 |
| `URL_CHANGE` | URL 변경 기대 |
| `TEXT_APPEAR` | 특정 텍스트 등장 기대 |
| `ELEMENT_APPEAR` | 특정 요소 등장 기대 |
| `MODAL_OPEN` | 모달 열림 기대 |
| `POPUP_OPEN` | 새 창/탭 열림 기대 |
| `URL_CHANGE_OR_TEXT_APPEAR` | URL 변경 또는 텍스트 등장 중 하나 허용 |

### 26.4 PageFlow의 역할

PageFlow는 반드시 모든 실행을 통제하는 필수 구조는 아니다. MVP에서는 다음 용도로 사용한다.

- 실행계획이 올바른 화면 순서를 따르는지 검증
- 예상 화면 전환이 발생했는지 확인
- 실패 시 어느 전환에서 실패했는지 기록
- 향후 자동 PageState 캡처의 기반으로 활용

### 26.5 추천 결정

MVP에서는 PageFlow를 “강제 실행 엔진”이 아니라 “검증 및 추적 보조 정보”로 사용한다.

즉, ExecutionPlan의 step이 실제 실행 순서를 결정하고, PageFlow는 그 순서가 예상 흐름과 맞는지 확인하는 기준으로 둔다.

---

## 27. ExecutionPlan과 PageState 연결 방식

### 27.1 기본 원칙

ExecutionPlan의 각 step은 자신이 실행되어야 할 PageState를 명시한다.

```json
{
  "stepId": "STEP_001",
  "pageStateId": "PAGE_001",
  "action": "click",
  "elementId": "PAGE_001.el_0001",
  "description": "등록 버튼 클릭"
}
```

### 27.2 화면 전환 step

화면 전환이 예상되는 step은 `expectedNextPageStateId`를 포함한다.

```json
{
  "stepId": "STEP_001",
  "pageStateId": "PAGE_001",
  "action": "click",
  "elementId": "PAGE_001.el_0001",
  "expectedNextPageStateId": "PAGE_002",
  "expectedNavigation": {
    "type": "URL_CHANGE",
    "urlPattern": "/users/new",
    "requiredTexts": ["사용자 등록"]
  },
  "description": "등록 버튼 클릭 후 등록 화면으로 이동"
}
```

### 27.3 실행 중 PageState 확인

Runner는 step 실행 전후로 PageState를 확인한다.

```text
step 실행 전:
- 현재 화면이 step.pageStateId와 맞는지 확인
- 맞지 않으면 PAGE_STATE_MISMATCH

step 실행 후:
- expectedNextPageStateId가 있으면 화면 전환 확인
- expectedNavigation 조건 확인
- 실패 시 NAVIGATION_FAILED 또는 PAGE_STATE_MISMATCH
```

### 27.4 신규 실행 상태 추가 검토

다중 화면 지원을 위해 다음 실행 상태를 추가하는 것을 권장한다.

| 상태 | 설명 |
|---|---|
| `PAGE_STATE_MISMATCH` | 현재 화면이 기대한 PageState와 다름 |
| `NAVIGATION_FAILED` | 기대한 화면 이동이 발생하지 않음 |
| `DIALOG_UNHANDLED` | alert/confirm/prompt 또는 모달을 처리하지 못함 |

최종 ExecutionStatus 목록에 포함할지 다음 단계에서 확정한다.

---

## 28. PageState 캡처 방식

### 28.1 선택지

#### 선택 A — 사용자 수동 캡처

사용자가 각 화면으로 이동한 뒤 `현재 화면 캡처` 버튼을 누른다.

장점:

- 구현이 쉽다.
- 실무자가 화면 의미를 직접 이름 붙일 수 있다.
- 잘못된 자동 탐색 위험이 낮다.

단점:

- 사용자가 여러 화면을 직접 캡처해야 하므로 번거롭다.

#### 선택 B — 실행 중 자동 캡처

앱이 실행계획에 따라 이동하다가 새 화면에 도달하면 자동으로 DOM을 캡처한다.

장점:

- 사용자 부담이 적다.
- 실제 실행 흐름과 캡처가 일치한다.

단점:

- 초기 구현 난도가 높다.
- 잘못된 화면을 PageState로 저장할 수 있다.
- GPT 실행계획 생성 전 필요한 DOM이 부족할 수 있다.

#### 선택 C — MVP는 수동 캡처, 후속으로 자동 캡처

추천 방식이다.

MVP에서는 사용자가 주요 화면을 직접 캡처하고, 후속 Phase에서 실행 중 자동 재캡처를 추가한다.

### 28.2 추천 결정

MVP에서는 **선택 C**를 채택한다.

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

## 29. 이번 단계의 확정 권장안

| 항목 | 추천 결정 |
|---|---|
| PageState 도입 | 도입 |
| elementId 형식 | `PAGE_001.el_0001` 형식 사용 |
| DOM Summary | GPT 전달용 요약 정보로 사용 |
| ElementRegistry | 앱 내부 실행용 selector 후보 저장 |
| selectorCandidates GPT 전달 여부 | 전달하지 않음 |
| PageFlow | 실행 검증 및 추적 보조 정보로 사용 |
| PageState 캡처 방식 | MVP는 수동 캡처, 후속 자동 캡처 |
| PageState 확인 | step 실행 전후로 확인 |
| 추가 실행 상태 | `PAGE_STATE_MISMATCH`, `NAVIGATION_FAILED`, `DIALOG_UNHANDLED` 추가 검토 |

---

## 30. 다음 결정이 필요한 질문

### 질문 1. PageState 캡처 방식은 추천안대로 갈 것인가?

선택지:

- A. MVP부터 사용자가 주요 화면을 직접 캡처한다.
- B. MVP부터 앱이 자동으로 화면을 탐색하고 캡처한다.
- C. 수동 캡처를 기본으로 하되, 실행 중 알 수 없는 화면은 임시 캡처한다.

추천: **C**

수동 캡처를 기본으로 하되, 실행 중 알 수 없는 화면에 도달하면 `UNKNOWN_PAGE_CAPTURE`로 임시 저장하고 사용자 검토 대상으로 두는 방식이 가장 현실적이다.

### 질문 2. PageFlow를 필수로 둘 것인가?

선택지:

- A. 모든 ExecutionPlan은 PageFlow를 반드시 참조해야 한다.
- B. PageFlow는 있으면 검증에 사용하고, 없어도 실행은 가능하게 한다.
- C. MVP에서는 PageFlow 없이 ExecutionPlan만 사용한다.

추천: **B**

MVP에서 PageFlow를 너무 강제하면 사용자가 준비해야 할 데이터가 많아진다. 다만 있으면 실행계획 검증과 실패 분석에 활용한다.

### 질문 3. ExecutionStatus에 다중 화면 전용 상태를 추가할 것인가?

추천 추가값:

- `PAGE_STATE_MISMATCH`
- `NAVIGATION_FAILED`
- `DIALOG_UNHANDLED`

추천: **추가**

다중 화면 자동화에서는 이 세 가지 실패가 자주 발생하므로, `SCRIPT_FAILED` 하나로 뭉개지 않는 것이 좋다.

## 31. 다음 결정이 필요한 질문

### 질문 1. CRUD의 Delete를 MVP에 어느 수준까지 포함할 것인가?

선택지:

- A. 실제 삭제는 제외하고 비활성화/취소 가능한 삭제만 허용
- B. 테스트 전용 데이터에 한해 삭제 허용
- C. 삭제는 항상 HIGH로 두고 실행마다 명시 승인
- D. 삭제는 MVP에서 제외

추천: **B + C 조합**

테스트 자동화가 직접 생성한 데이터에 한해서만 삭제를 허용하되, 삭제 액션은 기본적으로 HIGH로 보고 실행 전 명시 승인하도록 한다.

### 질문 2. 다중 PageState 캡처는 누가 주도할 것인가?

선택지:

- A. 사용자가 각 화면으로 직접 이동하고 캡처 버튼을 누른다.
- B. 앱이 실행계획에 따라 이동하며 필요한 시점에 자동 캡처한다.
- C. A를 MVP로 하고 B를 후속 Phase로 둔다.

추천: **C**

MVP에서는 사용자가 주요 화면을 직접 캡처할 수 있게 하고, 실행 중 자동 재캡처는 후속으로 확장한다.

### 질문 3. GPT에 selectorCandidates를 전달할 것인가?

선택지:

- A. 전달하지 않는다. elementId와 요약 정보만 전달한다.
- B. 일부 안정 selector만 전달한다.
- C. 모든 selectorCandidates를 전달한다.

추천: **A**

GPT에는 단순화된 DOM Summary만 전달하고, selectorCandidates는 앱 내부에서만 사용한다.

---

*문서 버전: v0.2*
*작성 기준: CRUD 중심 다중 화면 MVP 방향 반영*

