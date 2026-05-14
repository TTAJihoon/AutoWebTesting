# AutoWebTesting — 종합 설계문서

> 이 문서는 개발 전 단계에 걸쳐 참조하는 단일 설계 기준입니다.
> 세부 정책은 각 참조 문서(`data-schema.md`, `risk-policy.md`, `prompt-specs.md` 등)를 따릅니다.

---

## 1. 프로젝트 목표

비개발자(테스터, QA 담당자)가 GPT의 도움을 받아 웹 서비스를 자동으로 테스트할 수 있는 **Windows 11 데스크톱 앱**.

| 핵심 원칙 | 설명 |
|-----------|------|
| **로컬 우선** | 외부 API 없이 GPT 웹 복붙만으로 동작 |
| **안전 실행** | 리스크 정책 통과 후에만 Playwright 실행 |
| **검토 가능성** | 모든 LLM 출력을 사람이 검토한 후 실행 |
| **추적 가능성** | 제외/거부된 테스트케이스도 이력 보존 |

---

## 2. 전체 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                   Renderer (React)                  │
│  Tab1: TC 검토  Tab2: DOM 캡처  Tab3: 실행계획 검토  │
│  Tab4: 실행 모니터  Tab5: 결과 요약                  │
└──────────────────┬──────────────────────────────────┘
                   │ IPC (contextBridge)
┌──────────────────▼──────────────────────────────────┐
│                  Main Process (Electron)             │
│  ipcMain.handle: app:get-info                       │
│  ipcMain.handle: dom:capture-summary                │
│  ipcMain.handle: run:execute-plans                  │
│  ipcMain.handle: run:save-artifacts                 │
└──────┬─────────────────┬───────────────┬────────────┘
       │                 │               │
┌──────▼──────┐  ┌───────▼──────┐  ┌────▼────────────┐
│ DOM Capture │  │   Executor   │  │  Artifact Writer │
│ (Playwright)│  │  (Playwright)│  │  (파일/보고서)   │
└─────────────┘  └──────────────┘  └─────────────────┘
```

### 프로세스 경계

| 레이어 | 위치 | 역할 |
|--------|------|------|
| `src/renderer/` | Renderer (브라우저 컨텍스트) | UI, 상태 관리, 유효성 검사 |
| `src/preload/` | Preload | IPC 브릿지 노출 (contextBridge) |
| `src/main/` | Main (Node.js) | IPC 핸들러, Playwright 오케스트레이션, 파일 I/O |
| `src/runner/` | Main 내부 모듈 | Playwright 실행 엔진, DOM 캡처, 리스크 정책 |
| `src/shared/` | 공유 | 타입, 상수 |

---

## 3. IPC 계약

Renderer ↔ Main 간 채널 전체 목록. 이 계약은 `src/preload/index.ts`에 반드시 반영되어야 합니다.

| 채널 | 방향 | Request 타입 | Response 타입 | 구현 상태 |
|------|------|-------------|--------------|---------|
| `app:get-info` | R→M | — | `{ name, version, platform }` | ✅ |
| `dom:capture-summary` | R→M | `CaptureDomSummaryRequest` | `DomSummary` | ✅ |
| `run:execute-plans` | R→M | `ExecutePlansRequest` | `ExecutionResult[]` | ✅ |
| `run:save-artifacts` | R→M | `SaveRunArtifactsRequest` | `{ runId, outputDir }` | ✅ |
| `project:create` | R→M | `{ name: string }` | `ProjectRecord` | 🔲 Phase 6 |
| `project:list` | R→M | — | `ProjectRecord[]` | 🔲 Phase 6 |
| `run:list` | R→M | `{ projectId }` | `RunRecord[]` | 🔲 Phase 6 |
| `run:get-result` | R→M | `{ runId }` | `RunResult` | 🔲 Phase 6 |
| `llm:generate-testcases` | R→M | `LlmTestcaseRequest` | `TestCase[]` | 🔲 Phase 7 |
| `llm:generate-plan` | R→M | `LlmPlanRequest` | `ExecutionPlan[]` | 🔲 Phase 7 |
| `llm:analyze-failure` | R→M | `LlmFailureRequest` | `FailureAnalysis[]` | 🔲 Phase 7 |

---

## 4. 모듈 책임

### `src/shared/types.ts`
모든 데이터 타입 정의. Renderer와 Main이 공유. 변경 시 양쪽 영향 확인 필수.

### `src/shared/constants.ts`
스키마 버전, 액션 목록, 상태 열거값 등 매직 리터럴 제거용 상수.

### `src/runner/playwrightDomCapture.ts`
- URL 접속 → DOM 추출 → `DomSummary` 반환
- 최대 250개 요소, 80개 가시 텍스트 제한
- 요소에 `el_0001` 형식 ID 부여

### `src/runner/domSummarizer.ts`
- DOM에서 접근성 역할(role) 파악
- 버튼, 링크, 텍스트박스, 셀렉트 등 분류

### `src/runner/actionPolicy.ts`
- 리스크 정책 적용 (→ `docs/risk-policy.md`)
- PROHIBITED 액션 차단, HIGH 액션 승인 요청

### `src/runner/executor.ts`
- `ExecutionPlan[]` → Playwright 명령 순서 실행
- 14가지 액션 타입 지원 (→ `docs/data-schema.md`)
- 실패 시 스크린샷 캡처
- `ExecutionStatus` 반환

### `src/main/runArtifacts.ts`
- 결과를 `Documents/AutoWebTesting/runs/RUN-YYYYMMDDhhmmss/`에 저장
- `run-result.json`, `failure-package.json`, `report.html` 생성

### `src/renderer/src/App.tsx`
- 5단계 탭 UI
- 각 단계별 상태 보관 (React state)
- IPC 호출 → Main 위임

---

## 5. 개발 단계별 설계

---

### Phase 0 — Foundation ✅ 완료

**목표:** 프로젝트 뼈대 구성

| 체크 | 항목 |
|------|------|
| ✅ | Electron + React + TypeScript 셋업 |
| ✅ | `electron-vite` 빌드 파이프라인 |
| ✅ | `src/shared/types.ts` — 전체 타입 정의 |
| ✅ | `schemas/*.schema.json` — JSON 스키마 |
| ✅ | `src/preload/index.ts` — IPC 브릿지 |
| ✅ | `tsconfig.json` — strict 모드 |

**품질 게이트:**
- TypeScript 빌드 오류 0건
- 스키마 검증 스크립트(`scripts/validate-schemas.mjs`) 통과

---

### Phase 1 — 테스트케이스 임포트 & 검토 ✅ 완료

**목표:** GPT 생성 JSON을 업로드하고 사람이 검토

**UI 화면: Tab 1 — 테스트케이스 검토**

```
┌─────────────────────────────────────────┐
│ [JSON 업로드 버튼]   [검토 상태 필터]     │
│                                         │
│ TC_ID | 대분류 | 시나리오 | 리스크 | 자동화 | 상태  │
│ ──────────────────────────────────────  │
│ TC_001-001 | ... | LOW | ✅ | DRAFT      │
│ TC_001-002 | ... | HIGH | ❌ | APPROVED  │
│                                         │
│ [일괄 승인]  [일괄 제외]  [다음 단계 →]  │
└─────────────────────────────────────────┘
```

| 체크 | 항목 |
|------|------|
| ✅ | `testcaseImport.ts` — JSON 파싱 + Zod 유효성 검사 |
| ✅ | TC_ID 형식 검사 (`TC_\d{3}-\d{3}`) |
| ✅ | TC_ID 중복 검사 |
| ✅ | 리스크 수준/자동화 여부 표시 |
| ✅ | ReviewStatus 변경 UI |
| 🔲 | 검토 결과 로컬 저장 (Phase 6에서 SQLite 연동) |

**품질 게이트:**
- 잘못된 JSON 업로드 시 사용자 친화적 오류 메시지
- TC_ID 중복 시 경고 표시
- PROHIBITED 리스크는 자동화 대상에서 자동 제외

---

### Phase 2 — DOM 캡처 ✅ 완료

**목표:** 대상 URL의 DOM을 자동 요약하여 GPT에 전달할 수 있는 구조화 JSON 생성

**UI 화면: Tab 2 — DOM 캡처**

```
┌─────────────────────────────────────────┐
│ 대상 URL: [___________________________]  │
│ [DOM 자동 캡처]   또는   [JSON 직접 업로드] │
│                                         │
│ 캡처 결과:                               │
│ - 요소 수: 142개                         │
│ - 폼: 3개                               │
│ - 페이지 제목: ...                       │
│                                         │
│ [DOM 요약 JSON 다운로드]  [다음 단계 →]   │
└─────────────────────────────────────────┘
```

| 체크 | 항목 |
|------|------|
| ✅ | `playwrightDomCapture.ts` — URL → `DomSummary` |
| ✅ | 요소 최대 250개 제한 |
| ✅ | `el_0001` 형식 ID 자동 부여 |
| ✅ | 접근성 역할(role) 분류 |
| ✅ | JSON 직접 업로드 대안 경로 |
| 🔲 | 로그인 필요 페이지 처리 (계정 정보 입력 후 캡처) |
| 🔲 | 다중 페이지 DOM 캡처 (Phase 6) |

**품질 게이트:**
- elementId 중복 없음
- 캡처 실패 시 오류 메시지 + 수동 업로드로 폴백
- DOM JSON이 `schemas/dom-summary.schema.json` 통과

---

### Phase 3 — 실행계획 임포트 & Playwright 실행 ✅ 완료

**목표:** GPT 생성 실행계획을 리스크 검증 후 Playwright로 실행

**UI 화면: Tab 3 — 실행계획 검토**

```
┌─────────────────────────────────────────┐
│ [실행계획 JSON 업로드]                   │
│                                         │
│ TC_ID | 상태 | 신뢰도 | 단계 수 | 리스크  │
│ ─────────────────────────────────────── │
│ TC_001-001 | READY | 0.92 | 5 | LOW     │
│ TC_001-003 | NEEDS_MAPPING_REVIEW | ...  │
│                                         │
│ [실행 가능 TC만 보기]  [다음 단계 →]     │
└─────────────────────────────────────────┘
```

**UI 화면: Tab 4 — 실행 모니터**

```
┌─────────────────────────────────────────┐
│ [브라우저 표시 여부 토글]                 │
│ [실행 시작]                              │
│                                         │
│ TC_001-001 ✅ COMPLETED (P)              │
│ TC_001-002 ⏳ 실행 중...                 │
│ TC_001-003 ❌ SCRIPT_FAILED             │
│                                         │
│ 진행: 12 / 30 (40%)                     │
└─────────────────────────────────────────┘
```

| 체크 | 항목 |
|------|------|
| ✅ | `domPlanImport.ts` — 실행계획 JSON 파싱 + 검증 |
| ✅ | elementId ↔ DOM 요소 존재 여부 교차 검증 |
| ✅ | `actionPolicy.ts` — 리스크 정책 적용 |
| ✅ | `executor.ts` — 14가지 액션 Playwright 실행 |
| ✅ | 실패 시 스크린샷 캡처 |
| ✅ | `ExecutionStatus` 별 결과 추적 |
| 🔲 | 실행 중 진행률 실시간 표시 (IPC 이벤트 스트림) |
| 🔲 | 개별 TC 재실행 기능 |

**품질 게이트:**
- PROHIBITED 리스크 TC는 실행 전 차단 (SKIPPED_RISK)
- HIGH 리스크 TC는 사용자 명시 승인 후 실행
- 알 수 없는 액션명은 실행 거부
- 알 수 없는 elementId는 MAPPING_FAILED 처리

---

### Phase 4 — 아티팩트 & 보고서 ✅ 완료

**목표:** 실행 결과를 파일로 저장하고 HTML 보고서 생성

**출력 구조:**
```
Documents/AutoWebTesting/runs/RUN-20260514-143022/
├── run-result.json        # 전체 실행 결과
├── failure-package.json   # 실패 케이스 패키지 (GPT 분석용)
├── report.html            # HTML 요약 보고서
└── evidence/
    ├── TC_001-003_step4.png
    └── TC_002-001_step2.png
```

| 체크 | 항목 |
|------|------|
| ✅ | `runArtifacts.ts` — 타임스탬프 기반 폴더 생성 |
| ✅ | `run-result.json` 저장 |
| ✅ | `failure-package.json` 저장 (GPT 전달용) |
| ✅ | `report.html` 생성 (P/F/N/A 통계) |
| ✅ | 스크린샷 → `evidence/` 복사 |
| 🔲 | 실패 분석 JSON 업로드 → 보고서 반영 (Phase 5) |

**품질 게이트:**
- 결과 파일이 없을 경우 저장 전 오류 방지
- HTML 보고서가 브라우저에서 단독으로 열려야 함

---

### Phase 5 — Excel 보고서 & 실패 분석 🔲 예정

**목표:** 테스트케이스 Excel 내보내기 + GPT 실패 분석 결과 반영

| 체크 | 항목 |
|------|------|
| 🔲 | 실패 분석 JSON 업로드 (`schemas/failure-analysis.schema.json`) |
| 🔲 | 실패 상세 → TC 행에 반영 |
| 🔲 | 테스트케이스 Excel 내보내기 (ExcelJS) |
| 🔲 | 실행 결과 Excel 내보내기 |
| 🔲 | Evidence ZIP 패키징 |
| 🔲 | Tab 5 결과 요약 화면 완성 |

**UI 화면: Tab 5 — 결과 요약**

```
┌─────────────────────────────────────────┐
│  총 30건  P: 22  F: 5  N/A: 3           │
│  성공률: 73.3%                           │
│                                         │
│  실패 케이스:                             │
│  TC_001-003 | SCRIPT_FAILED | 원인: ... │
│  TC_002-001 | MAPPING_FAILED | 원인: .. │
│                                         │
│ [실패분석 JSON 업로드]                   │
│ [Excel 다운로드]  [HTML 열기]  [ZIP 생성] │
└─────────────────────────────────────────┘
```

**품질 게이트:**
- Excel 파일이 한글 Windows에서 깨지지 않아야 함 (UTF-8 BOM)
- 실패 분석 JSON이 TC_ID로 올바르게 매핑되어야 함

---

### Phase 6 — 프로젝트 관리 & 이력 🔲 예정

**목표:** SQLite 기반 프로젝트/런 이력 관리

**DB 스키마 (예정):**

```sql
projects (id, name, targetUrl, createdAt)
runs     (id, projectId, runId, startedAt, summary)
testcases(id, projectId, tcId, reviewStatus, ...)
```

| 체크 | 항목 |
|------|------|
| 🔲 | 프로젝트 생성/선택 화면 |
| 🔲 | 런 이력 목록 조회 |
| 🔲 | 런 결과 재조회 |
| 🔲 | TC 검토 상태 지속 저장 |
| 🔲 | IPC 채널 추가 (`project:*`, `run:*`) |

**품질 게이트:**
- DB 마이그레이션 스크립트 관리
- 앱 재시작 후 이전 상태 복원 가능

---

### Phase 7 — LLM API 직접 연동 🔲 미래

**목표:** GPT 웹 복붙 없이 Claude/OpenAI API 직접 호출

| 체크 | 항목 |
|------|------|
| 🔲 | API 키 입력 및 암호화 저장 |
| 🔲 | 테스트케이스 자동 생성 (API 호출) |
| 🔲 | 실행계획 자동 생성 (API 호출) |
| 🔲 | 실패 분석 자동화 |
| 🔲 | 기능목록 Excel 업로드 파싱 |
| 🔲 | IPC 채널 추가 (`llm:*`) |

**주의:**
- API 키는 Electron `safeStorage` 또는 OS 키체인에 저장
- LLM 응답은 GPT 웹 임포트와 동일한 스키마 검증 통과 필수

---

## 6. 상태 관리 설계

현재 React state로 관리. Phase 6 이후 DB 영속화.

```
AppState {
  testcases: TestCase[]          // Tab 1
  domSummary: DomSummary | null  // Tab 2
  executionPlans: ExecutionPlan[]// Tab 3
  runResults: ExecutionResult[]  // Tab 4
  failureAnalyses: FailureAnalysis[] // Tab 5
  currentRunId: string | null
}
```

**단방향 흐름:**
```
Tab1(TC검토) → Tab2(DOM캡처) → Tab3(실행계획) → Tab4(실행) → Tab5(결과)
```
각 탭은 이전 탭의 데이터를 소비. 뒤로 가도 데이터는 유지.

---

## 7. 에러 처리 전략

| 에러 유형 | 처리 방식 |
|-----------|----------|
| JSON 파싱 실패 | 사용자 친화적 메시지 + 줄 번호 표시 |
| 스키마 유효성 실패 | 실패 필드 목록 표시 |
| Playwright 타임아웃 | SCRIPT_FAILED + 스크린샷 + 에러 메시지 |
| elementId 불일치 | MAPPING_FAILED + 해당 단계 표시 |
| 파일 저장 실패 | 오류 메시지 + 재시도 버튼 |
| DOM 캡처 실패 | 수동 JSON 업로드로 폴백 안내 |

**원칙:** 오류가 발생해도 이미 처리된 결과는 보존. 부분 실패 허용.

---

## 8. 보안 고려사항

| 항목 | 방침 |
|------|------|
| Playwright sandbox | `sandbox: false` 유지 (Electron 필수), 대신 nodeIntegration은 false |
| LLM 출력 신뢰 | 항상 비신뢰 입력으로 처리. 스키마 검증 후 화이트리스트 액션만 실행 |
| 계정 정보 | LLM에 전달 금지. `valueSource` 변수명만 사용 |
| API 키 | Phase 7에서 `safeStorage` 암호화 저장 필수 |
| 임의 코드 실행 | GPT 출력에서 raw Playwright 코드 실행 절대 금지 |

---

## 9. 스킬(Skill) 배포 계획

앱 완성 후 Claude Code 스킬로 배포 가능한 항목:

### Skill 1: `autowebtest-generate`
**역할:** 기능목록 텍스트 입력 → 테스트케이스 JSON 자동 생성  
**트리거:** "테스트케이스 만들어줘", "TC 생성", "기능목록으로 테스트케이스"  
**동작:** `prompts/testcase-generation.prompt.md` 기반 Claude API 호출 → `schemas/testcase.schema.json` 검증

### Skill 2: `autowebtest-map`
**역할:** 승인된 TC + DOM 요약 → 실행계획 JSON 자동 생성  
**트리거:** "실행계획 만들어줘", "DOM 매핑", "Playwright 계획 생성"  
**동작:** `prompts/dom-mapping.prompt.md` 기반 Claude API 호출 → `schemas/execution-plan.schema.json` 검증

### Skill 3: `autowebtest-analyze`
**역할:** 실패 패키지 JSON → 실패 분석 리포트 생성  
**트리거:** "실패 분석", "테스트 실패 원인", "failure-package 분석"  
**동작:** `prompts/failure-analysis.prompt.md` 기반 Claude API 호출

### Skill 4: `autowebtest-review`
**역할:** 기존 런 결과를 요약하고 개선 제안  
**트리거:** "테스트 결과 검토", "실행 결과 분석"  
**동작:** `run-result.json` 파일 읽기 → 요약 보고서 생성

> **배포 조건:** Phase 7(LLM API 연동) 완료 후 스킬 패키징 적합.
> Skill 1~3은 `claude-api` 스킬 패턴 참고하여 구현.

---

## 10. 개발 품질을 높이는 권장 방법

### 10.1 모델 전략
```
/model opusplan   ← 아키텍처 결정, 새 Phase 시작 시
/model sonnet     ← 일반 코딩, 버그 수정 (기본값)
```

### 10.2 Phase 시작 전 체크리스트
- [ ] 이전 Phase의 품질 게이트 모두 통과했는가?
- [ ] 새 IPC 채널이 필요하면 `preload/index.ts`에 먼저 추가했는가?
- [ ] 새 타입이 필요하면 `shared/types.ts`에 먼저 정의했는가?
- [ ] 스키마 변경 시 `validate-schemas.mjs` 업데이트했는가?

### 10.3 Phase 완료 후 체크리스트
- [ ] TypeScript 빌드 오류 0건 (`npm run typecheck`)
- [ ] 샘플 JSON으로 스키마 검증 통과 (`npm run validate`)
- [ ] 새 기능이 `examples/*.sample.json`에 반영되었는가?
- [ ] 이 문서의 해당 Phase 체크박스 업데이트
- [ ] `/simplify` 스킬로 추가된 코드 품질 검토

### 10.4 코드 작성 원칙
- 에러 메시지는 **한국어**로 (UI 대상), 코드 주석은 **영어**로
- `any` 타입 사용 금지 — 명확한 타입 또는 `unknown` 사용
- IPC 핸들러에서 비즈니스 로직 작성 금지 — runner 모듈에 위임
- GPT 출력은 항상 `untrusted input`으로 취급

### 10.5 테스트 전략
```
Unit  → Zod 스키마 검증 함수, actionPolicy 규칙
E2E   → examples/*.sample.json 기반 전체 흐름 수동 검증
UI    → 각 Phase 완료 시 앱 실행하여 황금 경로 확인
```

---

## 11. 참조 문서

| 문서 | 내용 |
|------|------|
| [`data-schema.md`](data-schema.md) | JSON 스키마 상세 |
| [`risk-policy.md`](risk-policy.md) | 리스크 정책 |
| [`gpt-web-workflow.md`](gpt-web-workflow.md) | GPT 웹 임포트 단계별 절차 |
| [`product-requirements.md`](product-requirements.md) | 제품 요구사항 |
| [`prompt-specs.md`](prompt-specs.md) | LLM 프롬프트 명세 |
| [`architecture.md`](architecture.md) | 고수준 런타임 구조 |

---

*최종 수정: 2026-05-14*
