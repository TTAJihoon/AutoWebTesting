# AutoWebTesting 현재 작업 범위

## 현재 진행 상태

**Phase 1 — 문서/스키마 기반 구조 확정** 진행 중 (≈80% 완료)

### 완료
- ✅ ADR-006: JSON Schema = 사람용 계약, Zod = 런타임/TS 원천 (CI로 일치 검증)
- ✅ `docs/schemas/*.schema.json` 11개 모두 실제 필드 정의 (placeholder 교체)
- ✅ `docs/examples/*.sample.json` 12개 (모든 schema에 1개 이상의 sample)
- ✅ `src/shared/schemas/*.ts` 12개 Zod 스키마 + `index.ts` 작성
- ✅ `scripts/validate-schemas.mjs` 보강: ajv + Zod 양쪽 검증, examples 양방향 매칭
- ✅ `package.json`: `ajv`, `ajv-formats`, `tsx` 추가
- ✅ Phase 0.5 마이그레이션 단계 추가 ([`design/15-phase-roadmap.md`](design/15-phase-roadmap.md))

## Phase 1 — 완료 ✅

- ✅ `npm run schema:check` 통과 (36/36)
- ✅ `npm run typecheck` 오류 0

## Phase 0.5 — 진행 중

### 완료
- ✅ `src/shared/types.ts` → `src/shared/legacy/types.ts` 이동 (git rename)
- ✅ `src/shared/constants.ts` → `src/shared/legacy/constants.ts` 이동
- ✅ 새 `src/shared/types.ts`, `constants.ts`는 legacy를 re-export하는 진입점 (기존 코드 import 경로 변경 불필요)
- ✅ 기존 코드 typecheck 통과 (마이그레이션 후에도 동작 보존)

### 남은 작업 (Phase 0.5)
- ⬜ IPC 채널 명칭 정리: 신규 채널 추가 (`run:start` 등), 기존 `run:execute-plans` 등은 deprecated alias로 유지하다 다음 phase에서 제거
- ⬜ 기존 runner/main/renderer 모듈을 신규 `src/shared/schemas/*` 기반으로 점진 재구성
  - 새 코드는 schemas 사용, 기존 코드는 legacy 사용
  - 또는 신규 네임스페이스(`src/runner/v2/`)에 새 구조 작성 후 단계 교체
- ⬜ 샘플 JSON 기반 통합 테스트 (1개 TC 실행)

---

## 작업 대상 문서

- `design/03-data-schema-overview.md`
- `design/05-execution-plan.md`
- `design/10-ipc-contract.md`
- `design/11-runner-design.md`
- `design/15-phase-roadmap.md`
- `decisions/ADR-006-schema-as-contract-zod-as-runtime.md`

## 참조 문서

- `design/02-ai-exploration.md`
- `design/04-page-state-dom.md`
- `design/06-risk-policy.md`
- `design/07-test-data.md`
- `design/08-assertion-policy.md`
- `design/09-run-result-failure.md`

## 이번 작업에서 수정하지 않을 문서

- `design/00-product-overview.md`
- `design/01-mvp-scope.md`
- `design/12-gpt-web-workflow.md`
- `design/13-prompt-specs.md`
- `design/14-storage-structure.md`

## 현재 확정된 방향

1. MVP는 URL 기반 AI 탐색형 CRUD 테스트 자동화 도구를 목표로 한다.
2. GPT Web Import Mode는 비용 절감을 위한 초기 운용 방식이다.
3. 궁극적 방향은 API Mode 또는 내부 AI 서버 기반 탐색 루프다.
4. 테스트케이스 생성에는 기능목록/매뉴얼뿐 아니라 실제 웹 형상 정보가 포함된다.
5. Observation은 DOM Summary를 우선 사용하고, 필요한 경우 masked screenshot을 보강한다.
6. 실행은 이미지 좌표가 아니라 ElementRegistry와 selectorCandidates 기반으로 수행한다.
7. 위험 행동은 생성 전 지침, 생성 후 검증, 실행 직전 차단의 3단계로 통제한다.
8. Delete는 AutoWebTesting이 생성한 데이터에 대해서만 제한적으로 허용한다.
9. SMS/메일/푸시 등 외부 발송은 HIGH로 보고 명시 승인 후 실행한다.
10. P/F는 `executionStatus = COMPLETED`인 경우에만 부여한다.
11. JSON Schema는 사람용 계약, Zod는 런타임/TS 원천. `schema:check`가 일치를 보장.
