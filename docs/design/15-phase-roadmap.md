---
status: reviewing
lastUpdated: 2026-05-15
related:
  - 01-mvp-scope.md
  - 03-data-schema-overview.md
---

# Phase 로드맵

## 1. 개발 Phase 재정의

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
- `secret`/`testData`/`generated`/`file` 변수 구분
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

### Phase 9 — AI 탐색 및 API Mode

- ExplorationSession 도입
- Observation, AiDecision, ExplorationAction 구현
- API Mode (LLM API 직접 호출)
- API 키 입력 및 `safeStorage` 암호화 저장
- AI 탐색 루프 및 자동 PageState 캡처

---

## 2. 품질 게이트

### 2.1 공통 품질 게이트

- TypeScript 빌드 오류 0건
- `any` 타입 사용 금지
- 스키마 검증 통과
- 샘플 JSON 검증 통과
- UI 오류 메시지는 한국어
- 코드 주석은 영어
- GPT 출력은 항상 비신뢰 입력으로 처리

### 2.2 DOM/매핑 품질 게이트

- elementId 중복 없음
- PageState별 elementId namespace 분리
- Element Registry 생성 성공
- selectorCandidates 최소 1개 이상
- 매핑 실패 시 원인 로그 저장

### 2.3 실행 품질 게이트

- PROHIBITED 자동 실행 차단
- HIGH 실행 전 명시 승인
- 알 수 없는 action 거부
- 알 수 없는 elementId는 `MAPPING_FAILED`
- assertion 없는 TC는 자동 P/F 판단 금지
- 실패 시 스크린샷 저장

### 2.4 보고서 품질 게이트

- 실행 상태와 P/F 결과 분리
- 실패 원인 enum 표시
- 증적 파일 경로 연결
- 실행 당시 URL, 앱 버전, schemaVersion 기록
- 한글 Windows에서 Excel 깨짐 방지

---

## 3. Phase 진행 체크리스트

각 Phase 완료 시 다음을 점검한다.

**Phase 시작 전**

- [ ] 이전 Phase의 품질 게이트 모두 통과
- [ ] 새 IPC 채널 필요 시 `preload/index.ts`에 먼저 추가
- [ ] 새 타입 필요 시 `shared/types.ts`에 먼저 정의
- [ ] 스키마 변경 시 `validate-schemas.mjs` 업데이트
- [ ] 관련 design 문서를 stable 상태로 검토

**Phase 완료 후**

- [ ] `npm run typecheck` 오류 0건
- [ ] `npm run schema:check` 통과
- [ ] `examples/*.sample.json` 업데이트
- [ ] 관련 design 문서 체크박스 갱신
- [ ] WORKING.md 다음 작업 갱신

---

## 4. 현재 확정된 설계 결정

| 번호 | 결정 |
|---:|---|
| 1 | MVP는 단일 화면이 아니라 CRUD 중심 다중 화면 흐름을 지원한다. |
| 2 | API Mode는 후순위이며, MVP는 GPT Web Import Mode 중심이다. |
| 3 | `elementId`는 GPT 참조용 ID이고 실제 실행은 내부 selectorCandidates로 수행한다. |
| 4 | 테스트 데이터는 `secret`, `testData`, `generated`, `file`로 구분한다. |
| 5 | 자동 P/F 판정은 구조화된 assertion을 기준으로 한다. |
| 6 | 실행 이벤트 스트림을 도입한다. |
| 7 | 리스크 키워드 탐지를 적용한다. |
| 8 | 실패 원인은 enum으로 고정한다. |
| 9 | 저장 구조는 프로젝트 기준으로 통일한다. |
| 10 | GPT Web Import 결과는 안전한 범위에서 보정한다. |
| 11 | AI 탐색은 Phase 9 도입, MVP는 GPT Web Import 기반 다중 화면 자동화. |
| 12 | 위험 행동은 생성 전 지침 + 생성 후 검증 + 실행 직전 차단의 3단계로 통제한다. |
| 13 | Delete는 AutoWebTesting이 생성한 데이터에 대해서만 제한적으로 허용한다. |
| 14 | Observation은 DOM 우선 + 선택적 이미지 보강 방식으로 한다. |

---

## 5. 다음 단계 검토 안건

1. JSON Schema 파일 구성 (`schemas/*.schema.json` 갱신)
2. TypeScript 타입 구조 갱신 (`src/shared/types.ts`)
3. IPC 계약 재정리 (`preload/index.ts`, `main/index.ts`)
4. Runner 실행 흐름 구현
5. AI 탐색 루프와 ExecutionPlan 생성 프롬프트 구조 (Phase 9 준비)
6. 샘플 JSON 세트 (`examples/*.sample.json`)
7. Phase별 구현 순서 재정의
