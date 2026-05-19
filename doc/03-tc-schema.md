# TC 스키마 + 설계 기법 + 검증 규칙

> Stage 2 (TC 설계) + Stage 3 (V1~V5) + Stage 4 (Reviewer Gate) 산출의 컬럼·타입·검증 통합 정의.

---

## 1. 스키마 개요

TC 1행 = 시험 1건. 5개 그룹 컬럼:

| 그룹 | 컬럼 | 채워지는 시점 |
|---|---|---|
| **G1. 표준 양식** | tc_id, 대분류, 중분류, 소분류, scenario(시나리오), precondition, expected | Stage 2 |
| **G2. 설계 근거** | requirement_id, design_technique, source_quote | Stage 2 |
| **G3. 신뢰도** | gen_confidence, exec_confidence | Stage 2 / Stage 5 |
| **G4. Gate** | review_status, reviewer_note, reviewer_id | Stage 4 |
| **G5. 실행 결과** | actual, result, failure_reason | Stage 5 / Stage 6 |

---

## 2. 컬럼 정의

### G1. 표준 양식

| 컬럼 | 타입 | 필수 | 설명 | 예시 |
|---|---|---|---|---|
| `tc_id` | string | ✓ | `TC-XXX-YYY` 형식. XXX=leaf 일련번호, YYY=변형 번호. (D9·D17·D18·D19) | `TC-007-002` |
| `대분류` | string | ✓ | 기능리스트 대분류명 | `회원관리` |
| `중분류` | string | ✓ | 기능리스트 중분류명 | `비밀번호` |
| `소분류` | string | ✓ | 기능리스트 최하위(leaf) 분류명 | `변경` |
| `scenario` | string | ✓ | 테스트 시나리오 (자연어 한 문장) | `현재 비밀번호 입력 후 새 비밀번호로 변경` |
| `precondition` | string | ✓ | 사전입력조건. 없으면 "없음" | `회원가입 완료 + 로그인 상태` |
| `expected` | string | ✓ | 기대 출력 값. 객관 검증 가능한 형태 | `"비밀번호가 변경되었습니다" 토스트 + 로그아웃` |

### G2. 설계 근거

| 컬럼 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `requirement_id` | string | ✓ | 기능리스트의 해당 행 식별자 (대>중>소 경로) |
| `design_technique` | enum | ✓ | §3의 7가지 중 하나 |
| `source_quote` | string | ✓ | 매뉴얼 원문 발췌 + 위치, 또는 `INFERRED: <근거>` |

### G3. 신뢰도

| 컬럼 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `gen_confidence` | float [0,1] | ✓ | TC 생성 시 신뢰도. source_quote 명료성 + 명세 강도. 소수점 2자리 |
| `exec_confidence` | float [0,1] | 실행 후 ✓ | 실행 시 신뢰도. 셀렉터 안정성 + 재시도 + oracle 명료성 |

### G4. Reviewer Gate

| 컬럼 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `review_status` | enum | ✓ | `approved` / `edited` / `rejected` / `pending` |
| `reviewer_note` | string | 선택 | 검토자 메모 |
| `reviewer_id` | string | 변경 시 ✓ | 검토자 식별 |

### G5. 실행 결과

| 컬럼 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `actual` | string | 실행 후 ✓ | 실제 출력 |
| `result` | enum | 실행 후 ✓ | `pass` / `fail` / `blocked` / `not_executed` |
| `failure_reason` | string | result=fail 시 ✓ | 4축: 실제출력 / 차이 / 원인후보 / 재시도이력 |

---

## 3. 7가지 설계 기법 (design_technique enum)

| 기법 | 정의 | 적용 가이드 |
|---|---|---|
| `happy_path` | 정상 흐름. 명세대로 입력 → 명세대로 출력 | leaf당 최소 1개 |
| `equivalence` | 등가 분할. 입력 도메인 별 대표값 | 도메인 2개 이상이면 도메인별 1개 |
| `boundary` | 경계값. min/max ± 1, 빈 입력, 길이 상한 | 수치·길이 제약 있으면 양 경계 |
| `negative_basic` | 기본 부정. 명세 위반 입력에 대한 에러 | leaf당 1개 이상 |
| `negative_deep` | 심층 부정. 권한 우회, XSS, 메시지 적절성 | 위험 영역 1개 이상 |
| `state_transition` | 상태 전이. 다단계 워크플로 step 누락·역순 | 워크플로 기능 시 |
| `cross_feature` | 기능 결합. 의미 연관 기능과의 조합 | 기능 간 연관 시 |

**원칙:** 적용 불가능한 기법은 강제하지 않음. 단 `happy_path`는 모든 leaf에 필수.

**TC 수 가이드 (강제 아님):**
- 단순 CRUD: 3~8개
- 입력 검증 포함: 8~20개
- 다단계 워크플로: 15~40개
- 제품당 약 200~500개

---

## 4. 데이터 타입·형식 규칙

| 항목 | 규칙 |
|---|---|
| 인코딩 | UTF-8 (Excel은 BOM 포함) |
| 줄바꿈 | `\n` (Excel wrap text) |
| 셀 최대 길이 | Excel 한도 32,767자 |
| `tc_id` 정규식 | `^TC-\d{3}-\d{3}$` |
| enum 표기 | snake_case (소문자 + `_`) |
| confidence 범위 | `[0.0, 1.0]`, 소수점 2자리 |
| 빈 셀 정책 | 필수 컬럼 비면 V1 reject. 선택 컬럼은 빈 문자열 허용 |

---

## 5. V1~V5 검증 규칙 (Stage 3 자동 실행)

| # | 검증 | 대상 | 규칙 | 실패 시 |
|---|---|---|---|---|
| **V1** | 필수 컬럼 | G1 + G2 + G3의 gen_confidence | 빈 셀 금지 | 행 reject + 재호출 |
| **V2** | source_quote 실재성 | G2.source_quote | 매뉴얼 텍스트에 substring 일치 (공백·줄바꿈 정규화) | `INFERRED: verification failed` 마킹 + Gate 우선 |
| **V3** | INFERRED 비율 | G2.source_quote | 전체 TC 중 INFERRED 비율 ≤ 임계 | 임계 초과 시 재호출 (PoC-α 결과 41.5% → 임계 정량은 PoC-β 후 결정) |
| **V4** | 기법 분포 | G2.design_technique | `happy_path` 비율 ≤ 50% | 초과 시 "기법 다양화" prompt 재호출 |
| **V5** | leaf 커버리지 | G2.requirement_id | 기능리스트의 모든 leaf에 최소 1개 TC | 누락 leaf 명시 재호출 |

**재호출 prompt 패턴 (TC_REGEN Contract 사용):**
실패 TC만 추출 + 실패 사유 명시 + 수정 지침. 동일 사이클 최대 3회.

**3회 초과 처리:**
- 해당 항목 `INFERRED: max_retry_exceeded` 마킹
- Reviewer Gate 강제 검토 대상으로 표시

---

## 6. Excel 4시트 구조

`data/runs/<run-id>/tc_final.xlsx`:

| 시트 | 컬럼 | 목적 |
|---|---|---|
| **표준 양식** | G1 + G5 핵심 | 시험원이 익숙한 형태 (인증 산출물 추출용) |
| **AWT_Meta** | G2 + G3 + G4 | 설계 근거 + 신뢰도 + Gate 결정 |
| **Layer3_Aids** | 수동 시험 보조 자료 인덱스 | L3 영역 시험원 참고 |
| **Metrics** | 25023 메트릭 % 자동 계산 | Phase 2 |

→ 시트 1은 `tc_id`로 다른 시트와 join. 인증 제출 시 시트 1만 추출 가능.

---

## 7. Stage별 적용 시점 정리

| Stage | 채워지는 컬럼 | 채우는 주체 |
|---|---|---|
| Stage 2 종료 | G1 + G2 + G3.gen_confidence | LLM (TC_DESIGN) |
| Stage 3 종료 | G2.source_quote 보강 (V2 실패 시 INFERRED 마킹) | AWT 로컬 |
| Stage 4 종료 | G4 (review_status, reviewer_note, reviewer_id) | 사용자 |
| Stage 5 종료 | G3.exec_confidence + G5 (actual, result) | Playwright 로컬 |
| Stage 6 종료 | G5.failure_reason | LLM (FAILURE_ANALYSIS) |
| Stage 7 종료 | 모든 컬럼 동결 | AWT 로컬 |

---

## 8. 미해결 (운영 단계 결정)

| ID | 질문 |
|---|---|
| Q-SCH-1 | `precondition`을 별도 시트로 정규화할지 (반복 제거) |
| Q-SCH-2 | `steps`의 DSL화 — Playwright 자동 변환 위해 정형 단계 형식 도입할지 |
| Q-SCH-3 | `failure_reason` 4축의 컬럼 분리 vs 한 컬럼 |
| Q-SCH-4 | `reviewer_id` 익명화 여부 |
| Q-PA-1 | source_quote grep의 fuzzy 허용 범위 (한자↔한글, 띄어쓰기) |
| Q-PA-2 | V3 INFERRED 임계 정량 (PoC-β 후 확정) |
| Q-PA-3 | 재호출 3회 상한 적정성 |
