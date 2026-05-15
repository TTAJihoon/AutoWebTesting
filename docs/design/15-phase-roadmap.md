---
status: draft
lastUpdated: 2026-05-15
related:
  - 02-ai-exploration.md
  - 05-execution-plan.md
  - 11-runner-design.md
---

# 15. 개발 Phase Roadmap

## Phase 0 — Foundation

- Electron + React + TypeScript 설정
- IPC Bridge 구성
- TypeScript strict 설정
- 공통 타입과 스키마 기본 구성

## Phase 0.5 — 기존 코드 정리 및 마이그레이션

기존 `src/` 코드는 단일 화면 + 단순 elementId 기준이다. 새 설계는 다중 PageState, ElementRegistry 분리, ExplorationSession 등 신규 개념이 다수 도입된다.

### 작업

- `src/shared/types.ts` 기존 타입 → `src/shared/schemas/*.ts` (Zod) 기반으로 점진 교체
  - 기존 타입은 `legacy.ts`로 분리하여 단계적 제거
- 기존 `src/runner/` 모듈은 신규 모듈과 병행하다가 검증 후 교체
  - 신규 모듈은 `src/runner/v2/` 또는 별도 네임스페이스로 분리
- IPC 채널 명칭 정리 (구버전 `run:execute-plans` → 신버전 `run:start` 등)
- `schemas/`(프로젝트 루트) → `docs/schemas/`로 이전 검토
- `prompts/` 폴더 위치/내용 갱신 (다중 PageState 반영)

### 완료 조건 (DoD)

- [ ] 기존 `executor.ts`/`playwrightDomCapture.ts` 기능을 신규 구조에서 동일하게 실행 가능
- [ ] 통합 테스트(샘플 JSON 기반 1개 TC 실행) 통과
- [ ] 마이그레이션 완료 모듈 목록 문서화

## Phase 1 — 문서/스키마 기반 구조 확정

### 작업

- INDEX.md / WORKING.md 적용
- JSON Schema 11개 실제 필드까지 정의 (placeholder 제거)
- `src/shared/schemas/*.ts` Zod 스키마 작성 (JSON Schema와 일치)
- `src/shared/types.ts`를 `z.infer`로 단계 교체
- 샘플 JSON 작성 (`examples/*.sample.json`)
- CI 스크립트: JSON Schema + Zod + 샘플 양방향 검증

### 완료 조건 (DoD)

- [ ] `schemas/` 11개 모두 `additionalProperties: false` 또는 명시적 허용으로 정리
- [ ] 모든 schema 파일에 최소 1개 이상 `examples/*.sample.json` 존재
- [ ] `npm run schema:check`가 JSON Schema + Zod 둘 다 통과
- [ ] ADR-006 일치 검증 스크립트 통과
- [ ] `src/shared/schemas/`에 Zod 스키마 11개 존재
- [ ] `src/shared/types.ts`가 Zod에서 `z.infer`로 도출되도록 갱신

## Phase 2 — 프로젝트와 테스트 데이터

- 프로젝트 저장 구조 적용
- TestDataProfile 정의
- secret/testData/generated/file 변수 구분
- 테스트 데이터 snapshot 저장

## Phase 3 — DOM Summary와 ElementRegistry

- URL 접속
- 로그인 처리
- DOM Summary 생성
- ElementRegistry 생성
- masked screenshot 생성

## Phase 4 — AI 탐색 세션

- ExplorationSession 생성
- Observation 생성
- AiDecision import/API adapter 구조
- ExplorationMemory 관리
- CandidateFeature / CandidateCrudFlow 생성

## Phase 5 — ExecutionPlan import/검증

- ExecutionPlan JSON 업로드
- PageState/elementId 검증
- action whitelist 검증
- assertion 구조 검증
- riskCheck 검증

## Phase 6 — Playwright Runner

- ACTION Step 실행
- TABLE_ACTION 실행
- ASSERTION 실행
- expectedTransition 확인
- Dialog 처리
- 실행 이벤트 스트림

## Phase 7 — 결과 저장과 보고서

- RunResult 저장
- FailurePackage 생성
- HTML 보고서
- Excel 보고서
- Evidence ZIP

## Phase 8 — 실패분석

- 실패분석 JSON 업로드
- FailureCause enum 매핑
- 실패 상세 보고서 반영
- 개선 제안 표시

## Phase 9 — API Mode / 내부 AI 서버

- LLM Adapter 구조
- OpenAI/Claude/Internal AI Server 연동
- 탐색 루프 자동화
- 비용/보안 정책 적용
