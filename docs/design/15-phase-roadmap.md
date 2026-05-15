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

## Phase 1 — 문서/스키마 기반 구조 확정

- INDEX.md / WORKING.md 적용
- JSON Schema 초안 작성
- TypeScript 타입 초안 작성
- 샘플 JSON 작성

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
