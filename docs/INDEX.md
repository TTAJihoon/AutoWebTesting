# AutoWebTesting 설계문서 인덱스

이 문서는 AutoWebTesting 개발 시 참조할 설계문서 목록과 사용 기준을 안내한다.

## 기본 원칙

- 항상 이 문서를 먼저 읽는다.
- 현재 작업 범위는 `WORKING.md`에서 확인한다.
- 필요한 경우에만 개별 설계문서를 추가로 읽는다.
- `stable` 상태 문서는 특별한 이유가 없으면 수정하지 않는다.
- 코드 작성 전 관련 문서의 “확정된 결정”과 “주의사항”을 확인한다.
- 설명은 한글로 작성하되, 타입명/필드명/enum/파일명은 영어를 유지한다.

## 문서 목록

| 문서 | 목적 | 읽어야 하는 경우 |
|---|---|---|
| `design/00-product-overview.md` | 제품 개요와 핵심 원칙 | 제품 방향이 헷갈릴 때 |
| `design/01-mvp-scope.md` | MVP 범위와 제외 범위 | 기능 포함/제외 판단 시 |
| `design/02-ai-exploration.md` | AI 탐색 세션 구조 | URL 기반 탐색, Observation, AiDecision 구현 시 |
| `design/03-data-schema-overview.md` | 전체 JSON 스키마 관계 | 타입/스키마 수정 시 |
| `design/04-page-state-dom.md` | PageState, DOM Summary, ElementRegistry | 화면 캡처/DOM 분석/elementId 매핑 구현 시 |
| `design/05-execution-plan.md` | ExecutionPlan, Step, Transition, Cleanup | 실행계획 import/export/runner 구현 시 |
| `design/06-risk-policy.md` | 리스크 수준, 위험 키워드, 승인 정책 | 위험 행동 차단 구현 시 |
| `design/07-test-data.md` | 테스트 데이터 변수와 secret 처리 | 로그인, 입력값, generated 변수 구현 시 |
| `design/08-assertion-policy.md` | Assertion 분류와 P/F 판단 | 검증 로직 구현 시 |
| `design/09-run-result-failure.md` | RunResult, FailurePackage, FailureCause | 결과 저장/실패분석 구현 시 |
| `design/10-ipc-contract.md` | Electron IPC 채널 계약 | Renderer-Main 통신 구현 시 |
| `design/11-runner-design.md` | Playwright Runner 실행 구조 | 실제 자동 실행 엔진 구현 시 |
| `design/12-gpt-web-workflow.md` | GPT 웹 임포트 절차 | GPT 웹 기반 JSON 생성/업로드 구현 시 |
| `design/13-prompt-specs.md` | 프롬프트 입력/출력 규칙 | 프롬프트 작성/수정 시 |
| `design/14-storage-structure.md` | 프로젝트 폴더와 파일 저장 규칙 | 파일 저장/불러오기 구현 시 |
| `design/15-phase-roadmap.md` | 개발 단계와 우선순위 | 작업 순서 결정 시 |

## 주요 결정 문서

| 문서 | 내용 |
|---|---|
| `decisions/ADR-001-ai-exploration-mvp.md` | AI 탐색 기반 MVP 결정 |
| `decisions/ADR-002-dom-and-image-observation.md` | DOM 우선 + 선택적 이미지 보강 결정 |
| `decisions/ADR-003-risk-policy.md` | 3단계 리스크 정책 결정 |
| `decisions/ADR-004-test-data-cleanup.md` | 자동 생성 데이터 cleanup 정책 결정 |
| `decisions/ADR-005-gpt-web-import-vs-api-mode.md` | GPT Web Import와 API Mode의 관계 결정 |
| `decisions/ADR-006-schema-as-contract-zod-as-runtime.md` | JSON Schema는 계약 문서, Zod는 런타임/타입 원천 |

## 스키마와 샘플

JSON Schema 파일(`schemas/`)은 사람과 LLM이 읽는 **계약 문서**다. 실제 런타임 검증과 TS 타입은 `src/shared/schemas/*.ts`의 Zod 스키마가 담당하며, CI 스크립트가 둘의 일치를 검증한다. 자세한 내용은 [`ADR-006`](decisions/ADR-006-schema-as-contract-zod-as-runtime.md) 참고.

| 영역 | 위치 | 설명 |
|---|---|---|
| 계약 (사람용) | `schemas/*.schema.json` | 11개 JSON Schema |
| 샘플 | `examples/*.sample.json` | 각 스키마의 실제 사용 예시 |
| 런타임 (코드) | `src/shared/schemas/*.ts` | Zod 스키마, `z.infer`로 TS 타입 도출 |

## LLM 작업 지침

LLM 또는 개발 에이전트는 다음 순서로 문서를 읽는다.

1. `INDEX.md`
2. `WORKING.md`
3. 현재 작업과 관련된 design 문서
4. 필요한 경우 관련 ADR 문서
5. 필요한 경우 schemas/examples 문서

작업 범위 밖 문서는 수정하지 않는다.
