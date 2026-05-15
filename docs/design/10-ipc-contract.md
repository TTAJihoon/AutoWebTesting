---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 11-runner-design.md
---

# IPC 계약

Renderer ↔ Main 프로세스 사이의 IPC 채널을 정의한다.

`src/preload/index.ts`에서 `contextBridge.exposeInMainWorld`로 노출되며, Renderer에서는 `window.autoWebTesting` 객체로 접근한다.

## 1. 기본 원칙

- IPC 핸들러는 비즈니스 로직을 직접 구현하지 않고 runner/main 모듈에 위임한다.
- 요청/응답은 JSON 직렬화 가능한 객체만 사용한다.
- 모든 채널은 양방향이 아닌 단방향 또는 request/response.
- 진행률처럼 실시간 갱신이 필요한 경우 Event 채널을 별도로 둔다.
- 보안상 민감한 작업(파일 I/O, Playwright 실행 등)은 Main에서만 수행한다.

## 2. IPC Command (Renderer → Main)

| 채널 | Request | Response | 설명 | 구현 상태 |
|---|---|---|---|---|
| `app:get-info` | — | `{ name, version, platform }` | 앱 메타 정보 | ✅ |
| `project:create` | `{ name, targetUrl? }` | `ProjectRecord` | 새 프로젝트 생성 | 🔲 |
| `project:list` | — | `ProjectRecord[]` | 프로젝트 목록 조회 | 🔲 |
| `project:open` | `{ projectId }` | `ProjectRecord` | 프로젝트 열기 | 🔲 |
| `testcase:import` | `{ projectId, payload }` | `{ accepted, errors }` | TC JSON 임포트 | 🔲 |
| `testcase:update-review` | `{ tcId, reviewStatus }` | `TestCase` | TC 검토 상태 변경 | 🔲 |
| `dom:capture-summary` | `CaptureDomSummaryRequest` | `DomSummary` | DOM 자동 캡처 | ✅ |
| `dom:save-page-state` | `PageState` | `{ pageStateId }` | PageState 저장 | 🔲 |
| `plan:import` | `{ projectId, payload }` | `{ accepted, errors }` | 실행계획 임포트 | 🔲 |
| `run:start` | `ExecutePlansRequest` | `{ runId }` | 실행 시작 | ✅ (channel: `run:execute-plans`) |
| `run:cancel` | `{ runId }` | `{ cancelled }` | 실행 취소 | 🔲 |
| `run:rerun-testcase` | `{ runId, tcId }` | `{ rerunId }` | 특정 TC 재실행 | 🔲 |
| `run:save-artifacts` | `SaveRunArtifactsRequest` | `SaveRunArtifactsResponse` | 결과 저장 | ✅ |
| `run:export-excel` | `ExcelExportRequest` | `ExcelExportResponse` | Excel 내보내기 | 🔲 |
| `run:create-zip` | `{ runDir, runId }` | `{ zipPath, sizeMb }` | Evidence ZIP 생성 | 🔲 |
| `failure-analysis:import` | `FailureAnalysisPayload` | `{ accepted, errors }` | 실패분석 JSON 임포트 | 🔲 |
| `llm:generate-testcases` | `LlmTestcaseRequest` | `TestCase[]` | API Mode TC 생성 | 🔲 (Phase 9) |
| `llm:generate-plan` | `LlmPlanRequest` | `ExecutionPlan[]` | API Mode 계획 생성 | 🔲 (Phase 9) |
| `llm:analyze-failure` | `LlmFailureRequest` | `FailureAnalysis[]` | API Mode 실패분석 | 🔲 (Phase 9) |

## 3. IPC Event (Main → Renderer)

실행 중 실시간 상태 표시를 위해 사용한다.

| 이벤트 | Payload | 설명 |
|---|---|---|
| `run:started` | `{ runId, startedAt, totalTcCount }` | 실행 시작됨 |
| `run:progress` | `{ runId, completedTcCount, totalTcCount }` | 전체 진행률 갱신 |
| `run:testcase-started` | `{ runId, tcId, executionPlanId }` | 특정 TC 시작 |
| `run:step-started` | `{ runId, tcId, stepId, action, pageStateId }` | 특정 step 시작 |
| `run:step-finished` | `{ runId, tcId, stepId, status, message? }` | 특정 step 종료 |
| `run:testcase-finished` | `{ runId, tcId, executionStatus, testResult }` | 특정 TC 종료 |
| `run:failed` | `{ runId, error }` | 실행 중 치명 오류 발생 |
| `run:cancelled` | `{ runId }` | 사용자 취소 완료 |
| `run:finished` | `{ runId, summary }` | 전체 실행 완료 |

### 3.1 이벤트 예시

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

## 4. 탐색 모드 IPC (Phase 9 이후)

AI 탐색 모드용 채널은 Phase 9에서 확정한다.

| 채널 | 설명 |
|---|---|
| `exploration:start` | 탐색 세션 시작 |
| `exploration:next-action` | 다음 AI 결정 요청 |
| `exploration:approve-action` | HIGH 리스크 행동 승인 |
| `exploration:stop` | 탐색 종료 |
| `exploration:event` (Event) | 탐색 진행 이벤트 스트림 |

## 5. Preload 노출 예시

```typescript
// src/preload/index.ts
const api = {
  getAppInfo: () => ipcRenderer.invoke("app:get-info"),
  captureDomSummary: (request) => ipcRenderer.invoke("dom:capture-summary", request),
  executePlans: (request) => ipcRenderer.invoke("run:execute-plans", request),
  cancelRun: (request) => ipcRenderer.invoke("run:cancel", request),
  saveRunArtifacts: (request) => ipcRenderer.invoke("run:save-artifacts", request),
  exportExcel: (request) => ipcRenderer.invoke("run:export-excel", request),
  createZip: (request) => ipcRenderer.invoke("run:create-zip", request),
  // Event 구독
  onRunEvent: (handler: (event: RunEvent) => void) => {
    const listener = (_e: unknown, payload: RunEvent) => handler(payload);
    ipcRenderer.on("run:event", listener);
    return () => ipcRenderer.removeListener("run:event", listener);
  }
};

contextBridge.exposeInMainWorld("autoWebTesting", api);
```

## 6. 에러 처리

- IPC 핸들러는 가능한 한 throw하지 않고 `{ ok: false, error }` 형식으로 응답한다.
- 단, TypeScript 타입 단순화를 위해 throw 방식도 허용한다. 단, Renderer에서 try-catch로 반드시 처리한다.
- 에러 메시지는 한글로 작성한다 (UI 표시용).
- 디버그용 stack trace는 별도 필드(`debugInfo`)로 전달한다.

## 7. 보안

- Renderer는 직접 `node:fs`, `node:child_process` 등 Node API에 접근할 수 없다.
- 파일 시스템 접근은 모두 IPC를 통해 Main에서만 수행한다.
- `webPreferences.sandbox`는 false지만 `nodeIntegration`은 false 유지.
- `contextIsolation`은 true 유지.
