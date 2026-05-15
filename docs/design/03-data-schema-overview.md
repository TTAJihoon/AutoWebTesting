---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 04-page-state-dom.md
  - 05-execution-plan.md
  - 07-test-data.md
  - 09-run-result-failure.md
---

# 데이터 스키마 개요

이 문서는 AutoWebTesting에서 사용하는 모든 JSON 스키마의 관계와 흐름을 정리한다. 각 스키마의 세부 필드는 해당 design 문서를 참조한다.

## 1. 전체 런타임 구조

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

## 2. 프로세스 책임

| 레이어 | 위치 | 책임 |
|---|---|---|
| Renderer | `src/renderer/` | UI, 상태 표시, 사용자 검토, 입력 폼 |
| Preload | `src/preload/` | `contextBridge` 기반 IPC API 노출 |
| Main Process | `src/main/` | IPC 핸들러, 파일 I/O, 프로젝트 저장소, 보고서 생성 |
| Runner | `src/runner/` | DOM 캡처, Element Registry 생성, Playwright 실행, 리스크 정책 적용 |
| Shared | `src/shared/` | 공통 타입, 상수, 스키마 버전 |
| Schemas | `schemas/` | JSON 계약 정의 |

## 3. 핵심 스키마 관계

```text
Project
└── TestCase[]
    └── ExecutionPlan
        └── Step[]
            ├── pageStateId  ──→  PageState
            ├── elementId    ──→  ElementRegistry (내부) / DOM Summary (외부 GPT용)
            ├── valueSource  ──→  TestDataProfile
            └── assertion    ──→  AssertionResult

ExplorationSession (AI 탐색)
├── Observation[]
├── AiDecision[]
├── ExplorationAction[]
├── ExplorationMemory
├── CandidateFeature[]
└── CandidateCrudFlow[]

Run (실행 결과)
├── RunResult
│   └── StepResult[]
├── FailurePackage[]
└── CreatedDataRegistry
```

## 4. 스키마 파일 목록

| 스키마 파일 | 설명 | 상세 문서 |
|---|---|---|
| `schemas/testcase.schema.json` | 테스트케이스 JSON 계약 | [`05-execution-plan.md`](05-execution-plan.md), [`08-assertion-policy.md`](08-assertion-policy.md) |
| `schemas/exploration-session.schema.json` | AI 탐색 세션 | [`02-ai-exploration.md`](02-ai-exploration.md) |
| `schemas/page-state.schema.json` | 화면 상태 | [`04-page-state-dom.md`](04-page-state-dom.md) |
| `schemas/dom-summary.schema.json` | GPT 전달용 DOM 요약 | [`04-page-state-dom.md`](04-page-state-dom.md) |
| `schemas/element-registry.schema.json` | 내부 실행용 selector 매핑 | [`04-page-state-dom.md`](04-page-state-dom.md) |
| `schemas/execution-plan.schema.json` | 실행계획 | [`05-execution-plan.md`](05-execution-plan.md) |
| `schemas/run-result.schema.json` | 실행 결과 | [`09-run-result-failure.md`](09-run-result-failure.md) |
| `schemas/failure-package.schema.json` | 실패 분석용 패키지 | [`09-run-result-failure.md`](09-run-result-failure.md) |

## 5. 데이터 흐름

### 5.1 생성 흐름 (입력 → 실행계획)

```text
기능목록 + 매뉴얼 + URL
    ↓ (GPT 또는 AI 탐색)
TestCase (DRAFT)
    ↓ (사람 검토)
TestCase (APPROVED)
    ↓ (DOM 캡처)
PageState + DOM Summary + ElementRegistry
    ↓ (GPT 또는 AI 매핑)
ExecutionPlan (DRAFT)
    ↓ (스키마/리스크/매핑 검증)
ExecutionPlan (READY)
```

### 5.2 실행 흐름 (실행계획 → 결과)

```text
ExecutionPlan (READY)
    ↓ (Playwright Runner)
StepResult[]
    ↓ (집계)
RunResult
    ↓ (실패가 있으면)
FailurePackage[]
    ↓ (GPT 또는 AI 분석)
FailureAnalysis[]
    ↓ (보고서 반영)
report.html / execution-result.xlsx / evidence.zip
```

## 6. 식별자 규칙

| 식별자 | 형식 | 예시 |
|---|---|---|
| TC_ID | `TC_{소분류번호}-{순번}` | `TC_001-001` |
| pageStateId | `PAGE_{3자리}` | `PAGE_001` |
| elementId | `{pageStateId}.el_{4자리}` | `PAGE_001.el_0001` |
| stepId | `STEP_{3자리}` 또는 `ASSERT_{3자리}` | `STEP_001`, `ASSERT_001` |
| runId | `RUN-YYYYMMDD-hhmmss` | `RUN-20260515-103022` |
| explorationSessionId | `EXP_YYYYMMDD_{seq}` | `EXP_20260515_001` |

## 7. 스키마 버전 관리

모든 JSON 스키마는 최상위에 `schemaVersion` 필드를 가진다.

```json
{
  "schemaVersion": "0.3",
  ...
}
```

- 스키마 변경 시 버전을 올린다.
- 앱은 알 수 없는 schemaVersion을 만나면 import를 거부하고 사용자에게 경고한다.
- 마이너 버전 차이는 경고만, 메이저 버전 차이는 차단한다.

## 8. GPT에 전달하는 데이터와 내부 전용 데이터의 분리

| 데이터 | GPT 전달 | 내부 전용 |
|---|---|---|
| DOM Summary | O | - |
| ElementRegistry | X | O (실행용 selector 후보) |
| TestCase (시나리오) | O | - |
| TestData (`secret`) | X | O (계정정보, 토큰) |
| TestData (`testData`, `generated`) | O | - |
| 스크린샷 (masked) | 조건부 O | - |
| 스크린샷 (원본) | X | O (증적용) |

이 원칙은 모든 스키마 설계에 일관되게 적용된다.
