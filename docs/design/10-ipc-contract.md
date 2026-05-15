---
status: draft
lastUpdated: 2026-05-15
related:
  - 05-execution-plan.md
  - 11-runner-design.md
---

# 10. IPC 계약

## 목적

IPC 계약은 Electron Renderer와 Main Process 사이의 통신 규칙이다.

사용자가 직접 보는 것은 아니며, 개발자가 `preload`, `main`, `shared` 코드에서 관리한다.

## 권장 파일 구조

```text
src/shared/ipcChannels.ts
src/shared/ipcTypes.ts
src/preload/index.ts
src/main/ipcHandlers.ts
```

## IPC Command

| 채널 | 설명 |
|---|---|
| `app:get-info` | 앱 정보 조회 |
| `project:create` | 프로젝트 생성 |
| `project:list` | 프로젝트 목록 조회 |
| `exploration:start` | AI 탐색 세션 시작 |
| `exploration:cancel` | AI 탐색 취소 |
| `dom:capture-summary` | DOM Summary 생성 |
| `plan:import` | ExecutionPlan JSON 임포트 |
| `plan:validate` | 실행계획 검증 |
| `run:start` | 실행 시작 |
| `run:cancel` | 실행 취소 |
| `run:rerun-testcase` | 특정 TC 재실행 |
| `run:save-artifacts` | 결과 저장 |

## IPC Event

| 이벤트 | 설명 |
|---|---|
| `exploration:started` | 탐색 시작 |
| `exploration:observation-created` | Observation 생성 |
| `exploration:decision-created` | AiDecision 생성 |
| `exploration:action-executed` | ExplorationAction 실행 |
| `exploration:review-required` | 사람 검토 필요 |
| `exploration:finished` | 탐색 완료 |
| `run:started` | 실행 시작 |
| `run:progress` | 전체 진행률 갱신 |
| `run:testcase-started` | 특정 TC 시작 |
| `run:step-started` | 특정 step 시작 |
| `run:step-finished` | 특정 step 종료 |
| `run:testcase-finished` | 특정 TC 종료 |
| `run:failed` | 실행 중 치명 오류 발생 |
| `run:cancelled` | 사용자 취소 완료 |
| `run:finished` | 전체 실행 완료 |

## 원칙

- 채널명은 문자열 리터럴을 직접 쓰지 않고 상수로 관리한다.
- Request/Response/Event 타입은 `shared`에 둔다.
- Renderer에서는 `window.autowebtest.*` API만 사용한다.
- Main Process의 IPC 핸들러에는 비즈니스 로직을 직접 넣지 않고 runner/service에 위임한다.
