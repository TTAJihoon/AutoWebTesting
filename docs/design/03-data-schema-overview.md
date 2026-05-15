---
status: draft
lastUpdated: 2026-05-15
related:
  - 02-ai-exploration.md
  - 04-page-state-dom.md
  - 05-execution-plan.md
  - 09-run-result-failure.md
---

# 03. 데이터 스키마 개요

## 목적

이 문서는 AutoWebTesting에서 사용하는 JSON 스키마들의 관계를 정리한다.

실제 검증용 JSON Schema는 `docs/schemas/*.schema.json`에 둔다.

## 주요 스키마

| 스키마 | 목적 |
|---|---|
| `testcase.schema.json` | 테스트케이스 목록과 검토 상태 |
| `exploration-session.schema.json` | AI 탐색 세션 |
| `observation.schema.json` | 화면 관찰 데이터 |
| `page-state.schema.json` | 화면 상태 |
| `dom-summary.schema.json` | GPT/LLM 전달용 DOM 요약 |
| `element-registry.schema.json` | 앱 내부 실행용 selector 후보 |
| `page-flow.schema.json` | 화면 상태 전환 후보 |
| `execution-plan.schema.json` | Playwright 실행계획 |
| `run-result.schema.json` | 실행 결과 |
| `failure-package.schema.json` | 실패분석용 패키지 |
| `risk-policy.schema.json` | 리스크 정책과 키워드 |
| `test-data-profile.schema.json` | 테스트 데이터 변수 |

## 스키마 관계

```text
Project
├── TestDataProfile
├── ExplorationSession
│   ├── Observation[]
│   ├── PageState[]
│   │   ├── DomSummary
│   │   └── ElementRegistry
│   ├── PageFlow[]
│   ├── CandidateFeature[]
│   └── CandidateCrudFlow[]
├── TestCase[]
├── ExecutionPlan[]
└── RunResult[]
    └── FailurePackage[]
```

## 공통 필드 원칙

대부분의 스키마는 다음 공통 필드를 가진다.

| 필드 | 설명 |
|---|---|
| `schemaVersion` | 스키마 버전 |
| `createdAt` | 생성 시각 |
| `updatedAt` | 수정 시각 |
| `source` | 생성 출처 |
| `reviewStatus` | 사람 검토 상태가 필요한 경우 사용 |

## 상태값 관리 원칙

enum 값은 영어 대문자 snake case로 작성한다.

예:

```text
READY
NEEDS_MAPPING_REVIEW
PAGE_STATE_MISMATCH
NAVIGATION_FAILED
```
